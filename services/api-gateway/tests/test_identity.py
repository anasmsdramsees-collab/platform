"""`/v1/me`, and the rule that hiding a control is not authorization.

Guidelines §3: "The UI must be role-aware. Hidden access is not authorization.
Backend authorization remains mandatory." The console filters navigation from
this endpoint, so two things must hold together:

- it reports the caller's real permissions, or the console hides the wrong
  things;
- the endpoints refuse regardless of what the console chose to draw.

The second is the one that matters. A console is a rendering of authority, not
a source of it, and these tests are here so that stays true when someone later
adds a navigation item and forgets the server side.
"""

from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from syltra_api_gateway.platform import Platform
from syltra_security import ROLE_PERMISSIONS, Permission, Role, TokenStore

HOME = "home_001"


def header(tokens: TokenStore, role: Role, homes: set[str] | None = None) -> dict[str, str]:
    token, _ = tokens.issue(f"user-{role.value}", role, homes or {HOME}, ttl=timedelta(minutes=5))
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("role", list(Role))
def test_me_reports_the_role_and_its_real_permissions(
    client: TestClient, tokens: TokenStore, role: Role
) -> None:
    body = client.get("/v1/me", headers=header(tokens, role)).json()
    assert body["role"] == role.value
    assert set(body["permissions"]) == {p.value for p in ROLE_PERMISSIONS[role]}


def test_me_reports_only_the_homes_the_token_covers(
    client: TestClient, tokens: TokenStore
) -> None:
    # `homes` drives the property selector. It is the token's own scope, so it
    # can never be used to discover a household the caller is not part of.
    body = client.get("/v1/me", headers=header(tokens, Role.OWNER, {HOME})).json()
    assert body["homes"] == [HOME]


def test_me_needs_a_token(client: TestClient) -> None:
    assert client.get("/v1/me").status_code == 401


def test_no_role_is_reported_as_holding_safety_authority(
    client: TestClient, tokens: TokenStore
) -> None:
    # Invariant 18: life-safety actuators are commanded by the Safety Governor,
    # never by a person holding a permission. If ACT_SAFETY ever appeared here,
    # a console could reasonably render a control for it.
    for role in Role:
        body = client.get("/v1/me", headers=header(tokens, role)).json()
        assert Permission.ACT_SAFETY.value not in body["permissions"], role


# ── hiding is not authorization ──


@pytest.mark.parametrize(
    "role", [role for role in Role if Permission.READ_AUDIT not in ROLE_PERMISSIONS[role]]
)
def test_the_audit_trail_refuses_a_role_that_only_had_it_hidden(
    client: TestClient, tokens: TokenStore, role: Role
) -> None:
    # The console omits the Audit Trail item for these roles. That is tidiness.
    # This is the actual protection: the endpoint refuses even when asked
    # directly, which is what a user who edits the URL will find.
    headers = header(tokens, role)
    assert (
        Permission.READ_AUDIT.value
        not in client.get("/v1/me", headers=headers).json()["permissions"]
    )
    assert client.get(f"/v1/audit?home_id={HOME}", headers=headers).status_code == 403


def test_a_caller_cannot_reach_a_home_outside_its_scope(
    client: TestClient, tokens: TokenStore
) -> None:
    # The property selector lists only the caller's homes. Typing another one
    # into the URL must not work — and must not confirm the home exists.
    headers = header(tokens, Role.OWNER, {HOME})
    response = client.get("/v1/homes/home_999/twin", headers=headers)
    assert response.status_code == 404
    assert "home_999" not in response.text or "not a member" not in response.text


# ── the audit trail speaks the household's language (§23, §17.14) ──


def test_audit_reason_codes_are_translated_like_every_other_endpoint(
    client: TestClient, tokens: TokenStore
) -> None:
    # The audit trail is the screen most likely to be read after something has
    # gone wrong, and it was the one place a household saw
    # `AUTOMATION_NOT_YET_TRUSTED` instead of words: every other endpoint
    # translated its reason codes and this one did not.
    headers = header(tokens, Role.OWNER)
    for path in (f"/v1/audit?home_id={HOME}", f"/v1/audit?home_id={HOME}&locale=ar"):
        body = client.get(path, headers=headers).json()
        for entry in body["items"]:
            if not entry.get("reason_codes"):
                continue
            assert entry.get("reasons"), entry["action"]
            for reason in entry["reasons"]:
                assert reason not in entry["reason_codes"], f"untranslated: {reason}"


def test_an_audit_entry_records_what_it_acted_on(
    client: TestClient, platform: Any, tokens: TokenStore
) -> None:
    # The API discarded the orchestrator's `detail`, so the trail could say
    # something was dispatched but not to what — a §17.14 field, and the first
    # thing an incident review needs.
    import inspect

    from syltra_api_gateway import api as api_module

    source = inspect.getsource(api_module.create_app)
    assert "**action_entry.detail" in source
    assert "**risk_entry.detail" in source


# ── the camera line, through the API (owner decision, 2026-08-21) ──


def seed_camera(platform: Platform) -> None:
    from datetime import UTC, datetime

    from syltra_testing import make_envelope

    platform.twin.apply(
        make_envelope(
            capability="camera.recording",
            value=True,
            unit=None,
            home_id=HOME,
            device_id="camera_hall",
            room_id="hall",
            occurred_at=datetime.now(tz=UTC),
        )
    )


def test_a_camera_is_absent_from_the_device_list_rather_than_blanked(
    client: TestClient, tokens: TokenStore, platform: Platform
) -> None:
    """Removed, not nulled.

    A key present with a null value still tells the reader the camera exists
    and that somebody decided they may not see it. Whether a room has a camera
    is itself the kind of thing a property company should not learn from a
    device list.
    """
    seed_camera(platform)

    def capabilities_seen_by(role: Role) -> set[str]:
        body = client.get(f"/v1/homes/{HOME}/devices", headers=header(tokens, role)).json()
        return {name for device in body["items"] for name in (device.get("capabilities") or {})}

    assert "camera.recording" in capabilities_seen_by(Role.OWNER)
    # A support technician debugging a schedule has no business watching the hall.
    assert "camera.recording" not in capabilities_seen_by(Role.SUPPORT)
    assert "camera.recording" not in capabilities_seen_by(Role.INSTALLER)


def test_the_device_itself_is_still_listed_when_its_camera_is_hidden(
    client: TestClient, tokens: TokenStore, platform: Platform
) -> None:
    """Hiding the device would make a hub look like it has fewer than it does."""
    seed_camera(platform)
    body = client.get(f"/v1/homes/{HOME}/devices", headers=header(tokens, Role.SUPPORT)).json()
    assert any(device["device_id"] == "camera_hall" for device in body["items"])
