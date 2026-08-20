"""Policy and Safety Service (spec §14.6).

Turns a recommendation plus the current household state into a
`PolicyDecision` — the only object that authorizes an action. The service also
holds the small amount of state the rules need: recent manual changes, recent
actions, and household suppressions.

Every decision is recorded, including denials. A safety architecture that only
logs what it permitted cannot answer the question that matters after an
incident: *what did it refuse, and why?*
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from syltra_contracts import (
    PolicyDecision,
    PolicyOutcome,
    Recommendation,
    compute_input_hash,
)
from syltra_contracts.capability_definitions import Confirmation, get_definition
from syltra_policy_safety import metrics
from syltra_policy_safety.rules import (
    POLICY_RULES_VERSION,
    HomePolicy,
    PolicyInput,
    evaluate_chain,
    safety_class_for,
)

logger = logging.getLogger(__name__)

DECISION_TTL = timedelta(minutes=15)
APPROVAL_TTL = timedelta(minutes=30)
SAFETY_ISOLATION_TTL = timedelta(seconds=60)
"""How long a confirmed hazard's isolation stays executable."""
"""Approval requests live longer — a person needs time to answer."""


@dataclass
class HomeState:
    """The per-home facts the rules read."""

    policy: HomePolicy = field(default_factory=HomePolicy)
    last_manual_change: dict[str, datetime] = field(default_factory=dict)
    """Keyed by ``device_id:capability``."""
    last_action: dict[str, datetime] = field(default_factory=dict)
    recent_actions: deque[datetime] = field(default_factory=lambda: deque(maxlen=256))
    suppressed_types: set[str] = field(default_factory=set)
    active_risk: bool = False


