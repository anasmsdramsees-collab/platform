"""Config flow for SYLTRA Edge (spec §27).

Local configuration of the Edge Agent endpoint. The flow validates the endpoint
before accepting it, so a typo is caught while the installer is standing in
front of the hub rather than surfacing as a silent failure later.
"""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_EDGE_URL, CONF_VERIFY_TLS, DEFAULT_EDGE_URL, DOMAIN, LIVE_PATH
from .validation import normalize_url as _normalize
from .validation import validate_url

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EDGE_URL, default=DEFAULT_EDGE_URL): str,
        vol.Optional(CONF_VERIFY_TLS, default=True): bool,
    }
)


class SyltraEdgeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            url = _normalize(user_input[CONF_EDGE_URL])
            error = validate_url(url)
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                if await self._can_reach(url, user_input.get(CONF_VERIFY_TLS, True)):
                    return self.async_create_entry(
                        title="SYLTRA Edge",
                        data={
                            CONF_EDGE_URL: url,
                            CONF_VERIFY_TLS: user_input.get(CONF_VERIFY_TLS, True),
                        },
                    )
                errors["base"] = "cannot_connect"

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    async def _can_reach(self, url: str, verify_tls: bool) -> bool:
        session = async_get_clientsession(self.hass, verify_ssl=verify_tls)
        try:
            async with session.get(
                f"{url}{LIVE_PATH}", timeout=aiohttp.ClientTimeout(total=8)
            ) as response:
                return response.status == 200
        except (aiohttp.ClientError, TimeoutError):
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> OptionsFlow:
        return SyltraEdgeOptionsFlow(config_entry)


class SyltraEdgeOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: Any) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_VERIFY_TLS,
                        default=self._entry.data.get(CONF_VERIFY_TLS, True),
                    ): bool
                }
            ),
        )
