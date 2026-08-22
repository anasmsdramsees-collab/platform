"""What a scene may contain, decided where the object is built.

A scene that would unlock a door should not exist as an object — not be stored
and stopped later, when the stopping is one missing check away from not
happening. Every test here is about that line.
"""

import pytest
from pydantic import ValidationError
from syltra_contracts import Scene, SceneStep

pytestmark = pytest.mark.contract


def _scene(*steps: SceneStep) -> Scene:
    return Scene(home_id="home_1", name="وضع الخروج", steps=steps)


def test_a_scene_may_set_the_comfort_of_a_house() -> None:
    scene = _scene(
        SceneStep(capability="light.power", value=False),
        SceneStep(capability="cover.position", value=0, room_id="living_room"),
        SceneStep(capability="climate.target_temperature", value=24, device_id="ac_living"),
    )
    assert len(scene.steps) == 3
    assert scene.secures is False


def test_a_scene_may_lock_a_door() -> None:
    """An automation may not — a rule that unlocks at a time nobody predicted
    is a burglary waiting for a bug. A scene has a person behind it."""
    scene = _scene(SceneStep(capability="lock.state", value="locked", device_id="door_main"))
    assert scene.secures is True


@pytest.mark.parametrize(
    ("capability", "value"),
    [("lock.state", "unlocked"), ("garage.state", "open"), ("garage.state", "opening")],
)
def test_a_scene_may_not_open_the_house(capability: str, value: str) -> None:
    """The asymmetry is the point. Refusing to unlock costs somebody a key;
    permitting it costs one mistaken press, or one guest with a panel in a
    hallway."""
    with pytest.raises(ValidationError, match="deliberate act"):
        SceneStep(capability=capability, value=value)


@pytest.mark.parametrize(
    "capability", ["valve.state", "breaker.state", "siren.state", "camera.recording"]
)
def test_no_shortcut_reaches_life_safety_or_a_camera(capability: str) -> None:
    with pytest.raises(ValidationError, match="a scene may set comfort"):
        SceneStep(capability=capability, value="closed")


def test_a_scene_cannot_set_a_sensor() -> None:
    with pytest.raises(ValidationError, match="read-only"):
        SceneStep(capability="environment.temperature", value=20)


def test_a_value_outside_the_capability_is_refused() -> None:
    with pytest.raises(ValidationError, match="outside what"):
        SceneStep(capability="climate.target_temperature", value=95)


def test_a_scene_may_not_tell_the_same_device_two_things() -> None:
    """Whichever step ran last would win, which makes the scene's effect depend
    on the order somebody typed it in."""
    with pytest.raises(ValidationError, match="twice"):
        _scene(
            SceneStep(capability="light.power", value=True, device_id="light_hall"),
            SceneStep(capability="light.power", value=False, device_id="light_hall"),
        )


def test_the_same_capability_on_two_devices_is_fine() -> None:
    scene = _scene(
        SceneStep(capability="light.power", value=False, device_id="light_hall"),
        SceneStep(capability="light.power", value=True, device_id="light_porch"),
    )
    assert len(scene.steps) == 2


def test_a_scene_is_a_shortcut_rather_than_a_program() -> None:
    """Past two dozen steps it is a script somebody cannot read back to
    themselves before pressing it."""
    with pytest.raises(ValidationError):
        _scene(
            *(
                SceneStep(capability="light.power", value=False, device_id=f"light_{i}")
                for i in range(25)
            )
        )


def test_a_scene_needs_at_least_one_step() -> None:
    with pytest.raises(ValidationError):
        _scene()
