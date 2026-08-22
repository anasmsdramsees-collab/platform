"""Keeping a goal true — the loop that asks, and the rule about not knowing.

The contract says what a goal is. This decides, on a clock, whether it currently
holds, and what the hub is allowed to do about it.

## Unknown is a state, not a shade of satisfied

Most of this file exists for one rule. A goal whose sensor has gone quiet is not
satisfied — it is unmeasured. `assess` returns `UNKNOWN` when the twin has no
reading or when the reading is past the capability's own freshness budget, and
an unknown goal **never acts**: correcting a room nobody can see is guessing
with somebody's air conditioning.

A screen showing a green tick for a room whose thermometer died an hour ago is
the exact failure this platform is built to refuse.

## A room means the coldest corner of it

When a goal covers a room or the house, several devices may report the same
capability. The one that decides is the **worst** reading against the goal — the
warmest for an at-most, the coldest for an at-least — and never their mean. A
mean is a temperature no room has, and it satisfies a goal while one corner is
still 30 degrees.

## Held, rather than broken

A goal that wants to cool a room somebody has just turned the air conditioning
down in loses (§0 rule 5). That is not a failure and must not be shown as one:
the state is `HELD`, and it says a person is in charge of that device right now.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from syltra_contracts import Goal, GoalComparison, GoalState
from syltra_contracts.capability_definitions import get_definition

logger = logging.getLogger(__name__)

#: Reason codes a goal's status carries. Translated like every other code a
#: household is shown.
GOAL_HOLDS = "GOAL_HOLDS"
GOAL_BROKEN = "GOAL_NOT_HOLDING"
GOAL_UNMEASURED = "GOAL_UNMEASURED"
GOAL_HELD_BY_HAND = "GOAL_HELD_BY_HAND"
GOAL_SWITCHED_OFF = "GOAL_SWITCHED_OFF"


@dataclass(frozen=True)
class GoalStatus:
    """Where one goal stands, and why — the whole answer, not a colour."""

    goal_id: UUID
    name: str
    state: GoalState
    measured: Any
    target: Any
    comparison: GoalComparison
    device_id: str | None
    reason_code: str
    checked_at: datetime

    @property
    def needs_correcting(self) -> bool:
        """Only a measured violation. Never an unknown one."""
        return self.state is GoalState.VIOLATED


class GoalRegistry:
    """The household's goals, and what the hub last did about each."""

    def __init__(self) -> None:
        self._goals: dict[str, dict[UUID, Goal]] = {}
        self._last_reviewed: dict[tuple[str, UUID], datetime] = {}
        self._last_corrected: dict[tuple[str, UUID], datetime] = {}

    def upsert(self, goal: Goal) -> Goal:
        existing = self._goals.get(goal.home_id, {}).get(goal.goal_id)
        stored = goal
        if existing is not None:
            stored = goal.model_copy(
                update={"version": existing.version + 1, "created_at": existing.created_at}
            )
        self._goals.setdefault(goal.home_id, {})[stored.goal_id] = stored
        return stored

    def get(self, home_id: str, goal_id: UUID) -> Goal | None:
        return self._goals.get(home_id, {}).get(goal_id)

    def list_for(self, home_id: str) -> list[Goal]:
        return sorted(self._goals.get(home_id, {}).values(), key=lambda g: g.name)

    def remove(self, home_id: str, goal_id: UUID) -> bool:
        return self._goals.get(home_id, {}).pop(goal_id, None) is not None

    def set_enabled(self, home_id: str, goal_id: UUID, enabled: bool) -> Goal | None:
        goal = self.get(home_id, goal_id)
        if goal is None:
            return None
        return self.upsert(goal.model_copy(update={"enabled": enabled}))

    # ── the clock ──

    def due(self, goal: Goal, now: datetime) -> bool:
        last = self._last_reviewed.get((goal.home_id, goal.goal_id))
        return last is None or (now - last).total_seconds() >= goal.review_seconds

    def mark_reviewed(self, goal: Goal, now: datetime) -> None:
        self._last_reviewed[(goal.home_id, goal.goal_id)] = now

    def may_correct(self, goal: Goal, now: datetime) -> bool:
        last = self._last_corrected.get((goal.home_id, goal.goal_id))
        return last is None or (now - last).total_seconds() >= goal.rearm_seconds

    def mark_corrected(self, goal: Goal, now: datetime) -> None:
        self._last_corrected[(goal.home_id, goal.goal_id)] = now

    def last_corrected(self, home_id: str, goal_id: UUID) -> datetime | None:
        return self._last_corrected.get((home_id, goal_id))


