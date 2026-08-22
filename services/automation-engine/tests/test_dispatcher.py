"""The step between an automation firing and a light coming on.

This did not exist. `ActionOrchestrator.execute` had exactly one caller in the
platform — a person pressing a control — so no automation ever stored here had
turned on anything. These tests are what stops that being true again: the gap
was invisible because every component on both sides of it was correct and
tested.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from syltra_automation_engine import AutomationDispatcher
from syltra_automation_engine.engine import AutomationProposal
from syltra_contracts import ActionStatus, PolicyDecision, PolicyOutcome, SafetyClass
from syltra_contracts.automations import AutomationAction

NOW = datetime(2026, 8, 22, 21, 0, tzinfo=UTC)


def _proposal(
    capability: str = "light.power",
    value: Any = True,
    device_id: str = "light_hall",
    expires_in: float = 300.0,
) -> AutomationProposal:
    return AutomationProposal(
        automation_id=uuid4(),
        home_id="home_1",
        name="hall light at dusk",
        action=AutomationAction(capability=capability, value=value, device_id=device_id),
        triggered_at=NOW,
        expires_at=NOW + timedelta(seconds=expires_in),
        reason_codes=("AUTOMATION_TRIGGERED",),
    )


def _decision(outcome: PolicyOutcome, reasons: list[str]) -> PolicyDecision:
    return PolicyDecision(
        decision_id=uuid4(),
        recommendation_id=None,
        home_id="home_1",
        decision=outcome,
        evaluated_at=NOW,
        expires_at=NOW + timedelta(seconds=60),
        reason_codes=reasons,
        safety_class=SafetyClass.COMFORT,
        policy_version="test",
        input_hash="0" * 8,
    )


class _Policy:
    def __init__(self, outcome: PolicyOutcome, reasons: list[str] | None = None) -> None:
        self.outcome = outcome
        self.reasons = reasons or ["WITHIN_POLICY"]
        self.asked: list[tuple[str, Any]] = []

    def authorize_automation(
        self,
        home_id: str,
        device_id: str | None,
        capability: str,
        value: Any,
        automation_id: str,
        now: datetime | None = None,
    ) -> PolicyDecision:
        self.asked.append((capability, value))
        return _decision(self.outcome, self.reasons)


class _Refusing(_Policy):
    def authorize_automation(self, *args: Any, **kwargs: Any) -> PolicyDecision:
        msg = "valve.state is LIFE_SAFETY_CRITICAL"
        raise ValueError(msg)


class _Result:
    def __init__(self, status: ActionStatus, verified: bool) -> None:
        self.status = status
        self.verified = verified
        self.reason_codes = ["VERIFIED"] if verified else ["NOT_VERIFIED"]


class _Orchestrator:
    def __init__(
        self, status: ActionStatus = ActionStatus.SUCCEEDED, verified: bool = True
    ) -> None:
        self.status = status
        self.verified = verified
        self.executed: list[Any] = []

    async def execute(self, request: Any, now: datetime | None = None) -> _Result:
        self.executed.append(request)
        return _Result(self.status, self.verified)


class _Exploding(_Orchestrator):
    async def execute(self, request: Any, now: datetime | None = None) -> _Result:
        msg = "the device is not there"
        raise RuntimeError(msg)


async def test_an_automation_reaches_the_device() -> None:
    """The whole point. Before this, a household could write a rule, watch a
    test run say it would fire, enable it, and wait forever."""
    policy, orchestrator = _Policy(PolicyOutcome.ALLOW), _Orchestrator()
    outcome = await AutomationDispatcher(policy, orchestrator).dispatch(_proposal(), NOW)

    assert outcome.carried_out is True
    assert len(orchestrator.executed) == 1
    request = orchestrator.executed[0]
    assert request.target.device_id == "light_hall"
    assert request.value is True
    # The audit trail can name the rule that did it, and finds no model.
    assert "automation_id" in request.metadata


@pytest.mark.parametrize(
    "outcome",
    [PolicyOutcome.DENY, PolicyOutcome.REQUIRE_USER_APPROVAL, PolicyOutcome.PREPARE_ONLY],
)
async def test_only_allow_reaches_a_device(outcome: PolicyOutcome) -> None:
    """Anything the gate did not permit stops at the gate, and says why."""
    policy = _Policy(outcome, ["RECENT_MANUAL_OVERRIDE"])
    orchestrator = _Orchestrator()
    result = await AutomationDispatcher(policy, orchestrator).dispatch(_proposal(), NOW)

    assert orchestrator.executed == []
    assert result.carried_out is False
    assert result.reason_codes == ("RECENT_MANUAL_OVERRIDE",)


async def test_a_proposal_that_waited_out_its_window_is_not_dispatched_late() -> None:
    """§0: every action is time-bounded. The house has moved on, and a light
    answering a condition that stopped being true is worse than one that never
    answered."""
    policy, orchestrator = _Policy(PolicyOutcome.ALLOW), _Orchestrator()
    stale = _proposal(expires_in=1.0)
    result = await AutomationDispatcher(policy, orchestrator).dispatch(
        stale, NOW + timedelta(seconds=30)
    )

    assert orchestrator.executed == []
    assert result.reason_codes == ("PROPOSAL_EXPIRED",)
    # Not even asked: an expired proposal does not consume a policy decision.
    assert policy.asked == []


async def test_a_command_nothing_read_back_is_not_a_light_that_came_on() -> None:
    policy = _Policy(PolicyOutcome.ALLOW)
    orchestrator = _Orchestrator(status=ActionStatus.SUCCEEDED, verified=False)
    result = await AutomationDispatcher(policy, orchestrator).dispatch(_proposal(), NOW)

    assert result.status == "SUCCEEDED"
    assert result.carried_out is False


async def test_one_unplugged_device_does_not_lose_the_rest() -> None:
    """A bedroom lamp somebody unplugged should not stop the automation that
    was going to light the hall."""
    dispatcher = AutomationDispatcher(_Policy(PolicyOutcome.ALLOW), _Exploding())
    outcomes = await dispatcher.dispatch_all((_proposal(), _proposal()), NOW)

    assert len(outcomes) == 2
    assert all(o.reason_codes == ("DISPATCH_FAILED",) for o in outcomes)


async def test_something_outside_comfort_is_a_fault_not_a_command() -> None:
    """`AutomationAction` refuses to be built with one, so arriving here means
    a request was assembled some other way — reported, never dispatched."""
    orchestrator = _Orchestrator()
    dispatcher = AutomationDispatcher(_Refusing(PolicyOutcome.ALLOW), orchestrator)
    result = await dispatcher.dispatch(_proposal(), NOW)

    assert orchestrator.executed == []
    assert result.reason_codes == ("NOT_AUTOMATABLE",)
