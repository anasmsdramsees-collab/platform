"""A confirmed gas hazard closes the valve (owner decision, 2026-08-20).

import re
The decision: a certified detector reaching its alarm threshold is a hazard,
not a question. Waiting for a person means a household breathing gas while it
decides, and the cost of being wrong is a cold kitchen until someone reopens
the supply. That asymmetry only holds while the direction is fixed, so most of
this file is about the direction.

The chain under test, end to end:

    certified gas reading → governor confirms → plan isolates → policy mints a
    fixed-rule ALLOW → orchestrator executes → the device confirms → verified

and the failure branches, which matter more: no valve, a valve that will not
close, a valve that reports nothing back.
"""

import re
from datetime import UTC, datetime
from typing import Any

import pytest
from syltra_action_orchestrator import ActionOrchestrator, OrchestratorConfig
from syltra_contracts import ActionStatus, CommandResult, SafetyClass
from syltra_policy_safety import PolicyService
from syltra_risk_engine import SafetyGovernor
from syltra_risk_engine.isolation import IsolationRefused, dispatch_isolation
from syltra_risk_engine.response import (
    FAIL_SAFE_VALUES,
    ResponseStage,
    ResponseStep,
    plan_response,
)
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

pytestmark = pytest.mark.safety

NOW = datetime(2026, 8, 20, 2, 14, tzinfo=UTC)
HOME = "home_gas"


class ValveGateway:
    """A valve that closes, or does not, exactly as the test says."""

    def __init__(self, *, accepts: bool = True, actually_moves: bool = True) -> None:
        self.state: dict[tuple[str, str], Any] = {("kitchen_valve", "valve.state"): "open"}
        self.commands: list[Any] = []
        self._accepts = accepts
        self._moves = actually_moves

    async def execute_capability_command(self, command: Any) -> CommandResult:
        self.commands.append(command)
        if not self._accepts:
            return CommandResult(accepted=False, reason="VALVE_UNREACHABLE")
        if self._moves:
            self.state[(command.device_id, command.capability)] = command.value
        return CommandResult(accepted=True)

    async def read(self, device_id: str, capability: str) -> Any:
        return self.state.get((device_id, capability))


def alarming_home(*, with_valve: bool = True):  # type: ignore[no-untyped-def]
    devices = [
        device("gas_kitchen", "kitchen", a=reading("safety.gas_alarm", True, NOW)),
    ]
    if with_valve:
        devices.append(device("kitchen_valve", "kitchen", a=reading("valve.state", "open", NOW)))
    return home(*devices, home_id=HOME)


def build(gateway: ValveGateway, environment: str = "production"):  # type: ignore[no-untyped-def]
    policy = PolicyService()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision=policy.get,
        config=OrchestratorConfig(environment=environment, verify_delay_seconds=0.0),
    )
    return policy, orchestrator


def confirmed_plan(*, with_valve: bool = True):  # type: ignore[no-untyped-def]
    state = alarming_home(with_valve=with_valve)
    confirmations = SafetyGovernor().evaluate(HOME, state, NOW)
    assert len(confirmations) == 1, "the certified gas reading should confirm exactly once"
    return plan_response(confirmations[0], state, NOW)


# ── the happy path, which is the whole point ──


async def test_a_confirmed_gas_alarm_closes_the_valve_without_asking() -> None:
    gateway = ValveGateway()
    policy, orchestrator = build(gateway)

    outcomes = await dispatch_isolation(confirmed_plan(), HOME, policy, orchestrator, NOW)

    assert len(outcomes) == 1
    outcome = outcomes[0]
    assert outcome.succeeded
    assert outcome.reason_code == "ISOLATION_VERIFIED"
    assert await gateway.read("kitchen_valve", "valve.state") == "closed"


async def test_the_household_is_told_as_well_as_the_valve_being_closed() -> None:
    """Closing silently would be worse than not closing.

    People need to know the supply is off, and why, before they go looking for
    a pilot light that will not relight.
    """
    plan = confirmed_plan()
    assert len(plan.notifications) == 1
    assert len(plan.isolating) == 1


async def test_no_model_is_involved_in_the_chain() -> None:
    """The governor confirms from the certified reading alone.

    Nothing in this test constructs a recommendation, a model reference or a
    confidence score, and the isolation still happens — which is the property
    spec §0 rule 2 asks for stated the other way round.
    """
    gateway = ValveGateway()
    policy, orchestrator = build(gateway)
    outcomes = await dispatch_isolation(confirmed_plan(), HOME, policy, orchestrator, NOW)
    assert outcomes[0].succeeded

    decision = next(iter(policy.decisions.values()))
    assert decision.recommendation_id is None
    assert "AUTHORIZED_BY_SAFETY_GOVERNOR" in decision.reason_codes
    assert decision.safety_class is SafetyClass.LIFE_SAFETY_CRITICAL


# ── the direction, which is what makes this safe to have at all ──


async def test_nothing_in_the_isolation_path_can_open_a_valve() -> None:
    with pytest.raises(ValueError, match=re.escape("may only drive valve.state to 'closed'")):
        ResponseStep(stage=ResponseStage.ISOLATE, capability="valve.state", intended_value="open")


