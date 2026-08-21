"""Proposing a rule rather than the same action every evening (§19.2).

The bar here is deliberately higher than for recommending one action, and the
tests are mostly about the bar rather than the happy path: an action the model
got wrong happens once, and a rule the model got wrong happens every day until
somebody notices.
"""

from datetime import UTC, datetime

import pytest
from syltra_adaptive_engine.proposals import (
    MIN_DAYS,
    MIN_PROPOSAL_STRENGTH,
    AutomationProposal,
    propose,
)
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_contracts import TriggerKind

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
HOME = "home_routine"
DEVICE = "light_living"
CAPABILITY = "light.power"

BUCKETS_PER_DAY = 48


def slot(weekday: int, hour: int, minute: int = 0) -> int:
    """The half-hour bucket a weekday time falls in."""
    return weekday * BUCKETS_PER_DAY + (hour * 60 + minute) // 30


def weekday_evenings(strength: float = 0.9, days: range = range(5)) -> list[tuple[int, float]]:
    return [(slot(day, 19), strength) for day in days]


def make(**overrides: object) -> AutomationProposal:
    base = dict(
        proposal_id=propose(HOME, DEVICE, CAPABILITY, weekday_evenings(), NOW)[0].proposal_id,
        home_id=HOME,
        capability=CAPABILITY,
        device_id=DEVICE,
        at_hour=19,
        at_minute=0,
        weekdays=(0, 1, 2, 3, 4),
        strength=0.9,
        proposed_at=NOW,
    )
    base.update(overrides)
    return AutomationProposal(**base)  # type: ignore[arg-type]


# ── the grouping ──


def test_five_weekday_evenings_are_one_rule_not_five() -> None:
    """A household offered five near-identical rules accepts them all and then
    has five things to unpick when the routine changes."""
    proposals = propose(HOME, DEVICE, CAPABILITY, weekday_evenings(), NOW)
    assert len(proposals) == 1
    assert proposals[0].weekdays == (0, 1, 2, 3, 4)
    assert (proposals[0].at_hour, proposals[0].at_minute) == (19, 0)


def test_two_different_times_are_two_rules() -> None:
    strongest = weekday_evenings() + [(slot(day, 7), 0.9) for day in range(5)]
    proposals = propose(HOME, DEVICE, CAPABILITY, strongest, NOW)
    assert {(p.at_hour, p.at_minute) for p in proposals} == {(19, 0), (7, 0)}


def test_a_half_past_slot_keeps_its_minutes() -> None:
    proposals = propose(HOME, DEVICE, CAPABILITY, [(slot(d, 18, 30), 0.9) for d in range(5)], NOW)
    assert (proposals[0].at_hour, proposals[0].at_minute) == (18, 30)


# ── the bar ──


def test_a_weak_routine_is_not_worth_a_standing_instruction() -> None:
    weak = MIN_PROPOSAL_STRENGTH - 0.05
    assert propose(HOME, DEVICE, CAPABILITY, weekday_evenings(strength=weak), NOW) == []


def test_a_habit_on_too_few_days_is_not_a_schedule() -> None:
    """Two evenings out of seven is not something to write a rule about."""
    days = range(MIN_DAYS - 1)
    assert propose(HOME, DEVICE, CAPABILITY, weekday_evenings(days=days), NOW) == []


def test_the_strength_reported_is_the_weakest_day_not_the_best() -> None:
    """A rule is only as good as the day it fits worst.

    Reporting the peak would let one very strong Friday carry four ordinary
    days into a standing instruction.
    """
    mixed = [(slot(0, 19), 0.99), (slot(1, 19), 0.98), (slot(2, 19), 0.76)]
    assert propose(HOME, DEVICE, CAPABILITY, mixed, NOW)[0].strength == pytest.approx(0.76)


def test_no_routine_at_all_proposes_nothing() -> None:
    assert propose(HOME, DEVICE, CAPABILITY, [], NOW) == []


# ── identity ──


def test_the_same_routine_proposes_the_same_identity_twice() -> None:
    """A household that declined last week must not be asked again by a
    proposal wearing a new id."""
    first = propose(HOME, DEVICE, CAPABILITY, weekday_evenings(), NOW)[0]
    second = propose(HOME, DEVICE, CAPABILITY, weekday_evenings(), NOW)[0]
    assert first.proposal_id == second.proposal_id


def test_a_different_device_is_a_different_proposal() -> None:
    a = propose(HOME, DEVICE, CAPABILITY, weekday_evenings(), NOW)[0]
    b = propose(HOME, "light_hall", CAPABILITY, weekday_evenings(), NOW)[0]
    assert a.proposal_id != b.proposal_id


def test_a_different_household_is_a_different_proposal() -> None:
    a = propose(HOME, DEVICE, CAPABILITY, weekday_evenings(), NOW)[0]
    b = propose("home_other", DEVICE, CAPABILITY, weekday_evenings(), NOW)[0]
    assert a.proposal_id != b.proposal_id


