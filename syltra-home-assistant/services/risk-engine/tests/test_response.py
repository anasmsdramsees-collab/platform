"""What a confirmed hazard authorizes, and what it must never do (spec §20.4).

The safety-case gap this closes was recorded as "the authorized responses are
not wired to the Action Orchestrator". Half of that is now built — the half
that operates nothing — and the other half is refused here by construction
rather than by not having got round to it.

The guarantee every test below defends: **nothing on this path can dispatch.**
"""

import ast
import inspect
import re
from datetime import UTC, datetime

import pytest
from syltra_contracts.capability_definitions import Confirmation, get_definition
from syltra_digital_twin.core import HomeState
from syltra_risk_engine import response as response_module
from syltra_risk_engine.governor import CONFIRMATION_RULES, SafetyGovernor
from syltra_risk_engine.governor import Confirmation as HazardConfirmation
from syltra_risk_engine.response import (
    FAIL_SAFE_VALUES,
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
def test_the_response_path_has_no_general_execute_stage() -> None:
    # ISOLATE replaced nothing: it was added beside NOTIFY and PREPARE when the
    # owner decided a confirmed gas hazard closes the valve. What is still
    # absent is a stage that could drive any capability to any value.
    assert {stage.value for stage in ResponseStage} == {"NOTIFY", "PREPARE", "ISOLATE"}


@pytest.mark.safety
def test_an_isolate_step_cannot_open_a_valve() -> None:
    # The whole safety of the ISOLATE stage is that it points one way. A
    # confirmed hazard closes a gas supply; nothing here reopens one, because
    # reopening into an unrepaired leak is the hazard, not the recovery.
    with pytest.raises(ValueError, match=re.escape("may only drive valve.state to 'closed'")):
        ResponseStep(
            stage=ResponseStage.ISOLATE,
            capability="valve.state",
            intended_value="open",
        )


@pytest.mark.safety
def test_every_isolable_capability_declares_exactly_one_fail_safe_value() -> None:
    # A capability with two acceptable isolation values has a direction the
    # caller chooses, which is the thing this stage exists to prevent.
    for capability, value in FAIL_SAFE_VALUES.items():
        assert not isinstance(value, (list, set, tuple, frozenset)), capability
        definition = get_definition(capability)
        assert definition.confirmation is Confirmation.DETERMINISTIC_SAFETY_RULE, capability
        if definition.allowed_values:
            assert value in definition.allowed_values, capability


@pytest.mark.safety
def test_a_deterministic_capability_with_no_fail_safe_value_cannot_be_isolated() -> None:
    # `siren.state` passes the deterministic-rule gate and still cannot be
    # isolated, because nobody has decided which way is safe for it. Sounding a
    # siren is not cutting a supply, and silencing one during a fire is worse.
    assert "siren.state" not in FAIL_SAFE_VALUES
    with pytest.raises(ValueError, match="no fail-safe value"):
        ResponseStep(
            stage=ResponseStage.ISOLATE,
            capability="siren.state",
            intended_value="off",
        )


@pytest.mark.safety
def test_a_comfort_capability_never_reaches_the_direction_check() -> None:
    with pytest.raises(ValueError, match="does not require a deterministic safety rule"):
        ResponseStep(
            stage=ResponseStage.ISOLATE,
            capability="light.power",
            intended_value=False,
        )


@pytest.mark.safety
def test_no_response_definition_isolates_something_that_is_not_a_supply() -> None:
    # Reached through the definitions rather than the constructor, because a
    # response definition is where a future edit would try to add one.
    for response, definition in RESPONSE_DEFINITIONS.items():
        isolate = definition.get("isolate")
        if isolate is None:
            continue
        capability, value = isolate
        assert capability in FAIL_SAFE_VALUES, f"{response} isolates {capability}"
        assert value == FAIL_SAFE_VALUES[capability], f"{response} isolates the wrong way"


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


def test_a_gas_confirmation_closes_the_valve_and_says_so() -> None:
    confirmation, state = confirmed_gas()
    plan = plan_response(confirmation, state, NOW)

    assert len(plan.notifications) == 1
    assert plan.notifications[0].capability == NOTIFICATION_CAPABILITY

    # Gas isolates rather than prepares: the reading is the hazard, and a
    # household asked to approve a shutoff is a household breathing gas while
    # it decides.
    assert plan.prepared == ()
    assert len(plan.isolating) == 1
    isolating = plan.isolating[0]
    assert isolating.capability == "valve.state"
    assert isolating.intended_value == "closed"
    assert isolating.device_id == "kitchen_valve"
    assert isolating.reachable
    assert "told, not asked" in isolating.detail


@pytest.mark.safety
def test_a_water_confirmation_still_only_prepares() -> None:
    # A leak damages property; gas kills people. The decision that was made
    # covered gas, and quietly extending it to water would be a decision
    # nobody made.
    assert RESPONSE_DEFINITIONS["NOTIFY_AND_PREPARE_WATER_ISOLATION"]["isolate"] is None
    assert RESPONSE_DEFINITIONS["NOTIFY_AND_PREPARE_WATER_ISOLATION"]["prepare"] is not None


def test_the_plan_prefers_a_valve_in_the_affected_room() -> None:
    confirmation, state = confirmed_gas(valve_room="kitchen")
    assert plan_response(confirmation, state, NOW).isolating[0].device_id == "kitchen_valve"


@pytest.mark.safety
def test_an_isolation_with_no_reachable_valve_is_reported_not_hidden() -> None:
    # An isolation that names no valve is a shutoff that fails at the moment it
    # matters. Now that the platform closes the valve itself, this is the case
    # where it cannot — and silence would read as success.
    confirmation, state = confirmed_gas(with_valve=False)
    plan = plan_response(confirmation, state, NOW)
    assert plan.isolating
    assert plan.unreachable == plan.isolating
    assert plan.isolating[0].device_id is None
    assert "no reachable device" in plan.isolating[0].detail


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
