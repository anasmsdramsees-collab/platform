"""Storing and applying scenes — the one-press shortcuts a household writes.

The contract (`syltra_contracts.scenes`) decides what a scene may contain. This
decides what happens when somebody presses one.

## A scene names what, not always which

A step may name a device, a room, or neither:

- `device_id` — that device, and only it.
- `room_id` — every device in that room with the capability. "Turn the living
  room lights off" keeps meaning that after somebody adds a lamp.
- neither — every device in the house with it. This is how "all lights off" and
  "lock every door" stay true as the house changes.

Expansion happens at activation against the twin, not at authoring time. A scene
that stored a list of device ids would quietly stop covering the lamp bought
last week, and the household would find out in the dark.

## Authorization is all-or-nothing; execution is not

Every step is checked before any step runs. A "leaving" scene that turns off the
switches and fails to lock the door is worse than one that refused: somebody
walks away believing the house is shut. So if the person pressing it may not do
one part, none of it runs.

Execution is the opposite, and deliberately: once authorized, a device that does
not answer must not stop the rest. Each step reports its own outcome and the
caller is told exactly which ones the house did not confirm.

## Why every step goes through the manual gate

A scene is a person deciding, so each step is authorized as manual control —
which also records a manual change, so the adaptive layer backs off the devices
a household has just set by hand. Pressing "sleep" and having the platform
undo it four seconds later is how a household stops trusting the platform.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from syltra_contracts import PolicyDecision, Scene, SceneStep

logger = logging.getLogger(__name__)


class _Policy(Protocol):
    def authorize_manual_control(
        self,
        home_id: str,
        device_id: str,
        capability: str,
        value: Any,
        actor: str,
        now: datetime | None = ...,
    ) -> PolicyDecision: ...


class _Executor(Protocol):
    async def execute(self, request: Any, now: datetime | None = ...) -> Any: ...


class _Twin(Protocol):
    def home(self, home_id: str) -> Any: ...


class SceneRefused(PermissionError):
    """The scene was not applied at all, and the household needs telling why."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail


@dataclass(frozen=True)
class StepOutcome:
    """What happened to one step of a scene."""

    capability: str
    device_id: str
    value: Any
    status: str | None
    verified: bool
    reason_codes: tuple[str, ...]

    @property
    def carried_out(self) -> bool:
        return self.status == "SUCCEEDED" and self.verified


@dataclass(frozen=True)
class Activation:
    """One press of one scene, and everything it did or did not do."""

    scene_id: UUID
    name: str
    at: datetime
    actor: str
    outcomes: tuple[StepOutcome, ...]

    @property
    def fully_carried_out(self) -> bool:
        """True only when every step was confirmed by its device.

        Not "most of it worked". A household that presses *leaving* is owed a
        plain answer about the door.
        """
        return bool(self.outcomes) and all(o.carried_out for o in self.outcomes)

    @property
    def unconfirmed(self) -> tuple[StepOutcome, ...]:
        return tuple(o for o in self.outcomes if not o.carried_out)


class SceneRegistry:
    """The household's scenes, and when each was last pressed."""

    def __init__(self) -> None:
        self._scenes: dict[str, dict[UUID, Scene]] = {}
        self._last_activated: dict[tuple[str, UUID], datetime] = {}

    def upsert(self, scene: Scene) -> Scene:
        existing = self._scenes.get(scene.home_id, {}).get(scene.scene_id)
        stored = scene
        if existing is not None:
            stored = scene.model_copy(
                update={"version": existing.version + 1, "created_at": existing.created_at}
            )
        self._scenes.setdefault(scene.home_id, {})[stored.scene_id] = stored
        return stored

    def get(self, home_id: str, scene_id: UUID) -> Scene | None:
        return self._scenes.get(home_id, {}).get(scene_id)

    def list_for(self, home_id: str) -> list[Scene]:
        return sorted(self._scenes.get(home_id, {}).values(), key=lambda s: s.name)

    def remove(self, home_id: str, scene_id: UUID) -> bool:
        return self._scenes.get(home_id, {}).pop(scene_id, None) is not None

    def set_enabled(self, home_id: str, scene_id: UUID, enabled: bool) -> Scene | None:
        scene = self.get(home_id, scene_id)
        if scene is None:
            return None
        return self.upsert(scene.model_copy(update={"enabled": enabled}))

    def last_activated(self, home_id: str, scene_id: UUID) -> datetime | None:
        return self._last_activated.get((home_id, scene_id))

    def record_activation(self, home_id: str, scene_id: UUID, at: datetime) -> None:
        self._last_activated[(home_id, scene_id)] = at


