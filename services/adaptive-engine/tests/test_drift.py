"""Drift detection and automatic suspension (spec §19.4).

Suspension already existed and an operator could already trigger it. What these
tests cover is the platform noticing on its own — a model that has lost the
household's trust standing itself down before anyone has to ask.
"""

from datetime import UTC, datetime
from typing import Any

import pytest
from syltra_adaptive_engine.drift import (
    DriftReason,
    DriftThresholds,
    ModelHealth,
    assess,
)
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_contracts import ModelStatus
from syltra_testing import comfort_history

NOW = datetime.now(tz=UTC)
HOME = "home_001"
MODEL = "temperature_preference"


class NullPublisher:
    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


def health(**overrides: Any) -> ModelHealth:
    base = ModelHealth(model_name=MODEL, home_id=HOME)
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


# ── the seven spec §19.4 conditions ──


def test_a_healthy_model_is_left_alone() -> None:
    verdict = assess(health(accepted=10, rejected=1, actions_dispatched=10))
    assert not verdict.suspend
    assert verdict.reasons == []


@pytest.mark.safety
def test_repeated_rejection_suspends() -> None:
    verdict = assess(health(accepted=1, rejected=8, undone=2))
    assert verdict.suspend
    assert DriftReason.ACCEPTANCE_RATE_TOO_LOW in verdict.reasons
    assert verdict.evidence["acceptance_rate"] < 0.4


def test_a_handful_of_rejections_is_not_yet_evidence() -> None:
    # Two rejections out of two is noise, not a verdict.
    verdict = assess(health(accepted=0, rejected=2))
    assert not verdict.suspend


@pytest.mark.safety
def test_a_high_manual_override_rate_suspends() -> None:
    # The household keeps undoing what the model does.
    verdict = assess(health(actions_dispatched=10, manual_overrides=8))
    assert verdict.suspend
    assert DriftReason.OVERRIDE_RATE_TOO_HIGH in verdict.reasons


def test_a_few_overrides_are_not_yet_evidence() -> None:
    verdict = assess(health(actions_dispatched=2, manual_overrides=2))
    assert not verdict.suspend


@pytest.mark.safety
def test_repeated_inference_failure_suspends() -> None:
    verdict = assess(health(consecutive_inference_failures=3))
    assert verdict.suspend
    assert DriftReason.REPEATED_INFERENCE_FAILURE in verdict.reasons


@pytest.mark.safety
def test_feature_distribution_shift_suspends() -> None:
    verdict = assess(health(feature_shift=0.8))
    assert verdict.suspend
    assert DriftReason.FEATURE_DISTRIBUTION_SHIFT in verdict.reasons


@pytest.mark.safety
def test_invalid_calibration_suspends() -> None:
    verdict = assess(health(calibration_valid=False))
    assert verdict.suspend
    assert DriftReason.CALIBRATION_INVALID in verdict.reasons


@pytest.mark.safety
def test_a_single_stale_required_sensor_suspends() -> None:
    # A model reasoning about a capability it can no longer observe is
    # guessing, however good it was yesterday.
    verdict = assess(health(stale_required_sensors=1))
    assert verdict.suspend
    assert DriftReason.REQUIRED_SENSORS_UNAVAILABLE in verdict.reasons


@pytest.mark.safety
def test_a_changed_device_mapping_suspends() -> None:
    verdict = assess(health(trained_mapping_revision="rev_a", device_mapping_revision="rev_b"))
    assert verdict.suspend
    assert DriftReason.DEVICE_MAPPING_CHANGED in verdict.reasons


def test_an_unchanged_mapping_does_not_suspend() -> None:
    verdict = assess(health(trained_mapping_revision="rev_a", device_mapping_revision="rev_a"))
    assert not verdict.suspend


def test_every_spec_condition_has_a_reason_code() -> None:
    # Spec §19.4 lists seven conditions; each must be expressible.
    assert len(DriftReason) == 7


