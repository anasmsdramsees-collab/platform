"""Users and roles through the API (spec §21, UI-5).

The directory already refuses the dangerous changes; these tests are about the
gateway not losing that on the way through — the right status code, the reason
requirement surfacing as a 400 rather than a 500, and a caller seeing only the
roles it could actually hand out.
"""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from syltra_api_gateway.platform import Platform
from syltra_security import Role

HOME = "home_001"
pytestmark = pytest.mark.contract


def owner_header(auth: Callable[..., dict[str, str]]) -> dict[str, str]:
    return auth(Role.OWNER, {HOME})


def seed_owner(platform: Platform, subject: str = "user_owner") -> Any:
    return platform.users.grant(
        HOME,
        subject,
        Role.OWNER,
        actor="bootstrap",
        actor_role=Role.OWNER,
        reason="household set up",
    )


def test_a_household_with_no_members_says_so_rather_than_erroring(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    body = client.get(f"/v1/homes/{HOME}/users", headers=owner_header(auth)).json()
    assert body["members"] == []
    assert body["may_manage"] is True


def test_a_resident_can_see_who_holds_a_key_but_not_change_it(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    """Knowing who else can open your front door is not a privileged question."""
    seed_owner(platform)
    resident = auth(Role.ADULT, {HOME})

    listing = client.get(f"/v1/homes/{HOME}/users", headers=resident)
    assert listing.status_code == 200
    assert listing.json()["may_manage"] is False

    refused = client.post(
        f"/v1/homes/{HOME}/users",
        headers=resident,
        json={"subject": "stranger", "role": "GUEST", "reason": "a friend is over"},
    )
    assert refused.status_code == 403


def test_a_change_without_a_reason_is_a_bad_request_not_a_crash(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    response = client.post(
        f"/v1/homes/{HOME}/users",
        headers=owner_header(auth),
        json={"subject": "visitor", "role": "GUEST"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "REASON_REQUIRED"


def test_an_unknown_role_names_the_ones_that_exist(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    response = client.post(
        f"/v1/homes/{HOME}/users",
        headers=owner_header(auth),
        json={"subject": "visitor", "role": "ADMIN", "reason": "typo"},
    )
    assert response.status_code == 400
    assert "SAFETY_OPERATOR" in response.json()["detail"]["message"]


def test_granting_and_revoking_round_trips(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    seed_owner(platform)
    header = owner_header(auth)
    granted = client.post(
        f"/v1/homes/{HOME}/users",
        headers=header,
        json={"subject": "visitor", "role": "GUEST", "reason": "staying the weekend"},
    ).json()
    assert granted["active"] is True
    assert granted["expires_at"] is not None, "guest access must not be open-ended"

    revoked = client.post(
        f"/v1/homes/{HOME}/users/{granted['membership_id']}/revoke",
        headers=header,
        json={"reason": "visit ended"},
    ).json()
    assert revoked["active"] is False

    listing = client.get(f"/v1/homes/{HOME}/users", headers=header).json()
    assert any(m["membership_id"] == granted["membership_id"] for m in listing["members"])


def test_the_last_owner_cannot_be_removed_through_the_api(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    owner = seed_owner(platform)
    response = client.post(
        f"/v1/homes/{HOME}/users/{owner.membership_id}/revoke",
        headers=owner_header(auth),
        json={"reason": "leaving"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "LAST_OWNER"


def test_the_assignable_roles_are_the_ones_the_caller_could_actually_grant(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """The console hides controls it cannot use, rather than offering a button
    the server will refuse."""
    owner = client.get(f"/v1/homes/{HOME}/users", headers=owner_header(auth)).json()
    assert "OWNER" in owner["assignable_roles"]
    assert "SAFETY_OPERATOR" in owner["assignable_roles"]
    assert "SERVICE" not in owner["assignable_roles"]

    installer = client.get(f"/v1/homes/{HOME}/users", headers=auth(Role.INSTALLER, {HOME})).json()
    assert "OWNER" not in installer["assignable_roles"]


def test_a_missing_membership_is_a_404(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    response = client.post(
        f"/v1/homes/{HOME}/users/11111111-1111-4111-8111-111111111111/revoke",
        headers=owner_header(auth),
        json={"reason": "tidying up"},
    )
    assert response.status_code == 404
