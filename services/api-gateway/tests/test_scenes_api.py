"""Scenes over the API: who may write one, who may press one, and what a
household is told when part of it did not happen.
"""

from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient
from syltra_api_gateway.platform import Platform
from syltra_automation_engine import SceneActivator
from syltra_security import Role

HOME = "home_001"

SLEEP = {
    "name": "وضع النوم",
    "steps": [
        {"capability": "light.power", "value": False},
        {"capability": "climate.target_temperature", "value": 21, "device_id": "ac_bed"},
    ],
}
LEAVING = {
    "name": "وضع الخروج",
    "steps": [
        {"capability": "light.power", "value": False},
        {"capability": "lock.state", "value": "locked", "device_id": "door_main"},
    ],
}


def _activator(platform: Platform) -> None:
    platform.scene_activator = SceneActivator(
        platform.policy, platform.orchestrator, platform.twin
    )


def test_a_scene_is_stored_and_read_back(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    created = client.post(f"/v1/homes/{HOME}/scenes", json=SLEEP, headers=auth())
    assert created.status_code == 201, created.text
    assert created.json()["summary"].startswith("home:light.power=False")

    listed = client.get(f"/v1/homes/{HOME}/scenes", headers=auth())
    assert [s["name"] for s in listed.json()["items"]] == ["وضع النوم"]


def test_a_scene_that_would_open_the_house_is_refused_at_the_door(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """The contract refuses it, and the API turns that into a 400 rather than a
    500: an unlocking scene is a bad request, not a broken hub."""
    response = client.post(
        f"/v1/homes/{HOME}/scenes",
        json={
            "name": "الرجوع",
            "steps": [{"capability": "lock.state", "value": "unlocked", "device_id": "d"}],
        },
        headers=auth(),
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "INVALID_SCENE"


def test_a_panel_is_told_which_scenes_it_may_press(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    """`activatable` is answered by the server for the same reason `operable`
    is: a panel showing a "leaving" scene it cannot run lies once and is never
    trusted again."""
    client.post(f"/v1/homes/{HOME}/scenes", json=SLEEP, headers=auth())
    client.post(f"/v1/homes/{HOME}/scenes", json=LEAVING, headers=auth())

    seen = {
        scene["name"]: scene["activatable"]
        for scene in client.get(f"/v1/homes/{HOME}/scenes", headers=auth(Role.PANEL)).json()[
            "items"
        ]
    }
    assert seen == {"وضع النوم": True, "وضع الخروج": False}


def test_a_panel_pressing_a_scene_it_may_not_run_is_refused(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    _activator(platform)
    scene_id = client.post(f"/v1/homes/{HOME}/scenes", json=LEAVING, headers=auth()).json()[
        "scene_id"
    ]

    response = client.post(
        f"/v1/homes/{HOME}/scenes/{scene_id}/activate", headers=auth(Role.PANEL)
    )
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "NOT_ALLOWED_HERE"


def test_pressing_a_scene_reports_every_step(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    _activator(platform)
    scene_id = client.post(f"/v1/homes/{HOME}/scenes", json=SLEEP, headers=auth()).json()[
        "scene_id"
    ]

    response = client.post(f"/v1/homes/{HOME}/scenes/{scene_id}/activate", headers=auth())
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    # Not "ok": a household that pressed this is owed a per-device answer.
    assert "fully_carried_out" in body
    assert {step["device_id"] for step in body["steps"]} >= {"ac_bed"}
    assert all("reasons" in step for step in body["steps"])


def test_a_hub_that_cannot_apply_scenes_says_so(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """Rather than reporting a press that reached nothing."""
    scene_id = client.post(f"/v1/homes/{HOME}/scenes", json=SLEEP, headers=auth()).json()[
        "scene_id"
    ]
    response = client.post(f"/v1/homes/{HOME}/scenes/{scene_id}/activate", headers=auth())
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "DISPATCH_UNAVAILABLE"


def test_a_guest_may_not_write_scenes(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """A scene is a standing thing in the house that other people will press."""
    response = client.post(f"/v1/homes/{HOME}/scenes", json=SLEEP, headers=auth(Role.GUEST))
    assert response.status_code == 403