def test_all_reasons_are_reported_not_just_the_first() -> None:
    # An operator reading the audit record should see everything that was
    # wrong, not the first thing found.
    verdict = assess(
        health(accepted=0, rejected=10, consecutive_inference_failures=5, feature_shift=0.9)
    )
    assert len(verdict.reasons) >= 3
    assert "suspending:" in verdict.explain()


def test_thresholds_are_configurable() -> None:
    lenient = DriftThresholds(min_acceptance_rate=0.05, min_feedback_for_acceptance=100)
    assert not assess(health(accepted=1, rejected=9), lenient).suspend


# ── the service acts on the verdict ──


def trained_service() -> AdaptiveEngineService:
    service = AdaptiveEngineService(NullPublisher())  # type: ignore[arg-type]
    for event in comfort_history(days=21):
        service.observe(event)
    service.train_home(HOME)
    service.registry.promote(HOME, MODEL, "1.0.0")
    return service


@pytest.mark.safety
def test_a_drifted_model_is_suspended_without_anyone_asking() -> None:
    service = trained_service()
    assert service.registry.active(HOME, MODEL) is not None

    for _ in range(8):
        service.record_feedback(HOME, MODEL, "REJECT")
    verdicts = service.check_drift(HOME, NOW)

    assert verdicts[MODEL].suspend
    assert service.registry.active(HOME, MODEL) is None
    assert MODEL in service.suspended_models(HOME)


@pytest.mark.safety
def test_suspension_is_audited_with_its_reasons() -> None:
    service = trained_service()
    for _ in range(8):
        service.record_feedback(HOME, MODEL, "UNDO")
    service.check_drift(HOME, NOW)

    entry = next(e for e in service.registry.audit if e.action == "MODEL_SUSPENDED")
    assert "ACCEPTANCE_RATE_TOO_LOW" in entry.reason
    assert entry.actor == "adaptive-engine:drift"


def test_a_healthy_model_keeps_serving() -> None:
    service = trained_service()
    for _ in range(10):
        service.record_feedback(HOME, MODEL, "ACCEPT")
    verdicts = service.check_drift(HOME, NOW)

    assert not verdicts[MODEL].suspend
    assert service.registry.active(HOME, MODEL) is not None


@pytest.mark.safety
def test_stale_sensors_suspend_a_serving_model() -> None:
    service = trained_service()
    service.record_stale_sensors(HOME, MODEL, 1)
    service.check_drift(HOME, NOW)
    assert service.registry.active(HOME, MODEL) is None


def test_inference_success_clears_the_failure_streak() -> None:
    service = trained_service()
    for _ in range(2):
        service.record_inference_failure(HOME, MODEL)
    service.record_inference_success(HOME, MODEL)
    service.record_inference_failure(HOME, MODEL)

    assert not service.check_drift(HOME, NOW)[MODEL].suspend
    assert service.registry.active(HOME, MODEL) is not None


@pytest.mark.safety
def test_a_suspended_model_is_not_revived_by_later_acceptance() -> None:
    # Whatever caused the drift has not necessarily gone away. Coming back
    # requires a new version promoted through the same gate.
    service = trained_service()
    for _ in range(8):
        service.record_feedback(HOME, MODEL, "REJECT")
    service.check_drift(HOME, NOW)
    assert service.registry.active(HOME, MODEL) is None

    for _ in range(20):
        service.record_feedback(HOME, MODEL, "ACCEPT")
    service.check_drift(HOME, NOW)
    assert service.registry.active(HOME, MODEL) is None

    version = service.registry.get(HOME, MODEL, "1.0.0")
    assert version is not None
    assert version.status is ModelStatus.SUSPENDED


def test_homes_are_isolated() -> None:
    service = trained_service()
    for _ in range(8):
        service.record_feedback("home_other", MODEL, "REJECT")
    service.check_drift("home_other", NOW)
    # The other home's feedback must not suspend this home's model.
    assert service.registry.active(HOME, MODEL) is not None


def test_checking_a_home_with_no_models_is_harmless() -> None:
    service = AdaptiveEngineService(NullPublisher())  # type: ignore[arg-type]
    assert service.check_drift("quiet_home", NOW) == {}
