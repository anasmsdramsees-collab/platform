"""Layer 12 — comparing what was asked for with what actually happened.

From `docs/concept/SYLTRA_Adaptive_Concept.md` §08, which sets out a case this
build did not handle:

> The air conditioning is on. The room reaches 27° and stops. The goal is not
> met. **The system does not repeat the same command.** It examines the
> difference, finds the window open, the curtains open and 43° outside, and
> changes the plan.

Goals shipped without this. A violated goal issued its corrective actions, waited
out its rearm, and issued exactly the same actions again — forever, at whatever
interval the household set, against a room with a window open. Every individual
part was correct: the goal was right that the room was too warm, the correction
was right that the air conditioning should be colder, and the policy gate was
right to allow it. The loop as a whole was a machine for repeating a plan that
was not working.

## What this decides, and what it refuses to decide

It answers one question — **is the correction getting anywhere?** — by comparing
the reading now against the reading when the correction was issued.

- Moving toward the target, by more than the noise of the sensor: the plan is
  working. Leave it alone; slow is not stalled.
- Not moving, twice: the plan is **stalled**. Stop re-issuing it, and say so.

It does not invent a new plan. This platform does not have an Adaptive Planning
Engine (Layer 08) and inventing one here — closing a window on a household's
behalf because a room is warm — is exactly the kind of thing §0 keeps away from
a model. What a stalled goal produces is a **sentence a person can act on**:
"the living room is still 29°, the air conditioning has been asked twice, and
there is an opening open and 43° outside."

## Obstacles are observed, never guessed

Everything in `OBSTACLES` is read from the twin: a contact that reports open, a
cover that reports open, an outdoor thermometer. Each is a fact with a device id
behind it. Nothing here infers "somebody probably left a window open" from a
temperature curve — a household told that, and finding every window shut, stops
believing the next thing the panel says.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from syltra_contracts import Goal, GoalComparison, GoalState

from syltra_automation_engine.goals import GoalStatus

logger = logging.getLogger(__name__)

#: How many corrections may be issued before a goal that has not moved is called
#: stalled. Two, not one: the first correction may have been issued into a room
#: that had only just been disturbed, and one attempt is not evidence.
MAX_ATTEMPTS = 2

#: How much a reading must move to count as movement rather than sensor noise.
#: A tenth of a degree is a thermometer breathing; half a degree is a room
#: changing.
MEANINGFUL_MOVEMENT = 0.5

#: A cover reporting more open than this counts as open. Not a preference — a
#: curtain at 10% is not what is keeping a room at 29°.
COVER_OPEN_ABOVE = 40.0

#: How far outside has to be, beyond the target, before the weather itself is
#: worth naming as the obstacle.
OUTDOOR_MARGIN = 8.0

OBSTACLE_OPENING = "OBSTACLE_OPENING_OPEN"
OBSTACLE_COVER = "OBSTACLE_COVER_OPEN"
OBSTACLE_OUTDOOR = "OBSTACLE_OUTDOOR_EXTREME"
GOAL_STALLED = "GOAL_PLAN_NOT_WORKING"

#: Rooms whose sensors are outdoors — the same convention the weather band uses.
OUTDOOR_ROOMS = frozenset(
    {"outside", "outdoor", "outdoors", "garden", "yard", "balcony", "terrace", "roof"}
)


@dataclass(frozen=True)
class Attempt:
    """One correction, and what the house read when it was issued."""

    at: datetime
    measured: Any


def _in_scope(goal: Goal, device: Any) -> bool:
    if goal.device_id is not None:
        return bool(device.device_id == goal.device_id)
    if goal.room_id is not None:
        return bool(device.room_id == goal.room_id)
    return True


def _reading(device: Any, capability: str) -> Any:
    state = device.capabilities.get(capability)
    if state is None or not getattr(state, "observed", False):
        return None
    return state.value


def obstacles(goal: Goal, home: Any) -> tuple[tuple[str, str], ...]:
    """What the house can see that would explain a goal not being reached.

    Returns `(reason_code, device_id)` pairs — the device is part of the answer,
    because "a window is open" is advice and "the living room window is open" is
    something somebody can go and shut.
    """
    if home is None:
        return ()
    found: list[tuple[str, str]] = []

    for device in home.devices.values():
        if not _in_scope(goal, device):
            continue
        if _reading(device, "contact.open") is True:
            found.append((OBSTACLE_OPENING, device.device_id))
        position = _reading(device, "cover.position")
        if isinstance(position, int | float) and position > COVER_OPEN_ABOVE:
            found.append((OBSTACLE_COVER, device.device_id))

    # The weather itself, when it is far enough past the target to be the
    # explanation rather than a detail. Only for a temperature goal: an outdoor
    # thermometer says nothing about whether a light is on.
    if goal.capability == "environment.temperature" and isinstance(goal.value, int | float):
        for device in home.devices.values():
            if str(device.room_id or "").lower() not in OUTDOOR_ROOMS:
                continue
            outside = _reading(device, "environment.temperature")
            if not isinstance(outside, int | float):
                continue
            if goal.comparison is GoalComparison.AT_MOST and outside > goal.value + OUTDOOR_MARGIN:
                found.append((OBSTACLE_OUTDOOR, device.device_id))
            elif (
                goal.comparison is GoalComparison.AT_LEAST
                and outside < goal.value - OUTDOOR_MARGIN
            ):
                found.append((OBSTACLE_OUTDOOR, device.device_id))

    return tuple(found)


def _moved_toward(goal: Goal, before: Any, now: Any) -> bool:
    """Whether the reading has moved toward the target since the correction."""
    if not isinstance(before, int | float) or not isinstance(now, int | float):
        # Nothing to compare — an EQUALS goal on a switch either holds or does
        # not, and "progress" is not a thing it can make.
        return False
    if goal.comparison is GoalComparison.AT_MOST:
        return before - now >= MEANINGFUL_MOVEMENT
    if goal.comparison is GoalComparison.AT_LEAST:
        return now - before >= MEANINGFUL_MOVEMENT
    return False


def reconcile(
    goal: Goal, status: GoalStatus, attempts: Sequence[Attempt], home: Any
) -> tuple[GoalStatus, bool]:
    """Decide whether to correct again, and what to tell the household.

    Returns the status — possibly rewritten as `STALLED` — and whether a further
    correction should be dispatched.
    """
    if status.state is not GoalState.VIOLATED or not goal.actions:
        return status, False
    if not attempts:
        # Nothing has been tried yet. Try.
        return status, True

    last = attempts[-1]
    if _moved_toward(goal, last.measured, status.measured):
        # The plan is working; it has not finished. Re-issuing the same command
        # into a room that is already cooling is noise in an audit trail.
        logger.debug("goal %s is moving toward its target", goal.name)
        return status, False

    if len(attempts) < MAX_ATTEMPTS:
        return status, True

    seen = obstacles(goal, home)
    logger.info(
        "goal %s stalled after %d attempts at %s; obstacles: %s",
        goal.name,
        len(attempts),
        status.measured,
        ", ".join(f"{code}:{device}" for code, device in seen) or "none visible",
    )
    stalled = replace(
        status,
        state=GoalState.STALLED,
        reason_code=GOAL_STALLED,
        attempts=len(attempts),
        obstacles=seen,
    )
    return stalled, False
