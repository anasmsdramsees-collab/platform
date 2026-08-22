"""Carrying out an isolation (spec §20.5, owner decision of 2026-08-20).

`response.py` decides *what* a confirmed hazard isolates and refuses to build a
step pointing the wrong way. This module is the only thing that turns such a
step into a command a device receives.

It is a separate module for the same reason the planner has no gateway import:
the ability to plan and the ability to act should not live in one object. A
future edit that gives the risk engine a dispatcher has to add this dependency
explicitly at the composition root, where somebody will see it.

## What stands between a detector and a valve

    certified gas reading
      → Safety Governor confirms, deterministically, from that reading alone
      → plan_response builds an ISOLATE step, direction-locked to "closed"
      → PolicyService.authorize_safety_isolation mints a fixed-rule ALLOW
      → ActionOrchestrator executes it, blocking critical actuators outside
        production (safety invariant 16) and verifying the resulting state
      → an unverified close escalates; it never reports success

No model is anywhere in that chain, and none can be: the governor accepts
evidence only from certified alarm capabilities, and this module refuses any
step the planner did not mark ISOLATE.

## What it will not do

Reopen. There is no function here that sets a valve to "open", and the step it
consumes cannot carry that value. After a leak, a person reopens the supply —
having found out why it leaked. A platform that reopened on its own would be
restoring gas flow to a house whose fault it cannot see.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from syltra_contracts import ActionStatus, PolicyDecision

from syltra_risk_engine.response import FAIL_SAFE_VALUES, ResponsePlan, ResponseStage, ResponseStep

logger = logging.getLogger(__name__)


class IsolationRefused(RuntimeError):
    """The isolation could not even be attempted.

    Distinct from a failed attempt: this means the platform declined to try,
    and the household needs telling either way.
    """

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail


class _Authorizer(Protocol):
    def authorize_safety_isolation(
        self,
        home_id: str,
        capability: str,
        value: Any,
        confirmed_by: str,
        reason_codes: list[str],
        now: datetime | None = ...,
    ) -> PolicyDecision: ...


class _Executor(Protocol):
    async def execute(self, request: Any, now: datetime | None = ...) -> Any: ...


@dataclass(frozen=True)
class IsolationOutcome:
    """What happened to one isolation, stated without euphemism."""

    capability: str
    device_id: str | None
    intended_value: Any
    status: str
    verified: bool
    reason_code: str
    detail: str

    @property
    def succeeded(self) -> bool:
        """True only when the device confirmed the new state.

        A dispatched command that nothing read back is not a closed valve. It
        is a command that was sent.
        """
        return self.status == ActionStatus.SUCCEEDED.value and self.verified

    @property
    def needs_escalation(self) -> bool:
        return not self.succeeded


async def dispatch_isolation(
    plan: ResponsePlan,
    home_id: str,
    policy: _Authorizer,
    orchestrator: _Executor,
    now: datetime | None = None,
) -> tuple[IsolationOutcome, ...]:
    """Carry out every ISOLATE step in a plan, and report honestly on each.

    Never raises for a failed isolation — a valve that would not close is a
    result the caller must act on, not an exception to lose in a log. It raises
    only when handed something that is not an isolation at all, which is a
    programming error rather than a household event.
    """
    moment = now or datetime.now(tz=UTC)
    outcomes: list[IsolationOutcome] = []
    for step in plan.isolating:
        outcomes.append(await _isolate_one(step, home_id, plan, policy, orchestrator, moment))
    return tuple(outcomes)


async def _isolate_one(
    step: ResponseStep,
    home_id: str,
    plan: ResponsePlan,
    policy: _Authorizer,
    orchestrator: _Executor,
    now: datetime,
) -> IsolationOutcome:
    # Re-checked here rather than trusted from the planner. This module can be
    # called with any step, and the direction constraint is the one thing that
    # must not depend on the caller having been careful.
    if step.stage is not ResponseStage.ISOLATE:
        msg = f"{step.stage.value} is not an isolation"
        raise IsolationRefused("NOT_AN_ISOLATION", msg)
    fail_safe = FAIL_SAFE_VALUES.get(step.capability)
    if fail_safe is None or step.intended_value != fail_safe:
        msg = f"{step.capability} to {step.intended_value!r} is not the fail-safe direction"
        raise IsolationRefused("NOT_THE_FAIL_SAFE_DIRECTION", msg)

    def failure(reason_code: str, detail: str) -> IsolationOutcome:
        logger.error(
            "SAFETY: isolation of %s for %s not carried out — %s (%s)",
            step.capability,
            home_id,
            reason_code,
            detail,
        )
        return IsolationOutcome(
            capability=step.capability,
            device_id=step.device_id,
            intended_value=step.intended_value,
            status="NOT_ATTEMPTED",
            verified=False,
            reason_code=reason_code,
            detail=detail,
        )

    if step.device_id is None or not step.reachable:
        # The most important failure to report loudly. A confirmed gas hazard
        # in a home whose valve cannot be reached is exactly the situation
        # where silence reads as safety.
        return failure(
            "NO_REACHABLE_ISOLATION_DEVICE",
            f"no reachable device offers {step.capability}",
        )

    decision = policy.authorize_safety_isolation(
        home_id=home_id,
        capability=step.capability,
        value=step.intended_value,
        confirmed_by=plan.confirmed_by,
        reason_codes=[*_reason_codes(plan)],
        now=now,
    )

    request = _build_request(step, home_id, decision, now)
    try:
        result = await orchestrator.execute(request, now=now)
    except Exception as exc:  # noqa: BLE001 - every failure mode reports the same way
        return failure(type(exc).__name__.upper(), str(exc))

    status: Any = getattr(result, "status", None)
    status_value = str(getattr(status, "value", status))
    verified = bool(getattr(result, "verified", False))
    outcome = IsolationOutcome(
        capability=step.capability,
        device_id=step.device_id,
        intended_value=step.intended_value,
        status=status_value,
        verified=verified,
        reason_code="ISOLATION_VERIFIED" if verified else "ISOLATION_UNVERIFIED",
        detail=(
            "the device reports the supply closed"
            if verified
            else "the command was sent and the device did not confirm the new state"
        ),
    )
    if outcome.needs_escalation:
        logger.error(
            "SAFETY: isolation of %s for %s is %s and unverified",
            step.capability,
            home_id,
            status_value,
        )
    return outcome


def _reason_codes(plan: ResponsePlan) -> tuple[str, ...]:
    return ("DETERMINISTIC_SAFETY_RULE", f"RESPONSE_{plan.response}")


def _build_request(
    step: ResponseStep, home_id: str, decision: PolicyDecision, now: datetime
) -> Any:
    from datetime import timedelta

    from syltra_contracts import ActionRequest, ActionTarget, ExpectedState
    from syltra_contracts.capability_definitions import get_definition

    definition = get_definition(step.capability)
    return ActionRequest(
        action_id=uuid4(),
        # Deterministic in the decision, so a governor that confirms twice in
        # one incident does not close the valve twice.
        idempotency_key=f"{home_id}:{decision.decision_id}:{step.capability}",
        decision_id=decision.decision_id,
        home_id=home_id,
        correlation_id=uuid4(),
        target=ActionTarget(
            device_id=step.device_id or "",
            capability=step.capability,
            room_id=step.room_id,
        ),
        value=step.intended_value,
        expected_state=ExpectedState(
            capability=step.capability, value=step.intended_value
        ),
        safety_class=definition.safety_class,
        created_at=now,
        # Short. An isolation that has not gone out within a minute of a
        # confirmed gas alarm should not go out later, when the household may
        # already have opened windows and left.
        expires_at=now + timedelta(seconds=60),
    )
