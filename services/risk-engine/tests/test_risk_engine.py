"""Risk Engine tests (spec §14.5, §22 Phase 6 acceptance).

The headline acceptance criterion: **AI only creates watch and pre-alert
states.** These tests attack that from the rule layer, the service layer, and
the interaction between inference and confirmation.
"""

from datetime import UTC, datetime, timedelta

import pytest
from syltra_contracts import RiskCategory, RiskSeverity, RiskState
from syltra_digital_twin.core import HomeState
from syltra_risk_engine import (
    CaseChange,
    RiskEngineService,
    RiskInput,
    RiskProposal,
    evaluate_all,
)
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

NOW = datetime(2026, 8, 19, 3, 15, tzinfo=UTC)
HOME = "home_001"


def gas_home(value: bool = True, at: datetime = NOW) -> HomeState:
    return home(
        device("gas_kitchen", "kitchen", gas=reading("safety.gas_alarm", value, at)),
        home_id=HOME,
    )


def find(changes: list[CaseChange], category: RiskCategory) -> CaseChange | None:
    return next((c for c in changes if c.case.category is category), None)


# ── the headline criterion ──


@pytest.mark.safety
def test_inference_produces_only_watch_and_pre_alert() -> None:
    # Every rule in the inference layer, across a home full of hazards.
    state = home(
        device("gas_kitchen", "kitchen", gas=reading("safety.gas_alarm", True, NOW)),
        device("leak", "kitchen", leak=reading("safety.water_leak", True, NOW)),
        device("smoke", "hall", smoke=reading("safety.smoke_alarm", True, NOW)),
        device("meter", "utility", power=reading("energy.power", 9000.0, NOW, "W")),
        device("temp", "living_room", t=reading("environment.temperature", 60.0, NOW, "C")),
        device("door", "entrance", c=reading("contact.open", True, NOW)),
        home_id=HOME,
    )
    proposals = evaluate_all(RiskInput(home=state, now=NOW, occupied=False))
    assert proposals
    for proposal in proposals:
        assert proposal.state in {RiskState.WATCH, RiskState.PRE_ALERT}


@pytest.mark.safety
def test_a_rule_cannot_even_construct_a_confirmed_proposal() -> None:
    # Structural, not merely conventional: the type refuses.
    with pytest.raises(ValueError, match="WATCH or PRE_ALERT only"):
        RiskProposal(
            category=RiskCategory.GAS,
            state=RiskState.CONFIRMED,
            severity=RiskSeverity.CRITICAL,
            confidence=1.0,
            evidence=[],
            reason_codes=["X"],
        )


@pytest.mark.safety
def test_inference_alone_never_reaches_confirmed_through_the_service() -> None:
    # A governor with no rules cannot confirm anything; the service must then
    # leave every case advisory no matter how alarming the readings.
    from syltra_risk_engine.governor import SafetyGovernor

    service = RiskEngineService(governor=SafetyGovernor(rules=()))
    service.evaluate(HOME, gas_home(), NOW, occupied=False)
    for case in service.open_cases(HOME, NOW):
        assert case.is_advisory
        assert not case.permits_emergency_response
    assert not service.has_confirmed_case(HOME, NOW)


# ── confirmation ──


@pytest.mark.safety
def test_the_governor_confirms_and_the_case_records_its_rule() -> None:
    service = RiskEngineService()
    changes = service.evaluate(HOME, gas_home(), NOW, occupied=False)
    confirmed = find(changes, RiskCategory.GAS)
    assert confirmed is not None
    assert confirmed.case.state is RiskState.CONFIRMED
    assert confirmed.case.confirmed_by == "rule:gas_confirmed@1.0.0"
    assert confirmed.case.confidence == 1.0
    assert service.has_confirmed_case(HOME, NOW)


@pytest.mark.safety
def test_a_confirmed_case_carries_certified_evidence_only() -> None:
    service = RiskEngineService()
    service.evaluate(HOME, gas_home(), NOW)
    case = service.case_for(HOME, RiskCategory.GAS, "kitchen")
    assert case is not None
    assert any(item.can_confirm for item in case.evidence)


