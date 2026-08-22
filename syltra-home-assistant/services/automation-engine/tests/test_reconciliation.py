"""Layer 12 — the case the concept document describes and the build did not.

> The air conditioning is on. The room reaches 27° and stops. The goal is not
> met. **The system does not repeat the same command.** It examines the
> difference, finds the window open, the curtains open and 43° outside, and
> changes the plan.
>
> — `docs/concept/SYLTRA_Adaptive_Concept.md` §08

Before this, a violated goal issued its correction, waited out its rearm, and
issued exactly the same correction again, forever, into a room with a window
open. Every part was individually right and the loop as a whole was a machine
for repeating a plan that was not working.
"""

from datetime import UTC, datetime, timedelta

from syltra_automation_engine.goals import GoalStatus, assess
from syltra_automation_engine.reconciliation import (
    GOAL_STALLED,
    OBSTACLE_COVER,
    OBSTACLE_OPENING,
    OBSTACLE_OUTDOOR,
    Attempt,
    obstacles,
    reconcile,
)
from syltra_contracts import Goal, GoalComparison, GoalState
from syltra_contracts.automations import AutomationAction
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

HOME = "home_recon"
NOW = datetime(2026, 8, 23, 15, 0, tzinfo=UTC)
COOL = AutomationAction(capability="climate.target_temperature", value=21, device_id="ac_living")


def _goal(**overrides: object) -> Goal:
    fields: dict[str, object] = {
        "home_id": HOME,
        "name": "الصالة لا تتجاوز ٢٤",
        "capability": "environment.temperature",
        "comparison": GoalComparison.AT_MOST,
        "value": 24,
        "room_id": "living_room",
        "actions": (COOL,),
    }
    fields.update(overrides)
    return Goal(**fields)


def _house(
    indoor: float,
    *,
    window_open: bool = False,
    cover: float | None = None,
    outdoor: float | None = None,
) -> object:
    devices = [
        device("temp_living", "living_room", a=reading("environment.temperature", indoor, NOW))
    ]
    if window_open:
        devices.append(
            device("window_living", "living_room", a=reading("contact.open", True, NOW))
        )
    if cover is not None:
        devices.append(
            device("curtain_living", "living_room", a=reading("cover.position", cover, NOW))
        )
    if outdoor is not None:
        devices.append(
            device("temp_outside", "outside", a=reading("environment.temperature", outdoor, NOW))
        )
    return home(*devices, home_id=HOME)


def _status(goal: Goal, house: object) -> GoalStatus:
    return assess(goal, house, NOW)


def test_the_first_violation_is_corrected() -> None:
    goal = _goal()
    status, correct = reconcile(goal, _status(goal, _house(29.0)), [], _house(29.0))
    assert correct is True
    assert status.state is GoalState.VIOLATED


def test_a_plan_that_is_working_is_left_alone() -> None:
    """Slow is not stalled. Re-issuing the same command into a room that is
    already cooling is noise in an audit trail."""
    goal = _goal()
    house = _house(27.0)
    attempts = [Attempt(at=NOW - timedelta(minutes=10), measured=29.0)]
    status, correct = reconcile(goal, _status(goal, house), attempts, house)

    assert correct is False
    assert status.state is GoalState.VIOLATED


def test_a_room_that_has_not_moved_gets_one_more_attempt() -> None:
    """One attempt is not evidence — the first correction may have gone into a
    room somebody had just opened a door to."""
    goal = _goal()
    house = _house(29.0)
    attempts = [Attempt(at=NOW - timedelta(minutes=10), measured=29.0)]
    _, correct = reconcile(goal, _status(goal, house), attempts, house)
    assert correct is True


def test_after_two_attempts_that_changed_nothing_it_stops() -> None:
    """The whole point. The command is not sent a third time."""
    goal = _goal()
    house = _house(29.0)
    attempts = [
        Attempt(at=NOW - timedelta(minutes=20), measured=29.0),
        Attempt(at=NOW - timedelta(minutes=10), measured=29.0),
    ]
    status, correct = reconcile(goal, _status(goal, house), attempts, house)

    assert correct is False
    assert status.state is GoalState.STALLED
    assert status.reason_code == GOAL_STALLED
    assert status.attempts == 2


def test_a_stall_names_what_the_house_can_see() -> None:
    """The concept's example, exactly: a window open, curtains open, and it is
    43° outside."""
    goal = _goal()
    house = _house(29.0, window_open=True, cover=100.0, outdoor=43.0)
    attempts = [
        Attempt(at=NOW - timedelta(minutes=20), measured=29.0),
        Attempt(at=NOW - timedelta(minutes=10), measured=29.0),
    ]
    status, _ = reconcile(goal, _status(goal, house), attempts, house)

    seen = {code for code, _device in status.obstacles}
    assert seen == {OBSTACLE_OPENING, OBSTACLE_COVER, OBSTACLE_OUTDOOR}
    # Each one carries the device that reported it: "a window is open" is
    # advice; "the living room window is open" is something somebody can shut.
    assert dict(status.obstacles)[OBSTACLE_OPENING] == "window_living"


def test_an_obstacle_is_observed_rather_than_guessed() -> None:
    """A household told a window is open, that finds every window shut, stops
    believing the next thing the panel says."""
    goal = _goal()
    house = _house(29.0)  # nothing reports a contact, a cover or the outdoors
    attempts = [Attempt(at=NOW, measured=29.0), Attempt(at=NOW, measured=29.0)]
    status, _ = reconcile(goal, _status(goal, house), attempts, house)

    assert status.state is GoalState.STALLED
    assert status.obstacles == ()


def test_a_closed_curtain_is_not_an_obstacle() -> None:
    assert obstacles(_goal(), _house(29.0, cover=0.0)) == ()


def test_weather_close_to_the_target_is_not_the_explanation() -> None:
    """25° outside does not explain a room that will not get below 24."""
    assert obstacles(_goal(), _house(29.0, outdoor=25.0)) == ()


def test_a_cold_goal_names_the_cold_outside() -> None:
    goal = _goal(comparison=GoalComparison.AT_LEAST, value=20)
    seen = {code for code, _device in obstacles(goal, _house(15.0, outdoor=2.0))}
    assert OBSTACLE_OUTDOOR in seen


def test_an_outdoor_thermometer_says_nothing_about_a_light() -> None:
    goal = _goal(
        capability="light.power",
        comparison=GoalComparison.EQUALS,
        value=False,
        actions=(AutomationAction(capability="light.power", value=False, device_id="l"),),
    )
    assert obstacles(goal, _house(29.0, outdoor=43.0)) == ()


def test_a_goal_with_nothing_to_do_about_it_is_never_called_stalled() -> None:
    """A goal that only reports has no plan to fail."""
    goal = _goal(actions=())
    house = _house(29.0)
    attempts = [Attempt(at=NOW, measured=29.0), Attempt(at=NOW, measured=29.0)]
    status, correct = reconcile(goal, _status(goal, house), attempts, house)

    assert correct is False
    assert status.state is GoalState.VIOLATED
