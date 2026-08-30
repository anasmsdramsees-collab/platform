"""The text endpoint of phase one.

No voice yet, no websocket, no memory. One POST, one reply, so the tool loop,
the permission gate and the audit trail can be exercised end to end before
anything speaks.
"""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from audit.log import InMemoryAuditLog
from integrations.syltra.client import HttpSyltraClient
from integrations.syltra.mock import MockSyltraClient
from observability.logging import configure_logging
from providers.llm.anthropic import AnthropicLLM
from providers.llm.base import LLMProvider
from providers.llm.mock import MockLLM
from sella_core.config import Settings, get_settings
from sella_core.orchestrator import Orchestrator
from tools.home import build_registry


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[str]
    refused: list[str]
    hit_ceiling: bool


def build_llm(settings: Settings) -> LLMProvider:
    """A missing key means a mock, not a crash.

    §1 asks for this explicitly: development continues without credentials, and
    nobody is tempted to paste a key into a file to get the tests running.
    """
    if settings.mock_providers or settings.llm_provider == "mock" or not settings.anthropic_api_key:
        return MockLLM()
    return AnthropicLLM(settings.anthropic_api_key, settings.anthropic_model)


def create_app(
    settings: Settings | None = None, orchestrator: Orchestrator | None = None
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.secrets)

    client: Any
    if settings.mock_providers or not settings.syltra_token:
        client = MockSyltraClient()
    else:
        client = HttpSyltraClient(
            base_url=settings.syltra_base_url,
            token=settings.syltra_token,
            home_id=settings.syltra_home_id,
        )

    audit = InMemoryAuditLog()
    agent = orchestrator or Orchestrator(
        build_llm(settings),
        build_registry(client),
        audit=audit,
        high_risk_enabled=settings.enable_high_risk_tools,
        max_tool_calls=settings.max_tool_calls_per_turn,
        tool_timeout_seconds=settings.tool_timeout_seconds,
    )

    app = FastAPI(title="SELLA", version="0.1.0")
    app.state.settings = settings
    app.state.audit = audit
    app.state.orchestrator = agent

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> dict[str, Any]:
        """Ready means the house answered, not that the process started."""
        try:
            devices = await client.devices()
        except Exception as error:  # noqa: BLE001 - readiness reports, it does not raise
            return {"ready": False, "reason": type(error).__name__}
        return {"ready": True, "devices": len(devices), "mock": settings.mock_providers}

    @app.post("/v1/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        turn = await agent.handle(request.text, session_id=request.session_id)
        return ChatResponse(
            reply=turn.reply,
            tool_calls=turn.tool_calls,
            refused=turn.refused,
            hit_ceiling=turn.hit_ceiling,
        )

    return app


app = create_app()
