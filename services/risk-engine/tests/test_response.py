"""What a confirmed hazard authorizes, and what it must never do (spec §20.4).

The safety-case gap this closes was recorded as "the authorized responses are
not wired to the Action Orchestrator". Half of that is now built — the half
that operates nothing — and the other half is refused here by construction
rather than by not having got round to it.

The guarantee every test below defends: **nothing on this path can dispatch.**
"""

import ast
import inspect
from datetime import UTC, datetime

import pytest
from syltra_contracts.capability_definitions import Confirmation, get_definition
from syltra_digital_twin.core import HomeState
from syltra_risk_engine import response as response_module
from syltra_risk_engine.governor import CONFIRMATION_RULES, SafetyGovernor
from syltra_risk_engine.governor import Confirmation as HazardConfirmation
from syltra_risk_engine.response import (
    NOTIFICATION_CAPABILITY,
    RESPONSE_DEFINITIONS,
    ResponsePlan,
    ResponseStage,
    ResponseStep,
    UnknownResponse,
    plan_response,
)
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

NOW = datetime(2026, 8, 20, 3, 15, tzinfo=UTC)
HOME = "home_001"


def confirmed_gas(
    with_valve: bool = True, valve_room: str = "kitchen"
) -> tuple[HazardConfirmation, HomeState]:
    devices = [device("gas_kitchen", "kitchen", gas=reading("safety.gas_alarm", True, NOW))]
    if with_valve:
        devices.append(
            device(valve_room + "_valve", valve_room, v=reading("valve.state", "open", NOW))
        )
    state = home(*devices, home_id=HOME)
    governor = SafetyGovernor()
    confirmations = governor.evaluate(HOME, state, NOW)
    return next(c for c in confirmations if c.authorized_response.startswith("NOTIFY")), state


# ── the guarantee ──


@pytest.mark.safety
def test_the_response_path_has_no_execute_stage() -> None:
    # Structural, not conventional. There is no value a step could carry that
    # means "execute", so no caller can construct one — and adding one means
    # editing the enum and failing this test, which is the point.
    assert {stage.value for stage in ResponseStage} == {"NOTIFY", "PREPARE"}


@pytest.mark.safety
def test_nothing_in_the_response_module_can_reach_a_device() -> None:
    # A planner that imported a gateway would be one refactor away from
    # sending. It imports none, and calls nothing that could.
    #
    # Checked on the parsed tree, not the text: this module's own docstring
    # explains that it never reaches a gateway, and a substring search reports
    # the explanation as the offence.
    tree = ast.parse(inspect.getsource(response_module))

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported |= {alias.name for alias in node.names}
    for name in imported:
        lowered = name.lower()
        for forbidden in ("gateway", "orchestrator", "action"):
            assert forbidden not in lowered, f"the planner imports {name}"

    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    for forbidden in ("execute", "dispatch", "execute_capability_command", "send", "publish"):
        assert forbidden not in called, f"the planner calls {forbidden}()"


@pytest.mark.safety
def test_a_notify_step_can_only_send_a_message() -> None:
    # Without this, a valve command labelled NOTIFY would walk past every check
    # that reads the stage rather than the capability.
    with pytest.raises(ValueError, match=r"may only use notification\.send"):
        ResponseStep(
            stage=ResponseStage.NOTIFY,
            capability="valve.state",
            intended_value="closed",
        )


@pytest.mark.safety
def test_a_prepare_step_must_target_something_that_needs_a_safety_rule() -> None:
    # Preparing a light is not a hazard response, and letting it be one would
    # blur what "prepared" means.
    with pytest.raises(ValueError, match="does not require a deterministic safety rule"):
        ResponseStep(
            stage=ResponseStage.PREPARE,
            capability="light.power",
            intended_value=True,
        )