class PolicyService:
    def __init__(self) -> None:
        self._homes: dict[str, HomeState] = defaultdict(HomeState)
        self.decisions: dict[UUID, PolicyDecision] = {}
        self.audit: list[dict[str, Any]] = []

    # ── configuration and state ──

    def home(self, home_id: str) -> HomeState:
        return self._homes[home_id]

    def set_policy(self, home_id: str, policy: HomePolicy) -> None:
        self._homes[home_id].policy = policy

    def record_manual_change(
        self, home_id: str, device_id: str, capability: str, at: datetime
    ) -> None:
        """Note that a person operated this device directly.

        Feeds the manual-override rule (safety invariant 5). Recorded per
        device *and* capability so adjusting a light's brightness does not also
        block an unrelated thermostat action.
        """
        self._homes[home_id].last_manual_change[f"{device_id}:{capability}"] = at

    def record_action(
        self, home_id: str, device_id: str, capability: str, at: datetime
    ) -> None:
        state = self._homes[home_id]
        state.last_action[f"{device_id}:{capability}"] = at
        state.recent_actions.append(at)

    def suppress(self, home_id: str, recommendation_type: str) -> None:
        """Record a NEVER_REPEAT answer (spec §14.8)."""
        self._homes[home_id].suppressed_types.add(recommendation_type)

    def set_active_risk(self, home_id: str, active: bool) -> None:
        self._homes[home_id].active_risk = active

    # ── evaluation ──

    def evaluate(
        self,
        recommendation: Recommendation,
        now: datetime | None = None,
        twin_value: Any = None,
        twin_status: str = "KNOWN",
        twin_age_seconds: float | None = None,
    ) -> PolicyDecision:
        """Evaluate one recommendation and record the decision."""
        moment = now or datetime.now(tz=UTC)
        state = self._homes[recommendation.home_id]
        key = f"{recommendation.target.device_id}:{recommendation.target.capability}"

        window_start = moment - state.policy.rate_window
        recent = sum(1 for stamp in state.recent_actions if stamp >= window_start)

        inp = PolicyInput(
            recommendation=recommendation,
            now=moment,
            policy=state.policy,
            twin_value=twin_value,
            twin_status=twin_status,
            twin_age_seconds=twin_age_seconds,
            last_manual_change_at=state.last_manual_change.get(key),
            last_action_at=state.last_action.get(key),
            recent_action_count=recent,
            suppressed_types=frozenset(state.suppressed_types),
            active_risk=state.active_risk,
        )
        verdict, deciding_rule = evaluate_chain(inp)

        ttl = (
            APPROVAL_TTL
            if verdict.outcome is PolicyOutcome.REQUIRE_USER_APPROVAL
            else DECISION_TTL
        )
        decision = PolicyDecision(
            decision_id=uuid4(),
            recommendation_id=recommendation.recommendation_id,
            home_id=recommendation.home_id,
            decision=verdict.outcome,
            evaluated_at=moment,
            expires_at=moment + ttl,
            reason_codes=verdict.reason_codes,
            safety_class=safety_class_for(recommendation.target.capability),
            policy_version=POLICY_RULES_VERSION,
            input_hash=compute_input_hash(inp.hashable()),
            evidence={**verdict.evidence, "deciding_rule": deciding_rule},
            required_approval_from=(
                "occupant" if verdict.outcome is PolicyOutcome.REQUIRE_USER_APPROVAL else None
            ),
        )
        self._record(decision, recommendation)
        metrics.DECISIONS.labels(
            outcome=decision.decision.value, safety_class=decision.safety_class.value
        ).inc()
        metrics.DECIDING_RULE.labels(
            rule=str(deciding_rule), outcome=decision.decision.value
        ).inc()
        return decision

    def authorize_safety_isolation(
        self,
        home_id: str,
        capability: str,
        value: Any,
        confirmed_by: str,
        reason_codes: list[str] | None = None,
        now: datetime | None = None,
    ) -> PolicyDecision:
        """Mint the fixed-rule ALLOW that lets a confirmed hazard cut a supply.

        This is the ESCALATE_TO_FIXED_SAFETY_RULE branch arriving somewhere.
        Rule 15 escalates a life-safety capability out of the ordinary chain
        precisely because the ordinary chain — confidence thresholds, quiet
        hours, rate limits, the household's learning mode — must not be able to
        stop a gas shutoff. This method is the fixed rule those escalations
        escalate *to*, and it answers on three facts and nothing else.

        It refuses unless:

        - the capability declares `DETERMINISTIC_SAFETY_RULE`, so no comfort or
          security-sensitive device is reachable through it;
        - the value is that capability's single fail-safe value, so the
          decision it authorizes can only cut a supply, never restore one;
        - a Safety Governor confirmation is named as the authority.

        No recommendation, no model and no confidence score is involved. There
        is no argument through which one could be.
        """
        from syltra_risk_engine.response import FAIL_SAFE_VALUES

        moment = now or datetime.now(tz=UTC)
        definition = get_definition(capability)
        if definition.confirmation is not Confirmation.DETERMINISTIC_SAFETY_RULE:
            msg = f"{capability} is not governed by a deterministic safety rule"
            raise ValueError(msg)
        fail_safe = FAIL_SAFE_VALUES.get(capability)
        if fail_safe is None or value != fail_safe:
            msg = (
                f"a safety isolation may only drive {capability} to {fail_safe!r}, "
                f"not {value!r}"
            )
            raise ValueError(msg)
        if not confirmed_by:
            msg = "a safety isolation must name the confirmation that authorizes it"
            raise ValueError(msg)

        decision = PolicyDecision(
            decision_id=uuid4(),
            recommendation_id=None,
            home_id=home_id,
            decision=PolicyOutcome.ALLOW,
            evaluated_at=moment,
            # Deliberately short, and shorter than DECISION_TTL. An isolation
            # authorized during an alarm must not still be executable when
            # somebody finds it in a queue an hour later.
            expires_at=moment + SAFETY_ISOLATION_TTL,
            reason_codes=[*(reason_codes or []), "AUTHORIZED_BY_SAFETY_GOVERNOR"],
            safety_class=definition.safety_class,
            policy_version=POLICY_RULES_VERSION,
            input_hash=compute_input_hash(
                {
                    "home_id": home_id,
                    "capability": capability,
                    "value": value,
                    "confirmed_by": confirmed_by,
                }
            ),
            evidence={"deciding_rule": "fixed_safety_isolation", "confirmed_by": confirmed_by},
        )
        self.decisions[decision.decision_id] = decision
        self._audit(
            decision,
            action="SAFETY_ISOLATION_AUTHORIZED",
            actor=confirmed_by,
            extra={"capability": capability, "value": value},
        )
        metrics.DECISIONS.labels(
            outcome=decision.decision.value, safety_class=decision.safety_class.value
        ).inc()
        metrics.DECIDING_RULE.labels(
            rule="fixed_safety_isolation", outcome=decision.decision.value
        ).inc()
        logger.warning(
            "SAFETY: isolation authorized for %s — %s to %r, confirmed by %s",
            home_id,
            capability,
            value,
            confirmed_by,
        )
        return decision

    def approve(
        self, decision_id: UUID, actor: str = "occupant", now: datetime | None = None
    ) -> PolicyDecision:
        """Convert an approval request into an executable ALLOW.

        A *new* decision is issued rather than mutating the old one: the
        original REQUIRE_USER_APPROVAL stays in the audit trail exactly as it
        was evaluated, and the approval is a separate, attributable act.
        """
        moment = now or datetime.now(tz=UTC)
        original = self.decisions.get(decision_id)
        if original is None:
            msg = f"no decision {decision_id}"
            raise KeyError(msg)
        if original.decision is not PolicyOutcome.REQUIRE_USER_APPROVAL:
            msg = f"decision {decision_id} is {original.decision.value}, not awaiting approval"
            raise ValueError(msg)
        if original.is_expired_at(moment):
            msg = f"approval window for {decision_id} closed at {original.expires_at.isoformat()}"
            raise ValueError(msg)

        approved = PolicyDecision(
            decision_id=uuid4(),
            recommendation_id=original.recommendation_id,
            home_id=original.home_id,
            decision=PolicyOutcome.ALLOW,
            evaluated_at=moment,
            expires_at=moment + DECISION_TTL,
            reason_codes=["USER_APPROVED", *original.reason_codes],
            safety_class=original.safety_class,
            policy_version=POLICY_RULES_VERSION,
            input_hash=original.input_hash,
            evidence={
                **original.evidence,
                "approved_by": actor,
                "approves_decision": str(decision_id),
            },
        )
        self.decisions[approved.decision_id] = approved
        self._audit(approved, action="POLICY_APPROVAL_GRANTED", actor=actor)
        return approved

    def reject(
        self, decision_id: UUID, actor: str = "occupant", now: datetime | None = None
    ) -> PolicyDecision:
        """Record a human refusal as a DENY decision."""
        moment = now or datetime.now(tz=UTC)
        original = self.decisions.get(decision_id)
        if original is None:
            msg = f"no decision {decision_id}"
            raise KeyError(msg)
        denied = PolicyDecision(
            decision_id=uuid4(),
            recommendation_id=original.recommendation_id,
            home_id=original.home_id,
            decision=PolicyOutcome.DENY,
            evaluated_at=moment,
            expires_at=moment + DECISION_TTL,
            reason_codes=["USER_REJECTED"],
            safety_class=original.safety_class,
            policy_version=POLICY_RULES_VERSION,
            input_hash=original.input_hash,
            evidence={"rejected_by": actor, "rejects_decision": str(decision_id)},
        )
        self.decisions[denied.decision_id] = denied
        self._audit(denied, action="POLICY_APPROVAL_REJECTED", actor=actor)
        return denied

    def get(self, decision_id: UUID) -> PolicyDecision | None:
        return self.decisions.get(decision_id)

    # ── internals ──

    def _record(self, decision: PolicyDecision, recommendation: Recommendation) -> None:
        self.decisions[decision.decision_id] = decision
        self._audit(
            decision,
            action="POLICY_DECISION_CREATED",
            actor="policy-safety",
            extra={
                "recommendation_type": recommendation.recommendation_type,
                "capability": recommendation.target.capability,
                "model": recommendation.model.name,
            },
        )
        logger.info(
            "policy decision %s for %s: %s (%s)",
            decision.decision_id,
            recommendation.target.capability,
            decision.decision.value,
            ",".join(decision.reason_codes),
        )

    def _audit(
        self,
        decision: PolicyDecision,
        action: str,
        actor: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        # Denials are audited as carefully as approvals: after an incident the
        # question is what the system refused, not only what it permitted.
        self.audit.append(
            {
                "occurred_at": decision.evaluated_at.isoformat(),
                "home_id": decision.home_id,
                "action": action,
                "actor": actor,
                "decision_id": str(decision.decision_id),
                "outcome": decision.decision.value,
                "reason_codes": decision.reason_codes,
                "safety_class": decision.safety_class.value,
                "input_hash": decision.input_hash,
                **(extra or {}),
            }
        )
