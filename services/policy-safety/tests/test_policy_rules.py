"""Policy rule tests (spec §14.6, §18).

These are the project's most safety-critical tests. They run without any ML
service present, which is itself the point: safety invariant 17 requires safety
rules to be testable without ML, and invariant 7 requires them to work when the
Adaptive Engine is down.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from syltra_contracts import (
    ModelReference,
    PolicyDecision,
    PolicyOutcome,
    Recommendation,
    RecommendationTarget,
    SafetyClass,
)
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_policy_safety.rules import PolicyInput, evaluate_chain

MIDDAY = datetime(2026, 8, 18, 13, 0, tzinfo=UTC)
NIGHT = datetime(2026, 8, 18, 23, 30, tzinfo=UTC)


def recommendation(**overrides: object) -> Recommendation:
    payload: dict[str, object] = {
        "recommendation_id": uuid4(),
        "home_id": "home_001",
        "recommendation_type": "climate.precondition",
        "created_at": MIDDAY,
        "expires_at": MIDDAY + timedelta(minutes=15),
        "target": RecommendationTarget(
            device_id="ac_living", capability="climate.target_temperature"
        ),
        "proposed_value": 23,
        "confidence": 0.9,
        "reason_codes": ["REPEATED_USER_PATTERN"],
        "model": ModelReference(name="temperature_preference", version="1.0.0"),
        "required_policy": "COMFORT_AUTOMATION",
        "requires_user_approval": False,
    }
    payload.update(overrides)
    return Recommendation.model_validate(payload)


def trusting_policy(**overrides: object) -> HomePolicy:
    """A home that has earned unattended automation, so rules under test are
    not masked by the default 'not yet trusted' outcome."""
    base: dict[str, object] = {"unattended_automation": True, "require_approval_below": 0.0}
    base.update(overrides)
    return HomePolicy(**base)  # type: ignore[arg-type]


def decide(
    service: PolicyService | None = None,
    rec: Recommendation | None = None,
    now: datetime = MIDDAY,
    twin_value: object = 27.0,
    twin_status: str = "KNOWN",
    policy: HomePolicy | None = None,
) -> PolicyDecision:
    svc = service or PolicyService()
    svc.set_policy("home_001", policy or trusting_policy())
    return svc.evaluate(
        rec or recommendation(), now=now, twin_value=twin_value, twin_status=twin_status
    )


# ── the gate itself ──


@pytest.mark.safety
def test_a_clean_recommendation_is_allowed() -> None:
    result = decide()
    assert result.decision is PolicyOutcome.ALLOW
    assert result.authorizes_execution_at(MIDDAY)
    assert result.input_hash
    assert result.safety_class is SafetyClass.COMFORT


@pytest.mark.safety
def test_every_decision_records_reasons_and_an_input_hash() -> None:
    # A decision nobody can explain later is not an audit record.
    for rec in (recommendation(), recommendation(confidence=0.1)):
        result = decide(rec=rec)
        assert result.reason_codes
        assert len(result.input_hash) == 64
        assert result.policy_version == "1.0.0"


@pytest.mark.safety
def test_denials_are_audited_as_carefully_as_approvals() -> None:
    service = PolicyService()
    service.set_policy("home_001", trusting_policy())
    service.evaluate(recommendation(confidence=0.1), now=MIDDAY, twin_value=27.0)
    assert service.audit
    entry = service.audit[-1]
    assert entry["outcome"] == "DENY"
    assert entry["reason_codes"]
    assert entry["input_hash"]


# ── hard prohibitions ──


@pytest.mark.safety
def test_shadow_recommendations_are_denied() -> None:
    result = decide(rec=recommendation(shadow=True))
    assert result.decision is PolicyOutcome.DENY
    assert "SHADOW_MODE_RECOMMENDATION" in result.reason_codes


@pytest.mark.safety
def test_expired_recommendations_are_denied() -> None:
    # Safety invariant 3.
    result = decide(now=MIDDAY + timedelta(minutes=20))
    assert result.decision is PolicyOutcome.DENY
    assert "RECOMMENDATION_EXPIRED" in result.reason_codes


@pytest.mark.safety
def test_replayed_historical_recommendations_are_denied() -> None:
    # Safety invariant 11: replayed history cannot trigger live actions.
    old = recommendation(
        created_at=MIDDAY - timedelta(days=3),
        expires_at=MIDDAY + timedelta(minutes=15),
    )
    result = decide(rec=old)
    assert result.decision is PolicyOutcome.DENY
    assert "HISTORICAL_REPLAY_SUSPECTED" in result.reason_codes


@pytest.mark.safety
@pytest.mark.parametrize("capability", ["valve.state", "breaker.state", "siren.state"])
def test_life_safety_capabilities_escalate_to_fixed_rules(capability: str) -> None:
    # Safety invariants 6, 13 and 18: adaptive output never commands these.
    value = {"valve.state": "closed", "breaker.state": "off", "siren.state": "on"}[capability]
    rec = recommendation(
        target=RecommendationTarget(device_id="d", capability=capability),
        proposed_value=value,
        confidence=0.99,
    )
    result = decide(rec=rec, twin_value="open")
    assert result.decision is PolicyOutcome.ESCALATE_TO_FIXED_SAFETY_RULE
    assert "ADAPTIVE_OUTPUT_NOT_PERMITTED" in result.reason_codes


@pytest.mark.safety
def test_no_confidence_however_high_unlocks_a_life_safety_capability() -> None:
    # The escalation is categorical, not a threshold that certainty can clear.
    rec = recommendation(
        target=RecommendationTarget(device_id="d", capability="valve.state"),
        proposed_value="closed",
        confidence=1.0,
    )
    result = decide(rec=rec, twin_value="open")
    assert result.decision is not PolicyOutcome.ALLOW


@pytest.mark.safety
def test_an_open_risk_case_suspends_comfort_automation() -> None:
    service = PolicyService()
    service.set_policy("home_001", trusting_policy())
    service.set_active_risk("home_001", True)
    result = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert result.decision is PolicyOutcome.DENY
    assert "ACTIVE_RISK_CASE" in result.reason_codes


# ── household authority ──


@pytest.mark.safety
def test_consent_is_required() -> None:
    policy = trusting_policy(consented_policies=frozenset())
    result = decide(policy=policy)
    assert result.decision is PolicyOutcome.DENY
    assert "CONSENT_NOT_GRANTED" in result.reason_codes


@pytest.mark.safety
def test_never_repeat_suppresses_a_recommendation_type() -> None:
    service = PolicyService()
    service.set_policy("home_001", trusting_policy())
    service.suppress("home_001", "climate.precondition")
    result = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert result.decision is PolicyOutcome.DENY
    assert "SUPPRESSED_BY_USER" in result.reason_codes


@pytest.mark.safety
def test_recent_manual_control_blocks_a_conflicting_action() -> None:
    # Safety invariant 5 and spec §0 rule 16: manual control always wins.
    service = PolicyService()
    service.set_policy("home_001", trusting_policy())
    service.record_manual_change(
        "home_001", "ac_living", "climate.target_temperature", MIDDAY - timedelta(minutes=2)
    )
    result = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert result.decision is PolicyOutcome.DENY
    assert "USER_CONTROL_TAKES_PRECEDENCE" in result.reason_codes


def test_manual_control_on_another_device_does_not_block() -> None:
    # The override is scoped to the device and capability the person touched.
    service = PolicyService()
    service.set_policy("home_001", trusting_policy())
    service.record_manual_change(
        "home_001", "light_kitchen", "light.power", MIDDAY - timedelta(minutes=1)
    )
    result = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert result.decision is PolicyOutcome.ALLOW


def test_an_old_manual_change_stops_blocking_after_the_window() -> None:
    service = PolicyService()
    service.set_policy("home_001", trusting_policy())
    service.record_manual_change(
        "home_001", "ac_living", "climate.target_temperature", MIDDAY - timedelta(hours=2)
    )
    result = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert result.decision is PolicyOutcome.ALLOW


# ── data quality and model trust ──


@pytest.mark.safety
@pytest.mark.parametrize("status", ["STALE", "UNKNOWN"])
def test_acting_on_non_fresh_state_is_denied(status: str) -> None:
    # Safety invariant 4 applied to actions: acting on stale state is acting blind.
    result = decide(twin_status=status)
    assert result.decision is PolicyOutcome.DENY
    assert "TARGET_STATE_NOT_FRESH" in result.reason_codes


@pytest.mark.safety
def test_low_confidence_is_denied() -> None:
    result = decide(rec=recommendation(confidence=0.2))
    assert result.decision is PolicyOutcome.DENY
    assert "CONFIDENCE_BELOW_THRESHOLD" in result.reason_codes


def test_an_action_that_would_change_nothing_is_refused() -> None:
    result = decide(rec=recommendation(proposed_value=23), twin_value=23)
    assert result.decision is PolicyOutcome.DENY
    assert "ALREADY_AT_PROPOSED_VALUE" in result.reason_codes


# ── pacing ──


def test_cooldown_blocks_a_rapid_second_action() -> None:
    service = PolicyService()
    service.set_policy("home_001", trusting_policy())
    service.record_action(
        "home_001", "ac_living", "climate.target_temperature", MIDDAY - timedelta(minutes=1)
    )
    result = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert result.decision is PolicyOutcome.DENY
    assert "COOLDOWN_ACTIVE" in result.reason_codes


def test_rate_limit_blocks_excessive_actions() -> None:
    service = PolicyService()
    service.set_policy("home_001", trusting_policy(rate_limit=3))
    for minutes in (50, 40, 30):
        service.record_action(
            "home_001", "other_device", "light.power", MIDDAY - timedelta(minutes=minutes)
        )
    result = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert result.decision is PolicyOutcome.DENY
    assert "RATE_LIMIT_EXCEEDED" in result.reason_codes


def test_actions_outside_the_rate_window_do_not_count() -> None:
    service = PolicyService()
    service.set_policy("home_001", trusting_policy(rate_limit=2))
    for hours in (5, 4, 3):
        service.record_action(
            "home_001", "other_device", "light.power", MIDDAY - timedelta(hours=hours)
        )
    result = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert result.decision is PolicyOutcome.ALLOW


# ── quiet hours ──


def test_quiet_hours_prepare_only_for_disruptive_capabilities() -> None:
    rec = recommendation(
        recommendation_type="lighting.routine",
        target=RecommendationTarget(device_id="light_living", capability="light.power"),
        proposed_value=True,
        created_at=NIGHT,
        expires_at=NIGHT + timedelta(minutes=15),
    )
    result = decide(rec=rec, now=NIGHT, twin_value=False)
    assert result.decision is PolicyOutcome.PREPARE_ONLY
    assert "QUIET_HOURS_ACTIVE" in result.reason_codes


def test_silent_capabilities_may_still_act_during_quiet_hours() -> None:
    rec = recommendation(created_at=NIGHT, expires_at=NIGHT + timedelta(minutes=15))
    result = decide(rec=rec, now=NIGHT, twin_value=27.0)
    assert result.decision is PolicyOutcome.ALLOW


# ── approval ──


@pytest.mark.safety
def test_an_untrusted_home_requires_approval_for_everything() -> None:
    # The default posture: unattended execution is earned, not assumed.
    service = PolicyService()  # default HomePolicy: unattended_automation False
    result = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert result.decision is PolicyOutcome.REQUIRE_USER_APPROVAL
    assert "AUTOMATION_NOT_YET_TRUSTED" in result.reason_codes


@pytest.mark.safety
@pytest.mark.parametrize("capability", ["lock.state", "garage.state", "camera.recording"])
def test_security_sensitive_capabilities_always_require_approval(capability: str) -> None:
    # Safety invariant 13: separate policy classes for security-sensitive gear.
    value = {"lock.state": "unlocked", "garage.state": "open", "camera.recording": True}[
        capability
    ]
    rec = recommendation(
        target=RecommendationTarget(device_id="d", capability=capability),
        proposed_value=value,
    )
    result = decide(rec=rec, twin_value="locked" if capability == "lock.state" else False)
    assert result.decision is PolicyOutcome.REQUIRE_USER_APPROVAL
    assert "CAPABILITY_REQUIRES_APPROVAL" in result.reason_codes


def test_low_confidence_requires_approval_even_in_a_trusted_home() -> None:
    policy = trusting_policy(require_approval_below=0.95)
    result = decide(rec=recommendation(confidence=0.7), policy=policy)
    assert result.decision is PolicyOutcome.REQUIRE_USER_APPROVAL


def test_approval_issues_a_new_allow_and_preserves_the_original() -> None:
    service = PolicyService()
    pending = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    assert pending.decision is PolicyOutcome.REQUIRE_USER_APPROVAL

    approved = service.approve(pending.decision_id, actor="occupant", now=MIDDAY)
    assert approved.decision is PolicyOutcome.ALLOW
    assert approved.decision_id != pending.decision_id
    # The original stands unchanged in the record.
    original = service.get(pending.decision_id)
    assert original is not None
    assert original.decision is PolicyOutcome.REQUIRE_USER_APPROVAL
    assert approved.evidence["approved_by"] == "occupant"


@pytest.mark.safety
def test_an_expired_approval_request_cannot_be_approved() -> None:
    service = PolicyService()
    pending = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    with pytest.raises(ValueError, match="approval window"):
        service.approve(pending.decision_id, now=MIDDAY + timedelta(hours=2))


@pytest.mark.safety
def test_only_pending_approvals_can_be_approved() -> None:
    service = PolicyService()
    service.set_policy("home_001", trusting_policy())
    allowed = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    with pytest.raises(ValueError, match="not awaiting approval"):
        service.approve(allowed.decision_id, now=MIDDAY)


def test_rejection_is_recorded_as_a_denial() -> None:
    service = PolicyService()
    pending = service.evaluate(recommendation(), now=MIDDAY, twin_value=27.0)
    denied = service.reject(pending.decision_id, actor="occupant", now=MIDDAY)
    assert denied.decision is PolicyOutcome.DENY
    assert "USER_REJECTED" in denied.reason_codes


# ── chain properties ──


@pytest.mark.safety
def test_the_chain_short_circuits_on_the_first_prohibition() -> None:
    # A shadow recommendation that is *also* low-confidence must report the
    # shadow denial: priority is positional, so an earlier prohibition wins.
    inp = PolicyInput(
        recommendation=recommendation(shadow=True, confidence=0.1),
        now=MIDDAY,
        policy=trusting_policy(),
        twin_value=27.0,
        twin_status="KNOWN",
    )
    verdict, rule_id = evaluate_chain(inp)
    assert rule_id == "shadow_mode"
    assert verdict.outcome is PolicyOutcome.DENY


@pytest.mark.safety
def test_evaluation_is_deterministic() -> None:
    inp = PolicyInput(
        recommendation=recommendation(),
        now=MIDDAY,
        policy=trusting_policy(),
        twin_value=27.0,
        twin_status="KNOWN",
    )
    first = evaluate_chain(inp)
    for _ in range(10):
        assert evaluate_chain(inp) == first


@pytest.mark.safety
def test_the_same_inputs_produce_the_same_hash() -> None:
    service = PolicyService()
    service.set_policy("home_001", trusting_policy())
    rec = recommendation()
    a = service.evaluate(rec, now=MIDDAY, twin_value=27.0)
    b = service.evaluate(rec, now=MIDDAY, twin_value=27.0)
    assert a.input_hash == b.input_hash


def test_homes_are_isolated() -> None:
    service = PolicyService()
    service.suppress("home_a", "climate.precondition")
    service.set_policy("home_b", trusting_policy())
    other = recommendation(home_id="home_b")
    assert service.evaluate(other, now=MIDDAY, twin_value=27.0).decision is PolicyOutcome.ALLOW
