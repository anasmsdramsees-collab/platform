"""Pressing a scene: what it expands to, what it refuses to start, and what it
reports when a device does not answer.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from syltra_automation_engine import SceneActivator, SceneRefused, SceneRegistry
from syltra_contracts import (
    ActionStatus,
    PolicyDecision,
    PolicyOutcome,
    SafetyClass,
    Scene,
    SceneStep,
)

NOW = datetime(2026, 8, 22, 22, 30, tzinfo=UTC)


def _home(*devices: tuple[str, str, str]) -> Any:
    return SimpleNamespace(
        devices={
            device_id: SimpleNamespace(
                device_id=device_id, room_id=room_id, capabilities={capability: object()}
            )
            for device_id, room_id, capability in devices
        }
    )


class _Twin:
    def __init__(self, home: Any) -> None:
        self._home = home

    def home(self, home_id: str) -> Any:
        return self._home


class _Policy:
    def __init__(self, refuse: str | None = None) -> None:
        self.refuse = refuse
        self.authorized: list[tuple[str, str]] = []

    def authorize_manual_control(
        self,
        home_id: str,
        device_id: str,
        capability: str,
        value: Any,
        actor: str,
        now: datetime | None = None,
    ) -> PolicyDecision:
        if self.refuse is not None and capability == self.refuse:
            msg = f"{capability} is not operable by hand"
            raise ValueError(msg)
        self.authorized.append((device_id, capability))
        return PolicyDecision(
            decision_id=uuid4(),
            recommendation_id=None,
            home_id=home_id,
            decision=PolicyOutcome.ALLOW,
            evaluated_at=now or NOW,
            expires_at=(now or NOW) + timedelta(seconds=30),
            reason_codes=["MANUAL_CONTROL"],
            safety_class=SafetyClass.COMFORT,
            policy_version="test",
            input_hash="0" * 8,
        )


class _Orchestrator:
    def __init__(self, failing: str | None = None) -> None:
        self.failing = failing
        self.executed: list[Any] = []

    async def execute(self, request: Any, now: datetime | None = None) -> Any:
        self.executed.append(request)
        if self.failing is not None and request.target.device_id == self.failing:
            msg = "the device is not there"
            raise RuntimeError(msg)
        return SimpleNamespace(
            status=ActionStatus.SUCCEEDED, verified=True, reason_codes=["VERIFIED"]
        )


def _all_lights_off() -> Scene:
    return Scene(
        home_id="home_1",
        name="كل الأنوار",
        steps=(SceneStep(capability="light.power", value=False),),
    )


async def test_a_home_wide_step_means_every_device_that_has_it() -> None:
    """ "All lights off" keeps meaning that after somebody adds a lamp — which
    is why expansion happens when it is pressed, not when it was written."""
    twin = _Twin(
        _home(
            ("light_hall", "hall", "light.power"),
            ("light_kitchen", "kitchen", "light.power"),
            ("plug_tv", "living_room", "switch.power"),
        )
    )
    policy, orchestrator = _Policy(), _Orchestrator()
    activation = await SceneActivator(policy, orchestrator, twin).activate(
        _all_lights_off(), "someone", NOW
    )

    assert {o.device_id for o in activation.outcomes} == {"light_hall", "light_kitchen"}
    assert activation.fully_carried_out is True


async def test_a_room_step_stops_at_the_room() -> None:
    twin = _Twin(
        _home(("light_hall", "hall", "light.power"), ("light_bed", "bedroom", "light.power"))
    )
    scene = Scene(
        home_id="home_1",
        name="الممر",
        steps=(SceneStep(capability="light.power", value=False, room_id="hall"),),
    )
    activation = await SceneActivator(_Policy(), _Orchestrator(), twin).activate(
        scene, "someone", NOW
    )
    assert [o.device_id for o in activation.outcomes] == ["light_hall"]


async def test_a_device_the_twin_has_never_heard_of_is_still_attempted() -> None:
    """The household named it. "That device did not answer" is more useful than
    silently dropping the step."""
    scene = Scene(
        home_id="home_1",
        name="مصباح",
        steps=(SceneStep(capability="light.power", value=True, device_id="light_new"),),
    )
    orchestrator = _Orchestrator()
    await SceneActivator(_Policy(), orchestrator, _Twin(_home())).activate(scene, "s", NOW)
    assert orchestrator.executed[0].target.device_id == "light_new"


async def test_nothing_runs_when_one_step_is_not_permitted() -> None:
    """A "leaving" scene that turns off the switches and cannot lock the door
    must not run half way: somebody walks away believing the house is shut."""
    twin = _Twin(
        _home(("light_hall", "hall", "light.power"), ("door_main", "entrance", "lock.state"))
    )
    scene = Scene(
        home_id="home_1",
        name="وضع الخروج",
        steps=(
            SceneStep(capability="light.power", value=False),
            SceneStep(capability="lock.state", value="locked", device_id="door_main"),
        ),
    )
    orchestrator = _Orchestrator()
    with pytest.raises(SceneRefused, match="STEP_NOT_PERMITTED"):
        await SceneActivator(_Policy(refuse="lock.state"), orchestrator, twin).activate(
            scene, "someone", NOW
        )
    assert orchestrator.executed == []


async def test_one_device_that_does_not_answer_does_not_stop_the_rest() -> None:
    """Once authorized, the opposite rule applies — and the household is told
    exactly which steps the house did not confirm."""
    twin = _Twin(
        _home(("light_hall", "hall", "light.power"), ("light_kitchen", "kitchen", "light.power"))
    )
    activation = await SceneActivator(
        _Policy(), _Orchestrator(failing="light_kitchen"), twin
    ).activate(_all_lights_off(), "someone", NOW)

    assert len(activation.outcomes) == 2
    assert activation.fully_carried_out is False
    assert [o.device_id for o in activation.unconfirmed] == ["light_kitchen"]


async def test_a_scene_that_matches_nothing_is_refused_rather_than_reported_empty() -> None:
    """ "Nothing happened" and "it worked" must not look the same."""
    with pytest.raises(SceneRefused, match="SCENE_HAS_NO_TARGETS"):
        await SceneActivator(_Policy(), _Orchestrator(), _Twin(_home())).activate(
            _all_lights_off(), "someone", NOW
        )


async def test_a_scene_switched_off_does_not_run() -> None:
    scene = _all_lights_off().model_copy(update={"enabled": False})
    with pytest.raises(SceneRefused, match="SCENE_DISABLED"):
        await SceneActivator(_Policy(), _Orchestrator(), _Twin(_home())).activate(
            scene, "someone", NOW
        )


def test_the_registry_keeps_versions_and_remembers_the_last_press() -> None:
    registry = SceneRegistry()
    scene = registry.upsert(_all_lights_off())
    again = registry.upsert(scene.model_copy(update={"name": "كل الأنوار (معدّل)"}))
    assert again.version == 2
    assert registry.list_for("home_1") == [again]

    assert registry.last_activated("home_1", scene.scene_id) is None
    registry.record_activation("home_1", scene.scene_id, NOW)
    assert registry.last_activated("home_1", scene.scene_id) == NOW
    assert registry.remove("home_1", scene.scene_id) is True
    assert registry.list_for("home_1") == []
