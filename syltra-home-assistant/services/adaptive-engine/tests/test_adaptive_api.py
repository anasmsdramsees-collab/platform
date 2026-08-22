"""Adaptive Engine API tests (spec §21 subset, §19)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from syltra_adaptive_engine.api import create_app
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_testing import comfort_history

HOME = "home_001"


class _NullPublisher:
    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


@pytest.fixture
def service() -> AdaptiveEngineService:
    engine = AdaptiveEngineService(_NullPublisher())  # type: ignore[arg-type]
    for event in comfort_history(days=21):
        engine.observe(event)
    engine.train_home(HOME)
    engine.mark_ready(True)
    return engine


@pytest.fixture
def client(service: AdaptiveEngineService) -> TestClient:
    return TestClient(create_app(service))


def test_models_endpoint_reports_versions_and_metadata(client: TestClient) -> None:
    body = client.get(f"/v1/homes/{HOME}/models").json()
    assert body["learning_mode"] == "OBSERVE"
    assert body["history_events"] > 0
    assert body["models"]
    entry = body["models"][0]
    assert entry["feature_schema_version"] == "1.0"
    assert entry["evaluation_metrics"]
    assert entry["training_window"]["distinct_days"] > 0
    # Registered but not serving.
    assert entry["status"] == "TRAINED"
    assert entry["promoted_at"] is None


def test_model_card_endpoint_exposes_the_safety_language(client: TestClient) -> None:
    body = client.get(f"/v1/homes/{HOME}/models/temperature_preference/card").json()
    card = body["card"]
    assert "never an actuator command" in card["intended_use"]
    assert "life-safety" in card["out_of_scope_use"]


def test_unknown_model_card_is_a_structured_404(client: TestClient) -> None:
    response = client.get(f"/v1/homes/{HOME}/models/nope/card")
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "MODEL_NOT_FOUND"


def test_learning_mode_can_advance_one_step(client: TestClient) -> None:
    response = client.post(f"/v1/homes/{HOME}/learning-mode", json={"mode": "SHADOW"})
    assert response.status_code == 200
    assert response.json()["learning_mode"] == "SHADOW"


@pytest.mark.safety
def test_the_api_refuses_a_lifecycle_skip(client: TestClient) -> None:
    # Safety invariant 14 surfaced at the API: no caller can widen authority
    # by skipping stages, and the refusal explains itself.
    response = client.post(
        f"/v1/homes/{HOME}/learning-mode", json={"mode": "AUTHORIZED_AUTOMATION"}
    )
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "TRANSITION_NOT_PERMITTED"


def test_unknown_learning_mode_is_rejected(client: TestClient) -> None:
    response = client.post(f"/v1/homes/{HOME}/learning-mode", json={"mode": "TURBO"})
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "UNKNOWN_LEARNING_MODE"


@pytest.mark.safety
def test_promotion_below_the_gate_is_refused_by_the_api(
    client: TestClient, service: AdaptiveEngineService
) -> None:
    # Register a deliberately poor version and try to promote it.
    versions = service.registry.versions(HOME, "temperature_preference")
    assert versions
    service.registry.register(
        home_id=HOME,
        name="temperature_preference",
        version="9.9.9",
        model_type=versions[0].model_type,
        feature_schema_version="1.0",
        training_code_revision="test",
        training_window=versions[0].training_window,
        evaluation_metrics={"mae": 99.0},
        card=versions[0].card,
    )
    response = client.post(
        f"/v1/homes/{HOME}/models/temperature_preference/promote", json={"version": "9.9.9"}
    )
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "PROMOTION_REFUSED"


def test_promote_then_rollback_round_trip(
    client: TestClient, service: AdaptiveEngineService
) -> None:
    versions = service.registry.versions(HOME, "temperature_preference")
    first = versions[0].version
    promoted = client.post(
        f"/v1/homes/{HOME}/models/temperature_preference/promote", json={"version": first}
    )
    assert promoted.status_code == 200
    assert promoted.json()["status"] == "ACTIVE"

    # No predecessor to fall back to yet.
    rolled = client.post(f"/v1/homes/{HOME}/models/temperature_preference/rollback")
    assert rolled.status_code == 409
    assert rolled.json()["detail"]["error"] == "ROLLBACK_UNAVAILABLE"


def test_suspend_endpoint_withdraws_an_active_model(
    client: TestClient, service: AdaptiveEngineService
) -> None:
    version = service.registry.versions(HOME, "temperature_preference")[0].version
    client.post(
        f"/v1/homes/{HOME}/models/temperature_preference/promote", json={"version": version}
    )
    response = client.post(
        f"/v1/homes/{HOME}/models/temperature_preference/suspend",
        json={"reason": "sensor degradation"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUSPENDED"


def test_shadow_endpoint_labels_its_contents(client: TestClient) -> None:
    body = client.get(f"/v1/homes/{HOME}/recommendations/shadow").json()
    assert body["shadow"] is True
    assert "recommendations" in body


def test_train_endpoint_explains_refusals(client: TestClient) -> None:
    body = client.post("/v1/homes/quiet_home/train").json()
    for result in body["results"].values():
        assert result["trained"] is False
        assert "cannot train" in result["explanation"]


def test_audit_endpoint_lists_lifecycle_events(
    client: TestClient, service: AdaptiveEngineService
) -> None:
    version = service.registry.versions(HOME, "temperature_preference")[0].version
    client.post(
        f"/v1/homes/{HOME}/models/temperature_preference/promote", json={"version": version}
    )
    body = client.get(f"/v1/homes/{HOME}/audit").json()
    actions = [event["action"] for event in body["events"]]
    assert "MODEL_REGISTERED" in actions
    assert "MODEL_ACTIVATED" in actions
    for event in body["events"]:
        assert event["actor"] and event["reason"]


def test_homes_are_isolated_in_the_api(client: TestClient) -> None:
    body = client.get("/v1/homes/other_home/models").json()
    assert body["models"] == []
    assert body["learning_mode"] == "OBSERVE"


def test_health_and_metrics(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").status_code == 200
    assert "syltra_adaptive_events_consumed_total" in client.get("/metrics").text


def test_api_docs_are_disabled(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
