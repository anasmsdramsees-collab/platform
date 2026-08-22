"""Policy, action and feedback contract tests (spec §16, §17, §14.8).

Carries safety invariants 2 (every action passes policy), 3 (a stale
recommendation cannot execute), 10 (duplicates do not double-act) and 13
(critical actuators use separate policy classes).
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from syltra_contracts import (
    ActionRequest,
    ActionTarget,
    ExpectedState,
    FailureKind,
    FeedbackKind,
    FeedbackRecord,
    FeedbackSource,
    PolicyDecision,
    PolicyOutcome,
    SafetyClass,
    compute_input_hash,
    derive_idempotency_key,
)

pytestmark = pytest.mark.contract

NOW = datetime(2026, 8, 18, 15, 30, tzinfo=UTC)


def decision(**overrides: object) -> PolicyDecision:
    payload: dict[str, object] = {
        "decision_id": uuid4(),
        "recommendation_id": uuid4(),
        "home_id": "home_001",
        "decision": PolicyOutcome.ALLOW,
        "evaluated_at": NOW,
        "expires_at": NOW + timedelta(minutes=15),
        "reason_codes": ["WITHIN_COMFORT_POLICY"],
        "safety_class": SafetyClass.COMFORT,
        "input_hash": compute_input_hash({"state": "x"}),
    }
    payload.update(overrides)
    return PolicyDecision.model_validate(payload)


def action(**overrides: object) -> ActionRequest:
    decision_id = uuid4()
    payload: dict[str, object] = {
        "action_id": uuid4(),
        "idempotency_key": derive_idempotency_key(
            "home_001", decision_id, "climate.target_temperature"
        ),
        "decision_id": decision_id,
        "home_id": "home_001",
        "correlation_id": uuid4(),
        "target": ActionTarget(device_id="ac_living_01", capability="climate.target_temperature"),
        "value": 23,
        "expected_state": ExpectedState(
            capability="climate.target_temperature", operator="equals", value=23
        ),
        "safety_class": SafetyClass.COMFORT,
        "created_at": NOW,
        "expires_at": NOW + timedelta(minutes=15),
    }
    payload.update(overrides)
    return ActionRequest.model_validate(payload)


# ── policy decision (spec §16) ──


def test_spec_example_decision_parses() -> None:
    record = decision(decision=PolicyOutcome.REQUIRE_USER_APPROVAL)
    assert record.decision is PolicyOutcome.REQUIRE_USER_APPROVAL
    assert record.policy_version == "1.0.0"
    assert len(record.input_hash) == 64


@pytest.mark.safety
def test_only_a_live_allow_authorizes_execution() -> None:
    # Safety invariant 2: nothing but an ALLOW opens the gate.
    assert decision(decision=PolicyOutcome.ALLOW).authorizes_execution_at(NOW)
    for outcome in (
        PolicyOutcome.DENY,
        PolicyOutcome.REQUIRE_USER_APPROVAL,
        PolicyOutcome.PREPARE_ONLY,
        PolicyOutcome.ESCALATE_TO_FIXED_SAFETY_RULE,
    ):
        assert not decision(decision=outcome).authorizes_execution_at(NOW)


@pytest.mark.safety
def test_an_expired_allow_authorizes_nothing() -> None:
    # Safety invariant 3.
    allowed = decision(expires_at=NOW + timedelta(minutes=5))
    assert allowed.authorizes_execution_at(NOW)
    assert not allowed.authorizes_execution_at(NOW + timedelta(minutes=6))


def test_a_decision_must_carry_reason_codes() -> None:
    with pytest.raises(ValidationError):
        decision(reason_codes=[])


def test_a_decision_must_expire_after_evaluation() -> None:
    with pytest.raises(ValidationError, match="must expire after it is evaluated"):
        decision(expires_at=NOW - timedelta(seconds=1))


def test_input_hash_is_stable_and_order_independent() -> None:
    # An auditor must be able to recompute the hash from stored evidence.
    a = compute_input_hash({"temperature": 27.4, "occupied": True})
    b = compute_input_hash({"occupied": True, "temperature": 27.4})
    assert a == b
    assert a != compute_input_hash({"temperature": 27.5, "occupied": True})


def test_manual_actions_still_require_a_decision() -> None:
    # recommendation_id may be absent for a manual action, but the decision
    # itself is not optional.
    manual = decision(recommendation_id=None)
    assert manual.recommendation_id is None
    assert manual.decision is PolicyOutcome.ALLOW


# ── action request (spec §17) ──


@pytest.mark.safety
def test_an_action_cannot_exist_without_a_decision_id() -> None:
    # Safety invariant 2, enforced by the type rather than by convention.
    payload = action().model_dump()
    del payload["decision_id"]
    with pytest.raises(ValidationError):
        ActionRequest.model_validate(payload)


@pytest.mark.safety
def test_idempotency_keys_are_derived_and_stable() -> None:
    # Safety invariant 10: the same intent yields the same key, so a duplicate
    # request cannot become a second device command.
    decision_id = uuid4()
    first = derive_idempotency_key("home_001", decision_id, "light.power")
    second = derive_idempotency_key("home_001", decision_id, "light.power")
    assert first == second
    assert first != derive_idempotency_key("home_001", uuid4(), "light.power")
    assert first != derive_idempotency_key("home_002", decision_id, "light.power")


@pytest.mark.safety
def test_an_action_value_outside_the_capability_domain_is_rejected() -> None:
    with pytest.raises(ValidationError, match="outside the declared domain"):
        action(value=45)


def test_an_action_must_expire_after_creation() -> None:
    with pytest.raises(ValidationError, match="must expire after it is created"):
        action(expires_at=NOW - timedelta(seconds=1))


def test_expired_actions_are_recognisable() -> None:
    request = action(expires_at=NOW + timedelta(minutes=5))
    assert not request.is_expired_at(NOW)
    assert request.is_expired_at(NOW + timedelta(minutes=6))


def test_attempt_bounds_are_enforced() -> None:
    assert action(max_attempts=1).max_attempts == 1
    with pytest.raises(ValidationError):
        action(max_attempts=0)
    with pytest.raises(ValidationError):
        action(max_attempts=99)


def test_unknown_capability_targets_are_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown capability"):
        action(target=ActionTarget(device_id="d", capability="vendor.magic"))


# ── expected state verification ──


@pytest.mark.parametrize(
    ("operator", "expected", "observed", "satisfied"),
    [
        ("equals", 23, 23, True),
        ("equals", 23, 22.9, True),  # within tolerance
        ("equals", 23, 25, False),
        ("equals", True, True, True),
        ("equals", True, False, False),
        ("equals", "locked", "locked", True),
        ("equals", "locked", "unlocked", False),
        ("not_equals", "jammed", "locked", True),
        ("greater_than", 20, 25, True),
        ("greater_than", 20, 15, False),
        ("less_than", 30, 25, True),
        ("within", (20, 26), 23, True),
        ("within", (20, 26), 30, False),
    ],
)
def test_expected_state_verification(
    operator: str, expected: object, observed: object, satisfied: bool
) -> None:
    state = ExpectedState(
        capability="climate.target_temperature", operator=operator, value=expected
    )
    assert state.is_satisfied_by(observed) is satisfied


def test_an_unobserved_value_never_satisfies_an_expectation() -> None:
    # Absence of evidence is not verification.
    state = ExpectedState(capability="light.power", operator="equals", value=True)
    assert state.is_satisfied_by(None) is False


def test_unknown_verification_operator_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown verification operator"):
        ExpectedState(capability="light.power", operator="approximately", value=True)


# ── retry classification ──


@pytest.mark.safety
def test_only_transient_failures_are_retryable() -> None:
    # Spec §14.7: retry only safe retryable failures. Repeating a refusal would
    # just re-send a command the system already decided against.
    assert FailureKind.TRANSIENT.retryable
    assert not FailureKind.PERMANENT.retryable


# ── feedback (spec §14.8) ──


def feedback(**overrides: object) -> FeedbackRecord:
    payload: dict[str, object] = {
        "feedback_id": uuid4(),
        "home_id": "home_001",
        "recommendation_id": uuid4(),
        "kind": FeedbackKind.ACCEPT,
        "recorded_at": NOW,
    }
    payload.update(overrides)
    return FeedbackRecord.model_validate(payload)


def test_all_six_feedback_kinds_exist() -> None:
    assert {k.value for k in FeedbackKind} == {
        "ACCEPT",
        "REJECT",
        "NOT_NOW",
        "MODIFY",
        "UNDO",
        "NEVER_REPEAT",
    }


def test_negative_feedback_is_identified() -> None:
    for kind in (FeedbackKind.REJECT, FeedbackKind.UNDO, FeedbackKind.NEVER_REPEAT):
        assert feedback(kind=kind).is_negative
    for kind in (FeedbackKind.ACCEPT, FeedbackKind.NOT_NOW, FeedbackKind.MODIFY):
        assert not feedback(kind=kind).is_negative


@pytest.mark.safety
def test_automation_echoes_never_teach_preference() -> None:
    # Spec §14.8: prevent feedback loops caused by automation-generated state
    # changes. If SYLTRA's own thermostat write counted as a preference, the
    # system would keep reinforcing its own guesses.
    assert feedback(source=FeedbackSource.USER).teaches_preference
    assert not feedback(source=FeedbackSource.AUTOMATION_ECHO).teaches_preference
    assert not feedback(source=FeedbackSource.SYSTEM).teaches_preference


def test_modify_feedback_carries_the_value_the_household_wanted() -> None:
    record = feedback(kind=FeedbackKind.MODIFY, modified_value=21.5)
    assert record.modified_value == 21.5


def test_feedback_is_always_linked_to_a_recommendation() -> None:
    payload = feedback().model_dump()
    del payload["recommendation_id"]
    with pytest.raises(ValidationError):
        FeedbackRecord.model_validate(payload)
