"""Recommendation and model-lifecycle contract tests (spec §15, §19).

These carry the safety invariants that keep machine learning advisory:
1 (a recommendation is never a command), 3 (a stale recommendation cannot
execute), 14 (a model cannot raise its own permission level) and 15 (a version
cannot activate without evaluation and explicit promotion).
"""

from datetime import UTC, datetime, timedelta
from itertools import pairwise
from uuid import uuid4

import pytest
from pydantic import ValidationError
from syltra_contracts import (
    LearningMode,
    LearningModeTransitionError,
    ModelCard,
    ModelReference,
    ModelStatus,
    ModelType,
    ModelVersion,
    Recommendation,
    RecommendationTarget,
    TrainingWindow,
    allows_execution,
    allows_recommendations,
    allows_unattended_execution,
    assert_transition,
    can_transition,
)

pytestmark = pytest.mark.contract

NOW = datetime(2026, 8, 18, 15, 30, 0, tzinfo=UTC)


def recommendation(**overrides: object) -> Recommendation:
    payload: dict[str, object] = {
        "recommendation_id": uuid4(),
        "home_id": "home_001",
        "recommendation_type": "climate.precondition",
        "created_at": NOW,
        "expires_at": NOW + timedelta(minutes=15),
        "target": RecommendationTarget(
            device_id="ac_living_01", capability="climate.target_temperature"
        ),
        "proposed_value": 23,
        "confidence": 0.87,
        "reason_codes": ["EXPECTED_ARRIVAL", "REPEATED_USER_PATTERN"],
        "model": ModelReference(name="comfort_preference", version="1.0.0"),
        "required_policy": "COMFORT_AUTOMATION",
    }
    payload.update(overrides)
    return Recommendation.model_validate(payload)


def model_version(**overrides: object) -> ModelVersion:
    payload: dict[str, object] = {
        "model_id": uuid4(),
        "home_id": "home_001",
        "name": "comfort_preference",
        "version": "1.0.0",
        "model_type": ModelType.TEMPERATURE_PREFERENCE,
        "feature_schema_version": "1.0",
        "training_code_revision": "abc1234",
        "training_window": TrainingWindow(
            start=NOW - timedelta(days=30), end=NOW, sample_count=500, distinct_days=21
        ),
        "evaluation_metrics": {"mae": 0.8},
        "created_at": NOW,
        "card": ModelCard(
            summary="s",
            intended_use="i",
            out_of_scope_use="o",
            training_data="t",
            evaluation="e",
            limitations="l",
            ethical_and_safety_notes="n",
        ),
    }
    payload.update(overrides)
    return ModelVersion.model_validate(payload)


# ── recommendation contract (spec §15) ──


def test_spec_example_recommendation_parses() -> None:
    rec = recommendation()
    assert rec.target.capability == "climate.target_temperature"
    assert rec.proposed_value == 23
    assert rec.requires_user_approval is True


@pytest.mark.safety
def test_a_recommendation_carries_no_execution_capability() -> None:
    # Safety invariant 1: an AI recommendation is never an actuator command.
    # The type exposes no dispatch surface at all — reaching a device requires
    # a separate policy decision and action request.
    rec = recommendation()
    for forbidden in ("execute", "dispatch", "send", "call_service", "apply", "run"):
        assert not hasattr(rec, forbidden), f"Recommendation must not expose {forbidden}()"


@pytest.mark.safety
def test_recommendations_default_to_requiring_approval() -> None:
    # Untrusted until policy says otherwise, rather than the reverse.
    assert recommendation().requires_user_approval is True


@pytest.mark.safety
def test_expired_recommendation_is_never_actionable() -> None:
    # Safety invariant 3: a stale recommendation cannot execute.
    rec = recommendation(expires_at=NOW + timedelta(minutes=15))
    assert rec.is_actionable_at(NOW)
    assert not rec.is_actionable_at(NOW + timedelta(minutes=16))
    assert rec.is_expired_at(NOW + timedelta(minutes=16))


@pytest.mark.safety
def test_shadow_recommendations_are_never_actionable() -> None:
    # Spec §19.2 SHADOW: predictions are generated without being shown or executed.
    rec = recommendation(shadow=True)
    assert not rec.is_actionable_at(NOW)


def test_recommendation_must_expire_after_creation() -> None:
    with pytest.raises(ValidationError, match="must expire after it is created"):
        recommendation(expires_at=NOW - timedelta(minutes=1))


def test_recommendation_requires_reason_codes() -> None:
    # An unexplainable recommendation cannot be presented or audited.
    with pytest.raises(ValidationError):
        recommendation(reason_codes=[])


def test_recommendation_target_must_be_a_canonical_capability() -> None:
    with pytest.raises(ValidationError, match="unknown capability"):
        recommendation(target=RecommendationTarget(device_id="d", capability="vendor.magic"))


