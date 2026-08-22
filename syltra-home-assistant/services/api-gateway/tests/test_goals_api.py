"""Goals over the API — and the one answer a screen must never round off."""

from collections.abc import Callable

from fastapi.testclient import TestClient
from syltra_api_gateway.platform import Platform
from syltra_security import Role

HOME = "home_001"

WARM_ENOUGH = {
    "name": "الصالة لا تتجاوز ٢٦",
    "capability": "environment.temperature",
    "comparison": "AT_MOST",
    "value": 26,
    "room_id": "living_room",
}


def test_a_goal_is_answered_from_the_house_rather_than_from_memory(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """The conftest seeds this home at 27.4° — above the target, so the goal is
    not holding and the payload says which reading decided it."""
    created = client.post(f"/v1/homes/{HOME}/goals", json=WARM_ENOUGH, headers=auth())
    assert created.status_code == 201, created.text

    goal = client.get(f"/v1/homes/{HOME}/goals", headers=auth()).json()["items"][0]
    assert goal["state"] == "VIOLATED"
    assert goal["measured"] == 27.4
    assert goal["measured_by"] == f"{HOME}_sensor"


def test_a_goal_nothing_measures_is_unknown_rather_than_holding(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """The failure every product in this category ships: a green tick for a
    room whose sensor died an hour ago."""
    client.post(
        f"/v1/homes/{HOME}/goals",
        json={**WARM_ENOUGH, "name": "قبو بلا حسّاس", "room_id": "cellar"},
        headers=auth(),
    )
    goal = client.get(f"/v1/homes/{HOME}/goals", headers=auth()).json()["items"][0]

    assert goal["state"] == "UNKNOWN"
    assert goal["measured"] is None


def test_the_reason_is_translated_like_every_other_code(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    client.post(f"/v1/homes/{HOME}/goals", json=WARM_ENOUGH, headers=auth())
    goal = client.get(f"/v1/homes/{HOME}/goals?locale=ar", headers=auth()).json()["items"][0]
    assert goal["reason"] != goal["reason_code"]
    assert any("؀" <= ch <= "ۿ" for ch in goal["reason"])


def test_a_goal_a_person_is_overriding_reads_as_held(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    """Not as a failure. The screen and the loop call the same function, so
    they cannot give a household two different answers about the same room."""
    from datetime import UTC, datetime

    client.post(
        f"/v1/homes/{HOME}/goals",
        json={
            **WARM_ENOUGH,
            "actions": [
                {
                    "capability": "climate.target_temperature",
                    "value": 22,
                    "device_id": "ac_living",
                }
            ],
        },
        headers=auth(),
    )
    platform.policy.record_manual_change(
        HOME, "ac_living", "climate.target_temperature", datetime.now(tz=UTC)
    )

    goal = client.get(f"/v1/homes/{HOME}/goals", headers=auth()).json()["items"][0]
    assert goal["state"] == "HELD"


def test_a_goal_that_would_unlock_something_cannot_be_written(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    response = client.post(
        f"/v1/homes/{HOME}/goals",
        json={
            **WARM_ENOUGH,
            "actions": [{"capability": "lock.state", "value": "unlocked", "device_id": "d"}],
        },
        headers=auth(),
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "INVALID_GOAL"


def test_a_guest_may_not_write_goals(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    response = client.post(f"/v1/homes/{HOME}/goals", json=WARM_ENOUGH, headers=auth(Role.GUEST))
    assert response.status_code == 403


def test_a_goal_can_be_deleted(client: TestClient, auth: Callable[..., dict[str, str]]) -> None:
    goal_id = client.post(f"/v1/homes/{HOME}/goals", json=WARM_ENOUGH, headers=auth()).json()[
        "goal_id"
    ]
    assert client.delete(f"/v1/homes/{HOME}/goals/{goal_id}", headers=auth()).status_code == 204
    assert client.get(f"/v1/homes/{HOME}/goals", headers=auth()).json()["items"] == []