# ── the line it must not cross ──


def test_a_proposal_is_not_an_automation_until_somebody_says_so() -> None:
    """`propose` returns descriptions. Turning one into an automation is a
    separate, deliberate act by a person."""
    proposal = propose(HOME, DEVICE, CAPABILITY, weekday_evenings(), NOW)[0]
    assert not hasattr(proposal, "enabled")
    automation = proposal.as_automation(owner="amal", name="Evening lights")
    assert automation.trigger.kind is TriggerKind.AT_TIME
    assert automation.home_id == HOME


def test_a_proposal_cannot_express_a_critical_action() -> None:
    """Built through the same contracts a person's own automation goes through,
    so it can express nothing they could not have written by hand."""
    proposal = make(capability="valve.state", device_id="valve_main")
    with pytest.raises(ValueError):
        proposal.as_automation(owner="amal", name="Close the gas")


def test_nothing_in_the_module_can_reach_a_device() -> None:
    import ast
    import inspect

    from syltra_adaptive_engine import proposals as module

    tree = ast.parse(inspect.getsource(module))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    for forbidden in ("socket", "httpx", "requests", "nats", "syltra_action_orchestrator"):
        assert not any(name.startswith(forbidden) for name in imported), forbidden


# ── what a person is shown ──


def test_the_view_carries_evidence_a_person_can_check() -> None:
    """A confidence score alone is a number nobody can argue with."""
    view = propose(HOME, DEVICE, CAPABILITY, weekday_evenings(), NOW)[0].as_view()
    assert view["days_observed"] == 5
    assert view["reason_code"] == "REPEATED_USER_PATTERN"
    assert view["weekdays"] == [0, 1, 2, 3, 4]
    assert 0 < view["strength"] <= 1


# ── the whole path, because the parts passing is not the same as the path working ──


def trained_service() -> "AdaptiveEngineService":
    """A service with a real routine fitted from real activations."""
    from syltra_adaptive_engine.service import AdaptiveEngineService
    from syltra_testing import routine_history

    class NullPublisher:
        async def publish_envelope(self, subject: str, envelope: object) -> None: ...
        async def publish_deadletter(self, **kwargs: object) -> None: ...

    service = AdaptiveEngineService(NullPublisher())  # type: ignore[arg-type]
    for event in routine_history(days=28, hour=19, minute=0, home_id=HOME):
        service.observe(event.model_copy(update={"home_id": HOME}))
    service.train_home(HOME)
    return service


def test_a_trained_routine_actually_produces_a_proposal() -> None:
    """The check that would have caught an endpoint returning [] forever.

    Every unit above passes on hand-made buckets. This drives the real model
    through the real service, because a path whose parts all work is not the
    same as a path that works.
    """
    from syltra_contracts import LearningMode

    service = trained_service()
    assert "routine_baseline" in service.fitted_models(HOME), "the model must actually fit"

    service.set_mode(HOME, LearningMode.SHADOW, actor="test")
    service.set_mode(HOME, LearningMode.RECOMMEND, actor="test")
    proposals = service.propose_automations(HOME, "light_living", NOW)

    assert proposals, "a 28-day routine at 19:00 should be worth proposing"
    assert all(p.at_hour == 19 for p in proposals)
    assert all(len(p.weekdays) >= MIN_DAYS for p in proposals)


def test_a_household_still_being_watched_is_not_offered_standing_rules() -> None:
    """§19.2 puts the ladder in that order for a reason: a hub that is still
    observing has not earned the right to suggest a standing instruction."""
    from syltra_contracts import LearningMode

    service = trained_service()
    assert service.mode(HOME) is LearningMode.OBSERVE
    assert service.propose_automations(HOME, "light_living", NOW) == []


def test_a_suspended_model_proposes_nothing() -> None:
    """Drift suspends a model precisely because it stopped matching the home.

    A rule proposed from a model that no longer fits would be the worst
    possible moment to start writing standing instructions.
    """
    from syltra_contracts import LearningMode

    service = trained_service()
    service.set_mode(HOME, LearningMode.SHADOW, actor="test")
    service.set_mode(HOME, LearningMode.RECOMMEND, actor="test")
    assert service.propose_automations(HOME, "light_living", NOW)

    # Suspended the way drift detection suspends it, not by poking a private
    # attribute — a test that reaches past the real mechanism proves the real
    # mechanism nothing. Promoted first, because `suspend` withdraws an active
    # version and training alone leaves one TRAINED.
    version = next(v for v in service.registry.versions(HOME) if v.name == "routine_baseline")
    service.registry.promote(HOME, "routine_baseline", version.version)
    service.registry.suspend(HOME, "routine_baseline", reason="DRIFT_DETECTED")
    assert service.propose_automations(HOME, "light_living", NOW) == []
