"""``HomeAssistantDeviceGateway`` — the Home Assistant adapter behind the
SYLTRA-owned ``DeviceIntegrationGateway`` interface (spec §4.9).

Core services depend on the interface in ``syltra_contracts.gateway``; this
adapter is the only module allowed to translate capabilities into Home
Assistant service calls.

Safety invariant 16 is enforced here as defense in depth: in development and
simulation environments, commands against critical actuator capabilities
(locks, valves, breakers, sirens, garage) are refused outright — the Safety
Governor (Phase 6) adds the authoritative policy layer on top.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from syltra_contracts import (
    CapabilityCommand,
    CommandResult,
    DeviceHealth,
    DeviceInfo,
    EntityInfo,
    EntityState,
    RegistrySnapshot,
)
from syltra_contracts.capabilities import CRITICAL_ACTUATOR_CAPABILITIES
from syltra_edge_agent.ha_client import HomeAssistantWebSocketClient
from syltra_edge_agent.service import EdgeAgentService

_COMMAND_SERVICES: dict[str, tuple[str, str]] = {
    # capability → (HA domain, HA service); data mapping handled below.
    "light.power": ("light", "turn_on"),
    "light.brightness": ("light", "turn_on"),
    "switch.power": ("switch", "turn_on"),
    "climate.mode": ("climate", "set_hvac_mode"),
    "climate.target_temperature": ("climate", "set_temperature"),
    "cover.position": ("cover", "set_cover_position"),
    "notification.send": ("notify", "notify"),
}


class HomeAssistantDeviceGateway:
    """Implements ``DeviceIntegrationGateway`` over the Edge Agent's live
    Home Assistant connection and cached registry."""

    def __init__(
        self,
        client: HomeAssistantWebSocketClient,
        service: EdgeAgentService,
        environment: str,
    ) -> None:
        self._client = client
        self._service = service
        self._environment = environment
        self._state_queue: asyncio.Queue[EntityState] = asyncio.Queue(maxsize=1024)

    async def list_devices(self) -> list[DeviceInfo]:
        snapshot = self._service.registry_snapshot
        return list(snapshot.devices) if snapshot else []

    async def list_entities(self) -> list[EntityInfo]:
        snapshot = self._service.registry_snapshot
        return list(snapshot.entities) if snapshot else []

    async def get_state(self, entity_id: str) -> EntityState | None:
        for state in await self._client.get_states():
            if state.get("entity_id") == entity_id:
                return EntityState(
                    entity_id=entity_id,
                    state=str(state.get("state")),
                    attributes=dict(state.get("attributes") or {}),
                    available=str(state.get("state")) != "unavailable",
                )
        return None

    def subscribe_state_changes(self) -> AsyncIterator[EntityState]:
        queue = self._state_queue

        async def _iterate() -> AsyncIterator[EntityState]:
            while True:
                yield await queue.get()

        return _iterate()

    async def push_state_change(self, state: EntityState) -> None:
        """Feed the subscription stream (called by the service loop)."""
        if self._state_queue.full():
            _ = self._state_queue.get_nowait()  # drop oldest under pressure
        await self._state_queue.put(state)

    async def execute_capability_command(self, command: CapabilityCommand) -> CommandResult:
        if command.capability in CRITICAL_ACTUATOR_CAPABILITIES and self._environment in (
            "development",
            "simulation",
        ):
            return CommandResult(
                accepted=False,
                reason="CRITICAL_ACTUATOR_BLOCKED_IN_DEVELOPMENT",
            )
        mapped = _COMMAND_SERVICES.get(command.capability)
        if mapped is None:
            return CommandResult(accepted=False, reason="UNSUPPORTED_CAPABILITY_COMMAND")
        domain, service = mapped
        entity_id = self._primary_entity(command.device_id, domain)
        if entity_id is None:
            return CommandResult(accepted=False, reason="UNKNOWN_TARGET_MAPPING")
        service_data = _service_data(command)
        if command.capability in ("light.power", "switch.power") and command.value is False:
            service = "turn_off"
        await self._client.call_service(
            domain, service, service_data or None, target={"entity_id": entity_id}
        )
        return CommandResult(accepted=True)

    async def get_device_health(self, device_id: str) -> DeviceHealth | None:
        snapshot = self._service.registry_snapshot
        if snapshot is None:
            return None
        device = next((d for d in snapshot.devices if d.device_id == device_id), None)
        if device is None:
            return None
        states = {s.entity_id: s for s in snapshot.states}
        online = any(
            states[eid].available for eid in device.entity_ids if eid in states
        ) or not device.entity_ids
        battery = next(
            (
                float(states[eid].state)
                for eid in device.entity_ids
                if eid in states
                and states[eid].attributes.get("device_class") == "battery"
                and _is_float(states[eid].state)
            ),
            None,
        )
        return DeviceHealth(device_id=device_id, online=online, battery_percent=battery)

    async def get_registry_snapshot(self) -> RegistrySnapshot:
        snapshot = self._service.registry_snapshot
        if snapshot is None:
            msg = "registry snapshot not yet available (agent still bootstrapping)"
            raise RuntimeError(msg)
        return snapshot

    def _primary_entity(self, device_id: str, domain: str) -> str | None:
        snapshot = self._service.registry_snapshot
        if snapshot is None:
            return None
        device = next((d for d in snapshot.devices if d.device_id == device_id), None)
        if device is None:
            return None
        for entity_id in device.entity_ids:
            if entity_id.startswith(f"{domain}."):
                return entity_id
        return None


def _service_data(command: CapabilityCommand) -> dict[str, Any]:
    if command.capability == "light.brightness":
        return {"brightness_pct": command.value}
    if command.capability == "climate.target_temperature":
        return {"temperature": command.value}
    if command.capability == "climate.mode":
        return {"hvac_mode": command.value}
    if command.capability == "cover.position":
        return {"position": command.value}
    if command.capability == "notification.send":
        return {"message": command.value}
    return {}


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True
