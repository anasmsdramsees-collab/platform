"""Automation contracts (spec §2.3, ADR-009).

An automation is the one thing in this platform a household writes itself: a
trigger, some conditions, and an action. It is deterministic, it runs when the
Adaptive Engine is down (invariant 7), and it goes through the same policy gate
as everything else (invariant 2).

The types are closed on purpose. There is no expression to evaluate and no
script to run — ADR-009 explains why, and the short version is that "this
automation can only touch non-critical capabilities" is a question you can
answer by looking at typed data and cannot answer about arbitrary text.

The most important line in this file is the validator on `AutomationAction`.
Spec §2.3 permits automations to execute *non-critical* actions only, and that
is enforced where the object is built rather than where it would run: an
automation that would unlock a door cannot be constructed, so it cannot be
stored, listed, exported, or reasoned about as something that might one day
fire.
"""

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from syltra_contracts.capability_definitions import get_definition
from syltra_contracts.enums import SafetyClass

# §2.3: automations execute non-critical actions only. Comfort is the everyday
# case — lights, climate, covers, switches. Anything a household would consider
# a security or life-safety decision is out, and stays out.
AUTOMATABLE_SAFETY_CLASSES: frozenset[SafetyClass] = frozenset(
    {SafetyClass.NON_CRITICAL, SafetyClass.COMFORT}
)

# An automation that could fire every second is a fault, not a feature. This is
# the floor; an automation may ask for longer.
MINIMUM_REARM = timedelta(seconds=30)

# An automation's action is not allowed to sit pending indefinitely. §0 requires
# every action to be time-bounded, and a stale one must expire rather than run
# against a home that has moved on.
DEFAULT_ACTION_TTL = timedelta(minutes=5)


class AutomationSource(StrEnum):
    """Where an automation came from (UI guidelines §17.8).

    It matters to a reader: `MANUAL` is something a person wrote and owns;
    `SUGGESTED` is something SYLTRA proposed and a person accepted; `FIXED_SAFETY`
    is not editable by a household at all.
    """

    MANUAL = "MANUAL"
    SUGGESTED = "SUGGESTED"
    ADAPTIVE = "ADAPTIVE"
    FIXED_SAFETY = "FIXED_SAFETY"


class TriggerKind(StrEnum):
    STATE_EQUALS = "STATE_EQUALS"
    """A capability takes a specific value — a motion sensor reads true."""
    THRESHOLD_ABOVE = "THRESHOLD_ABOVE"
    THRESHOLD_BELOW = "THRESHOLD_BELOW"
    CONTEXT_STARTED = "CONTEXT_STARTED"
    AT_TIME = "AT_TIME"
    """A time of day in the household's own timezone.

    Stored as an hour and minute plus a set of weekdays rather than as a cron
    expression. A cron string is a small language, and ADR-009 refused to put a
    language in an automation for the same reason it refused an interpreter:
    the moment a household can write one, somebody can write one that surprises
    them, and nothing can read it back to them in Arabic.
    """
    """A deterministic context becomes active — quiet hours begin."""


class ConditionKind(StrEnum):
    CONTEXT_ACTIVE = "CONTEXT_ACTIVE"
    CONTEXT_INACTIVE = "CONTEXT_INACTIVE"
    STATE_EQUALS = "STATE_EQUALS"
    THRESHOLD_ABOVE = "THRESHOLD_ABOVE"
    THRESHOLD_BELOW = "THRESHOLD_BELOW"


