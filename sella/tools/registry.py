"""The tool catalogue.

Every tool declares its name, its schema, its risk level and its timeout, and
nothing reaches the model that is not registered here. The model never sends an
entity id: it sends a room and a device name, and the registry resolves them
against what the platform says exists.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from policies.risk import RiskLevel
from sella_core.errors import ToolError

ToolFn = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    risk: RiskLevel
    run: ToolFn
    timeout_seconds: float = 10.0
    idempotent: bool = True

    def as_claude_tool(self) -> dict[str, Any]:
        """The shape Anthropic's Tool Use expects."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ToolRegistry:
    _tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> Tool:
        if tool.name in self._tools:
            msg = f"tool {tool.name} is already registered"
            raise ValueError(msg)
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool:
        tool = self._tools.get(name)
        if tool is None:
            # Refused rather than ignored. A model asking for a tool that does
            # not exist is a model that has been talked into something, and the
            # attempt belongs in the audit trail.
            raise ToolError(
                code="UNKNOWN_TOOL",
                detail=f"no tool named {name}",
                spoken="ما عندي أداة بهذا الاسم.",
            )
        return tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def exposed_to_model(self, *, high_risk_enabled: bool) -> list[dict[str, Any]]:
        """What the model is allowed to see.

        A forbidden tool is never shown. A high risk tool is shown only when the
        approval path is switched on, because a model that can see `unlock_door`
        will eventually try it, and a refusal at the last moment is a worse
        experience than an absence.
        """
        out = []
        for name in self.names():
            tool = self._tools[name]
            if tool.risk is RiskLevel.FORBIDDEN:
                continue
            if tool.risk is RiskLevel.HIGH and not high_risk_enabled:
                continue
            out.append(tool.as_claude_tool())
        return out
