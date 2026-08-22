"""Context Engine API tests (spec §21: contexts/current)."""

from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from syltra_context_engine.api import create_app
from syltra_context_engine.service import ContextService
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading


class _NullPublisher:
    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


@pytest.fixture
def client() -> TestClient:
    service = ContextService(publisher=_NullPublisher())  # type: ignore[arg-type]
    now = datetime.now(tz=UTC)
    state = home(
        device("m1", "kitchen", motion=reading("occupancy.motion", True, now)),
        device("t1", "entrance", presence=reading("occupancy.presence", True, now)),
        device("leak", "kitchen", leak=reading("safety.water_leak", True, now)),
        home_id="home_001",
    )
    service.twin._homes["home_001"] = state
    service.engine.evaluate("home_001", state, now)
    service.mark_ready(True)
    return TestClient(create_app(service))


def test_current_contexts_include_evidence_and_expiry(client: TestClient) -> None:
    body = client.get("/v1/homes/home_001/contexts/current").json()
    assert body["home_id"] == "home_001"
    assert body["contexts"]
    for context in body["contexts"]:
        assert context["evidence"], f"{context['context_type']} exposed without evidence"
        assert context["expires_at"] > context["started_at"]
        assert context["seconds_until_expiry"] > 0
        assert context["producer"].startswith("rule:")
        assert 0.0 <= context["confidence"] <= 1.0


def test_evidence_entries_carry_provenance(client: TestClient) -> None:
    body = client.get("/v1/homes/home_001/contexts/current").json()
    occupied = next(c for c in body["contexts"] if c["context_type"] == "HOME_OCCUPIED")
    item = occupied["evidence"][0]
    assert item["capability"]
    assert item["status"] == "KNOWN"
    assert item["observed_at"]


def test_overlapping_contexts_are_all_reported(client: TestClient) -> None:
    body = client.get("/v1/homes/home_001/contexts/current").json()
    found = {(c["context_type"], c["scope"]) for c in body["contexts"]}
    assert ("HOME_OCCUPIED", "home") in found
    assert ("ROOM_OCCUPIED", "room:kitchen") in found


@pytest.mark.safety
def test_advisory_contexts_are_flagged_in_the_api(client: TestClient) -> None:
    # A consumer must be able to tell an advisory watch signal from a fact
    # without knowing the rule internals.
    body = client.get("/v1/homes/home_001/contexts/current").json()
    leak = next(c for c in body["contexts"] if c["context_type"] == "POSSIBLE_WATER_LEAK")
    assert leak["advisory_only"] is True
    occupied = next(c for c in body["contexts"] if c["context_type"] == "HOME_OCCUPIED")
    assert occupied["advisory_only"] is False


def test_unknown_home_returns_an_empty_list_not_an_error(client: TestClient) -> None:
    body = client.get("/v1/homes/nobody/contexts/current").json()
    assert body["contexts"] == []


def test_health_and_metrics(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").status_code == 200
    metrics = client.get("/metrics")
    assert "syltra_context_events_consumed_total" in metrics.text


def test_readiness_is_503_before_the_consumer_runs() -> None:
    service = ContextService(publisher=_NullPublisher())  # type: ignore[arg-type]
    assert TestClient(create_app(service)).get("/health/ready").status_code == 503


def test_api_docs_are_disabled(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
