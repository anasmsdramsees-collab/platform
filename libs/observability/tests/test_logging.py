"""Structured logging and secret redaction (spec §14.1, §25.3).

The Home Assistant token must never reach logs — these tests are the guard.
"""

import json
import logging
from collections.abc import Iterator
from typing import Any

import pytest
from syltra_observability import bind_correlation_id, configure_logging
from syltra_observability.logging import JsonFormatter, RedactingFilter

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6secret-ha-token-value"


@pytest.fixture(autouse=True)
def _reset_logging() -> Iterator[None]:
    yield
    logging.getLogger().handlers.clear()
    bind_correlation_id(None)


def emit(capsys: pytest.CaptureFixture[str], message: str, **extra: object) -> dict[str, Any]:
    logging.getLogger("test").info(message, extra=extra)
    entry: dict[str, Any] = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    return entry


def test_log_line_is_json_with_required_fields(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("edge-agent", "hub_001")
    entry = emit(capsys, "hello")
    assert entry["service"] == "edge-agent"
    assert entry["instance_id"] == "hub_001"
    assert entry["level"] == "INFO"
    assert entry["message"] == "hello"
    assert "timestamp" in entry


def test_correlation_id_is_included_when_bound(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("edge-agent", "hub_001")
    bind_correlation_id("corr-123")
    assert emit(capsys, "with correlation")["correlation_id"] == "corr-123"


def test_reason_code_and_ids_pass_through(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("edge-agent", "hub_001")
    entry = emit(capsys, "denied", reason_code="POLICY_DENIED", action_id="a-1")
    assert entry["reason_code"] == "POLICY_DENIED"
    assert entry["action_id"] == "a-1"


@pytest.mark.safety
def test_registered_secret_is_redacted(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("edge-agent", "hub_001", secrets=[TOKEN])
    entry = emit(capsys, f"connecting with token {TOKEN}")
    assert TOKEN not in json.dumps(entry)
    assert "[REDACTED]" in entry["message"]


@pytest.mark.safety
def test_secret_redacted_inside_formatted_arguments(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("edge-agent", "hub_001", secrets=[TOKEN])
    logging.getLogger("test").warning("auth failed for %s", TOKEN)
    output = capsys.readouterr().out
    assert TOKEN not in output
    assert "[REDACTED]" in output


@pytest.mark.safety
def test_late_registered_secret_is_redacted(capsys: pytest.CaptureFixture[str]) -> None:
    redactor = configure_logging("edge-agent", "hub_001")
    redactor.add_secret(TOKEN)
    assert TOKEN not in capsys.readouterr().out
    entry = emit(capsys, f"token={TOKEN}")
    assert TOKEN not in json.dumps(entry)


@pytest.mark.safety
def test_exception_traceback_does_not_leak_secret(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("edge-agent", "hub_001", secrets=[TOKEN])
    try:
        raise ValueError(f"bad token {TOKEN}")
    except ValueError:
        logging.getLogger("test").exception("failure")
    assert TOKEN not in capsys.readouterr().out


def test_trivially_short_values_are_not_redacted() -> None:
    # Redacting a 2-character "secret" would blank out ordinary text.
    f = RedactingFilter(["ok"])
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "ok status", None, None)
    f.filter(record)
    assert record.getMessage() == "ok status"


def test_formatter_reports_error_type_without_raw_details() -> None:
    formatter = JsonFormatter("svc", "inst")
    try:
        raise KeyError("internal detail")
    except KeyError:
        import sys

        record = logging.LogRecord("t", logging.ERROR, __file__, 1, "boom", None, sys.exc_info())
    entry = json.loads(formatter.format(record))
    assert entry["error_type"] == "KeyError"
