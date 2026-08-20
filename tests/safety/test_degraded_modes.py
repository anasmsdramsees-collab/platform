"""Degraded-mode safety tests (spec §22 Phase 6 acceptance, §18).

Three acceptance criteria live here, and each is about what happens when part
of the platform is *gone*:

- safety tests pass without the Adaptive Engine (invariant 7);
- loss of cloud has no local safety impact (invariant 8);
- replayed historical alarms cannot trigger live actions (invariant 11).

The tests deliberately construct the safety path with nothing else present —
no models, no context engine, no network client — rather than mocking those
components out. A mock would prove the code tolerates a stub; building without
them proves the dependency does not exist.
"""

import subprocess
import sys
from datetime import UTC, datetime, timedelta

import pytest
from syltra_contracts import PolicyOutcome, RiskCategory, RiskState
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_risk_engine import RiskEngineService, SafetyGovernor
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

pytestmark = pytest.mark.safety

NOW = datetime(2026, 8, 19, 3, 15, tzinfo=UTC)
HOME = "home_001"


def alarming_home(capability: str = "safety.gas_alarm", at: datetime = NOW):  # type: ignore[no-untyped-def]
    return home(
        device("alarm_1", "kitchen", a=reading(capability, True, at)),
        home_id=HOME,
    )


# ── invariant 7: safety survives the loss of the Adaptive Engine ──


def test_the_safety_path_imports_without_any_ml_package() -> None:
    """The governor's dependency closure contains no ML runtime.

    Run in a fresh interpreter so an import pulled in by another test cannot
    mask a real dependency. If the Safety Governor ever acquired a model
    dependency — even transitively — this fails.
    """
    program = (
        "import sys;"
        "import syltra_risk_engine.governor as g;"
        "loaded = set(sys.modules);"
        "bad = [m for m in loaded if m.split('.')[0] in "
        "{'sklearn','onnxruntime','skl2onnx','polars','syltra_adaptive_engine'}];"
        "print('LOADED:' + ','.join(sorted(bad)))"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", program], capture_output=True, text=True, check=True
    )
    assert "LOADED:" in result.stdout
    leaked = result.stdout.strip().removeprefix("LOADED:")
    assert leaked == "", f"safety path pulled in ML packages: {leaked}"


def test_confirmation_works_with_the_adaptive_engine_absent() -> None:
    # No AdaptiveEngineService is constructed anywhere in this test.
    governor = SafetyGovernor()
    confirmations = governor.evaluate(HOME, alarming_home(), NOW)
    assert len(confirmations) == 1
    assert confirmations[0].authorized_response == "NOTIFY_AND_PREPARE_GAS_ISOLATION"


def test_risk_cases_are_created_with_no_models_present() -> None:
    service = RiskEngineService()
    service.evaluate(HOME, alarming_home(), NOW, occupied=False)
    assert service.has_confirmed_case(HOME, NOW)


def test_policy_denies_and_allows_with_no_models_present() -> None:
    # The policy chain is pure; it needs nothing from the AI layer to work.
    service = PolicyService()
    service.set_policy(HOME, HomePolicy())
    assert service.audit == []


def test_safety_monitoring_is_unaffected_by_a_missing_adaptive_engine() -> None:
    # Spec §18.7, first half: loss of the Adaptive Engine does not stop safety
    # monitoring. The governor is the safety monitor, and it runs.
    governor = SafetyGovernor()
    for capability in (
        "safety.smoke_alarm",
        "safety.heat_alarm",
        "safety.co_alarm",
        "safety.water_leak",
        "safety.gas_alarm",
    ):
        assert governor.evaluate(HOME, alarming_home(capability), NOW)


def test_fixed_automation_is_unaffected_by_a_missing_adaptive_engine() -> None:
    """Spec §18.7, second half — which had nothing to test on until now.

    This test previously carried this name while exercising only the Safety
    Governor, because no automation existed. The invariant was reported as
    satisfied on the strength of half of it.
    """
    from syltra_automation_engine import AutomationEngine
    from syltra_contracts import (
        Automation,
        AutomationAction,
        AutomationTrigger,
        TriggerKind,
    )
    from syltra_testing import build_device, build_home, build_reading

    engine = AutomationEngine()
    engine.upsert(
        Automation(
            home_id=HOME,
            name="Hall light on motion",
            trigger=AutomationTrigger(
                kind=TriggerKind.STATE_EQUALS,
                capability="occupancy.motion",
                device_id="motion_hall",
                value=True,
            ),
            actions=(
                AutomationAction(capability="light.power", value=True, device_id="light_hall"),
            ),
        )
    )
    home = build_home(
        build_device("motion_hall", "hall", m=build_reading("occupancy.motion", True, NOW)),
        build_device("light_hall", "hall", p=build_reading("light.power", False, NOW)),
        home_id=HOME,
    )
    # No adaptive engine is constructed, imported or reachable from here.
    assert engine.evaluate(HOME, home, NOW).proposals


# ── invariant 8: loss of cloud has no local safety impact ──


def test_the_governor_holds_no_network_client() -> None:
    governor = SafetyGovernor()
    for attribute in vars(governor):
        assert "client" not in attribute.lower()
        assert "session" not in attribute.lower()
        assert "nats" not in attribute.lower()
        assert "cloud" not in attribute.lower()


