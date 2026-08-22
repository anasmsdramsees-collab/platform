"""Risk contract and state machine tests (spec §14.5, §18).

The central claim of Phase 6: inference can raise awareness but never confirm
an emergency. These tests attack that claim from every angle they can.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from syltra_contracts import (
    AI_REACHABLE_STATES,
    CERTIFIED_ALARM_CAPABILITIES,
    DETERMINISTIC_ONLY_STATES,
    EvidenceOrigin,
    RiskCase,
    RiskCategory,
    RiskEvidenceItem,
    RiskSeverity,
    RiskState,
    RiskTransitionError,
    UnauthorizedRiskTransition,
    assert_risk_transition,
    can_risk_transition,
)

pytestmark = pytest.mark.contract

NOW = datetime(2026, 8, 19, 3, 15, tzinfo=UTC)


def certified(value: bool = True, status: str = "KNOWN") -> RiskEvidenceItem:
    return RiskEvidenceItem(
        origin=EvidenceOrigin.CERTIFIED_ALARM,
        capability="safety.gas_alarm",
        value=value,
        device_id="gas_kitchen",
        observed_at=NOW,
        status=status,
    )


def inferred() -> RiskEvidenceItem:
    return RiskEvidenceItem(
        origin=EvidenceOrigin.INFERENCE,
        capability="energy.power",
        value=4200.0,
        observed_at=NOW,
        status="KNOWN",
        note="unusual draw combined with kitchen occupancy",
    )


def case(**overrides: object) -> RiskCase:
    payload: dict[str, object] = {
        "case_id": uuid4(),
        "home_id": "home_001",
        "category": RiskCategory.GAS,
        "state": RiskState.WATCH,
        "severity": RiskSeverity.MEDIUM,
        "confidence": 0.7,
        "opened_at": NOW,
        "last_updated_at": NOW,
        "evidence": [inferred()],
        "reason_codes": ["UNUSUAL_COMBINATION"],
        "producer": "rule:gas_watch@1.0.0",
    }
    payload.update(overrides)
    return RiskCase.model_validate(payload)


# ── the central claim ──


@pytest.mark.safety
def test_inference_can_reach_watch_and_pre_alert() -> None:
    assert can_risk_transition(RiskState.NORMAL, RiskState.WATCH)
    assert_risk_transition(RiskState.NORMAL, RiskState.WATCH)
    assert_risk_transition(RiskState.WATCH, RiskState.PRE_ALERT)


@pytest.mark.safety
@pytest.mark.parametrize("start", [RiskState.NORMAL, RiskState.WATCH, RiskState.PRE_ALERT])
def test_inference_can_never_reach_confirmed(start: RiskState) -> None:
    # Safety invariants 6 and 18, stated as a test: no amount of inference,
    # from any advisory state, may declare an emergency real.
    with pytest.raises(UnauthorizedRiskTransition, match="deterministic safety rule"):
        assert_risk_transition(start, RiskState.CONFIRMED, deterministic=False)


@pytest.mark.safety
def test_the_safety_governor_can_reach_confirmed() -> None:
    assert_risk_transition(RiskState.PRE_ALERT, RiskState.CONFIRMED, deterministic=True)
    assert_risk_transition(RiskState.NORMAL, RiskState.CONFIRMED, deterministic=True)


@pytest.mark.safety
def test_inference_cannot_start_an_emergency_response() -> None:
    with pytest.raises(UnauthorizedRiskTransition):
        assert_risk_transition(
            RiskState.CONFIRMED, RiskState.ACTION_IN_PROGRESS, deterministic=False
        )


@pytest.mark.safety
def test_ai_reachable_and_deterministic_states_do_not_overlap() -> None:
    assert AI_REACHABLE_STATES & DETERMINISTIC_ONLY_STATES == frozenset()
    assert RiskState.CONFIRMED not in AI_REACHABLE_STATES


# ── the fixed state machine ──


@pytest.mark.safety
def test_closed_is_terminal() -> None:
    for state in RiskState:
        if state is RiskState.CLOSED:
            continue
        assert not can_risk_transition(RiskState.CLOSED, state)


@pytest.mark.safety
def test_recovery_never_jumps_straight_to_normal() -> None:
    # A case is closed deliberately, so there is always a record of who or what
    # ended it rather than a silent return to normal.
    assert not can_risk_transition(RiskState.RECOVERY, RiskState.NORMAL)
    assert can_risk_transition(RiskState.RECOVERY, RiskState.CLOSED)


@pytest.mark.safety
def test_a_confirmed_case_cannot_be_downgraded_to_advisory() -> None:
    # Once confirmed, the path forward is response and recovery — not quietly
    # deciding it was only a watch after all.
    for target in (RiskState.WATCH, RiskState.PRE_ALERT, RiskState.NORMAL):
        assert not can_risk_transition(RiskState.CONFIRMED, target)


def test_an_unknown_transition_is_refused() -> None:
    with pytest.raises(RiskTransitionError, match="cannot move"):
        assert_risk_transition(RiskState.NORMAL, RiskState.RECOVERY)


def test_a_state_may_stay_where_it_is() -> None:
    for state in RiskState:
        assert can_risk_transition(state, state)
        assert_risk_transition(state, state)


# ── evidence ──


@pytest.mark.safety
def test_only_a_fresh_certified_alarm_can_confirm() -> None:
    assert certified().can_confirm
    # A stale reading cannot confirm (safety invariant 4).
    assert not certified(status="STALE").can_confirm
    assert not certified(status="UNKNOWN").can_confirm
    # An alarm reporting "no hazard" confirms nothing.
    assert not certified(value=False).can_confirm
    # Inference never confirms, however plausible.
    assert not inferred().can_confirm


@pytest.mark.safety
def test_a_non_certified_capability_cannot_confirm() -> None:
    # Even claiming CERTIFIED_ALARM origin is not enough: the capability must
    # actually be one of the approved alarm types.
    impostor = RiskEvidenceItem(
        origin=EvidenceOrigin.CERTIFIED_ALARM,
        capability="energy.power",
        value=True,
        observed_at=NOW,
    )
    assert not impostor.can_confirm


def test_the_certified_capability_set_is_the_spec_list() -> None:
    assert CERTIFIED_ALARM_CAPABILITIES == {
        "safety.smoke_alarm",
        "safety.heat_alarm",
        "safety.gas_alarm",
        "safety.co_alarm",
        "safety.water_leak",
    }


# ── the risk case record ──


def test_an_advisory_case_rests_on_inference() -> None:
    record = case()
    assert record.is_advisory
    assert not record.permits_emergency_response
    assert record.is_open


@pytest.mark.safety
def test_a_confirmed_case_must_name_the_rule_that_confirmed_it() -> None:
    with pytest.raises(ValidationError, match="must record the deterministic rule"):
        case(state=RiskState.CONFIRMED, evidence=[certified()], confirmed_by=None)


@pytest.mark.safety
def test_a_confirmed_case_must_carry_certified_evidence() -> None:
    # A case cannot be confirmed on inference alone, even if someone sets the
    # state directly and names a rule.
    with pytest.raises(ValidationError, match="certified alarm reading"):
        case(
            state=RiskState.CONFIRMED,
            evidence=[inferred()],
            confirmed_by="rule:gas_confirmed@1.0.0",
        )


@pytest.mark.safety
def test_a_confirmed_case_cannot_rest_on_a_stale_alarm() -> None:
    with pytest.raises(ValidationError, match="certified alarm reading"):
        case(
            state=RiskState.CONFIRMED,
            evidence=[certified(status="STALE")],
            confirmed_by="rule:gas_confirmed@1.0.0",
        )


def test_a_properly_confirmed_case_validates() -> None:
    record = case(
        state=RiskState.CONFIRMED,
        severity=RiskSeverity.CRITICAL,
        confidence=1.0,
        evidence=[certified()],
        confirmed_by="rule:gas_confirmed@1.0.0",
        reason_codes=["CERTIFIED_GAS_ALARM_ACTIVE"],
    )
    assert record.permits_emergency_response
    assert not record.is_advisory


def test_a_case_must_carry_evidence_and_reasons() -> None:
    with pytest.raises(ValidationError):
        case(evidence=[])
    with pytest.raises(ValidationError):
        case(reason_codes=[])


def test_advisory_cases_expire_but_confirmed_ones_do_not() -> None:
    watching = case(expires_at=NOW + timedelta(minutes=30))
    assert watching.is_active_at(NOW)
    assert not watching.is_active_at(NOW + timedelta(hours=2))

    confirmed = case(
        state=RiskState.CONFIRMED,
        evidence=[certified()],
        confirmed_by="rule:gas_confirmed@1.0.0",
        expires_at=None,
    )
    assert confirmed.is_active_at(NOW + timedelta(days=1))


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        case(opened_at=datetime(2026, 8, 19, 3, 15))  # noqa: DTZ001


def test_all_nine_risk_categories_exist() -> None:
    assert {c.value for c in RiskCategory} == {
        "GAS",
        "SMOKE_FIRE",
        "CARBON_MONOXIDE",
        "WATER_LEAK",
        "ELECTRICAL",
        "TEMPERATURE",
        "INTRUSION",
        "DEVICE_FAILURE",
        "CONNECTIVITY",
    }


def test_all_seven_risk_states_exist() -> None:
    assert {s.value for s in RiskState} == {
        "NORMAL",
        "WATCH",
        "PRE_ALERT",
        "CONFIRMED",
        "ACTION_IN_PROGRESS",
        "RECOVERY",
        "CLOSED",
    }
