"""Edge Agent core loop: connect → bootstrap registries → subscribe → publish.

Reconnects with bounded exponential backoff after any connection loss
(including Home Assistant restarts). Auth failures keep retrying at the
maximum interval — the operator fixes the token; the agent stays alive and
reports not-ready.
"""

import asyncio
import contextlib
import logging
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import aiohttp

from syltra_contracts import (
    DeviceInfo,
    EntityInfo,
    EntityState,
    EventEnvelope,
    EventSource,
    EventSubject,
    PrivacyClass,
    RegistrySnapshot,
)
from syltra_edge_agent import metrics
from syltra_edge_agent.backoff import BoundedExponentialBackoff
from syltra_edge_agent.config import EdgeAgentSettings
from syltra_edge_agent.ha_client import (
    HAAuthError,
    HAConnectionError,
    HomeAssistantWebSocketClient,
)
from syltra_edge_agent.mapping import MappingError
from syltra_edge_agent.normalizer import StateChangeNormalizer
from syltra_eventing import (
    EventPublisher,
    normalized_device_subject,
    raw_device_subject,
    sanitize_token,
)

logger = logging.getLogger(__name__)


class EdgeAgentService:
    def __init__(
        self,
        settings: EdgeAgentSettings,
        client: HomeAssistantWebSocketClient,
        publisher: EventPublisher,
    ) -> None:
        self._settings = settings
        self._client = client
        self._publisher = publisher
        self._entity_device: dict[str, str] = {}
        self._entity_room: dict[str, str | None] = {}
        self._devices: dict[str, DeviceInfo] = {}
        self._snapshot: RegistrySnapshot | None = None
        self._normalizer = self._new_normalizer()
        self._stopping = asyncio.Event()
        self._connected = False

    # ── public surface ──

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def client(self) -> HomeAssistantWebSocketClient:
        """The live Home Assistant connection, for the gateway adapter."""
        return self._client

    @property
    def registry_snapshot(self) -> RegistrySnapshot | None:
        return self._snapshot

    def device_id_for(self, entity_id: str) -> str:
        return self._entity_device.get(entity_id) or sanitize_token(entity_id)

    def room_id_for(self, entity_id: str) -> str | None:
        return self._entity_room.get(entity_id)

    def stop(self) -> None:
        self._stopping.set()

    async def run(self) -> None:
        """Supervision loop: connect, serve, back off, repeat until stopped."""
        backoff = BoundedExponentialBackoff(
            initial=self._settings.reconnect_initial_seconds,
            maximum=self._settings.reconnect_max_seconds,
        )
        async with aiohttp.ClientSession() as session:
            while not self._stopping.is_set():
                pump: asyncio.Task[None] | None = None
                try:
                    await self._client.connect(session)
                    self._connected = True
                    metrics.CONNECTED.set(1)
                    backoff.reset()
                    # The pump must run concurrently with bootstrap: command
                    # responses are correlated by the same message loop that
                    # dispatches events.
                    pump = asyncio.create_task(self._client.listen(self._handle_state_changed))
                    await self._bootstrap()
                    await self._client.subscribe_state_changed()
                    logger.info("edge agent online; streaming state changes")
                    await pump
                except HAAuthError:
                    delay = self._settings.reconnect_max_seconds
                    logger.error(
                        "Home Assistant rejected the token; retrying in %.0fs "
                        "(update HOME_ASSISTANT_TOKEN)",
                        delay,
                    )
                    await self._sleep_or_stop(delay)
                except (HAConnectionError, aiohttp.ClientError, OSError, TimeoutError) as exc:
                    delay = backoff.next_delay()
                    metrics.RECONNECTS.inc()
                    logger.warning(
                        "connection to Home Assistant lost (%s); reconnecting in %.1fs", exc, delay
                    )
                    await self._sleep_or_stop(delay)
                finally:
                    self._connected = False
                    metrics.CONNECTED.set(0)
                    if pump is not None and not pump.done():
                        pump.cancel()
                        with contextlib.suppress(asyncio.CancelledError, HAConnectionError):
                            await pump
                    await self._client.close()

    # ── internals ──

    async def _sleep_or_stop(self, delay: float) -> None:
        try:
            await asyncio.wait_for(self._stopping.wait(), timeout=delay)
        except TimeoutError:
            return

    def _new_normalizer(self) -> StateChangeNormalizer:
        return StateChangeNormalizer(
            home_id=self._settings.syltra_home_id,
            hub_id=self._settings.syltra_hub_id,
            device_id_for=self.device_id_for,
            room_id_for=self.room_id_for,
        )

    async def _bootstrap(self) -> None:
        """Load registries and current states; publish discovery events."""
        devices_raw = await self._client.get_device_registry()
        entities_raw = await self._client.get_entity_registry()
        areas_raw = await self._client.get_area_registry()
        states_raw = await self._client.get_states()

        area_names = {
            str(a.get("area_id")): str(a.get("name") or a.get("area_id"))
            for a in areas_raw
            if a.get("area_id")
        }
        device_area: dict[str, str | None] = {}
        self._devices = {}
        for d in devices_raw:
            device_id = str(d.get("id") or "")
            if not device_id:
                continue
            area_id = d.get("area_id")
            device_area[device_id] = area_names.get(str(area_id)) if area_id else None
            self._devices[device_id] = DeviceInfo(
                device_id=device_id,
                name=d.get("name_by_user") or d.get("name"),
                manufacturer=d.get("manufacturer"),
                model=d.get("model"),
                room_id=device_area[device_id],
                entity_ids=[],
            )

        self._entity_device = {}
        self._entity_room = {}
        entity_infos: list[EntityInfo] = []
        for e in entities_raw:
            entity_id = str(e.get("entity_id") or "")
            if not entity_id:
                continue
            owner_id = str(e.get("device_id")) if e.get("device_id") else None
            if owner_id:
                self._entity_device[entity_id] = owner_id
                if owner_id in self._devices:
                    self._devices[owner_id].entity_ids.append(entity_id)
            entity_area = e.get("area_id")
            room = (
                area_names.get(str(entity_area))
                if entity_area
                else (device_area.get(owner_id or "") if owner_id else None)
            )
            self._entity_room[entity_id] = room
            entity_infos.append(EntityInfo(entity_id=entity_id, device_id=owner_id, room_id=room))

        entity_states = [
            EntityState(
                entity_id=str(s.get("entity_id")),
                state=str(s.get("state")),
                attributes=dict(s.get("attributes") or {}),
                available=str(s.get("state")) != "unavailable",
            )
            for s in states_raw
            if s.get("entity_id")
        ]
        self._snapshot = RegistrySnapshot(
            taken_at=datetime.now(tz=UTC),
            devices=list(self._devices.values()),
            entities=entity_infos,
            states=entity_states,
        )

        # Fresh connection → fresh dedup/order state, then discovery events.
        self._normalizer = self._new_normalizer()
        for device in self._devices.values():
            await self._publish_discovery(device)
        # Seed current states through the normal pipeline so the twin can
        # bootstrap from the normalized stream alone.
        for s in states_raw:
            await self._handle_state_changed({"entity_id": s.get("entity_id"), "new_state": s})
        logger.info(
            "bootstrap complete: %d devices, %d entities, %d states",
            len(self._devices),
            len(entity_infos),
            len(entity_states),
        )

    async def _publish_discovery(self, device: DeviceInfo) -> None:
        now = datetime.now(tz=UTC)
        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type="device.discovered",
            schema_version="1.0",
            occurred_at=now,
            received_at=now,
            home_id=self._settings.syltra_home_id,
            correlation_id=uuid4(),
            source=EventSource(
                service="edge-agent",
                instance_id=self._settings.syltra_hub_id,
                protocol="home_assistant_websocket",
            ),
            subject=EventSubject(device_id=device.device_id, room_id=device.room_id),
            value=device.name,
            privacy_class=PrivacyClass.HOUSEHOLD_PRIVATE,
            metadata={"manufacturer": device.manufacturer, "model": device.model},
        )
        await self._publisher.publish_envelope(
            normalized_device_subject(self._settings.syltra_home_id, device.device_id),
            envelope,
        )
        metrics.EVENTS_PUBLISHED.labels(stream="normalized").inc()

    async def _handle_state_changed(self, data: dict[str, Any]) -> None:
        metrics.EVENTS_RECEIVED.inc()
        started = time.monotonic()
        home_id = self._settings.syltra_home_id
        try:
            outcome = self._normalizer.normalize(data)
        except MappingError as exc:
            metrics.EVENTS_INVALID.inc()
            logger.warning("invalid event → dead-letter (%s)", exc.reason_code)
            await self._publisher.publish_deadletter(
                reason_codes=[exc.reason_code],
                error=str(exc),
                payload=_shallow_safe(data),
            )
            return

        if outcome.duplicate:
            metrics.EVENTS_DUPLICATE.inc()
            return
        if outcome.out_of_order:
            metrics.EVENTS_OUT_OF_ORDER.inc()

        device_token = (
            outcome.raw_envelope.subject.device_id
            if outcome.raw_envelope and outcome.raw_envelope.subject.device_id
            else "unknown"
        )
        if outcome.raw_envelope is not None:
            await self._publisher.publish_envelope(
                raw_device_subject(home_id, device_token), outcome.raw_envelope
            )
            metrics.EVENTS_PUBLISHED.labels(stream="raw").inc()

        if outcome.unmapped:
            metrics.EVENTS_UNMAPPED.inc()
            return

        for envelope in outcome.envelopes:
            await self._publisher.publish_envelope(
                normalized_device_subject(home_id, device_token), envelope
            )
            metrics.EVENTS_PUBLISHED.labels(stream="normalized").inc()
        metrics.PUBLISH_LATENCY.observe(time.monotonic() - started)


def _shallow_safe(data: dict[str, Any]) -> dict[str, Any]:
    """Keep dead-letter payloads bounded and JSON-safe."""
    return {
        "entity_id": data.get("entity_id"),
        "new_state": data.get("new_state"),
        "old_state_present": data.get("old_state") is not None,
    }
