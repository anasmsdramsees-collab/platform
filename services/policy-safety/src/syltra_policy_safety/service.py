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
    SafetyClass,
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
MANUAL_CONTROL_TTL = timedelta(seconds=30)
AUTOMATION_CONTROL_TTL = timedelta(seconds=60)
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

    def manual_override_active(
        self, home_id: str, device_id: str | None, capability: str, now: datetime | None = None
    ) -> bool:
        """Whether a person has this device by the hand right now.

        Exposed as a question rather than kept private, because a screen has to
        answer it too: a goal that cannot cool a room somebody just adjusted is
        being *held*, not failing, and showing it as a failure teaches a
        household to ignore the colour.
        """
        moment = now or datetime.now(tz=UTC)
        at = self._homes[home_id].last_manual_change.get(f"{device_id}:{capability}")
        if at is None:
            return False
        return moment - at < self._homes[home_id].policy.manual_override_window

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

    def authorize_manual_control(
        self,
        home_id: str,
        device_id: str,
        capability: str,
        value: Any,
        actor: str,
        now: datetime | None = None,
    ) -> PolicyDecision:
        """Authorize a person operating a device directly (spec §0 rule 5).

        A person is not a recommendation. The rule chain exists to decide
        whether the *platform* should act — confidence, learning mode, quiet
        hours, rate limits — and none of it applies to somebody pressing a
        switch. Running a manual press through it would let a household's own
        adaptive settings refuse the household.

        So this is a separate, short-lived ALLOW carrying no recommendation,
        and it does two things the ordinary path does not:

        - it records the press as a manual change, so the adaptive engine backs
          off this device for the override window rather than immediately
          arguing with the person who just pressed it;
        - it refuses anything outside what the actor's own authority covers,
          which is checked at the API boundary and asserted again here, because
          a permissions check that exists in one layer is a check the next
          caller skips.
        """
        moment = now or datetime.now(tz=UTC)
        safety_class = safety_class_for(capability)

        # Manual or not, nobody commands a life-safety actuator through this
        # path. Those are driven by deterministic rules from certified
        # evidence, and a person wanting one operates it by hand.
        if safety_class in (SafetyClass.LIFE_SAFETY_CRITICAL, SafetyClass.SAFETY_RELATED):
            msg = (
                f"{capability} is {safety_class.value} and is not operable by hand "
                "through this platform"
            )
            raise ValueError(msg)

        decision = PolicyDecision(
            decision_id=uuid4(),
            recommendation_id=None,
            home_id=home_id,
            decision=PolicyOutcome.ALLOW,
            evaluated_at=moment,
            # Short: a press is a thing somebody is doing now. A manual
            # decision still sitting in a queue two minutes later is one nobody
            # is standing at the switch for any more.
            expires_at=moment + MANUAL_CONTROL_TTL,
            reason_codes=["MANUAL_CONTROL"],
            safety_class=safety_class,
            policy_version=POLICY_RULES_VERSION,
            input_hash=compute_input_hash(
                {
                    "home_id": home_id,
                    "device_id": device_id,
                    "capability": capability,
                    "value": value,
                    "actor": actor,
                }
            ),
            evidence={"deciding_rule": "manual_control", "actor": actor},
        )
        self.decisions[decision.decision_id] = decision
        # §0 rule 5: manual control overrides adaptive automation. Recorded
        # here rather than by the caller, so no path can operate a device
        # manually without the adaptive layer learning that it happened.
        self.record_manual_change(home_id, device_id, capability, moment)
        self._audit(
            decision,
            action="MANUAL_CONTROL_AUTHORIZED",
            actor=actor,
            extra={"capability": capability, "device_id": device_id, "value": value},
        )
        metrics.DECISIONS.labels(
            outcome=decision.decision.value, safety_class=decision.safety_class.value
        ).inc()
        metrics.DECIDING_RULE.labels(
            rule="manual_control", outcome=decision.decision.value
        ).inc()
        return decision

    def authorize_automation(
        self,
        home_id: str,
        device_id: str | None,
        capability: str,
        value: Any,
        automation_id: str,
        now: datetime | None = None,
    ) -> PolicyDecision:
        """Authorize a rule the household wrote acting on its own (spec §2.3).

        Between a recommendation and a press, and it is neither. A
        recommendation is SYLTRA's idea and is weighed for confidence, learning
        mode and quiet hours. A press is a person deciding, and skips all of
        it. An automation is the household's own decision, made earlier, being
        carried out now with nobody in the room — so it skips the rules that
        judge *SYLTRA's* judgement, and keeps every rule that protects the
        household from the house acting at a bad moment.

        Kept, and why:

        - **A confirmed hazard stops it.** While the platform is isolating a
          gas supply, nothing else may add commands to the same house.
        - **A person who just touched this overrides it** (§0 rule 5, safety
          invariant 5). The window is the household's own; inside it the rule
          loses, every time and without argument.
        - **The rate limit holds.** A rule that has gone wrong is exactly the
          thing a rate limit is for, and it is the same counter everything else
          shares.

        Dropped, and why:

        - **Confidence.** A rule is not a guess. It matched or it did not.
        - **Quiet hours.** They exist so SYLTRA does not wake a household with
          its own idea at 3am. A household that wrote "porch light on at 3am"
          asked for it.
        - **The learning ladder** (§19.2). It governs how far SYLTRA may act on
          what it inferred. It has nothing to say about a rule a person wrote,
          and gating one on the other would mean a new hub could not turn on a
          light until it had watched the household for a fortnight.
        """
        moment = now or datetime.now(tz=UTC)
        safety_class = safety_class_for(capability)
        state = self._homes[home_id]
        key = f"{device_id}:{capability}"

        if safety_class not in (SafetyClass.NON_CRITICAL, SafetyClass.COMFORT):
            # `AutomationAction` already refuses to be constructed with one of
            # these, so reaching this line means something built a request some
            # other way. Asserted again because a check that exists in one
            # layer is a check the next caller skips.
            msg = f"{capability} is {safety_class.value}; automations act on comfort only"
            raise ValueError(msg)

        reason_codes = ["WITHIN_POLICY"]
        outcome = PolicyOutcome.ALLOW
        deciding_rule = "automation_permitted"

        manual_at = state.last_manual_change.get(key)
        if state.active_risk:
            outcome, deciding_rule = PolicyOutcome.DENY, "active_risk"
            reason_codes = ["ACTIVE_RISK_CASE"]
        elif manual_at is not None and moment - manual_at < state.policy.manual_override_window:
            outcome, deciding_rule = PolicyOutcome.DENY, "manual_override"
            reason_codes = ["RECENT_MANUAL_OVERRIDE", "USER_CONTROL_TAKES_PRECEDENCE"]
        else:
            window_start = moment - state.policy.rate_window
            recent = sum(1 for stamp in state.recent_actions if stamp >= window_start)
            if recent >= state.policy.rate_limit:
                outcome, deciding_rule = PolicyOutcome.DENY, "rate_limit"
                reason_codes = ["RATE_LIMIT_EXCEEDED"]

        decision = PolicyDecision(
            decision_id=uuid4(),
            recommendation_id=None,
            home_id=home_id,
            decision=outcome,
            evaluated_at=moment,
            expires_at=moment + AUTOMATION_CONTROL_TTL,
            reason_codes=reason_codes,
            safety_class=safety_class,
            policy_version=POLICY_RULES_VERSION,
            input_hash=compute_input_hash(
                {
                    "home_id": home_id,
                    "device_id": device_id,
                    "capability": capability,
                    "value": value,
                    "automation_id": automation_id,
                }
            ),
            evidence={"deciding_rule": deciding_rule, "automation_id": automation_id},
        )
        self.decisions[decision.decision_id] = decision
        if outcome is PolicyOutcome.ALLOW and device_id is not None:
            # Counted against the same rate limit as everything else. A rule
            # that has gone wrong is exactly what that limit is for.
            self.record_action(home_id, device_id, capability, moment)
        self._audit(
            decision,
            action="AUTOMATION_AUTHORIZED",
            actor=f"automation:{automation_id}",
            extra={"capability": capability, "device_id": device_id, "value": value},
        )
        metrics.DECISIONS.labels(
            outcome=decision.decision.value, safety_class=decision.safety_class.value
        ).inc()
        metrics.DECIDING_RULE.labels(rule=deciding_rule, outcome=decision.decision.value).inc()
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
