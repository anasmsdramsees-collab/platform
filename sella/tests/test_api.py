from fastapi.testclient import TestClient

from apps.api.main import create_app
from sella_core.config import Settings


def _client() -> TestClient:
    return TestClient(create_app(Settings(mock_providers=True)))


def test_health_and_readiness_answer_separately() -> None:
    client = _client()
    assert client.get("/healthz").json() == {"status": "ok"}
    ready = client.get("/readyz").json()
    assert ready["ready"] is True
    assert ready["devices"] > 0


def test_a_chat_turn_switches_on_a_light() -> None:
    body = _client().post("/v1/chat", json={"text": "شغّل نور المجلس"}).json()
    assert body["tool_calls"] == ["control_light"]
    assert body["refused"] == []


def test_a_chat_turn_refuses_the_door() -> None:
    body = _client().post("/v1/chat", json={"text": "افتح قفل الباب"}).json()
    assert body["refused"] == ["unlock_door"]
    assert body["tool_calls"] == []


def test_an_empty_message_is_rejected_by_the_schema() -> None:
    assert _client().post("/v1/chat", json={"text": ""}).status_code == 422
