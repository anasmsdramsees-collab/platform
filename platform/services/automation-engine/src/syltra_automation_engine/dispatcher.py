"""Carrying out an automation (spec §2.3, §14).

The engine evaluates and proposes. The driver calls it on a timer. And between
the proposal and the light there was nothing at all: `ActionOrchestrator.execute`
had exactly one caller in the whole platform — a person pressing a control — so
**no automation this platform has ever stored has turned on a light.** A
household could write one, test-run it, watch the test say it would fire, enable
it, and wait forever.

This is the missing piece, and it is deliberately the same shape as
`IsolationDispatcher` in the risk engine: the two things that turn a decision
into a command should be recognisable as the same kind of object, and differ
only in what they are permitted to touch. That one may close a valve on a
certified alarm. This one cannot reach a valve at all — `AutomationAction`
refuses to be constructed with anything outside NON_CRITICAL and COMFORT, so the
restriction is upstream of every path that leads here.

## What stands between a rule and a device

    automation fires (deterministic, no model anywhere)
      → PolicyService.authorize_automation decides: a confirmed hazard stops
        it, a person who just touched the device overrides it, the rate limit
        holds
      → only ALLOW proceeds; every other outcome is reported and dropped
      → ActionOrchestrator executes, verifies, and compensates if it must

## Why an automation is neither a recommendation nor a press

There were two existing paths and this fits neither, which is why the policy
service has a third gate rather than a reused one.

`evaluate` weighs a **recommendation**: confidence, learning mode, quiet hours,
shadow. All of it judges *SYLTRA's* judgement, and a rule a household wrote is
not SYLTRA's judgement. Forcing one through it would also have meant inventing a
`Recommendation` with a fake model reference — which the audit trail would later
show as a model's decision, to somebody trying to work out what turned on a
light.

`authorize_manual_control` is a **person**, present and deciding, and §0 rule 5
lets that override adaptive behaviour. An automation is the house acting on its
own at three in the morning with nobody in the room. It must not inherit the
authority of somebody's hand on a switch.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from syltra_action_orchestrator import build_rule_action
from syltra_contracts import PolicyDecision, PolicyOutcome

from syltra_automation_engine.engine import AutomationProposal

logger = logging.getLogger(__name__)

class _Policy(Protocol):
    def authorize_automation(
        self,
        home_id: str,
        device_id: str | None,
        capability: str,
        value: Any,
        automation_id: str,
        now: datetime | None = ...,
    ) -> PolicyDecision: ...


class _Executor(Protocol):
    async def execute(self, request: Any, now: datetime | None = ...) -> Any: ...


@dataclass(frozen=True)
class DispatchOutcome:
    """What happened to one proposal, stated without euphemism."""

    automation_id: Any
    name: str
    capability: str
    device_id: str | None
    intended_value: Any
    outcome: str
    """The policy outcome — ALLOW, DENY, REQUIRE_USER_APPROVAL, and so on."""
    status: str | None
    """The action's status, or None when policy stopped it before dispatch."""
    verified: bool
    reason_codes: tuple[str, ...]

    @property
    def carried_out(self) -> bool:
        """True only when the device confirmed the new state.

        A dispatched command nothing read back is not a light that came on. It
        is a command that was sent.
        """
        return self.status == "SUCCEEDED" and self.verified


class AutomationDispatcher:
    """Turns automation proposals into commands, one policy gate at a time."""

    def __init__(self, policy: _Policy, orchestrator: _Executor) -> None:
        self._policy = policy
        self._orchestrator = orchestrator

    async def dispatch(
        self, proposal: AutomationProposal, now: datetime | None = None
    ) -> DispatchOutcome:
        moment = now or datetime.now(tz=UTC)

        if proposal.is_expired_at(moment):
            # §0: every action is time-bounded. A proposal that waited out its
            # own window is not dispatched late — the house has moved on, and
            # the household would be watching a light answer a condition that
            # stopped being true.
            return self._refused(proposal, "PROPOSAL_EXPIRED")

        action = proposal.action
        try:
            decision = self._policy.authorize_automation(
                proposal.home_id,
                action.device_id,
                action.capability,
                action.value,
                automation_id=str(proposal.automation_id),
                now=moment,
            )
        except ValueError:
            # The capability is outside what an automation may touch. It should
            # have been impossible to build, so this is a fault worth a trace
            # rather than a quiet skip.
            logger.exception("automation %s asked for something it may not", proposal.automation_id)
            return self._refused(proposal, "NOT_AUTOMATABLE")

        if decision.decision is not PolicyOutcome.ALLOW:
            logger.info(
                "automation %s not dispatched: %s (%s)",
                proposal.automation_id,
                decision.decision.value,
                ", ".join(decision.reason_codes),
            )
            return DispatchOutcome(
                automation_id=proposal.automation_id,
                name=proposal.name,
                capability=action.capability,
                device_id=action.device_id,
                intended_value=action.value,
                outcome=decision.decision.value,
                status=None,
                verified=False,
                reason_codes=tuple(decision.reason_codes),
            )

        request = build_rule_action(
            decision,
            action.device_id,
            action.capability,
            action.value,
            room_id=action.room_id,
            now=moment,
            metadata={"automation_id": str(proposal.automation_id), "name": proposal.name},
        )
        result = await self._orchestrator.execute(request, moment)
        return DispatchOutcome(
            automation_id=proposal.automation_id,
            name=proposal.name,
            capability=action.capability,
            device_id=action.device_id,
            intended_value=action.value,
            outcome=decision.decision.value,
            status=result.status.value,
            verified=bool(getattr(result, "verified", False)),
            reason_codes=tuple(result.reason_codes),
        )

    async def dispatch_all(
        self, proposals: tuple[AutomationProposal, ...], now: datetime | None = None
    ) -> tuple[DispatchOutcome, ...]:
        """Carry out each proposal, and never let one failure lose the rest.

        A device that has been unplugged should not stop the automation that
        was going to turn on a light in another room.
        """
        outcomes: list[DispatchOutcome] = []
        for proposal in proposals:
            try:
                outcomes.append(await self.dispatch(proposal, now))
            except Exception:
                logger.exception("dispatching automation %s failed", proposal.automation_id)
                outcomes.append(self._refused(proposal, "DISPATCH_FAILED"))
        return tuple(outcomes)

    # ── the parts ──

    def _refused(self, proposal: AutomationProposal, reason_code: str) -> DispatchOutcome:
        return DispatchOutcome(
            automation_id=proposal.automation_id,
            name=proposal.name,
            capability=proposal.action.capability,
            device_id=proposal.action.device_id,
            intended_value=proposal.action.value,
            outcome="NOT_DISPATCHED",
            status=None,
            verified=False,
            reason_codes=(reason_code,),
        )
