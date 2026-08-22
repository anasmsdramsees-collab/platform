"""Model version and lifecycle contracts (spec §19).

Two rules shape this module:

- **A model version cannot activate without evaluation and explicit promotion**
  (safety invariant 15). `ModelVersion` therefore cannot be constructed in a
  promoted state without evaluation metrics; promotion is a separate, recorded
  act.
- **A model cannot raise its own permission level** (safety invariant 14). The
  learning mode lives on the *home*, not the model, and only advances one step
  at a time through `can_transition`, so no model output can widen its own
  authority.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any, Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from syltra_contracts.enums import LearningMode, PrivacyClass


class ModelStatus(StrEnum):
    TRAINED = "TRAINED"
    """Artifact exists and has been evaluated, but is not serving."""
    ACTIVE = "ACTIVE"
    """Promoted and serving for this home."""
    ROLLED_BACK = "ROLLED_BACK"
    SUSPENDED = "SUSPENDED"
    """Withdrawn from service after drift, degradation or a safety event."""


class ModelType(StrEnum):
    ROUTINE_BASELINE = "ROUTINE_BASELINE"
    TEMPERATURE_PREFERENCE = "TEMPERATURE_PREFERENCE"
    ENERGY_ANOMALY = "ENERGY_ANOMALY"
    OCCUPANCY_FUSION = "OCCUPANCY_FUSION"
    RECOMMENDATION_ACCEPTANCE = "RECOMMENDATION_ACCEPTANCE"
    DEVICE_ANOMALY = "DEVICE_ANOMALY"


class TrainingWindow(BaseModel):
    model_config = ConfigDict(frozen=True)

    start: datetime
    end: datetime
    sample_count: int = Field(ge=0)
    distinct_days: int = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self) -> "TrainingWindow":
        if self.end < self.start:
            msg = "training window end precedes its start"
            raise ValueError(msg)
        return self


class ModelCard(BaseModel):
    """Human-readable account of what a model is and is not (spec §19.3)."""

    model_config = ConfigDict(extra="allow", frozen=True)

    summary: str
    intended_use: str
    out_of_scope_use: str
    training_data: str
    evaluation: str
    limitations: str
    ethical_and_safety_notes: str
    privacy_classification: PrivacyClass = PrivacyClass.HOUSEHOLD_PRIVATE


class ModelVersion(BaseModel):
    """Everything spec §19.3 requires a model version to record."""

    model_config = ConfigDict(extra="allow", frozen=True)

    model_id: UUID
    home_id: str
    name: str
    version: str
    model_type: ModelType
    feature_schema_version: str
    training_code_revision: str
    training_window: TrainingWindow
    evaluation_metrics: dict[str, float]
    calibration: dict[str, float] = Field(default_factory=dict)
    runtime: str = "onnxruntime"
    supported_hardware: list[str] = Field(default_factory=lambda: ["cpu"])
    created_at: datetime
    promoted_at: datetime | None = None
    rollback_target: str | None = None
    status: ModelStatus = ModelStatus.TRAINED
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    card: ModelCard
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at", "promoted_at")
    @classmethod
    def _timezone_aware(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            msg = "model timestamps must be timezone-aware (UTC storage)"
            raise ValueError(msg)
        return v

    @field_validator("evaluation_metrics")
    @classmethod
    def _evaluation_required(cls, v: dict[str, float]) -> dict[str, float]:
        # Safety invariant 15: a version without evaluation cannot exist in a
        # form the registry could later promote.
        if not v:
            msg = "a model version must record evaluation metrics"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def _active_versions_are_promoted(self) -> "ModelVersion":
        if self.status is ModelStatus.ACTIVE and self.promoted_at is None:
            msg = "an ACTIVE model version must record when it was promoted"
            raise ValueError(msg)
        return self

    @property
    def reference(self) -> str:
        return f"{self.name}@{self.version}"


# ── learning-mode progression (spec §19.2) ──

_ALLOWED_TRANSITIONS: Final[dict[LearningMode, frozenset[LearningMode]]] = {
    LearningMode.DISABLED: frozenset({LearningMode.OBSERVE}),
    LearningMode.OBSERVE: frozenset({LearningMode.SHADOW, LearningMode.DISABLED}),
    LearningMode.SHADOW: frozenset(
        {LearningMode.RECOMMEND, LearningMode.OBSERVE, LearningMode.SUSPENDED}
    ),
    LearningMode.RECOMMEND: frozenset(
        {LearningMode.APPROVAL_REQUIRED, LearningMode.SHADOW, LearningMode.SUSPENDED}
    ),
    LearningMode.APPROVAL_REQUIRED: frozenset(
        {
            LearningMode.AUTHORIZED_AUTOMATION,
            LearningMode.RECOMMEND,
            LearningMode.SUSPENDED,
        }
    ),
    LearningMode.AUTHORIZED_AUTOMATION: frozenset(
        {LearningMode.APPROVAL_REQUIRED, LearningMode.SUSPENDED}
    ),
    # Suspension is a safety state: recovery re-enters the ladder low down and
    # earns its way back up, never returning straight to automation.
    LearningMode.SUSPENDED: frozenset({LearningMode.OBSERVE, LearningMode.DISABLED}),
}


class LearningModeTransitionError(ValueError):
    """Raised when a mode change would skip a required stage."""


def can_transition(current: LearningMode, target: LearningMode) -> bool:
    """True if the home may move directly from ``current`` to ``target``.

    Spec §19.2: no home may skip from OBSERVE to AUTHORIZED_AUTOMATION. The
    ladder is enforced here so no service can invent its own progression.
    """
    if current is target:
        return True
    return target in _ALLOWED_TRANSITIONS[current]


def assert_transition(current: LearningMode, target: LearningMode) -> None:
    if not can_transition(current, target):
        msg = (
            f"cannot move from {current.value} to {target.value}: "
            "the adaptive lifecycle must advance one stage at a time (spec §19.2)"
        )
        raise LearningModeTransitionError(msg)


def allows_recommendations(mode: LearningMode) -> bool:
    """Modes in which a recommendation may be shown to a user at all."""
    return mode in {
        LearningMode.RECOMMEND,
        LearningMode.APPROVAL_REQUIRED,
        LearningMode.AUTHORIZED_AUTOMATION,
    }


def allows_execution(mode: LearningMode) -> bool:
    """Modes in which an approved action may execute.

    Even here, execution still requires a policy decision — this only reports
    that the lifecycle stage does not forbid it outright.
    """
    return mode in {LearningMode.APPROVAL_REQUIRED, LearningMode.AUTHORIZED_AUTOMATION}


def allows_unattended_execution(mode: LearningMode) -> bool:
    """The only mode permitting configured low-risk actions without approval."""
    return mode is LearningMode.AUTHORIZED_AUTOMATION
