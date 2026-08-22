"""Structured JSON logging (spec §29) with mandatory secret redaction.

Every log line carries: timestamp, service, instance, level, correlation ID,
and optional reason code / event or action id. Secrets registered at
configuration time are replaced with ``[REDACTED]`` anywhere they appear in a
message or its formatted arguments — the Home Assistant token must never reach
logs (spec §14.1).
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

_correlation_id: ContextVar[str | None] = ContextVar("syltra_correlation_id", default=None)

_REDACTED = "[REDACTED]"


def bind_correlation_id(correlation_id: str | None) -> None:
    """Bind the correlation id for the current async context."""
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


class RedactingFilter(logging.Filter):
    """Removes registered secret values from every record."""

    def __init__(self, secrets: list[str]) -> None:
        super().__init__()
        # Longest first so partial overlaps redact fully; ignore trivial values.
        self._secrets = sorted({s for s in secrets if s and len(s) >= 6}, key=len, reverse=True)

    def add_secret(self, secret: str) -> None:
        if secret and len(secret) >= 6:
            self._secrets = sorted({*self._secrets, secret}, key=len, reverse=True)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for secret in self._secrets:
            if secret in message:
                message = message.replace(secret, _REDACTED)
        record.msg = message
        record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str, instance_id: str) -> None:
        super().__init__()
        self._service = service
        self._instance_id = instance_id

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "service": self._service,
            "instance_id": self._instance_id,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if corr := _correlation_id.get():
            entry["correlation_id"] = corr
        for extra_key in ("reason_code", "event_id", "action_id", "entity_id", "subject"):
            value = record.__dict__.get(extra_key)
            if value is not None:
                entry[extra_key] = value
        if record.exc_info and record.exc_info[0] is not None:
            entry["error_type"] = record.exc_info[0].__name__
        return json.dumps(entry, ensure_ascii=False, default=str)


def configure_logging(
    service: str,
    instance_id: str,
    level: str = "INFO",
    secrets: list[str] | None = None,
) -> RedactingFilter:
    """Configure root logging for a SYLTRA service; returns the redaction
    filter so late-discovered secrets can be registered."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service=service, instance_id=instance_id))
    redactor = RedactingFilter(secrets or [])
    handler.addFilter(redactor)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
    return redactor
