"""Energy anomaly baseline (spec §14.4 model 5).

Robust statistics first, Isolation Forest later — the spec's ordering, and the
right one. A household's power history contains the very spikes we want to
detect, so mean and standard deviation are dragged upward by the anomalies
themselves. Median and MAD are not: a handful of extreme readings barely move
them, which is exactly the property an anomaly baseline needs.

Scoring uses the modified z-score:

    z = 0.6745 · (x − median) / MAD

The 0.6745 constant makes MAD a consistent estimator of the standard deviation
for normally distributed data, so the familiar "3 sigma" intuition still applies.

**This model never opens a breaker.** Spec §20.6 is explicit: do not
automatically open a breaker based only on anomaly-model output. It reports an
anomaly with suspected contributors; what happens next is a policy decision.
"""

from typing import Any

import numpy as np
import polars as pl

from syltra_adaptive_engine.features import DataRequirement
from syltra_adaptive_engine.models.base import (
    BaselineModel,
    InsufficientCapabilityData,
    Prediction,
)
from syltra_contracts import ModelType

POWER_CAPABILITY = "energy.power"

DEFAULT_THRESHOLD = 3.5
"""Modified z-score beyond which a reading is called anomalous."""

_MAD_SCALE = 0.6745
_MIN_MAD = 1e-6


class EnergyAnomalyModel(BaselineModel):
    name = "energy_anomaly"
    model_type = ModelType.ENERGY_ANOMALY

    def __init__(self, threshold: float = DEFAULT_THRESHOLD) -> None:
        super().__init__()
        if threshold <= 0:
            msg = "anomaly threshold must be positive"
            raise ValueError(msg)
        self._threshold = threshold

    @property
    def requirement(self) -> DataRequirement:
        # Robust statistics need enough history to establish a baseline, and
        # enough days that a single unusual day cannot define "normal".
        return DataRequirement(
            min_samples=50, min_distinct_days=3, min_distinct_time_buckets=6
        )

    def _fit(self, frame: pl.DataFrame) -> tuple[dict[str, Any], dict[str, float]]:
        readings = frame.filter(
            (pl.col("capability") == POWER_CAPABILITY) & pl.col("numeric_value").is_not_null()
        ).select("numeric_value")

        if readings.height < self.requirement.min_samples:
            # Plenty of household events, but not enough power readings among
            # them: refuse rather than register a model with no baseline.
            raise InsufficientCapabilityData(
                "INSUFFICIENT_POWER_SAMPLES", readings.height, self.requirement.min_samples
            )

        values = readings.to_numpy().ravel().astype(float)
        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        # A perfectly flat history has MAD 0, which would make every deviation
        # infinitely anomalous. Floor it so a constant baseline is simply
        # uninformative rather than a false-positive generator.
        effective_mad = max(mad, _MIN_MAD)

        scores = np.abs(_MAD_SCALE * (values - median) / effective_mad)
        flagged = int(np.sum(scores > self._threshold))

        parameters = {
            "median": round(median, 4),
            "mad": round(mad, 6),
            "effective_mad": round(effective_mad, 6),
            "threshold": self._threshold,
            "capability": POWER_CAPABILITY,
        }
        metrics = {
            "sample_count": float(len(values)),
            "median": round(median, 4),
            "mad": round(mad, 6),
            "flagged_in_training": float(flagged),
            "flagged_fraction": round(flagged / len(values), 4),
            "p95": round(float(np.percentile(values, 95)), 4),
        }
        return parameters, metrics

    def score(self, watts: float) -> float:
        """Modified z-score for a single reading."""
        self._require_fitted()
        median = float(self._parameters["median"])
        mad = float(self._parameters["effective_mad"])
        return float(abs(_MAD_SCALE * (watts - median) / mad))

    def predict(self, watts: float, contributors: list[str] | None = None) -> Prediction:
        """Report whether a reading is anomalous, and why.

        Never an action: spec §20.6 forbids opening a breaker on anomaly-model
        output alone.
        """
        self._require_fitted()
        z = self.score(watts)
        anomalous = z > self._threshold
        median = float(self._parameters["median"])

        # Confidence saturates: twice the threshold is as certain as this model
        # gets, rather than growing without bound on an extreme reading.
        confidence = round(min(z / (2 * self._threshold), 1.0), 4) if anomalous else 0.0

        reason_codes = []
        if anomalous:
            reason_codes.append(
                "ENERGY_ABOVE_BASELINE" if watts > median else "ENERGY_BELOW_BASELINE"
            )
            reason_codes.append("ROBUST_STATISTICS")
        else:
            reason_codes.append("WITHIN_BASELINE")

        return Prediction(
            value=anomalous,
            confidence=confidence,
            reason_codes=reason_codes,
            detail={
                "watts": watts,
                "modified_z_score": round(z, 4),
                "threshold": self._threshold,
                "baseline_median": median,
                "suspected_contributors": contributors or [],
                "advisory_only": True,
            },
        )
