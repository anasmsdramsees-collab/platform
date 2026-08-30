"""The turn loop, its gate, its ceiling and its audit trail."""

from typing import Any

from audit.log import InMemoryAuditLog
from integrations.syltra.mock import FailingSyltraClient, MockSyltraClient
from policies.risk import RiskLevel
from providers.llm.base import LLMProvider, LLMReply, ToolCall
from providers.llm.mock import MockLLM
from sella_core.orchestrator import Orchestrator
from tools.home import build_registry
from tools.registry import Tool, ToolRegistry


def _agent(client: Any, **kwargs: Any) -> tuple[Orchestrator, InMemoryAuditLog]:
    audit = InMemoryAuditLog()
    return (
        Orchestrator(MockLLM(), build_registry(client), audit=audit, **kwargs),
        audit,
    )


async def test_a_plain_request_turns_into_one_tool_call_and_one_sentence() -> None:
    client = MockSyltraClient()
    agent, audit = _agent(client)

    turn = await agent.handle("شغّل نور المجلس", session_id="s1")

    assert turn.tool_calls == ["control_light"]
    assert turn.reply == "تم."
    assert client.calls == [("set", ("light_majlis", "light.power", True))]
    assert len(audit.for_session("s1")) == 1
    assert audit.for_session("s1")[0].succeeded


async def test_an_unconfirmed_command_is_reported_as_unconfirmed() -> None:
    agent, _audit = _agent(FailingSyltraClient())
    turn = await agent.handle("شغّل نور المجلس")
    assert "ما أكّد" in turn.reply


async def test_the_door_is_refused_and_the_refusal_is_recorded() -> None:
    agent, audit = _agent(MockSyltraClient())

    turn = await agent.handle("افتح قفل الباب", session_id="s2")

    assert turn.refused == ["unlock_door"]
    assert turn.tool_calls == []
    entry = audit.for_session("s2")[0]
    assert entry.error_code == "RISK_NOT_ALLOWED"
    assert entry.risk_level == "HIGH"


async def test_a_tool_that_hangs_does_not_hang_the_house() -> None:
    async def never_returns(_: dict[str, Any]) -> dict[str, Any]:
        import asyncio

        await asyncio.sleep(5)
        return {}

    registry = ToolRegistry()
    registry.register(
        Tool(
            name="get_home_state",
            description="",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            risk=RiskLevel.LOW,
            run=never_returns,
            timeout_seconds=0.01,
        )
    )
    audit = InMemoryAuditLog()
    agent = Orchestrator(MockLLM(), registry, audit=audit)

    turn = await agent.handle("كيف حال البيت", session_id="s3")

    assert turn.refused == ["get_home_state"]
    assert audit.for_session("s3")[0].error_code == "TIMEOUT"


async def test_a_model_that_will_not_stop_calling_tools_is_stopped() -> None:
    class Relentless(LLMProvider):
        async def reply(
            self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
        ) -> LLMReply:
            return LLMReply(tool_calls=(ToolCall(id="x", name="get_home_state", arguments={}),))

    agent = Orchestrator(Relentless(), build_registry(MockSyltraClient()), max_tool_calls=3)

    turn = await agent.handle("...")

    assert turn.hit_ceiling
    assert len(turn.tool_calls) == 3
    assert turn.reply


async def test_a_crashing_tool_leaves_a_row_and_a_sentence() -> None:
    async def explode(_: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("device driver fell over")

    registry = ToolRegistry()
    registry.register(
        Tool(
            name="get_home_state",
            description="",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            risk=RiskLevel.LOW,
            run=explode,
        )
    )
    audit = InMemoryAuditLog()
    agent = Orchestrator(MockLLM(), registry, audit=audit)

    turn = await agent.handle("كيف حال البيت", session_id="s4")

    assert audit.for_session("s4")[0].error_code == "TOOL_CRASHED"
    assert turn.reply
