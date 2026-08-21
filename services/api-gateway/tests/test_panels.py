"""A wall panel is a light switch, not a console (owner decision, 2026-08-21).

A panel authenticates by somebody standing in front of it. That is a fair
credential for comfort — anyone in your hallway could already flip the switch —
and it is not a credential for anything else. Most of this file is about the
"anything else".
"""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from syltra_security import ROLE_PERMISSIONS, Permission, Role, TokenStore

HOME = "home_001"
pytestmark = pytest.mark.contract


def owner(auth: Callable[..., dict[str, str]]) -> dict[str, str]:
    return auth(Role.OWNER, {HOME})


def register(
    client: TestClient, auth: Callable[..., dict[str, str]], location: str = "Hall"
) -> dict[str, Any]:
    body: dict[str, Any] = client.post(
        f"/v1/homes/{HOME}/panels",
        headers=owner(auth),
        json={"location": location, "reason": "panel mounted by the front door"},
    ).json()
    return body


# ── what a panel may never do ──


def test_a_panel_cannot_reach_a_lock_or_a_garage_door() -> None:
    """The concrete risk: a panel by the front door that opens the front door
    is a panel a burglar reaches through a letterbox.

    Enforced by the capability registry rather than by a list in the panel
    code, so a new security-sensitive capability is out of reach the day it is
    added.
    """
    from syltra_security import permission_for_capability

    panel = ROLE_PERMISSIONS[Role.PANEL]
    for capability in ("lock.state", "garage.state", "camera.recording"):
        assert permission_for_capability(capability) not in panel, capability


def test_a_panel_cannot_reach_a_valve_or_a_siren() -> None:
    from syltra_security import permission_for_capability

    panel = ROLE_PERMISSIONS[Role.PANEL]
    for capability in ("valve.state", "siren.state", "breaker.state"):
        assert permission_for_capability(capability) not in panel, capability


def test_a_panel_can_do_exactly_what_a_light_switch_does() -> None:
    from syltra_security import permission_for_capability

    panel = ROLE_PERMISSIONS[Role.PANEL]
    for capability in ("light.power", "climate.target_temperature", "cover.position"):
        assert permission_for_capability(capability) in panel, capability


def test_a_panel_manages_nobody_and_reads_no_audit_trail() -> None:
    panel = ROLE_PERMISSIONS[Role.PANEL]
    for forbidden_permission in (
        Permission.MANAGE_USERS,
        Permission.READ_AUDIT,
        Permission.VIEW_CAMERA,
        Permission.MANAGE_POLICY,
        Permission.APPROVE_RECOMMENDATION,
    ):
        assert forbidden_permission not in panel, forbidden_permission


def test_a_panel_is_not_a_child_wearing_a_different_name() -> None:
    """They carry the same two permissions today for different reasons.

    A change to what a child may do must not silently change what a wall panel
    may do, which is why they are separate roles rather than an alias.
    """
    # Two entries in the table, not one aliased twice. The comparison mypy can
    # prove — that the members differ — proves nothing; what matters is that
    # each has its own row, so editing one leaves the other alone.
    assert {Role.PANEL, Role.CHILD} <= set(ROLE_PERMISSIONS)
    assert ROLE_PERMISSIONS[Role.PANEL] == ROLE_PERMISSIONS[Role.CHILD], (
        "they carry the same set today, for different reasons"
    )


# ── the console is in charge of it ──


def test_only_an_owner_may_put_a_panel_on_a_wall(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """Installing one is a physical decision about somebody's house."""
    response = client.post(
        f"/v1/homes/{HOME}/panels",
        headers=auth(Role.ADULT, {HOME}),
        json={"location": "Hall", "reason": "handy"},
    )
    assert response.status_code == 403


def test_a_panel_is_named_by_where_it_hangs(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """The audit trail will have to say this: "the hall panel" is checkable and
    "somebody" is not."""
    response = client.post(
        f"/v1/homes/{HOME}/panels",
        headers=owner(auth),
        json={"reason": "mounted"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "LOCATION_REQUIRED"


def test_registering_a_panel_returns_its_token_once(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    body = register(client, auth)
    assert body["token"]
    assert body["token_shown_once"] is True
    assert body["role"] == "PANEL"

    listed = client.get(f"/v1/homes/{HOME}/panels", headers=owner(auth)).json()
    assert listed["panels"], "the panel is listed"
    assert "token" not in listed["panels"][0], "and its token is not"


def test_a_panel_does_not_expire_the_way_a_visit_does(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """There is no visit for it to outlast. What ends it is the owner taking
    it down — not a default meant for a guest staying the weekend."""
    from datetime import UTC, datetime, timedelta

    body = register(client, auth)
    assert body["expires_at"] is not None
    expires = datetime.fromisoformat(body["expires_at"])
    assert expires > datetime.now(tz=UTC) + timedelta(days=365)


def test_taking_a_panel_down_stops_its_token_working(
    client: TestClient, auth: Callable[..., dict[str, str]], tokens: TokenStore
) -> None:
    """A row saying "access taken away" beside a credential that still opens
    the API is a console lying about the one thing it is for.
    """
    body = register(client, auth)
    panel_header = {"Authorization": f"Bearer {body['token']}"}

    assert client.get(f"/v1/homes/{HOME}/devices", headers=panel_header).status_code == 200

    revoked = client.post(
        f"/v1/homes/{HOME}/users/{body['membership_id']}/revoke",
        headers=owner(auth),
        json={"reason": "panel removed during redecorating"},
    ).json()
    assert revoked["tokens_revoked"] >= 1

    assert client.get(f"/v1/homes/{HOME}/devices", headers=panel_header).status_code == 401


def test_a_panel_may_read_the_home_it_hangs_in(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    body = register(client, auth)
    header = {"Authorization": f"Bearer {body['token']}"}
    assert client.get(f"/v1/homes/{HOME}/devices", headers=header).status_code == 200
    # And not the audit trail.
    assert client.get(f"/v1/audit?home_id={HOME}", headers=header).status_code == 403
