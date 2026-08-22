"""Drift detection and automatic suspension (spec §19.4).

Spec §19.4 lists seven conditions under which a model must be suspended. The
registry could already suspend, and an operator could already trigger it — what
was missing is the platform noticing on its own.

The design principle: **a model that has lost the household's trust should stand
itself down before anyone has to ask.** Every signal below is something the
platform already records for other reasons, so detection costs nothing extra.

Suspension is deliberately easier to trigger than to reverse. A suspended model
stops serving immediately; bringing it back requires training a new version and
promoting it through the same gate as any other, because whatever caused the
drift has not necessarily gone away.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)

DRIFT_RULES_VERSION = "1.0.0"


class DriftReason(StrEnum):
    """The spec §19.4 conditions, as machine-readable codes."""

    FEATURE_DISTRIBUTION_SHIFT = "FEATURE_DISTRIBUTION_SHIFT"
    DEVICE_MAPPING_CHANGED = "DEVICE_MAPPING_CHANGED"
    ACCEPTANCE_RATE_TOO_LOW = "ACCEPTANCE_RATE_TOO_LOW"
    OVERRIDE_RATE_TOO_HIGH = "OVERRIDE_RATE_TOO_HIGH"
    REPEATED_INFERENCE_FAILURE = "REPEATED_INFERENCE_FAILURE"
    CALIBRATION_INVALID = "CALIBRATION_INVALID"
    REQUIRED_SENSORS_UNAVAILABLE = "REQUIRED_SENSORS_UNAVAILABLE"


@dataclass(frozen=True)
class DriftThresholds:
    """Configured limits (spec §19.4: "beyond configured limits")."""

    min_acceptance_rate: float = 0.4
    """Below this, the household is telling us the model is wrong."""
    min_feedback_for_acceptance: int = 5
    """Two rejections out of two is noise, not evidence."""
    max_override_rate: float = 0.5
    """Manual overrides against the model's own actions."""
    min_actions_for_override_rate: int = 4
    max_consecutive_inference_failures: int = 3
    max_feature_shift: float = 0.35
    """Normalized distance between training and live feature distributions."""
    max_stale_required_sensors: int = 0
    """Any required sensor going stale is enough: a model reasoning about a
    capability it can no longer observe is guessing."""


@dataclass
class ModelHealth:
    """What the platform has observed about a serving model."""

    model_name: str
    home_id: str
    accepted: int = 0
    rejected: int = 0
    undone: int = 0
    actions_dispatched: int = 0
    manual_overrides: int = 0
    consecutive_inference_failures: int = 0
    feature_shift: float = 0.0
    calibration_valid: bool = True
    stale_required_sensors: int = 0
    device_mapping_revision: str | None = None
    trained_mapping_revision: str | None = None
    last_evaluated_at: datetime | None = None

    @property
    def feedback_count(self) -> int:
        return self.accepted + self.rejected + self.undone

    @property
    def acceptance_rate(self) -> float | None:
        if self.feedback_count == 0:
            return None
        return self.accepted / self.feedback_count

    @property
    def override_rate(self) -> float | None:
        if self.actions_dispatched == 0:
            return None
        return self.manual_overrides / self.actions_dispatched


@dataclass
class DriftVerdict:
    suspend: bool
    reasons: list[DriftReason] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def reason_codes(self) -> list[str]:
        return [reason.value for reason in self.reasons]

    def explain(self) -> str:
        if not self.suspend:
            return "model health is within configured limits"
        return "suspending: " + ", ".join(self.reason_codes)


def assess(health: ModelHealth, thresholds: DriftThresholds | None = None) -> DriftVerdict:
    """Decide whether a model should stand itself down (spec §19.4).

    Every condition is checked, not short-circuited: an operator reading the
    audit record should see *all* the reasons, not just the first one found.
    """
    limits = thresholds or DriftThresholds()
    reasons: list[DriftReason] = []
    evidence: dict[str, Any] = {}

    acceptance = health.acceptance_rate
    if (
        acceptance is not None
        and health.feedback_count >= limits.min_feedback_for_acceptance
        and acceptance < limits.min_acceptance_rate
    ):
        reasons.append(DriftReason.ACCEPTANCE_RATE_TOO_LOW)
        evidence["acceptance_rate"] = round(acceptance, 3)
        evidence["feedback_count"] = health.feedback_count

    override = health.override_rate
    if (
        override is not None
        and health.actions_dispatched >= limits.min_actions_for_override_rate
        and override > limits.max_override_rate
    ):
        reasons.append(DriftReason.OVERRIDE_RATE_TOO_HIGH)
        evidence["override_rate"] = round(override, 3)

    if health.consecutive_inference_failures >= limits.max_consecutive_inference_failures:
        reasons.append(DriftReason.REPEATED_INFERENCE_FAILURE)
        evidence["consecutive_inference_failures"] = health.consecutive_inference_failures

    if health.feature_shift > limits.max_feature_shift:
        reasons.append(DriftReason.FEATURE_DISTRIBUTION_SHIFT)
        evidence["feature_shift"] = round(health.feature_shift, 3)

    if not health.calibration_valid:
        reasons.append(DriftReason.CALIBRATION_INVALID)
        evidence["calibration_valid"] = False

    if health.stale_required_sensors > limits.max_stale_required_sensors:
        # A model reasoning about a capability it can no longer observe is
        # guessing, however good it was yesterday.
        reasons.append(DriftReason.REQUIRED_SENSORS_UNAVAILABLE)
        evidence["stale_required_sensors"] = health.stale_required_sensors

    if (
        health.trained_mapping_revision is not None
        and health.device_mapping_revision is not None
        and health.trained_mapping_revision != health.device_mapping_revision
    ):
        # The home's devices changed materially since training. The model's
        # features may no longer mean what they meant.
        reasons.append(DriftReason.DEVICE_MAPPING_CHANGED)
        evidence["trained_mapping"] = health.trained_mapping_revision
        evidence["current_mapping"] = health.device_mapping_revision

    return DriftVerdict(suspend=bool(reasons), reasons=reasons, evidence=evidence)
