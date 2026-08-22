"""Mock Home Assistant WebSocket boundary (spec §24.3).

Speaks the documented HA WebSocket protocol surface the Edge Agent uses:
auth handshake, ``get_states``, registry lists, ``subscribe_events``,
``call_service``, ping/pong. Supports deterministic state injection (with
explicit timestamps for duplicate and out-of-order scenarios) and simulated
restarts (drop all connections, keep state).
"""

import asyncio
import contextlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from aiohttp import WSMsgType, web

from syltra_simulator.home import VIRTUAL_DEVICES, VIRTUAL_HOME_STATES

class MockHomeAssistant:
    """A stand-in Home Assistant.

    ``start_time`` anchors the simulated clock. It defaults to *now* so
    simulated readings are contemporaneous with the consumers evaluating them —
    a fixed historical epoch would make every reading look stale to freshness
    checks. Pass an explicit value when a test needs a frozen clock; step
    ordering stays deterministic either way because the clock only ever
    advances by fixed increments.
    """

    def __init__(
        self,
        token: str | None = None,
        host: str = "127.0.0.1",
        start_time: datetime | None = None,
    ) -> None:
        self._start_time = start_time or datetime.now(tz=UTC)
        # Generated per instance rather than defaulted to a literal: the
        # simulator must never ship anything shaped like a real credential,
        # and each run gets its own value.
        self._token = token or secrets.token_urlsafe(24)
        self._host = host
        self.port: int = 0
        self._runner: web.AppRunner | None = None
        self._states: dict[str, dict[str, Any]] = {}
        self._clock = self._start_time
        self._subscribers: dict[web.WebSocketResponse, int] = {}
        self._sockets: set[web.WebSocketResponse] = set()
        self.reset_states()

    # ── lifecycle ──

    def reset_states(self) -> None:
        self._clock = self._start_time
        self._states = {
            entity_id: {
                "entity_id": entity_id,
                "state": initial["state"],
                "attributes": dict(initial["attributes"]),
                "last_updated": self._clock.isoformat(),
                "last_changed": self._clock.isoformat(),
            }
            for entity_id, initial in VIRTUAL_HOME_STATES.items()
        }

    async def start(self) -> None:
        app = web.Application()
        app.router.add_get("/api/websocket", self._websocket_handler)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self._host, 0)
        await site.start()
        # aiohttp exposes no public accessor for the OS-assigned port.
        server = site._server  # noqa: SLF001
        sockets = getattr(server, "sockets", None)
        if not sockets:
            msg = "mock Home Assistant failed to bind a port"
            raise RuntimeError(msg)
        self.port = int(sockets[0].getsockname()[1])

    async def stop(self) -> None:
        await self.restart_connections()
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None

    async def restart_connections(self) -> None:
        """Simulate a Home Assistant restart: drop every client connection."""
        for ws in list(self._sockets):
            with contextlib.suppress(Exception):
                await ws.close()
        self._sockets.clear()
        self._subscribers.clear()

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self.port}"

    @property
    def token(self) -> str:
        return self._token

    # ── deterministic state control ──

    def advance_clock(self, seconds: float) -> datetime:
        self._clock += timedelta(seconds=seconds)
        return self._clock

    async def set_state(
        self,
        entity_id: str,
        state: str,
        attributes: dict[str, Any] | None = None,
        last_updated: datetime | None = None,
    ) -> None:
        """Set a state and emit ``state_changed`` to all subscribers."""
        old = self._states.get(entity_id)
        stamp = (last_updated or self.advance_clock(1.0)).isoformat()
        merged_attributes = dict(old["attributes"]) if old else {}
        if attributes:
            merged_attributes.update(attributes)
        new = {
            "entity_id": entity_id,
            "state": state,
            "attributes": merged_attributes,
            "last_updated": stamp,
            "last_changed": stamp,
        }
        self._states[entity_id] = new
        await self._emit({"entity_id": entity_id, "old_state": old, "new_state": new})

    async def emit_raw_event(self, data: dict[str, Any]) -> None:
        """Emit an arbitrary state_changed payload (duplicates, malformed…)."""
        await self._emit(data)

    async def _emit(self, data: dict[str, Any]) -> None:
        for ws, sub_id in list(self._subscribers.items()):
            with contextlib.suppress(Exception):
                await ws.send_json(
                    {
                        "id": sub_id,
                        "type": "event",
                        "event": {"event_type": "state_changed", "data": data},
                    }
                )

    # ── protocol ──

    async def _websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=30.0)
        await ws.prepare(request)
        self._sockets.add(ws)
        try:
            await ws.send_json({"type": "auth_required", "ha_version": "2026.8.1-sim"})
            authed = False
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    break
                payload: dict[str, Any] = json.loads(msg.data)
                if not authed:
                    if payload.get("type") == "auth" and payload.get("access_token") == self._token:
                        authed = True
                        await ws.send_json({"type": "auth_ok", "ha_version": "2026.8.1-sim"})
                        continue
                    await ws.send_json({"type": "auth_invalid", "message": "invalid token"})
                    break
                await self._handle_command(ws, payload)
        finally:
            self._sockets.discard(ws)
            self._subscribers.pop(ws, None)
        return ws

    async def _handle_command(
        self, ws: web.WebSocketResponse, payload: dict[str, Any]
    ) -> None:
        message_id = int(payload.get("id", 0))
        command = payload.get("type")
        result: Any = None
        if command == "get_states":
            result = list(self._states.values())
        elif command == "config/device_registry/list":
            result = [
                {
                    "id": d.device_id,
                    "name": d.name,
                    "name_by_user": None,
                    "manufacturer": d.manufacturer,
                    "model": d.model,
                    "area_id": d.room,
                }
                for d in VIRTUAL_DEVICES
            ]
        elif command == "config/entity_registry/list":
            result = [
                {"entity_id": entity_id, "device_id": d.device_id, "area_id": None}
                for d in VIRTUAL_DEVICES
                for entity_id in d.entities
            ]
        elif command == "config/area_registry/list":
            rooms = sorted({d.room for d in VIRTUAL_DEVICES})
            result = [{"area_id": room, "name": room} for room in rooms]
        elif command == "subscribe_events":
            self._subscribers[ws] = message_id
            result = None
        elif command == "call_service":
            await self._apply_service(payload)
            result = {"context": {"id": f"sim_ctx_{message_id}"}}
        elif command == "ping":
            await ws.send_json({"id": message_id, "type": "pong"})
            return
        else:
            await ws.send_json(
                {
                    "id": message_id,
                    "type": "result",
                    "success": False,
                    "error": {"code": "unknown_command", "message": str(command)},
                }
            )
            return
        await ws.send_json(
            {"id": message_id, "type": "result", "success": True, "result": result}
        )

    async def _apply_service(self, payload: dict[str, Any]) -> None:
        """Minimal actuator behavior so command round-trips are observable."""
        domain = payload.get("domain")
        service = payload.get("service")
        data = payload.get("service_data") or {}
        target = payload.get("target") or {}
        entity_ids = target.get("entity_id")
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]
        for entity_id in entity_ids or []:
            if entity_id not in self._states:
                continue
            if domain in ("light", "switch") and service in ("turn_on", "turn_off"):
                attributes = (
                    {"brightness": round(float(data["brightness_pct"]) * 255 / 100)}
                    if "brightness_pct" in data
                    else None
                )
                await self.set_state(
                    entity_id, "on" if service == "turn_on" else "off", attributes
                )
            elif domain == "climate" and service == "set_temperature":
                current = self._states[entity_id]
                await self.set_state(
                    entity_id, current["state"], {"temperature": float(data["temperature"])}
                )
            elif domain == "climate" and service == "set_hvac_mode":
                await self.set_state(entity_id, str(data["hvac_mode"]))
            elif domain == "cover" and service == "set_cover_position":
                position = float(data["position"])
                await self.set_state(
                    entity_id,
                    "open" if position > 0 else "closed",
                    {"current_position": position},
                )
