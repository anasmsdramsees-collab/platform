import io
import json
import logging

from audit.log import REDACTED, InMemoryAuditLog, scrub
from observability.logging import configure_logging


def test_a_password_never_reaches_the_audit_trail() -> None:
    cleaned = scrub({"pin": "1234", "room": "المجلس", "nested": {"api_key": "sk-live"}})
    assert cleaned["pin"] == REDACTED
    assert cleaned["nested"]["api_key"] == REDACTED
    assert cleaned["room"] == "المجلس"


def test_the_row_exists_before_the_tool_finishes() -> None:
    audit = InMemoryAuditLog()
    execution = audit.start("s", "control_light", "LOW", {"on": True})
    assert audit.entries == [execution]
    assert execution.finished_at is None
    assert not execution.succeeded


def test_a_token_is_not_printed_in_a_log_line() -> None:
    configure_logging("INFO", ["sk-live-secret"])
    handler = logging.getLogger().handlers[0]
    captured = io.StringIO()
    handler.setStream(captured)  # type: ignore[attr-defined]

    logging.getLogger("sella.test").info(
        "calling with token sk-live-secret", extra={"tool_name": "control_light"}
    )

    line = json.loads(captured.getvalue().splitlines()[0])
    assert "sk-live-secret" not in captured.getvalue()
    assert line["tool_name"] == "control_light"
    assert REDACTED in line["message"]
