"""SYLTRA Adaptive Engine (spec §14.4).

Learns household routines and comfort preferences from local history and
detects non-safety anomalies. Everything it produces is **advisory**: the
engine emits `Recommendation` objects, a type with no path to an actuator
(safety invariant 1). Reaching a device requires a policy decision (Phase 5)
and then an action request — three separate types, so no shortcut exists.

Models progress through the lifecycle in spec §19.2 and start in SHADOW, where
predictions are recorded but never shown or executed. A version cannot serve
until it has been evaluated and explicitly promoted (safety invariant 15), and
nothing here can widen its own authority (safety invariant 14).
"""

from syltra_adaptive_engine.features import (
    FEATURE_SCHEMA_VERSION,
    DataRequirement,
    DataSufficiency,
    FeatureSchemaError,
    extract_events,
    validate_schema,
)
from syltra_adaptive_engine.models import (
    BaselineModel,
    EnergyAnomalyModel,
    Prediction,
    RoutineBaselineModel,
    TemperaturePreferenceModel,
    TrainingResult,
)

__all__ = [
    "FEATURE_SCHEMA_VERSION",
    "BaselineModel",
    "DataRequirement",
    "DataSufficiency",
    "EnergyAnomalyModel",
    "FeatureSchemaError",
    "Prediction",
    "RoutineBaselineModel",
    "TemperaturePreferenceModel",
    "TrainingResult",
    "extract_events",
    "validate_schema",
]
