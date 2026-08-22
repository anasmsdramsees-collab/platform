"""Diagnostics with secrets redacted (spec §27, §25.3, §26).

Diagnostic bundles are shared with support, so they must carry no credential
and no household-identifying data. Redaction is applied recursively by key
name, and the URL is reduced to scheme and host so a token embedded in a
userinfo component cannot survive.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_EDGE_URL, DOMAIN
from .validation import redact, safe_url


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    data = redact(dict(entry.data))
    if CONF_EDGE_URL in data:
        data[CONF_EDGE_URL] = safe_url(str(entry.data[CONF_EDGE_URL]))
    return {
        "entry": {"title": entry.title, "version": entry.version, "data": data},
        "coordinator": {
            "available": bool(coordinator and coordinator.last_update_success),
            "last_error": getattr(coordinator, "last_error", None),
            "data": redact(getattr(coordinator, "data", None) or {}),
        },
    }
