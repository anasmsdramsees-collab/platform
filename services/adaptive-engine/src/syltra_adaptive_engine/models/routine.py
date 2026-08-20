"""Routine baseline (spec §14.4 model 1).

Weekday and time buckets with exponentially weighted frequency: a device action
that happened at 18:30 on the last four Mondays is a routine; the same action
once, three weeks ago, is not.

Recency weighting matters because households change. A pattern from last week
should outweigh the same pattern from two months ago, so each occurrence is
weighted by ``decay ** age_in_days``. The result is a frequency in [0, 1] per
(capability, time bucket), which doubles as the prediction confidence.
"""

from datetime import UTC, datetime
from typing import Any

import polars as pl

from syltra_adaptive_engine.features import BUCKETS_PER_WEEK, DataRequirement, time_bucket
from syltra_adaptive_engine.models.base import (
    BaselineModel,
    InsufficientCapabilityData,
    Prediction,
)
from syltra_contracts import ModelType

DEFAULT_DECAY = 0.97
"""Per-day decay: an occurrence 30 days old carries ~40% of today's weight."""

MIN_ROUTINE_STRENGTH = 0.25
"""Below this, a pattern is coincidence rather than routine."""


class RoutineBaselineModel(BaselineModel):
    name = "routine_baseline"
    model_type = ModelType.ROUTINE_BASELINE

    def __init__(self, decay: float = DEFAULT_DECAY, capability: str = "light.power") -> None:
        super().__init__()
        if not 0.0 < decay <= 1.0:
            msg = "decay must fall in (0, 1]"
            raise ValueError(msg)
        self._decay = decay
        self._capability = capability

    @property
    def requirement(self) -> DataRequirement:
        # A routine needs repetition across days, not just a busy afternoon.
        return DataRequirement(
            min_samples=30, min_distinct_days=7, min_distinct_time_buckets=3
        )

    def _fit(self, frame: pl.DataFrame) -> tuple[dict[str, Any], dict[str, float]]:
        relevant = frame.filter(
            (pl.col("capability") == self._capability) & (pl.col("bool_value") == True)  # noqa: E712
        )
        reference = frame.select(pl.col("occurred_at").max()).item()

        if relevant.is_empty():
            # No activations of the tracked capability: there is no routine to
            # describe, so refuse rather than register an empty model.
            raise InsufficientCapabilityData("NO_CAPABILITY_ACTIVATIONS", 0, 1)

        weighted = relevant.with_columns(
            (
                self._decay
                ** ((pl.lit(reference) - pl.col("occurred_at")).dt.total_seconds() / 86400.0)
            ).alias("weight")
        )
        per_bucket = (
            weighted.group_by("time_bucket")
            .agg(pl.col("weight").sum().alias("weighted_count"))
            .sort("time_bucket")
        )
        # Normalize against the busiest bucket so strength is comparable
        # across homes and devices regardless of absolute activity levels.
        peak = per_bucket.select(pl.col("weighted_count").max()).item() or 1.0
        buckets = {
            int(row["time_bucket"]): round(float(row["weighted_count"]) / float(peak), 4)
            for row in per_bucket.iter_rows(named=True)
        }
        strong = [s for s in buckets.values() if s >= MIN_ROUTINE_STRENGTH]
        metrics = {
            "observed_buckets": float(len(buckets)),
            "strong_buckets": float(len(strong)),
            "peak_strength": 1.0 if buckets else 0.0,
            "mean_strength": round(sum(buckets.values()) / len(buckets), 4) if buckets else 0.0,
        }
        parameters = {
            "capability": self._capability,
            "decay": self._decay,
            "reference_time": reference.isoformat(),
            "buckets": buckets,
        }
        return parameters, metrics

    def predict(self, moment: datetime) -> Prediction:
        """Strength of the routine at ``moment``."""
        self._require_fitted()
        bucket = time_bucket(moment.astimezone(UTC))
        buckets: dict[int, float] = self._parameters["buckets"]
        strength = float(buckets.get(bucket, 0.0))
        is_routine = strength >= MIN_ROUTINE_STRENGTH
        return Prediction(
            value=is_routine,
            confidence=round(strength, 4),
            reason_codes=["REPEATED_USER_PATTERN"] if is_routine else ["NO_ESTABLISHED_PATTERN"],
            detail={
                "time_bucket": bucket,
                "strength": round(strength, 4),
                "capability": self._parameters["capability"],
                "threshold": MIN_ROUTINE_STRENGTH,
            },
        )

    def strongest_buckets(self, limit: int = 5) -> list[tuple[int, float]]:
        """The most established routine slots, for explanation and debugging."""
        self._require_fitted()
        buckets: dict[int, float] = self._parameters["buckets"]
        ranked = sorted(buckets.items(), key=lambda item: (-item[1], item[0]))
        return [(b, s) for b, s in ranked[:limit] if s >= MIN_ROUTINE_STRENGTH]

    @staticmethod
    def describe_bucket(bucket: int) -> str:
        """Human-readable slot label, e.g. 'Mon 18:30'."""
        bucket %= BUCKETS_PER_WEEK
        day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][bucket // 48]
        minutes = (bucket % 48) * 30
        return f"{day} {minutes // 60:02d}:{minutes % 60:02d}"
