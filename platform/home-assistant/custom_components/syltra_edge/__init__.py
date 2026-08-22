"""SYLTRA Edge integration for Home Assistant (spec §27).

A **diagnostic** integration. It reports whether the household's SYLTRA Edge
Agent is reachable, and nothing more.

What it deliberately does not do, and why:

- It does not create or mirror device entities. The Edge Agent already reads
  Home Assistant's state through the supported WebSocket API; duplicating that
  here would create two sources of truth for the same devices.
- It does not register services that shadow standard entity services
  (spec §27). Its one service refreshes health.
- It does not modify Home Assistant Core in any way (ADR-001, spec §0 rule 11).
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import CONF_EDGE_URL, CONF_VERIFY_TLS, DOMAIN, SERVICE_REFRESH_HEALTH
from .coordinator import SyltraEdgeCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = SyltraEdgeCoordinator(
        hass,
        edge_url=entry.data[CONF_EDGE_URL],
        verify_tls=entry.data.get(CONF_VERIFY_TLS, True),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _refresh_health(call: ServiceCall) -> None:
        """Refresh health on demand — useful during commissioning."""
        for stored in hass.data[DOMAIN].values():
            await stored.async_request_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_HEALTH):
        hass.services.async_register(DOMAIN, SERVICE_REFRESH_HEALTH, _refresh_health)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH_HEALTH)
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
