"""The contract between the console and the API (UI-2 acceptance: real contracts).

Phase UI-1 shipped views that read `status.healthy`, `context.label` and
`recommendation.title`. None of those fields exists. Nothing failed — JavaScript
returns `undefined` for a missing property, so the console rendered empty
headings and reported the system as degraded while every component was fine.
The tests all passed, because they checked the console's source against itself.

This file checks it against the API instead: every field name the console reads
off a response must actually be in that response. It is deliberately a list a
person maintains rather than something parsed out of the JavaScript — a parser
would have to model property access well enough to be its own bug source, and
the list is short enough to read.
"""

from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from syltra_security import Role, TokenStore

HOME = "home_001"

# field name -> where the console reads it. Kept in the order the console does.
RESPONSE_FIELDS: dict[str, tuple[str, ...]] = {
    "/v1/me": ("subject", "display_name", "role", "permissions", "homes"),
    "/v1/system/status": ("hub_id", "checked_at", "uptime_seconds", "homes", "components"),
    "/v1/homes/{home}/rooms": ("rooms",),
    "/v1/homes/{home}/devices": ("items",),
    "/v1/homes/{home}/contexts/current": ("contexts",),
    "/v1/homes/{home}/risks": ("cases",),
    "/v1/homes/{home}/recommendations": ("items", "total"),
    "/v1/homes/{home}/actions": ("items", "total"),
    "/v1/homes/{home}/models": ("learning_mode", "models"),
}

ITEM_FIELDS: dict[str, tuple[str, tuple[str, ...]]] = {
    "/v1/homes/{home}/devices": (
        "items",
        ("device_id", "room_id", "name", "available", "last_seen", "capabilities"),
    ),
    "/v1/homes/{home}/rooms": ("rooms", ("room_id", "device_ids", "device_count")),
    "/v1/homes/{home}/contexts/current": (
        "contexts",
        (
            "context_type",
            "scope",
            "confidence",
            "seconds_until_expiry",
            "advisory_only",
            "reasons",
            "evidence",
        ),
    ),
    "/v1/homes/{home}/recommendations": (
        "items",
        (
            "recommendation_id",
            "recommendation_type",
            "target",
            "proposed_value",
            "confidence",
            "created_at",
            "expires_at",
            "requires_user_approval",
            "shadow",
            "model",
            "reasons",
        ),
    ),
}

# Every capability reading the console inspects.
READING_FIELDS = ("value", "unit", "status", "age_seconds")


@pytest.fixture
def owner(tokens: TokenStore) -> dict[str, str]:
    token, _ = tokens.issue("console", Role.OWNER, {HOME}, ttl=timedelta(minutes=5))
    return {"Authorization": f"Bearer {token}"}


def fetch(client: TestClient, path: str, owner: dict[str, str]) -> Any:
    response = client.get(path.format(home=HOME), headers=owner)
    assert response.status_code == 200, f"{path} -> {response.status_code}"
    return response.json()


@pytest.mark.parametrize("path,fields", RESPONSE_FIELDS.items())
def test_the_console_reads_only_fields_the_response_has(
    client: TestClient, owner: dict[str, str], path: str, fields: tuple[str, ...]
) -> None:
    body = fetch(client, path, owner)
    missing = [field for field in fields if field not in body]
    assert not missing, f"{path} is missing {missing}; the console reads them"


@pytest.mark.parametrize("path,spec", ITEM_FIELDS.items())
def test_the_console_reads_only_item_fields_the_response_has(
    client: TestClient, owner: dict[str, str], path: str, spec: tuple[str, tuple[str, ...]]
) -> None:
    collection, fields = spec
    items = fetch(client, path, owner)[collection]
    assert items, f"{path} returned no {collection}; this test would prove nothing"
    for item in items:
        missing = [field for field in fields if field not in item]
        assert not missing, f"{path} {collection} item is missing {missing}"


def test_capability_readings_carry_what_the_device_state_rule_needs(
    client: TestClient, owner: dict[str, str]
) -> None:
    # `deviceState` derives ONLINE/STALE/UNKNOWN from `status` and `age_seconds`
    # rather than from a threshold invented in the console. If either field went
    # away, every device would silently read as unknown.
    devices = fetch(client, "/v1/homes/{home}/devices", owner)["items"]
    readings = [r for device in devices for r in device["capabilities"].values()]
    assert readings
    for reading in readings:
        for field in READING_FIELDS:
            assert field in reading, field
        assert reading["status"] in {"KNOWN", "STALE", "UNKNOWN"}, reading["status"]


def test_system_status_still_has_no_overall_health_flag(
    client: TestClient, owner: dict[str, str]
) -> None:
    # The console derives health by counting `components`, precisely because
    # there is no `healthy` field. If one is ever added, this fails and the
    # console should switch to it rather than keep a second definition.
    body = fetch(client, "/v1/system/status", owner)
    assert "healthy" not in body
    assert all(isinstance(value, str) for value in body["components"].values())


def test_recommendation_targets_name_a_device_and_capability(
    client: TestClient, owner: dict[str, str]
) -> None:
    items = fetch(client, "/v1/homes/{home}/recommendations", owner)["items"]
    assert items
    for item in items:
        assert set(item["target"]) >= {"device_id", "capability"}
        assert set(item["model"]) >= {"name", "version"}
