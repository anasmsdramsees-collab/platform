"""Pure helpers with no Home Assistant imports (spec §27).

Config-flow validation and diagnostic redaction are ordinary logic, and keeping
them free of Home Assistant imports makes them directly testable in this
repository — which does not depend on Home Assistant, and must not (ADR-001:
Home Assistant is embedded and replaceable, not a library this platform builds
on).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

REDACTED = "**REDACTED**"

REDACTED_KEYS: frozenset[str] = frozenset(
    {"token", "access_token", "password", "api_key", "authorization", "secret"}
)


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")


def validate_url(url: str) -> str | None:
    """Return an error key, or None when the URL is usable."""
    parsed = urlparse(normalize_url(url))
    if parsed.scheme not in {"http", "https"}:
        return "invalid_scheme"
    if not parsed.hostname:
        return "invalid_host"
    return None


def redact(value: Any) -> Any:
    """Recursively redact anything whose key looks like a secret."""
    if isinstance(value, dict):
        return {
            key: (REDACTED if key.lower() in REDACTED_KEYS else redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def safe_url(url: str) -> str:
    """Scheme and host only — never a path, query, or embedded credential.

    A URL like ``http://admin:token@hub.local/x?token=y`` would otherwise carry
    a secret into a diagnostic bundle shared with support.
    """
    parsed = urlparse(url)
    host = parsed.hostname or "unknown"
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{host}{port}"
