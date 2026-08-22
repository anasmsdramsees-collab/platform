"""Goal contracts — what a household says must stay true.

The earlier SYLTRA product called these *الأهداف* and described them in one
line: "you decide what must remain true". The hub checks, and says whether it
currently holds.

A goal is not an automation, and the difference is not cosmetic. An automation
is a sentence about an event — *when* motion is detected, turn on the light. It
fires on an edge and is then finished, whether or not the thing it wanted is
still true a minute later. A goal is a sentence about a state — the bedroom is
never above 26 — and it is either holding or it is not, right now, for a reason
the household can be shown.

That makes three things different:

**It is evaluated on a clock, not on an event.** A hub that only reacted to
readings would never notice a goal it broke by doing nothing.

**It has an answer, not just a history.** "Satisfied" or "violated" or — and
this is the one every other product gets wrong — **unknown**. A goal whose
sensor has gone quiet is not satisfied. It is unmeasured, and a screen that
shows a green tick for a room nobody can see is worse than one that admits it.

**Its correction is confined.** The check may read anything. What it *does*
about a violation reuses `AutomationAction`, which refuses to be constructed
with anything outside comfort — so a goal, which acts unattended and repeatedly,
can never be the thing that unlocks a door.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from syltra_contracts.automations import AutomationAction
from syltra_contracts.capability_definitions import DataType, get_definition

#: A floor, so a household cannot ask the hub to re-read the house every second.
MINIMUM_REVIEW_SECONDS = 30.0

#: The old product reviewed every sixty seconds and said so on the screen. It is
#: a good number: fast enough that a person watching sees it react, slow enough
#: that a hub is not spending its life checking.
DEFAULT_REVIEW_SECONDS = 60.0

#: How long after correcting a goal before it may correct again. A thermostat
#: does not cool a room in a minute, and a goal that re-issues its correction
#: every review is a goal fighting physics and filling an audit trail.
DEFAULT_REARM_SECONDS = 600.0


class GoalComparison(StrEnum):
    """What "true" means for this goal."""

    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"
    EQUALS = "EQUALS"


class GoalState(StrEnum):
    """Where a goal stands, right now."""

    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"
    """Nothing measured it, or the reading is past its freshness budget.

    Deliberately not a third shade of satisfied. A room whose thermometer has
    been silent for an hour is a room nobody can vouch for.
    """
    HELD = "HELD"
    """Violated, and deliberately not acted on — a person has just set this
    device by hand, and §0 rule 5 says they win."""
    STALLED = "STALLED"
    """Violated, corrected more than once, and not moving.

    The concept document's §08 case: the air conditioning is on, the room sits
    at 27°, and repeating the command is not going to change that. The platform
    stops re-issuing a plan that is not working and says what it can see —
    a window open, a curtain open, 43° outside.
    """
    OFF = "OFF"


class Goal(BaseModel):
    """A statement about the house that the hub keeps checking."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    goal_id: UUID = Field(default_factory=uuid4)
    home_id: str
    name: str = Field(min_length=1, max_length=120)
    enabled: bool = True

    #: What is measured. Any readable capability — the check is a read, and
    #: reading is not what needs restricting.
    capability: str
    comparison: GoalComparison
    value: Any
    #: Where it applies. A room means every device in it that reports the
    #: capability; neither means the whole house.
    room_id: str | None = None
    device_id: str | None = None

    #: What to do about a violation. May be empty: a goal that only reports is
    #: a perfectly good goal, and is the honest shape for anything the hub
    #: cannot fix by itself ("the front door is locked overnight").
    actions: tuple[AutomationAction, ...] = ()

    review_seconds: float = Field(default=DEFAULT_REVIEW_SECONDS, ge=MINIMUM_REVIEW_SECONDS)
    rearm_seconds: float = Field(default=DEFAULT_REARM_SECONDS, ge=0)
    owner: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: int = Field(default=1, ge=1)

    @field_validator("capability")
    @classmethod
    def _must_be_a_known_capability(cls, capability: str) -> str:
        get_definition(capability)
        return capability

    @model_validator(mode="after")
    def _the_comparison_must_fit_what_is_measured(self) -> "Goal":
        definition = get_definition(self.capability)
        numeric = definition.data_type is DataType.NUMBER
        if self.comparison in (GoalComparison.AT_LEAST, GoalComparison.AT_MOST) and not numeric:
            msg = (
                f"{self.capability} is {definition.data_type.value}; "
                f"{self.comparison.value} needs something with an order"
            )
            raise ValueError(msg)
        if numeric and not isinstance(self.value, int | float):
            msg = f"{self.capability} is measured as a number; {self.value!r} is not one"
            raise ValueError(msg)
        if not definition.is_within_range(self.value):
            msg = f"{self.value!r} is outside what {self.capability} can read"
            raise ValueError(msg)
        return self

    def holds_for(self, measured: Any) -> bool:
        """Whether this goal is satisfied by a reading.

        Called with a value the caller has already established is fresh —
        deciding *that* is the evaluator's job, and mixing the two here would
        let a stale reading answer this question.
        """
        if self.comparison is GoalComparison.EQUALS:
            return bool(measured == self.value)
        if not isinstance(measured, int | float) or isinstance(measured, bool):
            return False
        if self.comparison is GoalComparison.AT_LEAST:
            return bool(measured >= self.value)
        return bool(measured <= self.value)

    def summary(self) -> str:
        where = self.device_id or self.room_id or "home"
        word = {
            GoalComparison.AT_LEAST: "≥",
            GoalComparison.AT_MOST: "≤",
            GoalComparison.EQUALS: "=",
        }[self.comparison]
        return f"{where}:{self.capability} {word} {self.value}"