@pytest.mark.safety
def test_notification_is_the_only_capability_the_plan_may_actually_use() -> None:
    # The one capability on this path that is NON_CRITICAL and needs no
    # confirmation — which is exactly why notifying is safe to carry out and
    # everything else is not.
    definition = get_definition(NOTIFICATION_CAPABILITY)
    assert definition.confirmation is Confirmation.NONE
    assert definition.safety_class.value == "NON_CRITICAL"


# ── the plan ──


def test_every_confirmation_rule_has_a_response_definition() -> None:
    # A confirmed hazard whose response nobody defined must not pass silently
    # as "nothing to do".
    for rule in CONFIRMATION_RULES:
        assert rule.response in RESPONSE_DEFINITIONS, rule.rule_id


def test_an_undefined_response_is_refused_rather_than_ignored() -> None:
    confirmation, _ = confirmed_gas()
    renamed = type(confirmation)(
        **{**confirmation.__dict__, "authorized_response": "NOTIFY_AND_INVENT_SOMETHING"}
    )
    with pytest.raises(UnknownResponse):
        plan_response(renamed, None, NOW)


def test_a_gas_confirmation_notifies_and_prepares_the_valve() -> None:
    confirmation, state = confirmed_gas()
    plan = plan_response(confirmation, state, NOW)

    assert len(plan.notifications) == 1
    assert plan.notifications[0].capability == NOTIFICATION_CAPABILITY

    assert len(plan.prepared) == 1
    prepared = plan.prepared[0]
    assert prepared.capability == "valve.state"
    assert prepared.intended_value == "closed"
    assert prepared.device_id == "kitchen_valve"
    assert prepared.reachable
    assert "not sent" in prepared.detail


def test_the_plan_prefers_a_valve_in_the_affected_room() -> None:
    confirmation, state = confirmed_gas(valve_room="kitchen")
    assert plan_response(confirmation, state, NOW).prepared[0].device_id == "kitchen_valve"


@pytest.mark.safety
def test_a_prepared_step_with_no_reachable_valve_is_reported_not_hidden() -> None:
    # A prepared isolation that names no valve is a plan that fails at the
    # moment it matters. The household should learn that now.
    confirmation, state = confirmed_gas(with_valve=False)
    plan = plan_response(confirmation, state, NOW)
    assert plan.prepared
    assert plan.unreachable == plan.prepared
    assert plan.prepared[0].device_id is None
    assert "no reachable device" in plan.prepared[0].detail


@pytest.mark.safety
def test_unlocking_egress_is_named_as_blocked_rather_than_prepared() -> None:
    # There is no half of unlocking a door that changes nothing, so it is not
    # preparable — and saying so is better than a plan that looks complete.
    rule = next(r for r in CONFIRMATION_RULES if r.response == "NOTIFY_AND_UNLOCK_EGRESS")
    definition = RESPONSE_DEFINITIONS[rule.response]
    assert definition["prepare"] is None
    blocked = definition["blocked"]
    assert blocked and blocked[0][0] == "lock.state"


@pytest.mark.safety
def test_every_blocked_action_says_why() -> None:
    # `blocked` is not an error list; it is the honest half of the plan.
    for response, definition in RESPONSE_DEFINITIONS.items():
        for capability, _value, reason in definition["blocked"]:
            assert reason, f"{response} blocks {capability} without saying why"


def test_the_plan_records_what_confirmed_it() -> None:
    # A response with no traceable origin is one nobody can review afterwards.
    confirmation, state = confirmed_gas()
    plan = plan_response(confirmation, state, NOW)
    assert plan.confirmed_by.startswith("rule:")
    assert plan.planned_at == NOW
    assert plan.category
    assert isinstance(plan, ResponsePlan)


@pytest.mark.safety
def test_planning_the_same_confirmation_twice_changes_nothing() -> None:
    # The planner is a pure function of the confirmation and the twin. If it
    # accumulated state, a second hazard could be handled differently from the
    # first for reasons nobody could see.
    confirmation, state = confirmed_gas()
    first = plan_response(confirmation, state, NOW)
    second = plan_response(confirmation, state, NOW)
    assert first == second
