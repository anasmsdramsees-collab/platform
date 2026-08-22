"""Health and metrics endpoint tests (spec §29)."""

from fastapi.testclient import TestClient
from syltra_edge_agent.health import create_health_app


def test_liveness_is_independent_of_readiness() -> None:
    # A live-but-not-ready service must stay alive: an orchestrator should
    # stop routing traffic to it, not restart it in a loop.
    client = TestClient(create_health_app(lambda: False))
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_reflects_dependencies() -> None:
    ready = TestClient(create_health_app(lambda: True)).get("/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}

    not_ready = TestClient(create_health_app(lambda: False)).get("/health/ready")
    assert not_ready.status_code == 503
    assert not_ready.json() == {"status": "not_ready"}


def test_metrics_endpoint_exposes_prometheus_format() -> None:
    client = TestClient(create_health_app(lambda: True))
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    for metric in (
        "syltra_edge_events_received_total",
        "syltra_edge_events_published_total",
        "syltra_edge_events_invalid_total",
        "syltra_edge_events_duplicate_total",
        "syltra_edge_reconnects_total",
        "syltra_edge_connected",
    ):
        assert metric in body


def test_interactive_api_docs_are_disabled() -> None:
    # The Edge Agent is an internal service; it exposes no browsable API surface.
    client = TestClient(create_health_app(lambda: True))
    assert client.get("/docs").status_code == 404
