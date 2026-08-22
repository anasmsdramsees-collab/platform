"""Health polling coordinator for the SYLTRA Edge Agent (spec §27).

The integration's only job is to show whether the household's SYLTRA Edge Agent
is reachable and healthy. It deliberately does **not** mirror device state,
issue commands, or duplicate what the Edge Agent already does through the
supported Home Assistant APIs — that would put two components in charge of the
same thing (ADR-001).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, HEALTH_PATH, LIVE_PATH

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=8)


class SyltraEdgeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the Edge Agent's health endpoints."""

    def __init__(self, hass: HomeAssistant, edge_url: str, verify_tls: bool = True) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._edge_url = edge_url.rstrip("/")
        self._verify_tls = verify_tls
        self.last_error: str | None = None

    @property
    def edge_url(self) -> str:
        return self._edge_url

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass, verify_ssl=self._verify_tls)
        try:
            live = await self._probe(session, LIVE_PATH)
            ready = await self._probe(session, HEALTH_PATH)
        except aiohttp.ClientError as err:
            # The message is kept short and carries no URL credentials.
            self.last_error = type(err).__name__
            raise UpdateFailed(f"SYLTRA Edge unreachable ({type(err).__name__})") from err
        except TimeoutError as err:
            self.last_error = "timeout"
            raise UpdateFailed("SYLTRA Edge did not respond in time") from err

        self.last_error = None
        return {
            "alive": live,
            "ready": ready,
            "checked_at": datetime.now(tz=UTC).isoformat(),
        }

    async def _probe(self, session: aiohttp.ClientSession, path: str) -> bool:
        async with session.get(f"{self._edge_url}{path}", timeout=REQUEST_TIMEOUT) as response:
            return response.status == 200
