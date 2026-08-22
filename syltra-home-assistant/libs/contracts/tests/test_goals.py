"""What a goal may say, and what it may do about it.

A goal is a sentence about a state rather than an event, and these tests hold
the two lines that keeps it safe: the check may read anything, and the
correction is confined to comfort — because a goal acts unattended, repeatedly,
with nobody in the room.
"""

import pytest
from pydantic import ValidationError
from syltra_contracts import Goal, GoalComparison
from syltra_contracts.automations import AutomationAction
from syltra_contracts.goals import MINIMUM_REVIEW_SECONDS

pytestmark = pytest.mark.contract


def _goal(**overrides: object) -> Goal:
    fields: dict[str, object] = {
        "home_id": "home_1",
        "name": "المجلس لا يتجاوز ٢٦",
        "capability": "environment.temperature",
        "comparison": GoalComparison.AT_MOST,
        "value": 26,
        "room_id": "majlis",
    }
    fields.update(overrides)
    return Goal(**fields)


def test_a_goal_reads_a_sensor_and_says_what_must_be_true() -> None:
    goal = _goal()
    assert goal.holds_for(24) is True
    assert goal.holds_for(26) is True
    assert goal.holds_for(26.1) is False


def test_at_least_is_the_other_direction() -> None:
    goal = _goal(comparison=GoalComparison.AT_LEAST, value=18)
    assert goal.holds_for(19) is True
    assert goal.holds_for(17) is False


def test_equals_works_on_something_without_an_order() -> None:
    goal = _goal(capability="light.power", comparison=GoalComparison.EQUALS, value=False)
    assert goal.holds_for(False) is True
    assert goal.holds_for(True) is False


def test_an_ordering_needs_something_with_an_order() -> None:
    with pytest.raises(ValidationError, match="needs something with an order"):
        _goal(capability="light.power", comparison=GoalComparison.AT_MOST, value=True)


def test_a_target_outside_what_the_sensor_can_read_is_refused() -> None:
    """A goal of "under 900 degrees" is not a goal, it is a typo that would
    report itself satisfied forever."""
    with pytest.raises(ValidationError, match="outside what"):
        _goal(value=900)


def test_a_goal_may_only_correct_with_comfort() -> None:
    """Inherited from `AutomationAction`, deliberately: a goal acts unattended
    and repeatedly, which is exactly the shape that must never reach a lock."""
    with pytest.raises(ValidationError):
        _goal(actions=(AutomationAction(capability="lock.state", value="locked"),))


def test_a_goal_may_correct_with_comfort() -> None:
    goal = _goal(
        actions=(
            AutomationAction(
                capability="climate.target_temperature", value=22, device_id="ac_majlis"
            ),
        )
    )
    assert len(goal.actions) == 1


def test_a_goal_that_only_reports_is_a_goal() -> None:
    """The honest shape for anything the hub cannot fix by itself."""
    assert _goal(actions=()).actions == ()


def test_a_household_cannot_ask_the_hub_to_read_the_house_every_second() -> None:
    with pytest.raises(ValidationError):
        _goal(review_seconds=MINIMUM_REVIEW_SECONDS - 1)


def test_an_unknown_capability_is_refused() -> None:
    """As a `KeyError` from the registry rather than a validation error — the
    capability set is closed, and asking for one outside it is a programming
    mistake, not a household typing something odd."""
    with pytest.raises(KeyError, match="unknown capability"):
        _goal(capability="environment.mood")
