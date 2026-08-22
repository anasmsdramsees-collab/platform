"""API authorization tests (spec §14.9, §21, §25.1).

Phase 7 acceptance: authorization isolates homes and roles.
"""

from collections.abc import Callable
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from syltra_security import Role, TokenStore

pytestmark = pytest.mark.safety

HOME = "home_001"
OTHER_HOME = "home_002"

Auth = Callable[..., dict[str, str]]

READ_ENDPOINTS = [
    f"/v1/homes/{HOME}/twin",
    f"/v1/homes/{HOME}/rooms",
    f"/v1/homes/{HOME}/devices",
    f"/v1/homes/{HOME}/contexts/current",
    f"/v1/homes/{HOME}/recommendations",
    f"/v1/homes/{HOME}/risks",
    f"/v1/homes/{HOME}/models",
]


# ── authentication ──


@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_every_home_endpoint_requires_a_credential(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 401


def test_a_malformed_credential_is_rejected(client: TestClient) -> None:
    response = client.get(
        f"/v1/homes/{HOME}/twin", headers={"Authorization": "Basic bm90LWEtdG9rZW4="}
    )
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "MISSING_TOKEN"


def test_an_unknown_token_is_rejected(client: TestClient) -> None:
    response = client.get(
        f"/v1/homes/{HOME}/twin", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "INVALID_TOKEN"


def test_an_expired_token_is_rejected(client: TestClient, tokens: TokenStore, auth: Auth) -> None:
    token, _ = tokens.issue("owner", Role.OWNER, {HOME}, ttl=timedelta(seconds=-1))
    response = client.get(f"/v1/homes/{HOME}/twin", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "TOKEN_EXPIRED"


def test_a_revoked_token_stops_working(client: TestClient, tokens: TokenStore, auth: Auth) -> None:
    token, _ = tokens.issue("owner", Role.OWNER, {HOME})
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get(f"/v1/homes/{HOME}/twin", headers=headers).status_code == 200
    tokens.revoke(token)
    assert client.get(f"/v1/homes/{HOME}/twin", headers=headers).status_code == 401


# ── home isolation ──


@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_a_foreign_home_is_reported_as_absent_not_forbidden(
    client: TestClient, auth: Auth, path: str
) -> None:
    # "Forbidden" would confirm the home exists. Across households that is a
    # real leak, however small.
    foreign_path = path.replace(HOME, OTHER_HOME)
    response = client.get(foreign_path, headers=auth(Role.OWNER, {HOME}))
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "HOME_NOT_FOUND"


def test_a_member_of_both_homes_sees_both(
    client: TestClient, tokens: TokenStore, auth: Auth
) -> None:
    headers = auth(Role.OWNER, {HOME, OTHER_HOME})
    for home in (HOME, OTHER_HOME):
        assert client.get(f"/v1/homes/{home}/twin", headers=headers).status_code == 200


def test_one_household_never_sees_another_households_devices(
    client: TestClient, tokens: TokenStore, auth: Auth
) -> None:
    body = client.get(f"/v1/homes/{HOME}/devices", headers=auth()).json()
    device_ids = {item["device_id"] for item in body["items"]}
    assert device_ids
    assert not any(OTHER_HOME in device_id for device_id in device_ids)


def test_the_audit_endpoint_is_home_scoped(
    client: TestClient, tokens: TokenStore, auth: Auth
) -> None:
    response = client.get(
        "/v1/audit", params={"home_id": OTHER_HOME}, headers=auth(Role.OWNER, {HOME})
    )
    assert response.status_code == 404


# ── role separation ──


def test_a_guest_may_read_but_not_approve(
    client: TestClient, tokens: TokenStore, auth: Auth
) -> None:
    headers = auth(Role.GUEST)
    assert client.get(f"/v1/homes/{HOME}/twin", headers=headers).status_code == 200
    response = client.post(
        f"/v1/homes/{HOME}/recommendations/{'0' * 8}-0000-0000-0000-000000000000/approve",
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "INSUFFICIENT_PERMISSION"


def test_a_child_cannot_approve_automation(
    client: TestClient, tokens: TokenStore, auth: Auth
) -> None:
    response = client.post(
        f"/v1/homes/{HOME}/recommendations/{'0' * 8}-0000-0000-0000-000000000000/approve",
        headers=auth(Role.CHILD),
    )
    assert response.status_code == 403


def test_only_an_owner_may_suspend_a_model(
    client: TestClient, tokens: TokenStore, auth: Auth
) -> None:
    for role in (Role.ADULT, Role.CHILD, Role.GUEST, Role.INSTALLER):
        response = client.post(
            f"/v1/homes/{HOME}/models/temperature_preference/suspend",
            headers=auth(role),
            json={"reason": "test"},
        )
        assert response.status_code == 403, f"{role} should not suspend models"


def test_only_privileged_roles_read_the_audit_trail(
    client: TestClient, tokens: TokenStore, auth: Auth
) -> None:
    # The audit reveals who did what — a separate permission from reading state.
    assert (
        client.get("/v1/audit", params={"home_id": HOME}, headers=auth(Role.OWNER)).status_code
        == 200
    )
    for role in (Role.ADULT, Role.CHILD, Role.GUEST, Role.INSTALLER):
        response = client.get("/v1/audit", params={"home_id": HOME}, headers=auth(role))
        assert response.status_code == 403, f"{role} should not read the audit trail"


# ── the WebSocket stream ──


def test_the_stream_rejects_an_unauthenticated_peer(client: TestClient) -> None:
    # The socket is closed before it is accepted, so an unauthenticated peer
    # never reaches an open connection.
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/v1/stream?home_id={HOME}") as ws:
            ws.receive_json()
    assert exc.value.code == 4401


def test_the_stream_rejects_a_foreign_home(client: TestClient, tokens: TokenStore) -> None:
    token, _ = tokens.issue("owner", Role.OWNER, {HOME})
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/v1/stream?home_id={OTHER_HOME}&token={token}") as ws:
            ws.receive_json()
    assert exc.value.code == 4403


def test_an_authorized_peer_connects(client: TestClient, tokens: TokenStore, auth: Auth) -> None:
    token, _ = tokens.issue("owner", Role.OWNER, {HOME})
    with client.websocket_connect(f"/v1/stream?home_id={HOME}&token={token}") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "connected"
        assert hello["home_id"] == HOME
        ws.send_text("ping")
        assert ws.receive_json()["type"] == "pong"


# ── no internal detail leaks ──


def test_responses_expose_no_transport_or_storage_internals(
    client: TestClient, tokens: TokenStore, auth: Auth
) -> None:
    # Spec §14.9: avoid exposing internal NATS or database details.
    headers = auth()
    forbidden = (
        "nats://",
        "postgresql",
        "syltra.normalized",
        "jetstream",
        "asyncpg",
        "stream_sequence",
        "SELECT ",
    )
    for path in [*READ_ENDPOINTS, "/v1/system/status"]:
        body = client.get(path, headers=headers).text
        for needle in forbidden:
            assert needle.lower() not in body.lower(), f"{path} leaked {needle}"


def test_system_status_reports_components_not_connection_details(
    client: TestClient, tokens: TokenStore, auth: Auth
) -> None:
    body = client.get("/v1/system/status", headers=auth()).json()
    assert set(body["components"]) >= {"digital_twin", "policy_safety", "risk_engine"}
    assert "nats_url" not in body
    assert "database_url" not in body