async def test_the_dispatcher_rechecks_the_direction_it_was_handed() -> None:
    """The planner already refuses the wrong direction. So does this.

    The dispatcher can be called by anything, and a check that only exists
    upstream is a check that a new caller skips.
    """
    plan = confirmed_plan()
    forged = object.__new__(ResponseStep)
    object.__setattr__(forged, "stage", ResponseStage.ISOLATE)
    object.__setattr__(forged, "capability", "valve.state")
    object.__setattr__(forged, "intended_value", "open")
    object.__setattr__(forged, "device_id", "kitchen_valve")
    object.__setattr__(forged, "room_id", "kitchen")
    object.__setattr__(forged, "reachable", True)
    object.__setattr__(forged, "detail", "")
    object.__setattr__(plan, "steps", (forged,))

    gateway = ValveGateway()
    policy, orchestrator = build(gateway)
    with pytest.raises(IsolationRefused, match="NOT_THE_FAIL_SAFE_DIRECTION"):
        await dispatch_isolation(plan, HOME, policy, orchestrator, NOW)
    assert gateway.commands == [], "a forged step must not reach the device"


async def test_policy_refuses_to_authorize_reopening_a_supply() -> None:
    policy, _ = build(ValveGateway())
    with pytest.raises(ValueError, match=re.escape("may only drive valve.state to 'closed'")):
        policy.authorize_safety_isolation(
            home_id=HOME,
            capability="valve.state",
            value="open",
            confirmed_by="rule:gas_confirmed@1.0.0",
            now=NOW,
        )


async def test_policy_refuses_to_authorize_a_comfort_device_as_an_isolation() -> None:
    policy, _ = build(ValveGateway())
    with pytest.raises(ValueError, match="not governed by a deterministic safety rule"):
        policy.authorize_safety_isolation(
            home_id=HOME,
            capability="light.power",
            value=False,
            confirmed_by="rule:gas_confirmed@1.0.0",
            now=NOW,
        )


async def test_an_isolation_must_name_the_confirmation_that_authorized_it() -> None:
    policy, _ = build(ValveGateway())
    with pytest.raises(ValueError, match="must name the confirmation"):
        policy.authorize_safety_isolation(
            home_id=HOME,
            capability="valve.state",
            value="closed",
            confirmed_by="",
            now=NOW,
        )


# ── the failures, which are the ones a pilot will actually meet ──


async def test_a_home_with_no_valve_reports_it_loudly_rather_than_silently() -> None:
    gateway = ValveGateway()
    policy, orchestrator = build(gateway)

    outcomes = await dispatch_isolation(
        confirmed_plan(with_valve=False), HOME, policy, orchestrator, NOW
    )

    assert len(outcomes) == 1
    assert outcomes[0].needs_escalation
    assert outcomes[0].reason_code == "NO_REACHABLE_ISOLATION_DEVICE"
    assert gateway.commands == []


async def test_a_valve_that_refuses_the_command_is_not_reported_as_closed() -> None:
    gateway = ValveGateway(accepts=False)
    policy, orchestrator = build(gateway)

    outcomes = await dispatch_isolation(confirmed_plan(), HOME, policy, orchestrator, NOW)

    assert outcomes[0].needs_escalation
    assert not outcomes[0].succeeded
    assert await gateway.read("kitchen_valve", "valve.state") == "open"


async def test_a_valve_that_accepts_and_does_not_move_is_not_reported_as_closed() -> None:
    """The failure mode that a naive implementation misses.

    The command was accepted. Nothing errored. The gas is still flowing, and
    only the read-back knows.
    """
    gateway = ValveGateway(actually_moves=False)
    policy, orchestrator = build(gateway)

    outcomes = await dispatch_isolation(confirmed_plan(), HOME, policy, orchestrator, NOW)

    assert not outcomes[0].succeeded
    assert outcomes[0].needs_escalation
    assert outcomes[0].status != ActionStatus.SUCCEEDED.value or not outcomes[0].verified


# ── still blocked where it must be ──


async def test_development_still_blocks_the_valve() -> None:
    """Spec §0 rule 16, unchanged by this decision.

    A development machine has no gas valve, and a simulation that closed one
    would be closing something real by accident.
    """
    gateway = ValveGateway()
    policy, orchestrator = build(gateway, environment="development")

    outcomes = await dispatch_isolation(confirmed_plan(), HOME, policy, orchestrator, NOW)

    assert outcomes[0].needs_escalation
    assert gateway.commands == [], "no command may reach a critical actuator in development"
    assert await gateway.read("kitchen_valve", "valve.state") == "open"


async def test_only_the_gas_response_isolates() -> None:
    """Water still prepares, egress and ventilation are still blocked.

    The decision covered gas. Every other response keeps the posture it had,
    and a test says so rather than a comment.
    """
    from syltra_risk_engine.response import RESPONSE_DEFINITIONS

    isolating = {
        name for name, definition in RESPONSE_DEFINITIONS.items() if definition.get("isolate")
    }
    assert isolating == {"NOTIFY_AND_ISOLATE_GAS"}


async def test_the_fail_safe_map_covers_only_supplies() -> None:
    assert set(FAIL_SAFE_VALUES) == {"valve.state"}
