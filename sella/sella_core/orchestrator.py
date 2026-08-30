"""The turn loop: a message in, tools in the middle, one spoken sentence out.

Three things happen here that do not happen in the model:

1. **The risk gate.** `may_execute` decides, not the prompt. A model can be
   talked out of an instruction; it cannot be talked out of a function that
   returns False.
2. **The audit row.** Written before the tool runs, so an attempt that crashes
   still leaves a trace.
3. **The ceiling.** `max_tool_calls_per_turn` ends a loop that is going nowhere,
   because a runaway loop against a real house is a house being switched on and
   off all night.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from audit.log import AuditLog, InMemoryAuditLog
from policies.risk import RiskLevel, may_execute
from providers.llm.base import LLMProvider, ToolCall
from sella_core.errors import PermissionRefused, SellaError
from sella_core.prompt import SYSTEM_PROMPT
from tools.registry import ToolRegistry

log = logging.getLogger("sella.orchestrator")


@dataclass
class Turn:
    """What one exchange produced, including what it refused to do."""

    reply: str
    tool_calls: list[str] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)
    hit_ceiling: bool = False


@dataclass
class Session:
    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    confirmed_actions: set[str] = field(default_factory=set)


class Orchestrator:
    def __init__(
        self,
        llm: LLMProvider,
        registry: ToolRegistry,
        *,
        audit: AuditLog | None = None,
        high_risk_enabled: bool = False,
        max_tool_calls: int = 8,
        tool_timeout_seconds: float = 10.0,
    ) -> None:
        self._llm = llm
        self._registry = registry
        self._audit = audit or InMemoryAuditLog()
        self._high_risk = high_risk_enabled
        self._max_calls = max_tool_calls
        self._timeout = tool_timeout_seconds
        self._sessions: dict[str, Session] = {}

    def session(self, session_id: str | None = None) -> Session:
        key = session_id or str(uuid4())
        if key not in self._sessions:
            self._sessions[key] = Session(session_id=key)
        return self._sessions[key]

    async def handle(self, text: str, *, session_id: str | None = None) -> Turn:
        session = self.session(session_id)
        session.messages.append({"role": "user", "content": text})
        tools = self._registry.exposed_to_model(high_risk_enabled=self._high_risk)

        turn = Turn(reply="")
        for _ in range(self._max_calls):
            reply = await self._llm.reply(SYSTEM_PROMPT, session.messages, tools)
            if not reply.wants_tools:
                turn.reply = reply.text
                session.messages.append({"role": "assistant", "content": reply.text})
                return turn

            session.messages.append(
                {"role": "assistant_tools", "content": "", "tool_calls": list(reply.tool_calls)}
            )
            for call in reply.tool_calls:
                outcome = await self._run(session, call, turn)
                session.messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": outcome}
                )

        # The loop ran out of room. Say so rather than returning an empty reply
        # that the caller will render as silence.
        turn.hit_ceiling = True
        turn.reply = turn.reply or "طلبك احتاج خطوات كثيرة. وضّح لي المطلوب بجملة واحدة."
        return turn

    async def _run(self, session: Session, call: ToolCall, turn: Turn) -> dict[str, Any]:
        try:
            tool = self._registry.get(call.name)
        except SellaError as error:
            turn.refused.append(call.name)
            log.warning("unknown tool requested", extra={"tool_name": call.name})
            return {"error": error.code, "spoken": error.spoken}

        allowed = may_execute(
            tool.risk,
            confirmed=call.name in session.confirmed_actions,
            approved=False,
            high_risk_enabled=self._high_risk,
        )
        if not allowed:
            refusal = PermissionRefused(
                code="RISK_NOT_ALLOWED",
                detail=f"{call.name} at {tool.risk}",
                spoken=_refusal_sentence(tool.risk),
            )
            turn.refused.append(call.name)
            execution = self._audit.start(
                session.session_id, call.name, str(tool.risk), call.arguments
            )
            self._audit.fail(execution, refusal.code, refusal.detail)
            log.warning(
                "tool refused",
                extra={
                    "session_id": session.session_id,
                    "tool_name": call.name,
                    "risk_level": str(tool.risk),
                },
            )
            return {"error": refusal.code, "spoken": refusal.spoken}

        execution = self._audit.start(session.session_id, call.name, str(tool.risk), call.arguments)
        try:
            result = await asyncio.wait_for(
                tool.run(call.arguments), timeout=tool.timeout_seconds or self._timeout
            )
        except TimeoutError:
            self._audit.fail(execution, "TIMEOUT", f"{call.name} exceeded {tool.timeout_seconds}s")
            turn.refused.append(call.name)
            return {"error": "TIMEOUT", "spoken": "الجهاز ما ردّ في الوقت. جرّب مرة ثانية."}
        except SellaError as error:
            self._audit.fail(execution, error.code, error.detail)
            turn.refused.append(call.name)
            return {"error": error.code, "spoken": error.spoken}
        except Exception as error:
            self._audit.fail(execution, "TOOL_CRASHED", repr(error))
            turn.refused.append(call.name)
            log.exception("tool crashed", extra={"tool_name": call.name})
            return {"error": "TOOL_CRASHED", "spoken": "صار خطأ عندي. ما نفّذت شيئاً."}

        self._audit.finish(execution, result)
        turn.tool_calls.append(call.name)
        return result


def _refusal_sentence(level: RiskLevel) -> str:
    if level is RiskLevel.FORBIDDEN:
        return "هذا خارج صلاحيتي. لازم تعمله بنفسك."
    return "هذا يحتاج تأكيد من التطبيق، وما عندي هذي الصلاحية الآن."