@pytest.mark.safety
def test_inference_does_not_modify_a_confirmed_case() -> None:
    # Once confirmed, a later low-confidence inference pass must not soften it.
    service = RiskEngineService()
    service.evaluate(HOME, gas_home(), NOW)
    case = service.case_for(HOME, RiskCategory.GAS, "kitchen")
    assert case is not None and case.state is RiskState.CONFIRMED

    # Re-evaluate with cooking context, which lowers inference confidence.
    service.evaluate(HOME, gas_home(), NOW + timedelta(seconds=30), cooking=True)
    still = service.case_for(HOME, RiskCategory.GAS, "kitchen")
    assert still is not None
    assert still.state is RiskState.CONFIRMED
    assert still.confidence == 1.0


@pytest.mark.safety
def test_a_stale_alarm_leaves_the_case_advisory() -> None:
    # Inference sees nothing (stale), and the governor refuses to confirm, so
    # no case claims an emergency on stale data.
    service = RiskEngineService()
    service.evaluate(HOME, gas_home(at=NOW - timedelta(hours=1)), NOW)
    assert not service.has_confirmed_case(HOME, NOW)


# ── inference behaviour ──


def test_gas_watch_lowers_confidence_while_cooking() -> None:
    inp_cooking = RiskInput(home=gas_home(), now=NOW, occupied=True, cooking=True)
    inp_plain = RiskInput(home=gas_home(), now=NOW, occupied=True, cooking=False)
    cooking = evaluate_all(inp_cooking)[0]
    plain = evaluate_all(inp_plain)[0]
    assert cooking.confidence < plain.confidence
    assert "COOKING_IN_PROGRESS" in cooking.reason_codes


def test_gas_watch_is_more_severe_in_an_empty_home() -> None:
    # An alarm with nobody home has no innocent explanation.
    empty = evaluate_all(RiskInput(home=gas_home(), now=NOW, occupied=False))[0]
    assert empty.severity is RiskSeverity.CRITICAL
    assert "HOME_EMPTY" in empty.reason_codes


def test_cooking_never_suppresses_a_gas_watch() -> None:
    # Context adjusts confidence; it never silences a hazard signal.
    proposals = evaluate_all(RiskInput(home=gas_home(), now=NOW, cooking=True))
    assert proposals
    assert proposals[0].category is RiskCategory.GAS


@pytest.mark.safety
def test_stale_safety_sensors_raise_a_protection_gap_case() -> None:
    # The risk nobody looks for: the home is quiet because the sensors that
    # would say otherwise have stopped reporting.
    state = home(
        device(
            "smoke",
            "hall",
            smoke=reading("safety.smoke_alarm", False, NOW - timedelta(hours=2)),
        ),
        home_id=HOME,
    )
    proposals = evaluate_all(RiskInput(home=state, now=NOW))
    gap = next(p for p in proposals if p.category is RiskCategory.DEVICE_FAILURE)
    assert "PROTECTION_GAP" in gap.reason_codes
    assert gap.severity is RiskSeverity.HIGH


@pytest.mark.safety
def test_electrical_anomaly_never_proposes_a_breaker_action() -> None:
    # Spec §20.6: do not open a breaker on anomaly-model output alone.
    state = home(
        device("meter", "utility", power=reading("energy.power", 9000.0, NOW, "W")),
        home_id=HOME,
    )
    electrical = next(
        p
        for p in evaluate_all(RiskInput(home=state, now=NOW, occupied=False))
        if p.category is RiskCategory.ELECTRICAL
    )
    assert electrical.state is RiskState.WATCH
    assert "NO_AUTOMATIC_BREAKER_ACTION" in electrical.reason_codes


def test_intrusion_watch_requires_a_believed_empty_home() -> None:
    state = home(
        device("door", "entrance", c=reading("contact.open", True, NOW)),
        home_id=HOME,
    )
    assert not [
        p
        for p in evaluate_all(RiskInput(home=state, now=NOW, occupied=True))
        if p.category is RiskCategory.INTRUSION
    ]
    assert [
        p
        for p in evaluate_all(RiskInput(home=state, now=NOW, occupied=False))
        if p.category is RiskCategory.INTRUSION
    ]


