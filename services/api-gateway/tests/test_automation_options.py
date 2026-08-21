"""What a household may build an automation out of (§2.3, ADR-009).

The console asks the server rather than carrying its own copy of the capability
vocabulary, so this endpoint is where the builder's honesty lives: it cannot
offer a device the home does not have, and it cannot offer a capability the
platform would refuse.
"""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from syltra_api_gateway.platform import Platform
from syltra_security import Role

HOME = "home_001"
pytestmark = pytest.mark.contract


def options(client: TestClient, auth: Callable[..., dict[str, str]]) -> dict[str, Any]:
    body: dict[str, Any] = client.get(
        f"/v1/homes/{HOME}/automations/options", headers=auth(Role.OWNER, {HOME})
    ).json()
    return body


def test_the_literal_route_is_not_swallowed_by_the_id_route(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """FastAPI matches in registration order.

    Declared after `/{automation_id}`, "options" was parsed as a UUID and
    answered 422 — the same shape of bug as a static mount shadowing a route.
    """
    response = client.get(
        f"/v1/homes/{HOME}/automations/options", headers=auth(Role.OWNER, {HOME})
    )
    assert response.status_code == 200


def test_nothing_outside_comfort_may_be_acted_on(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """`AutomationAction` refuses these at construction, so offering one would
    produce a form whose submission always fails."""
    from syltra_contracts import SafetyClass
    from syltra_contracts.capability_definitions import get_definition

    for entry in options(client, auth)["act_on"]:
        assert get_definition(entry["capability"]).safety_class in (
            SafetyClass.NON_CRITICAL,
            SafetyClass.COMFORT,
        )


def test_what_cannot_be_automated_is_named_rather_than_hidden(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    """§20: a household that cannot automate its gas valve should be told that
    is deliberate."""
    from datetime import UTC, datetime

    from syltra_testing import make_envelope

    platform.twin.apply(
        make_envelope(
            capability="valve.state",
            value="open",
            unit=None,
            home_id=HOME,
            device_id="valve_main",
            room_id="utility",
            occurred_at=datetime.now(tz=UTC),
        )
    )
    excluded = options(client, auth)["not_automatable"]
    assert any(entry["capability"] == "valve.state" for entry in excluded)
    assert all(entry["reason"] for entry in excluded), "each must say why, translated"


def test_the_options_come_from_the_home_rather_than_from_a_list(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    home = platform.twin.home(HOME)
    assert home is not None, "the fixture seeds this home; without it the test proves nothing"
    known = {device.device_id for device in home.devices.values()}
    for entry in options(client, auth)["act_on"]:
        assert entry["device_id"] in known


def test_the_form_is_told_the_engine_s_own_guard_rails(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    """So it can explain a refusal before it happens rather than after."""
    assert options(client, auth)["minimum_rearm_seconds"] > 0


def test_every_trigger_kind_the_contract_allows_is_offered(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    from syltra_contracts import TriggerKind

    assert set(options(client, auth)["trigger_kinds"]) == {k.value for k in TriggerKind}
