"""SYLTRA-owned device integration boundary (spec §4.9).

Core services (Digital Twin, Context Engine, Adaptive Engine, Risk Engine,
Policy Service, Safety Governor, Action Orchestrator, SILA, UI) depend only on
this interface and the canonical contracts — never on Home Assistant entity
objects or internal modules. ``HomeAssistantDeviceGateway`` (services/edge-agent)
is one adapter; native Matter/Zigbee adapters may replace it without touching
core services.
"""

from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class DeviceInfo(BaseModel):
    """A physical or logical device, vendor-neutral."""

    model_config = ConfigDict(extra="allow", frozen=True)

    device_id: str
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    room_id: str | None = None
    entity_ids: list[str] = Field(default_factory=list)


class EntityInfo(BaseModel):
    """A single addressable signal or control surface on a device."""

    model_config = ConfigDict(extra="allow", frozen=True)

    entity_id: str
    device_id: str | None = None
    capability: str | None = None  # canonical capability id, if mapped
    room_id: str | None = None


class EntityState(BaseModel):
    """Point-in-time state of an entity as reported by the integration runtime."""

    model_config = ConfigDict(extra="allow", frozen=True)

    entity_id: str
    state: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime | None = None
    available: bool = True


class DeviceHealth(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    device_id: str
    online: bool
    battery_percent: float | None = None
    last_seen: datetime | None = None


class RegistrySnapshot(BaseModel):
    """Devices + entities + states at one instant, for twin bootstrap."""

    model_config = ConfigDict(extra="allow", frozen=True)

    taken_at: datetime
    devices: list[DeviceInfo]
    entities: list[EntityInfo]
    states: list[EntityState]


class CapabilityCommand(BaseModel):
    """A normalized write against a capability — the ONLY way core services
    express device control. Vendor service mapping happens inside the adapter."""

    model_config = ConfigDict(frozen=True)

    device_id: str
    capability: str
    value: Any
    correlation_id: str | None = None


class CommandResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    accepted: bool
    reason: str | None = None


StateChangeHandler = Callable[[EntityState, EntityState | None], Awaitable[None]]


class DeviceIntegrationGateway(Protocol):
    """Required gateway operations (spec §4.9)."""

    async def list_devices(self) -> list[DeviceInfo]: ...

    async def list_entities(self) -> list[EntityInfo]: ...

    async def get_state(self, entity_id: str) -> EntityState | None: ...

    def subscribe_state_changes(self) -> AsyncIterator[EntityState]: ...

    async def execute_capability_command(self, command: CapabilityCommand) -> CommandResult: ...

    async def get_device_health(self, device_id: str) -> DeviceHealth | None: ...

    async def get_registry_snapshot(self) -> RegistrySnapshot: ...