def _readings(goal: Goal, home: Any, now: datetime) -> list[tuple[str, Any]]:
    """Every fresh reading of this goal's capability inside its scope."""
    if home is None:
        return []
    freshness = get_definition(goal.capability).freshness_seconds
    found: list[tuple[str, Any]] = []
    for device in home.devices.values():
        if goal.capability not in device.capabilities:
            continue
        if goal.device_id is not None and device.device_id != goal.device_id:
            continue
        if goal.device_id is None and goal.room_id is not None and device.room_id != goal.room_id:
            continue
        state = device.capabilities[goal.capability]
        if not getattr(state, "observed", False) or state.occurred_at is None:
            continue
        if (now - state.occurred_at).total_seconds() > freshness:
            # Past its own freshness budget. Dropped rather than aged: a stale
            # reading must not be the thing that says a room is fine.
            continue
        found.append((device.device_id, state.value))
    return found


def _worst(goal: Goal, readings: list[tuple[str, Any]]) -> tuple[str, Any]:
    """The reading that decides — never the mean of several.

    A mean is a temperature no room has, and it reports a goal as satisfied
    while one corner of the room is still thirty degrees.
    """
    if goal.comparison is GoalComparison.AT_MOST:
        return max(readings, key=lambda pair: pair[1])
    if goal.comparison is GoalComparison.AT_LEAST:
        return min(readings, key=lambda pair: pair[1])
    # EQUALS: any reading that differs breaks it, so report the first that does.
    for device_id, value in readings:
        if value != goal.value:
            return device_id, value
    return readings[0]


def assess(goal: Goal, home: Any, now: datetime | None = None) -> GoalStatus:
    """Where this goal stands, from what the twin currently knows."""
    moment = now or datetime.now(tz=UTC)

    def status(state: GoalState, measured: Any, reason: str, device_id: str | None) -> GoalStatus:
        return GoalStatus(
            goal_id=goal.goal_id,
            name=goal.name,
            state=state,
            measured=measured,
            target=goal.value,
            comparison=goal.comparison,
            device_id=device_id,
            reason_code=reason,
            checked_at=moment,
        )

    if not goal.enabled:
        return status(GoalState.OFF, None, GOAL_SWITCHED_OFF, goal.device_id)

    readings = _readings(goal, home, moment)
    if not readings:
        # Nothing measured it, or everything that did has gone quiet. Not
        # satisfied — unmeasured.
        return status(GoalState.UNKNOWN, None, GOAL_UNMEASURED, goal.device_id)

    device_id, measured = _worst(goal, readings)
    if goal.holds_for(measured):
        return status(GoalState.SATISFIED, measured, GOAL_HOLDS, device_id)
    return status(GoalState.VIOLATED, measured, GOAL_BROKEN, device_id)


def with_manual_hold(
    status: GoalStatus, goal: Goal, is_overridden: Callable[[str | None, str], bool]
) -> GoalStatus:
    """Re-read a violation as *held* when a person owns one of its targets.

    One place decides this, and both the loop and the screen call it — because
    a goal that the hub declines to correct and a goal it is showing as broken
    must never be two different answers to the same question.
    """
    if status.state is not GoalState.VIOLATED:
        return status
    if any(is_overridden(action.device_id, action.capability) for action in goal.actions):
        return held(status)
    return status


def held(status: GoalStatus) -> GoalStatus:
    """The same status, marked as deliberately not acted on.

    A goal that wanted to cool a room somebody has just adjusted by hand is not
    failing. Showing it as a violation would train a household to ignore the
    colour, which is how a screen stops meaning anything.
    """
    from dataclasses import replace

    return replace(status, state=GoalState.HELD, reason_code=GOAL_HELD_BY_HAND)
