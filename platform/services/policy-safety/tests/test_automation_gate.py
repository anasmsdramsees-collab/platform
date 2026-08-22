"""The gate an automation goes through, and the three things that stop it.

An automation is neither a recommendation nor a press, and this gate exists
because forcing it through either would have been wrong in a way that matters:
through `evaluate` a household's own rule would be judged for *SYLTRA's*
confidence and refused by quiet hours it never asked for; through
`authorize_manual_control` it would inherit the authority of a hand on a switch
that nobody's hand is on.
"""

from datetime import UTC, datetime, timedelta

import pytest
from syltra_contracts import PolicyOutcome
from syltra_policy_safety import HomePolicy, PolicyService

NOW = datetime(2026, 8, 22, 3, 12, tzinfo=UTC)  # deliberately the middle of the night


def _service() -> PolicyService:
    service = PolicyService()
    service.set_policy("home_1", HomePolicy())
    return service


def test_a_rule_the_household_wrote_is_allowed_at_three_in_the_morning() -> None:
    """Quiet hours exist so SYLTRA does not wake a household with its own idea.
    A household that wrote "porch light at 3am" asked for it."""
    decision = _service().authorize_automation(
        "home_1", "light_porch", "light.power", True, automation_id="a1", now=NOW
    )
    assert decision.decision is PolicyOutcome.ALLOW
    assert decision.reason_codes == ["WITHIN_POLICY"]


def test_a_person_who_just_touched_it_wins() -> None:
    """§0 rule 5, safety invariant 5. Inside the household's own override
    window the rule loses, every time and without argument."""
    service = _service()
    service.record_manual_change("home_1", "light_hall", "light.power", NOW)

    decision = service.authorize_automation(
        "home_1",
        "light_hall",
        "light.power",
        True,
        automation_id="a1",
        now=NOW + timedelta(seconds=30),
    )
    assert decision.decision is PolicyOutcome.DENY
    assert "RECENT_MANUAL_OVERRIDE" in decision.reason_codes
    assert "USER_CONTROL_TAKES_PRECEDENCE" in decision.reason_codes


def test_the_override_expires_rather_than_disabling_the_rule_forever() -> None:
    service = _service()
    service.record_manual_change("home_1", "light_hall", "light.power", NOW)
    later = NOW + HomePolicy().manual_override_window + timedelta(seconds=1)

    decision = service.authorize_automation(
        "home_1", "light_hall", "light.power", True, automation_id="a1", now=later
    )
    assert decision.decision is PolicyOutcome.ALLOW


def test_an_override_is_per_device_and_capability() -> None:
    """Adjusting a light's brightness must not silence a rule about a
    thermostat in another room."""
    service = _service()
    service.record_manual_change("home_1", "light_hall", "light.power", NOW)

    decision = service.authorize_automation(
        "home_1", "ac_living", "climate.target_temperature", 23, automation_id="a1", now=NOW
    )
    assert decision.decision is PolicyOutcome.ALLOW


def test_a_confirmed_hazard_stops_everything_else() -> None:
    """While the platform is isolating a gas supply, nothing else may add
    commands to the same house."""
    service = _service()
    service.set_active_risk("home_1", True)

    decision = service.authorize_automation(
        "home_1", "light_hall", "light.power", True, automation_id="a1", now=NOW
    )
    assert decision.decision is PolicyOutcome.DENY
    assert decision.reason_codes == ["ACTIVE_RISK_CASE"]


def test_a_rule_that_has_gone_wrong_hits_the_rate_limit() -> None:
    """The same counter everything else shares — which is the point: a runaway
    automation is exactly what a rate limit is for."""
    service = _service()
    policy = HomePolicy()
    for i in range(policy.rate_limit):
        decision = service.authorize_automation(
            "home_1",
            "light_hall",
            "light.power",
            i % 2 == 0,
            automation_id="a1",
            now=NOW + timedelta(seconds=i),
        )
        assert decision.decision is PolicyOutcome.ALLOW, i

    stopped = service.authorize_automation(
        "home_1", "light_hall", "light.power", True, automation_id="a1", now=NOW
    )
    assert stopped.decision is PolicyOutcome.DENY
    assert stopped.reason_codes == ["RATE_LIMIT_EXCEEDED"]


def test_a_denied_automation_does_not_count_against_the_limit() -> None:
    """Otherwise a house under an active hazard would spend its whole budget on
    commands nobody carried out, and stay throttled after the hazard cleared."""
    service = _service()
    service.set_active_risk("home_1", True)
    for _ in range(20):
        service.authorize_automation(
            "home_1", "light_hall", "light.power", True, automation_id="a1", now=NOW
        )

    service.set_active_risk("home_1", False)
    decision = service.authorize_automation(
        "home_1", "light_hall", "light.power", True, automation_id="a1", now=NOW
    )
    assert decision.decision is PolicyOutcome.ALLOW


@pytest.mark.parametrize("capability", ["valve.state", "lock.state", "safety.gas_alarm"])
def test_nothing_outside_comfort_reaches_this_gate(capability: str) -> None:
    """`AutomationAction` refuses to be constructed with one of these, so this
    is the second lock on the same door — because a check that exists in one
    layer is the check the next caller skips."""
    with pytest.raises(ValueError, match="comfort"):
        _service().authorize_automation(
            "home_1", "d1", capability, "closed", automation_id="a1", now=NOW
        )


def test_every_decision_is_recorded_and_findable() -> None:
    service = _service()
    decision = service.authorize_automation(
        "home_1", "light_hall", "light.power", True, automation_id="a1", now=NOW
    )
    assert service.get(decision.decision_id) is decision
    assert decision.evidence["automation_id"] == "a1"
    assert any(entry.get("action") == "AUTOMATION_AUTHORIZED" for entry in service.audit)