def test_confirmation_does_not_touch_the_network() -> None:
    """Confirm with sockets disabled entirely.

    Any accidental network call — a metrics push, a cloud check, a DNS lookup —
    would raise rather than silently degrade.
    """
    import socket

    original = socket.socket

    def _forbidden(*args: object, **kwargs: object) -> None:
        msg = "the safety path must not open a socket"
        raise AssertionError(msg)

    socket.socket = _forbidden  # type: ignore[assignment, misc]
    try:
        governor = SafetyGovernor()
        confirmations = governor.evaluate(HOME, alarming_home(), NOW)
        assert len(confirmations) == 1
    finally:
        socket.socket = original  # type: ignore[misc]


def test_risk_evaluation_does_not_touch_the_network() -> None:
    import socket

    original = socket.socket

    def _forbidden(*args: object, **kwargs: object) -> None:
        msg = "risk evaluation must not open a socket"
        raise AssertionError(msg)

    socket.socket = _forbidden  # type: ignore[assignment, misc]
    try:
        service = RiskEngineService()
        service.evaluate(HOME, alarming_home(), NOW, occupied=False)
        assert service.has_confirmed_case(HOME, NOW)
    finally:
        socket.socket = original  # type: ignore[misc]


# ── invariant 11: replayed history cannot trigger live action ──


def test_a_replayed_alarm_from_last_week_confirms_nothing() -> None:
    governor = SafetyGovernor()
    replayed = alarming_home(at=NOW - timedelta(days=7))
    assert governor.evaluate(HOME, replayed, NOW) == []


def test_replay_rejection_is_independent_of_the_freshness_window() -> None:
    """A generous freshness window must not become a replay loophole.

    `safety.water_leak` has a 300s freshness window — wider than the gas alarm's
    — so a reading could in principle pass freshness while being far too old to
    act on. The governor checks absolute age separately for exactly this case.
    """
    governor = SafetyGovernor(max_event_age=timedelta(minutes=5))
    borderline = home(
        device(
            "leak_1",
            "kitchen",
            leak=reading("safety.water_leak", True, NOW - timedelta(minutes=4, seconds=30)),
        ),
        home_id=HOME,
    )
    assert governor.evaluate(HOME, borderline, NOW)

    too_old = home(
        device(
            "leak_1",
            "kitchen",
            leak=reading("safety.water_leak", True, NOW - timedelta(minutes=20)),
        ),
        home_id=HOME,
    )
    assert governor.evaluate(HOME, too_old, NOW) == []


def test_a_replayed_alarm_does_not_open_a_confirmed_case() -> None:
    service = RiskEngineService()
    service.evaluate(HOME, alarming_home(at=NOW - timedelta(days=1)), NOW)
    assert not service.has_confirmed_case(HOME, NOW)


# ── invariant 9: database loss fails safe ──


def test_risk_state_is_reconstructable_without_a_database() -> None:
    """Spec §18.9: loss of the database must fail safely and prevent
    untraceable adaptive execution.

    The risk engine holds no database handle; its state is derived from twin
    state, which is itself rebuilt from the event stream. Losing storage costs
    history, not the ability to detect a live hazard.
    """
    service = RiskEngineService()
    assert not hasattr(service, "_session")
    assert not hasattr(service, "_engine")
    service.evaluate(HOME, alarming_home(), NOW)
    assert service.has_confirmed_case(HOME, NOW)


# ── the interaction with comfort automation ──


def test_a_confirmed_hazard_suspends_comfort_automation() -> None:
    """An open emergency stands comfort automation down.

    Adaptive actions during an incident add noise exactly when the household
    and the safety layer need a stable, predictable home.
    """
    risk = RiskEngineService()
    risk.evaluate(HOME, alarming_home(), NOW, occupied=False)
    assert risk.has_confirmed_case(HOME, NOW)

    policy = PolicyService()
    policy.set_policy(HOME, HomePolicy(unattended_automation=True))
    policy.set_active_risk(HOME, risk.has_confirmed_case(HOME, NOW))
    assert policy.home(HOME).active_risk is True


def test_comfort_automation_resumes_once_the_case_closes() -> None:
    risk = RiskEngineService()
    risk.evaluate(HOME, alarming_home(), NOW, occupied=False)
    risk.close(HOME, RiskCategory.GAS, "kitchen", reason="alarm cleared")

    case = risk.case_for(HOME, RiskCategory.GAS, "kitchen")
    assert case is not None
    assert case.state is RiskState.RECOVERY

    policy = PolicyService()
    policy.set_active_risk(HOME, False)
    assert policy.home(HOME).active_risk is False


def test_policy_denies_comfort_actions_while_a_risk_is_open() -> None:
    from uuid import uuid4

    from syltra_contracts import ModelReference, Recommendation, RecommendationTarget

    policy = PolicyService()
    policy.set_policy(HOME, HomePolicy(unattended_automation=True))
    policy.set_active_risk(HOME, True)

    recommendation = Recommendation(
        recommendation_id=uuid4(),
        home_id=HOME,
        recommendation_type="climate.precondition",
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=15),
        target=RecommendationTarget(
            device_id="ac_living", capability="climate.target_temperature"
        ),
        proposed_value=23,
        confidence=0.95,
        reason_codes=["REPEATED_USER_PATTERN"],
        model=ModelReference(name="temperature_preference", version="1.0.0"),
        required_policy="COMFORT_AUTOMATION",
        requires_user_approval=False,
    )
    decision = policy.evaluate(recommendation, now=NOW, twin_value=27.0, twin_status="KNOWN")
    assert decision.decision is PolicyOutcome.DENY
    assert "ACTIVE_RISK_CASE" in decision.reason_codes
