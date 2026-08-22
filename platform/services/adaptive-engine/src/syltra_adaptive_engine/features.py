"""Versioned feature pipeline (spec §22 Phase 4).

Turns local event history into model features. Three properties are
load-bearing:

- **The schema is versioned and explicit.** Every model records the
  ``FEATURE_SCHEMA_VERSION`` it was trained against, and inference validates the
  incoming frame against the same schema. A silently reordered or retyped column
  cannot reach a model.
- **Extraction is deterministic.** The same events produce the same frame, in
  the same row order, on any machine — otherwise "reproducible training"
  (a Phase 4 acceptance criterion) is unverifiable.
- **Insufficient data is a first-class outcome**, not an exception to handle
  later. Spec §14.4 forbids training before minimum sample and diversity
  requirements are met, so the pipeline reports why it cannot proceed.

Polars is the dataframe layer (ADR-006); the conversion to NumPy happens at the
scikit-learn boundary, which is also where column order is pinned.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import polars as pl
from polars.datatypes import DataTypeClass

from syltra_contracts import EventEnvelope

# Polars schemas mix dtype instances (Datetime) with dtype classes (String).
PolarsDataType = pl.DataType | DataTypeClass

FEATURE_SCHEMA_VERSION = "1.0"
"""Bump on any change to column names, types, or semantics."""

# Columns every extracted frame carries, in this exact order.
EVENT_FRAME_SCHEMA: dict[str, PolarsDataType] = {
    "occurred_at": pl.Datetime(time_unit="us", time_zone="UTC"),
    "home_id": pl.String,
    "device_id": pl.String,
    "room_id": pl.String,
    "capability": pl.String,
    "numeric_value": pl.Float64,
    "bool_value": pl.Boolean,
    "string_value": pl.String,
    "quality": pl.Float64,
    "weekday": pl.Int8,          # 0 = Monday
    "hour": pl.Int8,
    "time_bucket": pl.Int16,     # index of a 30-minute bucket within the week
    "is_weekend": pl.Boolean,
}

BUCKET_MINUTES = 30
BUCKETS_PER_DAY = 24 * 60 // BUCKET_MINUTES
BUCKETS_PER_WEEK = BUCKETS_PER_DAY * 7


@dataclass(frozen=True)
class DataRequirement:
    """Minimum data a model needs before training may begin (spec §14.4)."""

    min_samples: int
    min_distinct_days: int
    min_distinct_time_buckets: int = 1

    def evaluate(self, frame: pl.DataFrame) -> "DataSufficiency":
        if frame.is_empty():
            return DataSufficiency(
                sufficient=False,
                sample_count=0,
                distinct_days=0,
                distinct_time_buckets=0,
                reasons=["NO_DATA"],
                requirement=self,
            )
        samples = frame.height
        days = frame.select(pl.col("occurred_at").dt.date().n_unique()).item()
        buckets = frame.select(pl.col("time_bucket").n_unique()).item()
        reasons: list[str] = []
        if samples < self.min_samples:
            reasons.append("INSUFFICIENT_SAMPLES")
        if days < self.min_distinct_days:
            reasons.append("INSUFFICIENT_DAY_DIVERSITY")
        if buckets < self.min_distinct_time_buckets:
            reasons.append("INSUFFICIENT_TIME_DIVERSITY")
        return DataSufficiency(
            sufficient=not reasons,
            sample_count=samples,
            distinct_days=int(days),
            distinct_time_buckets=int(buckets),
            reasons=reasons,
            requirement=self,
        )


@dataclass(frozen=True)
class DataSufficiency:
    sufficient: bool
    sample_count: int
    distinct_days: int
    distinct_time_buckets: int
    reasons: list[str]
    requirement: DataRequirement

    def explain(self) -> str:
        if self.sufficient:
            return (
                f"{self.sample_count} samples across {self.distinct_days} days "
                "meets the training requirement"
            )
        return (
            f"cannot train: {', '.join(self.reasons)} "
            f"({self.sample_count}/{self.requirement.min_samples} samples, "
            f"{self.distinct_days}/{self.requirement.min_distinct_days} days)"
        )


class FeatureSchemaError(ValueError):
    """Raised when a frame does not match the declared feature schema."""


def time_bucket(moment: datetime) -> int:
    """Index of the 30-minute bucket within the week (0 … 335)."""
    return moment.weekday() * BUCKETS_PER_DAY + (moment.hour * 60 + moment.minute) // BUCKET_MINUTES


def empty_frame() -> pl.DataFrame:
    return pl.DataFrame(schema=EVENT_FRAME_SCHEMA)


def extract_events(events: Iterable[EventEnvelope]) -> pl.DataFrame:
    """Build the canonical feature frame from normalized events.

    Rows are sorted by ``(occurred_at, device_id, capability)`` so the frame is
    byte-identical for identical input regardless of iteration order.
    """
    rows: list[dict[str, Any]] = []
    for event in events:
        if event.capability is None:
            continue
        moment = event.occurred_at.astimezone(UTC)
        value = event.value
        rows.append(
            {
                "occurred_at": moment,
                "home_id": event.home_id,
                "device_id": event.subject.device_id or "",
                "room_id": event.subject.room_id or "",
                "capability": event.capability,
                "numeric_value": (
                    float(value) if isinstance(value, int | float) and not isinstance(value, bool)
                    else None
                ),
                "bool_value": value if isinstance(value, bool) else None,
                "string_value": value if isinstance(value, str) else None,
                "quality": float(event.quality),
                "weekday": moment.weekday(),
                "hour": moment.hour,
                "time_bucket": time_bucket(moment),
                "is_weekend": moment.weekday() >= 5,
            }
        )
    if not rows:
        return empty_frame()
    frame = pl.DataFrame(rows, schema=EVENT_FRAME_SCHEMA)
    return frame.sort(["occurred_at", "device_id", "capability"])


def validate_schema(frame: pl.DataFrame) -> None:
    """Reject a frame whose columns or types differ from the declared schema."""
    expected = list(EVENT_FRAME_SCHEMA)
    actual = list(frame.columns)
    if actual != expected:
        msg = (
            f"feature frame columns do not match schema v{FEATURE_SCHEMA_VERSION}: "
            f"expected {expected}, got {actual}"
        )
        raise FeatureSchemaError(msg)
    for column, dtype in EVENT_FRAME_SCHEMA.items():
        if frame.schema[column] != dtype:
            msg = (
                f"column {column!r} has type {frame.schema[column]}, "
                f"schema v{FEATURE_SCHEMA_VERSION} requires {dtype}"
            )
            raise FeatureSchemaError(msg)


def for_capability(frame: pl.DataFrame, capability: str) -> pl.DataFrame:
    return frame.filter(pl.col("capability") == capability)


def for_home(frame: pl.DataFrame, home_id: str) -> pl.DataFrame:
    """Per-home isolation at the feature layer (spec §14.4: per-home models)."""
    return frame.filter(pl.col("home_id") == home_id)


def to_matrix(frame: pl.DataFrame, columns: Sequence[str]) -> Any:
    """Convert to a NumPy matrix with column order pinned by ``columns``.

    Passing the ordering explicitly is what stops a reordered frame from
    silently feeding a model features in the wrong positions.
    """
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        msg = f"feature frame is missing required columns: {missing}"
        raise FeatureSchemaError(msg)
    return frame.select(list(columns)).to_numpy()


def training_window(frame: pl.DataFrame) -> tuple[datetime, datetime]:
    """First and last observation in the frame."""
    if frame.is_empty():
        now = datetime.now(tz=UTC)
        return now, now
    start = frame.select(pl.col("occurred_at").min()).item()
    end = frame.select(pl.col("occurred_at").max()).item()
    return start, end
