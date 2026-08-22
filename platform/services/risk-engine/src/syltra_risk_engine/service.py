"""Risk Engine service (spec §14.5).

Holds risk cases per home and drives both paths:

- **inference** (`rules.py`) proposes `WATCH` and `PRE_ALERT`;
- **the Safety Governor** (`governor.py`) confirms, and only it.

Spec §14.5 ends with "never dispatch device actions", and this service has no
gateway, no orchestrator, and no command method. A confirmation produces an
*authorized response name*; turning that into a device command remains the
Action Orchestrator's job, under the same policy gate as everything else
(safety invariant 2).
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from syltra_contracts import (
    RiskCase,
    RiskCategory,
    RiskState,
    UnauthorizedRiskTransition,
    assert_risk_transition,
)
from syltra_digital_twin.core import HomeState
from syltra_risk_engine import metrics
from syltra_risk_engine.response import ResponsePlan, plan_response
from syltra_risk_engine.governor import Confirmation, SafetyGovernor
from syltra_risk_engine.rules import RiskInput, RiskProposal, evaluate_all

logger = logging.getLogger(__name__)


@dataclass
class CaseChange:
    case: RiskCase
    previous_state: RiskState | None
    kind: str
    """OPENED, ESCALATED, CONFIRMED, UPDATED, EXPIRED or CLOSED."""


@dataclass
class RiskAudit:
    occurred_at: datetime
    home_id: str
    action: str
    actor: str
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IsolationDispatcher:
    """What a risk engine needs in order to actually close a valve.

    A named pair rather than two loose constructor arguments, so "this risk
    engine can act" is one visible thing in the wiring rather than something a
    reader assembles from two parameters.
    """

    policy: Any
    orchestrator: Any


class RiskEngineService:
    def __init__(
        self,
        governor: SafetyGovernor | None = None,
        isolation: IsolationDispatcher | None = None,
    ) -> None:
        self._cases: dict[str, dict[tuple[RiskCategory, str | None], RiskCase]] = defaultdict(
            dict
        )
        # What each confirmed hazard's response consists of, kept beside the
        # case rather than inside it: a case is a state, a plan is what that
        # state authorizes, and the two are reviewed by different people.
        self._plans: dict[str, dict[tuple[RiskCategory, str | None], ResponsePlan]] = (
            defaultdict(dict)
        )
        # What actually happened when an isolation was carried out. Empty until
        # something outside this service dispatches and reports back — the
        # service plans, it does not act.
        self._isolations: dict[
            str, dict[tuple[RiskCategory, str | None], tuple[Any, ...]]
        ] = {}
        # Absent by default, and that default is the safety property: a risk
        # engine constructed the ordinary way cannot operate anything. Handing
        # it a dispatcher is an explicit act at the composition root, where
        # somebody reviewing the wiring will see it.
        self._isolation = isolation
        self.governor = governor or SafetyGovernor()
        self.audit: list[RiskAudit] = []

    # ── queries ──

    def response_plan(
        self, home_id: str, category: RiskCategory, room_id: str | None = None
    ) -> ResponsePlan | None:
        """What the confirmed hazard in this category authorizes, if any.

        Returns None for an advisory case: only a confirmation authorizes a
        response, so only a confirmation has a plan.
        """
        return self._plans[home_id].get((category, room_id))

    async def carry_out_confirmed_isolations(
        self, home_id: str, now: datetime | None = None
    ) -> tuple[Any, ...]:
        """Close what the confirmed hazards in this home authorize closing.

        Separate from `evaluate` and asynchronous on purpose. Evaluation is
        deterministic, synchronous and safe to run anywhere; closing a valve
        talks to a device and can fail. Fusing them would make every caller of
        `evaluate` — including tests that only want to know what the rules say —
        a caller that might operate a household's gas supply.

        Does nothing at all unless the service was constructed with an
        `IsolationDispatcher`. A risk engine built without one plans and never
        acts, which is what every test outside `test_gas_isolation.py` relies
        on.

        Idempotent by outcome: a plan whose isolation already succeeded is
        skipped, so a driver calling this on a timer does not reclose a valve
        every few seconds.
        """
        if self._isolation is None:
            return ()
        from syltra_risk_engine.isolation import dispatch_isolation

        moment = now or datetime.now(tz=UTC)
        carried: list[Any] = []
        for (category, room_id), plan in list(self._plans[home_id].items()):
            if not plan.isolating:
                continue
            if all(
                self.isolation_carried_out(home_id, category, room_id, step.capability)
                for step in plan.isolating
            ):
                continue
            outcomes = await dispatch_isolation(
                plan,
                home_id,
                self._isolation.policy,
                self._isolation.orchestrator,
                moment,
            )
            self.record_isolation_outcomes(home_id, category, room_id, outcomes)
            carried.extend(outcomes)
        return tuple(carried)

    def isolation_carried_out(
        self,
        home_id: str,
        category: RiskCategory,
        room_id: str | None,
        capability: str,
    ) -> bool:
        """Whether this isolation was actually performed and verified.

        The service plans; it does not dispatch. Something outside it must call
        `dispatch_confirmed_isolations` and hand the outcomes back, and until
        that happens the honest answer is False. A screen that showed a planned
        shutoff as a completed one would be the worst possible lie for this
        particular screen to tell.
        """
        outcomes = self._isolations.get(home_id, {}).get((category, room_id), ())
        return any(o.capability == capability and o.succeeded for o in outcomes)

    def record_isolation_outcomes(
        self,
        home_id: str,
        category: RiskCategory,
        room_id: str | None,
        outcomes: tuple[Any, ...],
    ) -> None:
        """Store what happened when an isolation was carried out."""
        self._isolations.setdefault(home_id, {})[(category, room_id)] = outcomes
        for outcome in outcomes:
            self._record(
                home_id,
                "SAFETY_ISOLATION_VERIFIED" if outcome.succeeded else "SAFETY_ISOLATION_FAILED",
                "risk-engine",
                outcome.reason_code,
                {
                    "capability": outcome.capability,
                    "device_id": outcome.device_id,
                    "status": outcome.status,
                    "verified": outcome.verified,
                    "detail": outcome.detail,
                },
            )

    def response_plans(self, home_id: str) -> list[ResponsePlan]:
        return list(self._plans[home_id].values())


    def open_cases(self, home_id: str, now: datetime | None = None) -> list[RiskCase]:
        moment = now or datetime.now(tz=UTC)
        return sorted(
            (c for c in self._cases[home_id].values() if c.is_active_at(moment)),
            key=lambda c: (c.category.value, c.room_id or ""),
        )

    def case_for(
        self, home_id: str, category: RiskCategory, room_id: str | None = None
    ) -> RiskCase | None:
        return self._cases[home_id].get((category, room_id))

    def has_confirmed_case(self, home_id: str, now: datetime | None = None) -> bool:
        """Used by the Policy Service to suspend comfort automation."""
        return any(c.permits_emergency_response for c in self.open_cases(home_id, now))

    # ── evaluation ──

    def evaluate(
        self,
        home_id: str,
        home: HomeState,
        now: datetime | None = None,
        occupied: bool | None = None,
        cooking: bool = False,
    ) -> list[CaseChange]:
        """Run inference, then the governor. Confirmation always wins.

        Order matters: inference runs first so a developing situation is
        recorded with its context, then the governor is asked whether the
        certified evidence justifies confirmation. A confirmation overrides
        whatever inference concluded — including inference that saw nothing.
        """
        moment = now or datetime.now(tz=UTC)
        advisory: dict[tuple[RiskCategory, str | None], CaseChange] = {}

        inp = RiskInput(home=home, now=moment, occupied=occupied, cooking=cooking)
        for proposal in evaluate_all(inp):
            change = self._apply_proposal(home_id, proposal, moment)
            if change is not None:
                advisory[(proposal.category, proposal.room_id)] = change

        confirmed: list[CaseChange] = []
        for confirmation in self.governor.evaluate(home_id, home, moment):
            key = (confirmation.category, confirmation.room_id)
            # A confirmation in the same pass supersedes whatever inference
            # concluded about that hazard. Publishing both would show consumers
            # a PRE_ALERT that never really held — a UI flash, and a misleading
            # entry in any transition history.
            superseded = advisory.pop(key, None)
            change = self._apply_confirmation(home_id, confirmation, moment, home)
            if superseded is not None:
                change.previous_state = superseded.previous_state
            confirmed.append(change)

        return [*advisory.values(), *confirmed]

    def sweep_expired(self, home_id: str, now: datetime | None = None) -> list[CaseChange]:
        """Age out advisory cases. Confirmed cases never expire on a timer."""
        moment = now or datetime.now(tz=UTC)
        changes: list[CaseChange] = []
        for key, case in list(self._cases[home_id].items()):
            if case.permits_emergency_response or not case.is_open:
                continue
            if case.expires_at is not None and moment >= case.expires_at:
                closed = case.model_copy(
                    update={
                        "state": RiskState.CLOSED,
                        "closed_at": moment,
                        "last_updated_at": moment,
                    }
                )
                self._cases[home_id].pop(key, None)
                changes.append(
                    CaseChange(case=closed, previous_state=case.state, kind="EXPIRED")
                )
                self._record(home_id, "RISK_CASE_EXPIRED", "risk-engine",
                             "advisory case aged out", {"category": case.category.value})
        return changes

    def close(
        self, home_id: str, category: RiskCategory, room_id: str | None = None,
        actor: str = "operator", reason: str = "resolved", now: datetime | None = None,
    ) -> RiskCase | None:
        """Close a case deliberately, recording who ended it."""
        moment = now or datetime.now(tz=UTC)
        case = self._cases[home_id].get((category, room_id))
        if case is None:
            return None
        if case.permits_emergency_response:
            # A confirmed case moves through recovery, never straight to closed.
            recovered = case.model_copy(
                update={"state": RiskState.RECOVERY, "last_updated_at": moment}
            )
            self._cases[home_id][(category, room_id)] = recovered
            self._record(home_id, "RISK_CASE_RECOVERING", actor, reason,
                         {"category": category.value})
            return recovered
        closed = case.model_copy(
            update={"state": RiskState.CLOSED, "closed_at": moment, "last_updated_at": moment}
        )
        self._cases[home_id].pop((category, room_id), None)
        self._record(home_id, "RISK_CASE_CLOSED", actor, reason, {"category": category.value})
        return closed

    # ── internals ──

    def _apply_proposal(
        self, home_id: str, proposal: RiskProposal, now: datetime
    ) -> CaseChange | None:
        key = (proposal.category, proposal.room_id)
        existing = self._cases[home_id].get(key)

        if existing is not None and existing.permits_emergency_response:
            # Inference must not touch a confirmed case. The contract layer
            # would refuse the transition anyway; refusing here keeps the
            # confirmed record pristine rather than relying on the exception.
            self._record(
                home_id, "INFERENCE_IGNORED_ON_CONFIRMED_CASE", "risk-engine",
                "a confirmed case is not modified by inference",
                {"category": proposal.category.value},
            )
            return None

        current_state = existing.state if existing else RiskState.NORMAL
        try:
            assert_risk_transition(current_state, proposal.state, deterministic=False)
        except UnauthorizedRiskTransition:
            logger.error(
                "risk inference attempted an unauthorized transition to %s", proposal.state
            )
            return None

        case = RiskCase(
            case_id=existing.case_id if existing else uuid4(),
            home_id=home_id,
            category=proposal.category,
            state=proposal.state,
            severity=proposal.severity,
            confidence=proposal.confidence,
            opened_at=existing.opened_at if existing else now,
            last_updated_at=now,
            expires_at=now + proposal.ttl,
            evidence=proposal.evidence,
            reason_codes=proposal.reason_codes,
            producer=proposal.producer,
            room_id=proposal.room_id,
            metadata=proposal.metadata,
        )
        self._cases[home_id][key] = case

        if existing is None:
            kind = "OPENED"
        elif existing.state is not proposal.state:
            kind = "ESCALATED"
        elif abs(existing.confidence - proposal.confidence) >= 0.1:
            kind = "UPDATED"
        else:
            return None

        self._record(
            home_id, f"RISK_CASE_{kind}", "risk-engine", ",".join(proposal.reason_codes),
            {
                "category": proposal.category.value,
                "state": proposal.state.value,
                "severity": proposal.severity.value,
                "confidence": proposal.confidence,
                "advisory": True,
            },
        )
        return CaseChange(
            case=case,
            previous_state=existing.state if existing else None,
            kind=kind,
        )

    def _apply_confirmation(
        self,
        home_id: str,
        confirmation: Confirmation,
        now: datetime,
        home: HomeState | None = None,
    ) -> CaseChange:
        key = (confirmation.category, confirmation.room_id)
        existing = self._cases[home_id].get(key)
        current_state = existing.state if existing else RiskState.NORMAL

        if existing is not None and existing.permits_emergency_response:
            return CaseChange(case=existing, previous_state=current_state, kind="UPDATED")

        # The deterministic flag is what makes this transition legal; nothing
        # else in the platform passes it.
        assert_risk_transition(current_state, RiskState.CONFIRMED, deterministic=True)

        case = RiskCase(
            case_id=existing.case_id if existing else uuid4(),
            home_id=home_id,
            category=confirmation.category,
            state=RiskState.CONFIRMED,
            severity=confirmation.severity,
            confidence=1.0,
            opened_at=existing.opened_at if existing else now,
            last_updated_at=now,
            expires_at=None,  # a confirmed case does not age out
            evidence=confirmation.evidence,
            reason_codes=confirmation.reason_codes,
            producer=confirmation.confirmed_by,
            room_id=confirmation.room_id,
            confirmed_by=confirmation.confirmed_by,
            metadata={
                "authorized_response": confirmation.authorized_response,
                **confirmation.metadata,
            },
        )
        # What that response actually consists of, resolved against the home:
        # who is told, which valve would be closed, whether it can be reached,
        # and what this system will not do without approval. The plan operates
        # nothing — see `response.py` — but recording it turns a response name
        # into something a person can read and check.
        plan = plan_response(confirmation, home, now)
        self._plans[home_id][key] = plan
        self._cases[home_id][key] = case
        metrics.CONFIRMATIONS.labels(
            category=confirmation.category.value, rule=confirmation.rule.rule_id
        ).inc()
        self._record(
            home_id, "RISK_CASE_CONFIRMED", confirmation.confirmed_by,
            ",".join(confirmation.reason_codes),
            {
                "category": confirmation.category.value,
                "severity": confirmation.severity.value,
                "authorized_response": confirmation.authorized_response,
                "advisory": False,
                "notifications": len(plan.notifications),
                "prepared": len(plan.prepared),
                "prepared_unreachable": len(plan.unreachable),
                "blocked_pending_approval": [b.capability for b in plan.blocked],
            },
        )
        return CaseChange(case=case, previous_state=current_state, kind="CONFIRMED")

    def _record(
        self, home_id: str, action: str, actor: str, reason: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.audit.append(
            RiskAudit(
                occurred_at=datetime.now(tz=UTC),
                home_id=home_id,
                action=action,
                actor=actor,
                reason=reason,
                detail=detail or {},
            )
        )


def case_ids(cases: list[RiskCase]) -> list[UUID]:
    return [c.case_id for c in cases]
