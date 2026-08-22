"""Deterministic policy rules (spec §14.6).

Every rule is a pure function of a `PolicyInput`. Nothing here calls a model,
reads a network, or consults an LLM — spec §18 invariant 17 requires safety
rules to be testable *without ML services running*, and invariant 7 requires
them to keep working when the Adaptive Engine is down. A pure rule chain is the
only way to make both claims true.

The chain is **ordered and short-circuiting**, and the order encodes priority:
life-safety escalation is checked before consent, consent before confidence,
and so on. The first rule to return a non-ALLOW outcome decides, so a denial
can never be overridden by a later, more permissive rule.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta
from typing import Any

from syltra_contracts import PolicyOutcome, Recommendation, SafetyClass
from syltra_contracts.capability_definitions import Confirmation, get_definition

POLICY_RULES_VERSION = "1.0.0"

DEFAULT_MIN_CONFIDENCE = 0.6
DEFAULT_QUIET_START = time(22, 0)
DEFAULT_QUIET_END = time(7, 0)
DEFAULT_COOLDOWN = timedelta(minutes=10)
DEFAULT_MANUAL_OVERRIDE_WINDOW = timedelta(minutes=30)
DEFAULT_RATE_LIMIT = 6
DEFAULT_RATE_WINDOW = timedelta(hours=1)


@dataclass(frozen=True)
class HomePolicy:
    """Per-household policy configuration (spec §14.6)."""

    consented_policies: frozenset[str] = frozenset({"COMFORT_AUTOMATION"})
    """Feature-level consent (spec §26: per-feature consent)."""
    min_confidence: float = DEFAULT_MIN_CONFIDENCE
    quiet_start: time = DEFAULT_QUIET_START
    quiet_end: time = DEFAULT_QUIET_END
    quiet_hours_allow_silent: frozenset[str] = frozenset(
        {"climate.target_temperature", "climate.mode"}
    )
    """Capabilities that may still act during quiet hours because they are
    silent; lights and covers are not, and would wake a household."""
    cooldown: timedelta = DEFAULT_COOLDOWN
    manual_override_window: timedelta = DEFAULT_MANUAL_OVERRIDE_WINDOW
    rate_limit: int = DEFAULT_RATE_LIMIT
    rate_window: timedelta = DEFAULT_RATE_WINDOW
    require_approval_below: float = 0.85
    """Confidence beneath which even a permitted action needs a human yes."""
    unattended_automation: bool = False
    """False until the home reaches AUTHORIZED_AUTOMATION (spec §19.2)."""


@dataclass(frozen=True)
class PolicyInput:
    """Everything a decision is made against, and nothing else.

    Keeping this explicit is what makes `input_hash` meaningful: the hash covers
    exactly the facts listed here, so an auditor can reconstruct the decision.
    """

    recommendation: Recommendation
    now: datetime
    policy: HomePolicy
    twin_value: Any = None
    twin_status: str = "UNKNOWN"
    """Twin status of the target capability: KNOWN, STALE or UNKNOWN."""
    twin_age_seconds: float | None = None
    last_manual_change_at: datetime | None = None
    last_action_at: datetime | None = None
    recent_action_count: int = 0
    suppressed_types: frozenset[str] = frozenset()
    """Recommendation types the household said NEVER_REPEAT to."""
    active_risk: bool = False
    """True while a confirmed risk case is open for this home."""

    def hashable(self) -> dict[str, Any]:
        return {
            "recommendation_id": str(self.recommendation.recommendation_id),
            "recommendation_type": self.recommendation.recommendation_type,
            "capability": self.recommendation.target.capability,
            "device_id": self.recommendation.target.device_id,
            "proposed_value": self.recommendation.proposed_value,
            "confidence": self.recommendation.confidence,
            "evaluated_at": self.now.isoformat(),
            "twin_value": self.twin_value,
            "twin_status": self.twin_status,
            "last_manual_change_at": (
                self.last_manual_change_at.isoformat() if self.last_manual_change_at else None
            ),
            "recent_action_count": self.recent_action_count,
            "active_risk": self.active_risk,
            "policy_version": POLICY_RULES_VERSION,
        }


@dataclass
class RuleVerdict:
    outcome: PolicyOutcome
    reason_codes: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def decisive(self) -> bool:
        """Anything but a plain ALLOW ends the chain."""
        return self.outcome is not PolicyOutcome.ALLOW


Rule = Callable[[PolicyInput], RuleVerdict | None]

_ALLOW = RuleVerdict(PolicyOutcome.ALLOW)


# ── the chain, in priority order ──


def rule_shadow_recommendations_never_execute(inp: PolicyInput) -> RuleVerdict | None:
    """A shadow prediction is not a proposal (spec §19.2)."""
    if inp.recommendation.shadow:
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["SHADOW_MODE_RECOMMENDATION"],
            {"learning_mode": "SHADOW"},
        )
    return None


def rule_expired_recommendations_never_execute(inp: PolicyInput) -> RuleVerdict | None:
    """Safety invariant 3: a stale recommendation cannot execute."""
    if inp.recommendation.is_expired_at(inp.now):
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["RECOMMENDATION_EXPIRED"],
            {"expired_at": inp.recommendation.expires_at.isoformat()},
        )
    return None


def rule_replayed_history_never_executes(inp: PolicyInput) -> RuleVerdict | None:
    """Safety invariant 11: replayed historical events cannot trigger live actions.

    A recommendation created implausibly far in the past is a replay artifact,
    not a live proposal — even if its TTL somehow still covers `now`.
    """
    age = inp.now - inp.recommendation.created_at
    if age > timedelta(hours=1):
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["HISTORICAL_REPLAY_SUSPECTED"],
            {"age_seconds": round(age.total_seconds(), 1)},
        )
    return None


def rule_life_safety_escalates_to_fixed_rules(inp: PolicyInput) -> RuleVerdict | None:
    """Safety invariants 6, 13 and 18.

    Life-safety capabilities are never commanded by adaptive output. The
    decision escalates to the deterministic safety rule that owns them, which
    is the only authority permitted to act on a gas valve, breaker or siren.
    """
    definition = get_definition(inp.recommendation.target.capability)
    if definition.confirmation is Confirmation.DETERMINISTIC_SAFETY_RULE:
        return RuleVerdict(
            PolicyOutcome.ESCALATE_TO_FIXED_SAFETY_RULE,
            ["LIFE_SAFETY_CAPABILITY", "ADAPTIVE_OUTPUT_NOT_PERMITTED"],
            {
                "capability": inp.recommendation.target.capability,
                "safety_class": definition.safety_class.value,
            },
        )
    return None


def rule_active_risk_suspends_comfort_automation(inp: PolicyInput) -> RuleVerdict | None:
    """While a risk case is open, comfort automation stands down.

    Adaptive actions during an incident add noise exactly when the household
    and the safety layer need a stable, predictable home.
    """
    if inp.active_risk:
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["ACTIVE_RISK_CASE", "COMFORT_AUTOMATION_SUSPENDED"],
            {"active_risk": True},
        )
    return None


def rule_consent_required(inp: PolicyInput) -> RuleVerdict | None:
    """Spec §14.6 and §26: per-feature consent, checked before anything else."""
    required = inp.recommendation.required_policy
    if required not in inp.policy.consented_policies:
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["CONSENT_NOT_GRANTED"],
            {"required_policy": required},
        )
    return None


def rule_never_repeat_suppression(inp: PolicyInput) -> RuleVerdict | None:
    """The household said never again; that answer is durable (spec §14.8)."""
    if inp.recommendation.recommendation_type in inp.suppressed_types:
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["SUPPRESSED_BY_USER"],
            {"recommendation_type": inp.recommendation.recommendation_type},
        )
    return None


def rule_data_freshness(inp: PolicyInput) -> RuleVerdict | None:
    """Safety invariant 4, applied to actions: act only on fresh, known state.

    Acting on a stale or unknown reading means acting blind — the device may
    already be where we want it, or somewhere we did not expect.
    """
    if inp.twin_status != "KNOWN":
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["TARGET_STATE_NOT_FRESH", f"TWIN_STATUS_{inp.twin_status}"],
            {"twin_status": inp.twin_status, "twin_age_seconds": inp.twin_age_seconds},
        )
    return None


def rule_confidence_threshold(inp: PolicyInput) -> RuleVerdict | None:
    if inp.recommendation.confidence < inp.policy.min_confidence:
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["CONFIDENCE_BELOW_THRESHOLD"],
            {
                "confidence": inp.recommendation.confidence,
                "threshold": inp.policy.min_confidence,
            },
        )
    return None


def rule_manual_override_conflict(inp: PolicyInput) -> RuleVerdict | None:
    """Safety invariant 5 and spec §0 rule 16: manual control always wins.

    A person who just adjusted this device has expressed an intent more
    recent and more authoritative than any model's. The action is refused
    outright rather than queued, because queuing would resume overriding them
    the moment the window lapsed.
    """
    if inp.last_manual_change_at is None:
        return None
    since = inp.now - inp.last_manual_change_at
    if since <= inp.policy.manual_override_window:
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["RECENT_MANUAL_OVERRIDE", "USER_CONTROL_TAKES_PRECEDENCE"],
            {
                "seconds_since_manual_change": round(since.total_seconds(), 1),
                "window_seconds": inp.policy.manual_override_window.total_seconds(),
            },
        )
    return None


def rule_cooldown(inp: PolicyInput) -> RuleVerdict | None:
    """Spec §14.6: cooldowns. Prevents a device being nudged repeatedly."""
    if inp.last_action_at is None:
        return None
    since = inp.now - inp.last_action_at
    if since < inp.policy.cooldown:
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["COOLDOWN_ACTIVE"],
            {
                "seconds_since_last_action": round(since.total_seconds(), 1),
                "cooldown_seconds": inp.policy.cooldown.total_seconds(),
            },
        )
    return None


def rule_rate_limit(inp: PolicyInput) -> RuleVerdict | None:
    """Spec §14.6: action rate limits, per home per window."""
    if inp.recent_action_count >= inp.policy.rate_limit:
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["RATE_LIMIT_EXCEEDED"],
            {
                "recent_actions": inp.recent_action_count,
                "limit": inp.policy.rate_limit,
                "window_seconds": inp.policy.rate_window.total_seconds(),
            },
        )
    return None


def rule_quiet_hours(inp: PolicyInput) -> RuleVerdict | None:
    """Quiet hours: prepare, do not disturb.

    Returns PREPARE_ONLY rather than DENY for audible or visible capabilities —
    the intent stays valid and can execute when quiet hours end, which is more
    useful than discarding it.
    """
    local = inp.now.timetz().replace(tzinfo=None)
    start, end = inp.policy.quiet_start, inp.policy.quiet_end
    within = (local >= start or local < end) if start > end else (start <= local < end)
    if not within:
        return None
    if inp.recommendation.target.capability in inp.policy.quiet_hours_allow_silent:
        return None
    return RuleVerdict(
        PolicyOutcome.PREPARE_ONLY,
        ["QUIET_HOURS_ACTIVE"],
        {"quiet_hours": f"{start.isoformat()}-{end.isoformat()}"},
    )


def rule_confirmation_level(inp: PolicyInput) -> RuleVerdict | None:
    """Spec §10.3 confirmation levels, honoured per capability."""
    definition = get_definition(inp.recommendation.target.capability)
    if definition.confirmation is Confirmation.USER_APPROVAL:
        return RuleVerdict(
            PolicyOutcome.REQUIRE_USER_APPROVAL,
            ["CAPABILITY_REQUIRES_APPROVAL", definition.safety_class.value],
            {"capability": inp.recommendation.target.capability},
        )
    return None


def rule_approval_required(inp: PolicyInput) -> RuleVerdict | None:
    """Unattended execution is earned, not assumed (spec §19.2).

    Until a home reaches AUTHORIZED_AUTOMATION, and until confidence clears the
    configured bar, a permitted action still waits for a human yes.
    """
    if not inp.policy.unattended_automation:
        return RuleVerdict(
            PolicyOutcome.REQUIRE_USER_APPROVAL,
            ["AUTOMATION_NOT_YET_TRUSTED"],
            {"unattended_automation": False},
        )
    if inp.recommendation.confidence < inp.policy.require_approval_below:
        return RuleVerdict(
            PolicyOutcome.REQUIRE_USER_APPROVAL,
            ["CONFIDENCE_BELOW_UNATTENDED_THRESHOLD"],
            {
                "confidence": inp.recommendation.confidence,
                "threshold": inp.policy.require_approval_below,
            },
        )
    if inp.recommendation.requires_user_approval:
        return RuleVerdict(
            PolicyOutcome.REQUIRE_USER_APPROVAL,
            ["RECOMMENDATION_REQUESTS_APPROVAL"],
            {},
        )
    return None


def rule_no_op(inp: PolicyInput) -> RuleVerdict | None:
    """Refuse an action that would change nothing.

    Dispatching a command whose effect is already true wastes an action budget
    slot and pollutes the audit trail with meaningless entries.
    """
    expected = get_definition(inp.recommendation.target.capability)
    proposed = inp.recommendation.proposed_value
    observed = inp.twin_value
    if observed is None:
        return None
    same = (
        abs(float(observed) - float(proposed)) < 0.01
        if expected.data_type.value == "NUMBER"
        and isinstance(observed, int | float)
        and isinstance(proposed, int | float)
        and not isinstance(observed, bool)
        and not isinstance(proposed, bool)
        else observed == proposed
    )
    if same:
        return RuleVerdict(
            PolicyOutcome.DENY,
            ["ALREADY_AT_PROPOSED_VALUE"],
            {"observed": observed, "proposed": proposed},
        )
    return None


RULE_CHAIN: tuple[tuple[str, Rule], ...] = (
    # Hard prohibitions first: nothing later can re-permit these.
    ("shadow_mode", rule_shadow_recommendations_never_execute),
    ("expired", rule_expired_recommendations_never_execute),
    ("historical_replay", rule_replayed_history_never_executes),
    ("life_safety", rule_life_safety_escalates_to_fixed_rules),
    ("active_risk", rule_active_risk_suspends_comfort_automation),
    # Household authority.
    ("consent", rule_consent_required),
    ("never_repeat", rule_never_repeat_suppression),
    ("manual_override", rule_manual_override_conflict),
    # Data quality and model trust.
    ("freshness", rule_data_freshness),
    ("confidence", rule_confidence_threshold),
    ("no_op", rule_no_op),
    # Pacing.
    ("cooldown", rule_cooldown),
    ("rate_limit", rule_rate_limit),
    # Timing and confirmation.
    ("quiet_hours", rule_quiet_hours),
    ("confirmation_level", rule_confirmation_level),
    ("approval", rule_approval_required),
)


def evaluate_chain(inp: PolicyInput) -> tuple[RuleVerdict, str | None]:
    """Run the chain; returns the deciding verdict and the rule that decided.

    Short-circuits on the first non-ALLOW outcome, so priority is positional
    and a denial can never be softened by a later rule.
    """
    for rule_id, rule in RULE_CHAIN:
        verdict = rule(inp)
        if verdict is not None and verdict.decisive:
            return verdict, rule_id
    return RuleVerdict(PolicyOutcome.ALLOW, ["WITHIN_POLICY"], {}), None


def safety_class_for(capability: str) -> SafetyClass:
    return get_definition(capability).safety_class


def utc_now() -> datetime:
    return datetime.now(tz=UTC)