def targets_for(step: SceneStep, home: Any) -> list[str]:
    """Which devices this step means, right now.

    A device-scoped step is taken at its word even when the twin has never
    heard of the device: the household named it, and reporting "that device did
    not answer" is more useful than silently dropping the step.
    """
    if step.device_id is not None:
        return [step.device_id]
    if home is None:
        return []
    found = [
        device.device_id
        for device in home.devices.values()
        if step.capability in device.capabilities
        and (step.room_id is None or device.room_id == step.room_id)
    ]
    return sorted(found)


class SceneActivator:
    """Applies a scene, one authorized step at a time."""

    def __init__(
        self, policy: _Policy, orchestrator: _Executor, twin: _Twin | None = None
    ) -> None:
        self._policy = policy
        self._orchestrator = orchestrator
        self._twin = twin

    def plan(self, scene: Scene) -> list[tuple[SceneStep, str]]:
        """The steps as devices, before anything is authorized or sent."""
        home = self._twin.home(scene.home_id) if self._twin is not None else None
        plan: list[tuple[SceneStep, str]] = []
        for step in scene.steps:
            plan.extend((step, device_id) for device_id in targets_for(step, home))
        return plan

    async def activate(
        self, scene: Scene, actor: str, now: datetime | None = None
    ) -> Activation:
        moment = now or datetime.now(tz=UTC)
        if not scene.enabled:
            msg = f"the scene {scene.name!r} is switched off"
            raise SceneRefused("SCENE_DISABLED", msg)

        plan = self.plan(scene)
        if not plan:
            # Every step named a room or the house, and nothing in the twin has
            # the capability. Refused rather than reported as a success with no
            # steps, which is what "nothing happened" would look like.
            msg = f"nothing in this home matches the steps in {scene.name!r}"
            raise SceneRefused("SCENE_HAS_NO_TARGETS", msg)

        # Authorize everything first. A "leaving" scene that turns off the
        # switches and cannot lock the door must not run half way.
        decisions: list[tuple[SceneStep, str, PolicyDecision]] = []
        for step, device_id in plan:
            try:
                decision = self._policy.authorize_manual_control(
                    scene.home_id, device_id, step.capability, step.value, actor, moment
                )
            except ValueError as exc:
                msg = f"{step.capability} cannot be set from a scene: {exc}"
                raise SceneRefused("STEP_NOT_PERMITTED", msg) from exc
            decisions.append((step, device_id, decision))

        from syltra_action_orchestrator import build_manual_action

        outcomes: list[StepOutcome] = []
        for step, device_id, decision in decisions:
            request = build_manual_action(
                decision, device_id, step.capability, step.value, now=moment
            )
            try:
                result = await self._orchestrator.execute(request, moment)
            except Exception as exc:  # noqa: BLE001 - one device must not stop the scene
                logger.warning("scene %s: %s did not answer (%s)", scene.name, device_id, exc)
                outcomes.append(
                    StepOutcome(
                        capability=step.capability,
                        device_id=device_id,
                        value=step.value,
                        status=None,
                        verified=False,
                        reason_codes=("DEVICE_DID_NOT_ANSWER",),
                    )
                )
                continue
            outcomes.append(
                StepOutcome(
                    capability=step.capability,
                    device_id=device_id,
                    value=step.value,
                    status=result.status.value,
                    verified=bool(getattr(result, "verified", False)),
                    reason_codes=tuple(result.reason_codes),
                )
            )

        return Activation(
            scene_id=scene.scene_id,
            name=scene.name,
            at=moment,
            actor=actor,
            outcomes=tuple(outcomes),
        )
