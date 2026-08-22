"""Home Assistant WebSocket client (supported API only — ADR-001).

Implements the documented handshake (auth_required → auth → auth_ok),
request/response correlation by message id, event subscription, registry
reads, and service calls. The access token is held as ``SecretStr`` and never
appears in logs or published events.
"""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp
from pydantic import SecretStr

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT_SECONDS = 15.0


class HAConnectionError(Exception):
    """Connection, handshake, or protocol failure toward Home Assistant."""


class HAAuthError(HAConnectionError):
    """The supplied token was rejected — not retryable without a new token."""


class HomeAssistantWebSocketClient:
    def __init__(self, websocket_url: str, token: SecretStr) -> None:
        self._url = websocket_url
        self._token = token
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._next_id = 1
        self._pending: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._event_subscription_id: int | None = None

    @property
    def connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def connect(self, session: aiohttp.ClientSession) -> None:
        """Open the socket and complete the auth handshake."""
        try:
            ws = await session.ws_connect(self._url, heartbeat=30.0)
        except (aiohttp.ClientError, OSError) as exc:
            raise HAConnectionError(f"cannot reach Home Assistant websocket: {exc}") from exc

        first = await self._receive_json(ws)
        if first.get("type") != "auth_required":
            await ws.close()
            raise HAConnectionError(f"unexpected handshake message type {first.get('type')!r}")

        await ws.send_json({"type": "auth", "access_token": self._token.get_secret_value()})
        verdict = await self._receive_json(ws)
        if verdict.get("type") == "auth_invalid":
            await ws.close()
            raise HAAuthError("Home Assistant rejected the access token")
        if verdict.get("type") != "auth_ok":
            await ws.close()
            raise HAConnectionError(f"unexpected auth response type {verdict.get('type')!r}")

        self._ws = ws
        self._next_id = 1
        self._pending = {}
        self._event_subscription_id = None
        logger.info("authenticated to Home Assistant %s", verdict.get("ha_version", "unknown"))

    async def close(self) -> None:
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        self._ws = None

    async def _receive_json(self, ws: aiohttp.ClientWebSocketResponse) -> dict[str, Any]:
        msg = await ws.receive(timeout=_REQUEST_TIMEOUT_SECONDS)
        if msg.type != aiohttp.WSMsgType.TEXT:
            raise HAConnectionError(f"websocket closed during handshake ({msg.type.name})")
        data: dict[str, Any] = json.loads(msg.data)
        return data

    async def _send_command(self, message: dict[str, Any]) -> dict[str, Any]:
        """Send a command and await its correlated result."""
        if self._ws is None or self._ws.closed:
            raise HAConnectionError("not connected")
        message_id = self._next_id
        self._next_id += 1
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[message_id] = future
        try:
            await self._ws.send_json({**message, "id": message_id})
            return await asyncio.wait_for(future, timeout=_REQUEST_TIMEOUT_SECONDS)
        finally:
            self._pending.pop(message_id, None)

    async def get_states(self) -> list[dict[str, Any]]:
        result = await self._send_command({"type": "get_states"})
        states: list[dict[str, Any]] = result.get("result") or []
        return states

    async def get_entity_registry(self) -> list[dict[str, Any]]:
        result = await self._send_command({"type": "config/entity_registry/list"})
        entries: list[dict[str, Any]] = result.get("result") or []
        return entries

    async def get_device_registry(self) -> list[dict[str, Any]]:
        result = await self._send_command({"type": "config/device_registry/list"})
        entries: list[dict[str, Any]] = result.get("result") or []
        return entries

    async def get_area_registry(self) -> list[dict[str, Any]]:
        result = await self._send_command({"type": "config/area_registry/list"})
        entries: list[dict[str, Any]] = result.get("result") or []
        return entries

    async def subscribe_state_changed(self) -> None:
        result = await self._send_command(
            {"type": "subscribe_events", "event_type": "state_changed"}
        )
        if not result.get("success", False):
            raise HAConnectionError("state_changed subscription refused")
        self._event_subscription_id = result["id"]

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        message: dict[str, Any] = {"type": "call_service", "domain": domain, "service": service}
        if service_data:
            message["service_data"] = service_data
        if target:
            message["target"] = target
        return await self._send_command(message)

    async def listen(self, on_event: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """Pump messages until the socket closes: resolve pending command
        futures and dispatch subscribed events to ``on_event``."""
        if self._ws is None:
            raise HAConnectionError("not connected")
        ws = self._ws
        async for msg in ws:
            if msg.type != aiohttp.WSMsgType.TEXT:
                break
            payload: dict[str, Any] = json.loads(msg.data)
            msg_type = payload.get("type")
            if msg_type == "result":
                future = self._pending.get(int(payload.get("id", -1)))
                if future is not None and not future.done():
                    future.set_result(payload)
            elif msg_type == "event":
                event = payload.get("event") or {}
                if event.get("event_type") == "state_changed":
                    await on_event(event.get("data") or {})
            elif msg_type == "pong":
                continue
        for future in self._pending.values():
            if not future.done():
                future.set_exception(HAConnectionError("connection closed"))
        raise HAConnectionError("Home Assistant websocket closed")
