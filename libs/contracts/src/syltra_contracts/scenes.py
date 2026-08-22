"""Scene contracts — the household's own one-press shortcuts.

A scene is a named set of things to set at once: *sleep* dims the living room,
closes the curtains and drops the air conditioning a degree; *leaving* turns the
switches off and locks the door. The earlier SYLTRA product had these on its
home screen and they are the most-pressed control in any smart home, because a
household does not think in devices — it thinks in what it is about to do.

## Why this is not an automation with a button on it

An automation asks "when should this happen?" and answers it itself. A scene
never fires on its own: somebody presses it, every time. That difference is the
whole security model here, and it is why a scene may reach one thing an
automation may not.

## The securing direction

Automations are confined to comfort (§2.3) — no automation may touch a lock,
because a rule that unlocks a door at a time nobody predicted is a burglary
waiting for a bug. A scene has a person behind it, so it may lock a door.

**It may not unlock one.** `SECURING_VALUES` is a direction lock in the same
spirit as the risk engine's `FAIL_SAFE_VALUES`: for the two capabilities a scene
may reach outside comfort, only the securing value can be stored. A "leaving"
scene locks; a "coming home" scene cannot unlock, and a household that wants
their door open opens it deliberately, with the confirmation that capability
declares.

The asymmetry is the point. The failure mode of refusing to unlock is somebody
using a key. The failure mode of permitting it is one mistaken press — or one
guest with a panel in a hallway — opening the house.

## What no scene may ever reach

Valves, breakers, sirens, and every alarm sensor. Those are life-safety, driven
by deterministic rules from certified evidence, and a person who wants one
operates it by hand. Cameras are excluded too, for a different reason: a shortcut
that starts recording the people in a room is not a convenience.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from syltra_contracts.automations import AUTOMATABLE_SAFETY_CLASSES
from syltra_contracts.capability_definitions import Access, get_definition

#: The only values a scene may set outside comfort, and the only capabilities it
#: may set them on. A direction lock, not a permission: the value is part of it.
SECURING_VALUES: dict[str, frozenset[str]] = {
    "lock.state": frozenset({"locked"}),
    "garage.state": frozenset({"closed"}),
}

#: A scene is a shortcut, not a program. Past this many steps it is a script
#: somebody will not be able to read back to themselves before pressing it —
#: and a single press that issues fifty commands is a rate-limit event wearing
#: a friendly name.
MAX_STEPS = 24


class SceneStep(BaseModel):
    """One thing a scene sets. Never what it does — policy decides that."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability: str
    value: Any
    device_id: str | None = None
    room_id: str | None = None

    @model_validator(mode="after")
    def _must_be_reachable_by_a_shortcut(self) -> "SceneStep":
        """Refused here rather than at activation.

        A scene that would unlock a door should not exist as an object — not be
        stored and stopped later, when the stopping is one missing check away
        from not happening.
        """
        definition = get_definition(self.capability)
        if definition.access is Access.READ:
            msg = f"{self.capability} is read-only; a scene cannot set it"
            raise ValueError(msg)

        if definition.safety_class in AUTOMATABLE_SAFETY_CLASSES:
            if not definition.is_within_range(self.value):
                msg = f"{self.value!r} is outside what {self.capability} accepts"
                raise ValueError(msg)
            return self

        securing = SECURING_VALUES.get(self.capability)
        if securing is None:
            msg = (
                f"{self.capability} is {definition.safety_class.value}; a scene may set "
                "comfort capabilities, and may only secure a lock or a garage door"
            )
            raise ValueError(msg)
        if self.value not in securing:
            msg = (
                f"a scene may set {self.capability} to "
                f"{' or '.join(sorted(securing))} and nothing else — unlocking is a "
                "deliberate act, not a shortcut"
            )
            raise ValueError(msg)
        return self

    @property
    def secures(self) -> bool:
        """True when this step is the securing exception rather than comfort."""
        return self.capability in SECURING_VALUES


class Scene(BaseModel):
    """A named set of settings a person applies in one press.

    `enabled` rather than deletion, for the same reason automations have it: a
    household that turns something off usually wants it back, and an audit
    trail that cannot say "this was switched off on Tuesday" is missing the
    fact that explains the week.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    scene_id: UUID = Field(default_factory=uuid4)
    home_id: str
    name: str = Field(min_length=1, max_length=120)
    enabled: bool = True
    steps: tuple[SceneStep, ...] = Field(min_length=1, max_length=MAX_STEPS)
    owner: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: int = Field(default=1, ge=1)

    @field_validator("steps")
    @classmethod
    def _one_value_per_target(cls, steps: tuple[SceneStep, ...]) -> tuple[SceneStep, ...]:
        """A scene may not tell the same device two different things.

        Whichever step ran last would win, which makes the scene's effect
        depend on the order somebody typed it in — and makes "what does this
        scene do?" unanswerable by reading it.
        """
        seen: set[tuple[str | None, str | None, str]] = set()
        for step in steps:
            key = (step.device_id, step.room_id, step.capability)
            if key in seen:
                target = step.device_id or step.room_id or "home"
                msg = f"this scene sets {target}:{step.capability} twice"
                raise ValueError(msg)
            seen.add(key)
        return steps

    @property
    def secures(self) -> bool:
        """True if any step locks something — which changes who may press it."""
        return any(step.secures for step in self.steps)

    def summary(self) -> str:
        """A one-line description, for a list a person reads."""
        return ", ".join(
            f"{s.device_id or s.room_id or 'home'}:{s.capability}={s.value}" for s in self.steps
        )
