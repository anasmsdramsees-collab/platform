"""Whether a goal holds — and the answer that is neither yes nor no.

Most of this file is about `UNKNOWN`. Every other product in this category shows
a green tick for a room whose thermometer died an hour ago, because "no reading"
and "no problem" are the same absence in a naive check. Here they are different
states, and only one of them may cause the hub to act.
"""

from datetime import UTC, datetime, timedelta

from syltra_automation_engine import GoalRegistry, assess, with_manual_hold
from syltra_contracts import Goal, GoalComparison, GoalState
from syltra_contracts.automations import AutomationAction
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

HOME = "home_goal"
NOW = datetime(2026, 8, 22, 15, 0, tzinfo=UTC)
COOL_THE_ROOM = AutomationAction(
    capability="climate.target_temperature", value=22, device_id="ac_living"
)


def _goal(**overrides: object) -> Goal:
    fields: dict[str, object] = {
        "home_id": HOME,
        "name": "الصالة لا تتجاوز ٢٤",
        "capability": "environment.temperature",
        "comparison": GoalComparison.AT_MOST,
        "value": 24,
        "room_id": "living_room",
        "actions": (COOL_THE_ROOM,),
    }
    fields.update(overrides)
    return Goal(**fields)


def _house(*readings: tuple[str, float, datetime]) -> object:
    return home(
        *(
            device(
                device_id,
                "living_room",
                a=reading("environment.temperature", value, at),
            )
            for device_id, value, at in readings
        ),
        home_id=HOME,
    )


def test_a_measured_room_within_its_target_holds() -> None:
    status = assess(_goal(), _house(("temp_a", 22.0, NOW)), NOW)
    assert status.state is GoalState.SATISFIED
    assert status.measured == 22.0
    assert status.needs_correcting is False


def test_a_measured_room_outside_its_target_does_not() -> None:
    status = assess(_goal(), _house(("temp_a", 27.0, NOW)), NOW)
    assert status.state is GoalState.VIOLATED
    assert status.needs_correcting is True


def test_a_room_nobody_is_measuring_is_unknown_rather_than_fine() -> None:
    """The rule this whole module exists for."""
    status = assess(_goal(), _house(), NOW)
    assert status.state is GoalState.UNKNOWN
    assert status.measured is None
    assert status.needs_correcting is False


def test_a_reading_past_its_freshness_budget_stops_counting() -> None:
    """A thermometer that last spoke an hour ago cannot vouch for a room now —
    and it must not be the thing that reports the room as fine."""
    stale = NOW - timedelta(hours=2)
    status = assess(_goal(), _house(("temp_a", 22.0, stale)), NOW)
    assert status.state is GoalState.UNKNOWN


def test_the_worst_corner_decides_rather_than_the_average() -> None:
    """A mean is a temperature no room has, and it reports a goal as satisfied
    while one corner is still thirty degrees."""
    house = _house(("temp_cool", 20.0, NOW), ("temp_hot", 30.0, NOW))
    status = assess(_goal(), house, NOW)
    assert status.state is GoalState.VIOLATED
    assert status.measured == 30.0
    assert status.device_id == "temp_hot"


def test_the_worst_corner_is_the_coldest_for_an_at_least_goal() -> None:
    goal = _goal(comparison=GoalComparison.AT_LEAST, value=18)
    house = _house(("temp_cool", 15.0, NOW), ("temp_warm", 25.0, NOW))
    status = assess(goal, house, NOW)
    assert status.state is GoalState.VIOLATED
    assert status.measured == 15.0


def test_a_goal_switched_off_reports_off_rather_than_holding() -> None:
    status = assess(_goal(enabled=False), _house(("temp_a", 30.0, NOW)), NOW)
    assert status.state is GoalState.OFF


def test_a_violation_a_person_is_overriding_is_held_not_broken() -> None:
    """Showing it as a failure would teach a household to ignore the colour,
    which is how a screen stops meaning anything."""
    goal = _goal()
    status = assess(goal, _house(("temp_a", 27.0, NOW)), NOW)
    held = with_manual_hold(status, goal, lambda device_id, capability: device_id == "ac_living")

    assert held.state is GoalState.HELD
    assert held.needs_correcting is False


def test_a_satisfied_goal_is_never_re_read_as_held() -> None:
    goal = _goal()
    status = assess(goal, _house(("temp_a", 20.0, NOW)), NOW)
    assert with_manual_hold(status, goal, lambda d, c: True).state is GoalState.SATISFIED


def test_review_and_rearm_are_separate_clocks() -> None:
    """A goal is checked every minute and corrected far less often: a
    thermostat does not cool a room in a minute, and a goal that re-issues its
    correction every review is a goal fighting physics."""
    registry = GoalRegistry()
    goal = registry.upsert(_goal(review_seconds=60, rearm_seconds=600))

    assert registry.due(goal, NOW) is True
    registry.mark_reviewed(goal, NOW)
    assert registry.due(goal, NOW + timedelta(seconds=30)) is False
    assert registry.due(goal, NOW + timedelta(seconds=61)) is True

    assert registry.may_correct(goal, NOW) is True
    registry.mark_corrected(goal, NOW)
    assert registry.may_correct(goal, NOW + timedelta(seconds=300)) is False
    assert registry.may_correct(goal, NOW + timedelta(seconds=601)) is True


def test_the_registry_versions_and_forgets_on_request() -> None:
    registry = GoalRegistry()
    goal = registry.upsert(_goal())
    again = registry.upsert(goal.model_copy(update={"value": 25}))
    assert again.version == 2
    assert registry.remove(HOME, goal.goal_id) is True
    assert registry.list_for(HOME) == []
