"""Digital Twin read API tests (spec §21 subset).

The API is exercised against a projection populated directly, so these run
without infrastructure.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from syltra_digital_twin.api import create_app
from syltra_digital_twin.service import DigitalTwinService
from syltra_testing import make_envelope


class _NullPublisher:
    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


@pytest.fixture
def client() -> TestClient:
    service = DigitalTwinService(session_factory=None, publisher=_NullPublisher())  # type: ignore[arg-type]
    # Ages are expressed relative to real 'now' because the API evaluates
    # freshness against the wall clock; a fixed past instant would drift.
    now = datetime.now(tz=UTC)
    service.twin.apply(
        make_envelope(value=24.5, device_id="dev_1", room_id="living_room", occurred_at=now)
    )
    service.twin.apply(
        make_envelope(
            capability="light.power",
            value=True,
            unit=None,
            device_id="dev_2",
            room_id="bedroom",
            occurred_at=now,
        )
    )
    service.twin.apply(
        make_envelope(
            capability="safety.gas_alarm",
            value=False,
            unit=None,
            device_id="dev_1",
            room_id="living_room",
            # Gas-alarm freshness is 120s, so two hours old is decisively stale.
            occurred_at=now - timedelta(hours=2),
        )
    )
    service.mark_ready(True)
    return TestClient(create_app(service))


def test_twin_endpoint_returns_devices_rooms_and_fingerprint(client: TestClient) -> None:
    body = client.get("/v1/homes/home_001/twin").json()
    assert body["home_id"] == "home_001"
    assert set(body["devices"]) == {"dev_1", "dev_2"}
    assert body["rooms"]["living_room"] == ["dev_1"]
    assert len(body["fingerprint"]) == 64  # sha256 hex


def test_rooms_endpoint(client: TestClient) -> None:
    body = client.get("/v1/homes/home_001/rooms").json()
    rooms = {room["room_id"]: room["device_ids"] for room in body["rooms"]}
    assert rooms == {"living_room": ["dev_1"], "bedroom": ["dev_2"]}


def test_devices_endpoint(client: TestClient) -> None:
    body = client.get("/v1/homes/home_001/devices").json()
    assert {d["device_id"] for d in body["devices"]} == {"dev_1", "dev_2"}


def test_single_device_endpoint(client: TestClient) -> None:
    body = client.get("/v1/homes/home_001/devices/dev_2").json()
    assert body["device_id"] == "dev_2"
    assert body["capabilities"]["light.power"]["value"] is True


def test_missing_device_returns_structured_404(client: TestClient) -> None:
    response = client.get("/v1/homes/home_001/devices/nope")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "DEVICE_NOT_FOUND"


def test_capability_endpoint_reports_known_value(client: TestClient) -> None:
    body = client.get(
        "/v1/homes/home_001/devices/dev_1/capabilities/environment.temperature"
    ).json()
    assert body["value"] == 24.5
    assert body["unit"] == "C"
    assert body["observed"] is True


def test_unobserved_capability_is_unknown_and_unusable(client: TestClient) -> None:
    # Not a 404 and not a falsy default: the caller must be able to distinguish
    # "never observed" from "observed as false".
    body = client.get("/v1/homes/home_001/devices/dev_1/capabilities/occupancy.motion").json()
    assert body["status"] == "UNKNOWN"
    assert body["value"] is None
    assert body["observed"] is False
    assert body["usable_for_decisions"] is False


def test_stale_capability_is_reported_stale_and_unusable(client: TestClient) -> None:
    body = client.get("/v1/homes/home_001/devices/dev_1/capabilities/safety.gas_alarm").json()
    assert body["status"] == "STALE"
    assert body["value"] is False  # the value is still visible …
    assert body["usable_for_decisions"] is False  # … but must not drive a decision


def test_stale_listing_endpoint(client: TestClient) -> None:
    body = client.get("/v1/homes/home_001/stale").json()
    stale = {(item["device_id"], item["capability"]) for item in body["stale"]}
    assert ("dev_1", "safety.gas_alarm") in stale


def test_unknown_home_returns_empty_twin_not_an_error(client: TestClient) -> None:
    body = client.get("/v1/homes/some_other_home/twin").json()
    assert body["devices"] == {}
    assert body["rooms"] == {}


def test_homes_are_isolated_across_endpoints(client: TestClient) -> None:
    # A device in home_001 must not be reachable through another home's path.
    assert client.get("/v1/homes/other_home/devices/dev_1").status_code == 404


def test_health_and_metrics(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").status_code == 200
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "syltra_twin_events_consumed_total" in metrics.text


def test_readiness_is_503_before_the_consumer_is_running() -> None:
    service = DigitalTwinService(session_factory=None, publisher=_NullPublisher())  # type: ignore[arg-type]
    response = TestClient(create_app(service)).get("/health/ready")
    assert response.status_code == 503


def test_api_docs_are_disabled(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
