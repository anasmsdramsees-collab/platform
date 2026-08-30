"""Every tool call, recorded before it runs and completed after.

Written first, not last. A tool that crashes the process must still leave a row
saying it was attempted; a log written only on success is a log that hides
exactly the events somebody will need.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

REDACTED = "[redacted]"
SECRET_KEYS = frozenset({"token", "password", "otp", "api_key", "secret", "pin", "card"})


def scrub(payload: Any) -> Any:
    """Take the secrets out before anything is stored.

    §10.2 forbids storing passwords, one time codes and keys. Applied here as
    well as at the memory layer, because the audit trail is the other place a
    secret would end up sitting for years.
    """
    if isinstance(payload, dict):
        return {
            k: (REDACTED if any(s in str(k).lower() for s in SECRET_KEYS) else scrub(v))
            for k, v in payload.items()
        }
    if isinstance(payload, list):
        return [scrub(v) for v in payload]
    return payload


@dataclass
class ToolExecution:
    execution_id: UUID
    session_id: str
    tool_name: str
    risk_level: str
    arguments: dict[str, Any]
    started_at: datetime
    finished_at: datetime | None = None
    result: dict[str, Any] | None = None
    error_code: str | None = None
    approval_id: str | None = None
    idempotency_key: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error_code is None and self.finished_at is not None


class AuditLog(Protocol):
    def start(
        self, session_id: str, tool_name: str, risk: str, arguments: dict[str, Any]
    ) -> ToolExecution: ...
    def finish(self, execution: ToolExecution, result: dict[str, Any]) -> None: ...
    def fail(self, execution: ToolExecution, code: str, detail: str) -> None: ...


@dataclass
class InMemoryAuditLog:
    entries: list[ToolExecution] = field(default_factory=list)

    def start(
        self, session_id: str, tool_name: str, risk: str, arguments: dict[str, Any]
    ) -> ToolExecution:
        execution = ToolExecution(
            execution_id=uuid4(),
            session_id=session_id,
            tool_name=tool_name,
            risk_level=risk,
            arguments=scrub(arguments),
            started_at=datetime.now(tz=UTC),
        )
        self.entries.append(execution)
        return execution

    def finish(self, execution: ToolExecution, result: dict[str, Any]) -> None:
        execution.finished_at = datetime.now(tz=UTC)
        execution.result = scrub(result)

    def fail(self, execution: ToolExecution, code: str, detail: str) -> None:
        execution.finished_at = datetime.now(tz=UTC)
        execution.error_code = code
        execution.result = {"detail": detail[:500]}

    def for_session(self, session_id: str) -> list[ToolExecution]:
        return [e for e in self.entries if e.session_id == session_id]