class AutomationTrigger(BaseModel):
    """What starts the automation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: TriggerKind
    capability: str | None = None
    device_id: str | None = None
    room_id: str | None = None
    value: Any = None
    context_type: str | None = None
    #: Local wall-clock time, in the household's timezone. Not UTC: a person
    #: who asks for 7pm means 7pm on their own clock, in summer and in winter.
    at_hour: int | None = None
    at_minute: int | None = None
    #: Days it may fire on, 0 = Monday. Empty means every day.
    weekdays: tuple[int, ...] = ()

    @model_validator(mode="after")
    def _needs_what_it_watches(self) -> "AutomationTrigger":
        if self.kind is TriggerKind.AT_TIME:
            if self.at_hour is None or self.at_minute is None:
                msg = "an AT_TIME trigger must name an hour and a minute"
                raise ValueError(msg)
            if not 0 <= self.at_hour <= 23 or not 0 <= self.at_minute <= 59:
                msg = f"{self.at_hour:02d}:{self.at_minute:02d} is not a time of day"
                raise ValueError(msg)
            if any(day not in range(7) for day in self.weekdays):
                msg = "weekdays are 0 (Monday) through 6 (Sunday)"
                raise ValueError(msg)
            return self
        if self.kind is TriggerKind.CONTEXT_STARTED:
            if not self.context_type:
                msg = "a CONTEXT_STARTED trigger must name a context type"
                raise ValueError(msg)
            return self
        if not self.capability:
            msg = f"a {self.kind.value} trigger must name a capability"
            raise ValueError(msg)
        get_definition(self.capability)  # unknown capability raises
        if self.kind is not TriggerKind.STATE_EQUALS and not isinstance(
            self.value, int | float
        ):
            msg = f"a {self.kind.value} trigger needs a numeric threshold"
            raise ValueError(msg)
        return self


class AutomationCondition(BaseModel):
    """Something that must also be true, checked at evaluation time."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ConditionKind
    capability: str | None = None
    device_id: str | None = None
    room_id: str | None = None
    value: Any = None
    context_type: str | None = None

    @model_validator(mode="after")
    def _needs_what_it_checks(self) -> "AutomationCondition":
        if self.kind in {ConditionKind.CONTEXT_ACTIVE, ConditionKind.CONTEXT_INACTIVE}:
            if not self.context_type:
                msg = f"a {self.kind.value} condition must name a context type"
                raise ValueError(msg)
            return self
        if not self.capability:
            msg = f"a {self.kind.value} condition must name a capability"
            raise ValueError(msg)
        get_definition(self.capability)
        return self


class AutomationAction(BaseModel):
    """What the automation asks for. Never what it does — policy decides that."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability: str
    value: Any
    device_id: str | None = None
    room_id: str | None = None

    @field_validator("capability")
    @classmethod
    def _must_be_automatable(cls, capability: str) -> str:
        """Spec §2.3: user-authorized, **non-critical** actions only.

        Refused here rather than at dispatch. An automation that would close a
        valve or unlock a door should not exist as an object — not be stored
        and stopped later, when the stopping is one missing check away from not
        happening.
        """
        definition = get_definition(capability)
        if definition.safety_class not in AUTOMATABLE_SAFETY_CLASSES:
            msg = (
                f"{capability} is {definition.safety_class.value}; automations may only "
                f"act on {', '.join(sorted(c.value for c in AUTOMATABLE_SAFETY_CLASSES))} "
                "capabilities (spec §2.3)"
            )
            raise ValueError(msg)
        if definition.access.value == "READ":
            msg = f"{capability} is read-only; an automation cannot set it"
            raise ValueError(msg)
        return capability


class Automation(BaseModel):
    """A user-authored rule.

    `enabled` is a first-class field rather than deletion: a household that
    turns an automation off usually wants it back, and an audit trail that
    cannot say "this was switched off on Tuesday" is missing the fact that
    explains the week.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    automation_id: UUID = Field(default_factory=uuid4)
    home_id: str
    name: str = Field(min_length=1, max_length=120)
    enabled: bool = True
    source: AutomationSource = AutomationSource.MANUAL
    trigger: AutomationTrigger
    conditions: tuple[AutomationCondition, ...] = ()
    actions: tuple[AutomationAction, ...] = Field(min_length=1)
    rearm_seconds: float = Field(default=MINIMUM_REARM.total_seconds(), ge=0)
    owner: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: int = Field(default=1, ge=1)

    @field_validator("rearm_seconds")
    @classmethod
    def _not_faster_than_the_floor(cls, seconds: float) -> float:
        if seconds < MINIMUM_REARM.total_seconds():
            msg = (
                f"rearm_seconds must be at least {MINIMUM_REARM.total_seconds():.0f}; "
                "an automation that can fire every second is a fault, not a feature"
            )
            raise ValueError(msg)
        return seconds

    @property
    def safety_class(self) -> SafetyClass:
        """The most consequential class any of its actions touches."""
        order = [SafetyClass.NON_CRITICAL, SafetyClass.COMFORT]
        worst = SafetyClass.NON_CRITICAL
        for action in self.actions:
            definition = get_definition(action.capability)
            if order.index(definition.safety_class) > order.index(worst):
                worst = definition.safety_class
        return worst

    def summary(self) -> str:
        """A one-line description, for a list a person reads (§17.8)."""
        targets = ", ".join(
            f"{a.device_id or a.room_id or 'home'}:{a.capability}={a.value}"
            for a in self.actions
        )
        return f"{self.trigger.kind.value} → {targets}"
