"""Claude, through the Messages API with tool use.

Imported lazily so the project runs, and its tests pass, on a machine with no
Anthropic SDK and no key.
"""

from typing import Any

from providers.llm.base import LLMProvider, LLMReply, ToolCall
from sella_core.errors import ProviderError


class AnthropicLLM(LLMProvider):
    def __init__(self, api_key: str, model: str, max_tokens: int = 1024) -> None:
        if not api_key:
            raise ProviderError(
                code="NO_API_KEY",
                detail="ANTHROPIC_API_KEY is empty",
                spoken="النموذج غير مهيّأ.",
            )
        self._key = api_key
        self._model = model
        self._max_tokens = max_tokens

    async def reply(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMReply:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise ProviderError(
                code="SDK_MISSING",
                detail="anthropic package is not installed",
                spoken="النموذج غير متاح.",
            ) from exc

        client = AsyncAnthropic(api_key=self._key)
        response = await client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            tools=tools,
            messages=_to_anthropic(messages),
        )
        text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
        calls = tuple(
            ToolCall(id=b.id, name=b.name, arguments=dict(b.input))
            for b in response.content
            if getattr(b, "type", "") == "tool_use"
        )
        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", 0),
            "output_tokens": getattr(response.usage, "output_tokens", 0),
        }
        return LLMReply(text=text, tool_calls=calls, usage=usage)


def _to_anthropic(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """SELLA's transcript, in the shape the Messages API expects."""
    out: list[dict[str, Any]] = []
    for message in messages:
        role = message["role"]
        if role == "tool":
            out.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message["tool_call_id"],
                            "content": str(message["content"]),
                        }
                    ],
                }
            )
        elif role == "assistant_tools":
            out.append(
                {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments}
                        for c in message["tool_calls"]
                    ],
                }
            )
        else:
            out.append({"role": role, "content": message["content"]})
    return out
