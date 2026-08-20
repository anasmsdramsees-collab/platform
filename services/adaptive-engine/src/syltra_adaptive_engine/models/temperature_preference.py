"""Temperature preference baseline (spec §14.4 model 3).

Contextual regression: what setpoint does this household choose, given the hour,
the weekday, and the indoor temperature at the time? Trained on the setpoints
people actually selected — `climate.target_temperature` changes — so the model
learns preference, not thermostat behavior.

Ridge regression rather than plain least squares: household data is small and
its features correlate (hour and indoor temperature move together across a day),
which makes an unregularized fit swing wildly on a handful of samples. Ridge
keeps the coefficients modest, and a modest wrong answer is a far better failure
mode for something that proposes temperatures.

The output is always clamped to the capability's declared safe range, so no
extrapolation can propose an unsafe setpoint even if the fit is poor.
"""

from datetime import UTC, datetime
from typing import Any

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error

from syltra_adaptive_engine.features import DataRequirement
from syltra_adaptive_engine.models.base import (
    BaselineModel,
    InsufficientCapabilityData,
    Prediction,
)
from syltra_contracts import ModelType
from syltra_contracts.capability_definitions import get_definition

TARGET_CAPABILITY = "climate.target_temperature"
INDOOR_CAPABILITY = "environment.temperature"

FEATURE_COLUMNS = ("hour_sin", "hour_cos", "is_weekend_num", "indoor_temperature")
"""Pinned order — the model is trained and served with exactly this layout."""


class TemperaturePreferenceModel(BaselineModel):
    name = "temperature_preference"
    model_type = ModelType.TEMPERATURE_PREFERENCE

    def __init__(self, alpha: float = 1.0) -> None:
        super().__init__()
        self._alpha = alpha
        self._estimator: Ridge | None = None
        definition = get_definition(TARGET_CAPABILITY)
        self._minimum = float(definition.minimum if definition.minimum is not None else 16)
        self._maximum = float(definition.maximum if definition.maximum is not None else 30)

    @property
    def requirement(self) -> DataRequirement:
        return DataRequirement(
            min_samples=20, min_distinct_days=5, min_distinct_time_buckets=3
        )

    @property
    def estimator(self) -> Ridge | None:
        return self._estimator

    def build_design_matrix(self, frame: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Join setpoint changes with the indoor temperature at that time.

        Cyclical hour encoding (sin/cos) so 23:00 and 01:00 are near neighbours
        rather than opposite extremes — a linear model given a raw hour would
        treat midnight as maximally distant from 23:00.
        """
        setpoints = frame.filter(
            (pl.col("capability") == TARGET_CAPABILITY) & pl.col("numeric_value").is_not_null()
        ).sort("occurred_at")
        if setpoints.is_empty():
            return np.empty((0, len(FEATURE_COLUMNS))), np.empty(0)

        indoor = (
            frame.filter(
                (pl.col("capability") == INDOOR_CAPABILITY)
                & pl.col("numeric_value").is_not_null()
            )
            .select(["occurred_at", "numeric_value"])
            .rename({"numeric_value": "indoor_temperature"})
            .sort("occurred_at")
        )

        if indoor.is_empty():
            joined = setpoints.with_columns(
                pl.lit(None, dtype=pl.Float64).alias("indoor_temperature")
            )
        else:
            # As-of join: the most recent indoor reading at or before each
            # setpoint change — the temperature the occupant was reacting to.
            joined = setpoints.join_asof(indoor, on="occurred_at", strategy="backward")

        median_indoor = joined.select(pl.col("indoor_temperature").median()).item()
        fallback = float(median_indoor) if median_indoor is not None else 24.0
        prepared = joined.with_columns(
            (2 * np.pi * pl.col("hour") / 24).sin().alias("hour_sin"),
            (2 * np.pi * pl.col("hour") / 24).cos().alias("hour_cos"),
            pl.col("is_weekend").cast(pl.Float64).alias("is_weekend_num"),
            pl.col("indoor_temperature").fill_null(fallback),
        )
        features = prepared.select(list(FEATURE_COLUMNS)).to_numpy()
        target = prepared.select("numeric_value").to_numpy().ravel()
        return features, target

    def _fit(self, frame: pl.DataFrame) -> tuple[dict[str, Any], dict[str, float]]:
        features, target = self.build_design_matrix(frame)
        if features.shape[0] < self.requirement.min_samples:
            # The frame met the global requirement but holds too few setpoint
            # changes to learn a preference from.
            raise InsufficientCapabilityData(
                "INSUFFICIENT_SETPOINT_SAMPLES",
                int(features.shape[0]),
                self.requirement.min_samples,
            )

        estimator = Ridge(alpha=self._alpha)
        estimator.fit(features, target)
        self._estimator = estimator

        predicted = estimator.predict(features)
        mae = float(mean_absolute_error(target, predicted))
        residual_std = float(np.std(target - predicted))
        parameters = {
            "alpha": self._alpha,
            "feature_columns": list(FEATURE_COLUMNS),
            "coefficients": [round(float(c), 6) for c in estimator.coef_],
            "intercept": round(float(estimator.intercept_), 6),
            "target_mean": round(float(np.mean(target)), 4),
            "residual_std": round(residual_std, 4),
            "clamp": [self._minimum, self._maximum],
        }
        metrics = {
            "mae": round(mae, 4),
            "residual_std": round(residual_std, 4),
            "sample_count": float(features.shape[0]),
            "target_std": round(float(np.std(target)), 4),
        }
        return parameters, metrics

    def predict(self, moment: datetime, indoor_temperature: float | None = None) -> Prediction:
        """Preferred setpoint for the given moment and indoor temperature."""
        self._require_fitted()
        if self._estimator is None:
            msg = "temperature preference model has no fitted estimator"
            raise RuntimeError(msg)

        local = moment.astimezone(UTC)
        indoor = (
            float(indoor_temperature)
            if indoor_temperature is not None
            else float(self._parameters.get("target_mean", 24.0))
        )
        row = np.array(
            [
                [
                    np.sin(2 * np.pi * local.hour / 24),
                    np.cos(2 * np.pi * local.hour / 24),
                    1.0 if local.weekday() >= 5 else 0.0,
                    indoor,
                ]
            ]
        )
        raw = float(self._estimator.predict(row)[0])
        clamped = min(max(raw, self._minimum), self._maximum)

        # Confidence falls as residual spread grows: a model that fits the
        # household tightly earns more trust than one that barely explains it.
        residual_std = float(self._parameters.get("residual_std", 1.0))
        confidence = round(max(0.0, min(1.0, 1.0 / (1.0 + residual_std))), 4)

        reason_codes = ["REPEATED_USER_PATTERN", "CONTEXTUAL_PREFERENCE"]
        if clamped != round(raw, 6):
            reason_codes.append("CLAMPED_TO_SAFE_RANGE")

        return Prediction(
            value=round(clamped, 1),
            confidence=confidence,
            reason_codes=reason_codes,
            detail={
                "raw_prediction": round(raw, 3),
                "indoor_temperature": indoor,
                "residual_std": residual_std,
                "safe_range": [self._minimum, self._maximum],
            },
        )