def test_unknown_occupancy_does_not_imply_an_empty_home() -> None:
    # occupied=None means unknown, and unknown must not be read as empty.
    state = home(
        device("door", "entrance", c=reading("contact.open", True, NOW)),
        home_id=HOME,
    )
    assert not [
        p
        for p in evaluate_all(RiskInput(home=state, now=NOW, occupied=None))
        if p.category is RiskCategory.INTRUSION
    ]


# ── the engine dispatches nothing ──


@pytest.mark.safety
def test_the_risk_engine_has_no_way_to_command_a_device() -> None:
    # Spec §14.5: never dispatch device actions.
    service = RiskEngineService()
    for forbidden in ("execute", "dispatch", "call_service", "control_device", "act"):
        assert not hasattr(service, forbidden)
    assert not hasattr(service, "_gateway")


# ── lifecycle ──


def test_advisory_cases_expire_and_confirmed_cases_do_not() -> None:
    service = RiskEngineService()
    state = home(
        device("meter", "utility", power=reading("energy.power", 9000.0, NOW, "W")),
        home_id=HOME,
    )
    service.evaluate(HOME, state, NOW, occupied=False)
    assert service.open_cases(HOME, NOW)

    expired = service.sweep_expired(HOME, NOW + timedelta(hours=2))
    assert any(c.kind == "EXPIRED" for c in expired)
    assert service.open_cases(HOME, NOW + timedelta(hours=2)) == []

    service.evaluate(HOME, gas_home(), NOW)
    assert service.sweep_expired(HOME, NOW + timedelta(days=1)) == []
    assert service.has_confirmed_case(HOME, NOW + timedelta(days=1))


def test_a_confirmed_case_enters_recovery_rather_than_closing_directly() -> None:
    service = RiskEngineService()
    service.evaluate(HOME, gas_home(), NOW)
    recovered = service.close(HOME, RiskCategory.GAS, "kitchen", reason="alarm cleared")
    assert recovered is not None
    assert recovered.state is RiskState.RECOVERY


def test_case_escalation_is_recorded() -> None:
    service = RiskEngineService()
    from syltra_risk_engine.governor import SafetyGovernor

    service = RiskEngineService(governor=SafetyGovernor(rules=()))
    changes = service.evaluate(HOME, gas_home(), NOW, occupied=True)
    assert any(c.kind == "OPENED" for c in changes)


@pytest.mark.safety
def test_every_case_change_is_audited() -> None:
    service = RiskEngineService()
    service.evaluate(HOME, gas_home(), NOW)
    assert service.audit
    confirmed = next(e for e in service.audit if e.action == "RISK_CASE_CONFIRMED")
    assert confirmed.detail["advisory"] is False
    assert confirmed.detail["authorized_response"]


def test_homes_are_isolated() -> None:
    service = RiskEngineService()
    service.evaluate(HOME, gas_home(), NOW)
    assert service.open_cases(HOME, NOW)
    assert service.open_cases("home_other", NOW) == []
    assert not service.has_confirmed_case("home_other", NOW)


def test_a_healthy_home_opens_no_cases() -> None:
    state = home(
        device("gas_kitchen", "kitchen", gas=reading("safety.gas_alarm", False, NOW)),
        device("m1", "living_room", motion=reading("occupancy.motion", True, NOW)),
        home_id=HOME,
    )
    service = RiskEngineService()
    service.evaluate(HOME, state, NOW, occupied=True)
    assert service.open_cases(HOME, NOW) == []


@pytest.mark.safety
def test_a_confirmation_supersedes_the_advisory_change_in_the_same_pass() -> None:
    # A single evaluation must not report a PRE_ALERT that never really held.
    # Consumers should see one transition, to the state that actually applies.
    service = RiskEngineService()
    changes = service.evaluate(HOME, gas_home(), NOW, occupied=False)
    gas_changes = [c for c in changes if c.case.category is RiskCategory.GAS]
    assert len(gas_changes) == 1
    assert gas_changes[0].case.state is RiskState.CONFIRMED
    assert gas_changes[0].kind == "CONFIRMED"