@pytest.mark.safety
def test_a_model_cannot_propose_a_value_outside_the_capability_domain() -> None:
    # climate.target_temperature is bounded to 16-30 C by its definition, so a
    # dangerous setpoint fails at the contract rather than at the device.
    with pytest.raises(ValidationError, match="outside the declared domain"):
        recommendation(proposed_value=45)
    with pytest.raises(ValidationError, match="outside the declared domain"):
        recommendation(proposed_value=5)


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        recommendation(created_at=datetime(2026, 8, 18, 15, 30))  # noqa: DTZ001


# ── model version contract (spec §19.3) ──


def test_model_version_records_every_required_field() -> None:
    version = model_version()
    assert version.feature_schema_version
    assert version.training_code_revision
    assert version.training_window.sample_count > 0
    assert version.evaluation_metrics
    assert version.runtime == "onnxruntime"
    assert version.card.summary
    assert version.reference == "comfort_preference@1.0.0"


@pytest.mark.safety
def test_a_version_without_evaluation_cannot_exist() -> None:
    # Safety invariant 15: no activation without evaluation.
    with pytest.raises(ValidationError, match="must record evaluation metrics"):
        model_version(evaluation_metrics={})


@pytest.mark.safety
def test_an_active_version_must_record_its_promotion() -> None:
    with pytest.raises(ValidationError, match="must record when it was promoted"):
        model_version(status=ModelStatus.ACTIVE)

    promoted = model_version(status=ModelStatus.ACTIVE, promoted_at=NOW)
    assert promoted.promoted_at == NOW


def test_new_versions_start_unpromoted() -> None:
    assert model_version().status is ModelStatus.TRAINED
    assert model_version().promoted_at is None


def test_training_window_must_be_ordered() -> None:
    with pytest.raises(ValidationError, match="end precedes its start"):
        model_version(
            training_window=TrainingWindow(
                start=NOW, end=NOW - timedelta(days=1), sample_count=10, distinct_days=2
            )
        )


# ── learning lifecycle (spec §19.2) ──


@pytest.mark.safety
def test_observe_cannot_jump_to_authorized_automation() -> None:
    # The explicit prohibition in spec §19.2.
    assert not can_transition(LearningMode.OBSERVE, LearningMode.AUTHORIZED_AUTOMATION)
    with pytest.raises(LearningModeTransitionError, match="one stage at a time"):
        assert_transition(LearningMode.OBSERVE, LearningMode.AUTHORIZED_AUTOMATION)


@pytest.mark.safety
def test_the_ladder_must_be_climbed_one_rung_at_a_time() -> None:
    ladder = [
        LearningMode.DISABLED,
        LearningMode.OBSERVE,
        LearningMode.SHADOW,
        LearningMode.RECOMMEND,
        LearningMode.APPROVAL_REQUIRED,
        LearningMode.AUTHORIZED_AUTOMATION,
    ]
    for current, nxt in pairwise(ladder):
        assert can_transition(current, nxt), f"{current} → {nxt} should be allowed"
    # Every non-adjacent forward jump is refused.
    for i, current in enumerate(ladder):
        for target in ladder[i + 2 :]:
            assert not can_transition(current, target), f"{current} → {target} must be refused"


@pytest.mark.safety
def test_suspension_is_reachable_from_every_active_mode() -> None:
    for mode in (
        LearningMode.SHADOW,
        LearningMode.RECOMMEND,
        LearningMode.APPROVAL_REQUIRED,
        LearningMode.AUTHORIZED_AUTOMATION,
    ):
        assert can_transition(mode, LearningMode.SUSPENDED)


@pytest.mark.safety
def test_recovery_from_suspension_cannot_return_straight_to_automation() -> None:
    assert can_transition(LearningMode.SUSPENDED, LearningMode.OBSERVE)
    for mode in (
        LearningMode.SHADOW,
        LearningMode.RECOMMEND,
        LearningMode.APPROVAL_REQUIRED,
        LearningMode.AUTHORIZED_AUTOMATION,
    ):
        assert not can_transition(LearningMode.SUSPENDED, mode)


@pytest.mark.safety
def test_shadow_mode_permits_neither_display_nor_execution() -> None:
    assert not allows_recommendations(LearningMode.SHADOW)
    assert not allows_execution(LearningMode.SHADOW)
    assert not allows_unattended_execution(LearningMode.SHADOW)


@pytest.mark.safety
def test_only_authorized_automation_permits_unattended_execution() -> None:
    for mode in LearningMode:
        expected = mode is LearningMode.AUTHORIZED_AUTOMATION
        assert allows_unattended_execution(mode) is expected


def test_observe_mode_permits_nothing_but_collection() -> None:
    assert not allows_recommendations(LearningMode.OBSERVE)
    assert not allows_execution(LearningMode.OBSERVE)


def test_same_mode_transition_is_a_noop() -> None:
    for mode in LearningMode:
        assert can_transition(mode, mode)
