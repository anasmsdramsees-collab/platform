"""Deterministic twin projection (spec §14.2).

Pure state machine with no I/O: events in, state out. Keeping it pure is what
makes the acceptance criterion testable — an identical event sequence must
produce an identical twin state, every time, on any machine.

Rules enforced here:

- **Unknown is not false.** A capability never observed reports
  ``StateStatus.UNKNOWN`` with ``value=None``. A boolean that was observed as
  ``False`` reports ``KNOWN`` with ``value=False``. Confusing the two would let
  a risk decision treat "no data" as "no alarm" (safety invariant 4).
- **Older updates lose.** An event whose ``occurred_at`` precedes the stored
  observation is ignored, unless it is an explicit correction.
- **Duplicates are inert.** Applying the same ``event_id`` twice changes
  nothing (safety invariant 10).
- **Homes are isolated.** State is keyed by ``home_id`` throughout; no read
  path can cross homes.
"""

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from syltra_contracts import EventEnvelope
from syltra_contracts.capability_definitions import CAPABILITY_DEFINITIONS

_SEEN_EVENT_CAPACITY = 8192

CORRECTION_FLAG = "correction"
"""Metadata flag marking an event that intentionally supersedes newer state."""


class StateStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    """Never observed. Explicitly not the same as False or off."""
    KNOWN = "KNOWN"
    STALE = "STALE"
    """Observed, but older than the capability's freshness requirement."""


@dataclass(frozen=True)
class CapabilityState:
    """The twin's view of one capability on one device."""

    capability: str
    value: Any = None
    unit: str | None = None
    quality: float = 0.0
    occurred_at: datetime | None = None
    received_at: datetime | None = None
    last_event_id: str | None = None
    observed: bool = False

    def status_at(self, now: datetime) -> StateStatus:
        if not self.observed or self.occurred_at is None:
            return StateStatus.UNKNOWN
        definition = CAPABILITY_DEFINITIONS.get(self.capability)
        if definition is None:
            return StateStatus.KNOWN
        if now - self.occurred_at > timedelta(seconds=definition.freshness_seconds):
            return StateStatus.STALE
        return StateStatus.KNOWN

    def age_seconds(self, now: datetime) -> float | None:
        if self.occurred_at is None:
            return None
        return max((now - self.occurred_at).total_seconds(), 0.0)

    def is_usable_for_decisions(self, now: datetime) -> bool:
        """Only a KNOWN (fresh, observed) value may support a decision."""
        return self.status_at(now) is StateStatus.KNOWN


@dataclass
class DeviceState:
    device_id: str
    room_id: str | None = None
    name: str | None = None
    available: bool | None = None
    """None until observed — unknown availability is not 'offline'."""
    capabilities: dict[str, CapabilityState] = field(default_factory=dict)
    last_seen: datetime | None = None

    def capability(self, capability: str) -> CapabilityState:
        """Return the capability state, or an explicit UNKNOWN placeholder."""
        return self.capabilities.get(capability, CapabilityState(capability=capability))


@dataclass
class RoomState:
    room_id: str
    device_ids: set[str] = field(default_factory=set)


@dataclass
class HomeState:
    home_id: str
    devices: dict[str, DeviceState] = field(default_factory=dict)
    rooms: dict[str, RoomState] = field(default_factory=dict)
    events_applied: int = 0
    last_event_at: datetime | None = None


@dataclass(frozen=True)
class TwinSnapshot:
    """Serializable point-in-time view, used for APIs and equality checks."""

    home_id: str
    taken_at: datetime
    devices: dict[str, dict[str, Any]]
    rooms: dict[str, list[str]]
    events_applied: int

    def fingerprint(self) -> str:
        """Order-independent digest of observable state.

        Two twins built from the same event sequence must produce the same
        fingerprint; it deliberately excludes receive-time and event ids, which
        are transport artifacts rather than observable home state.
        """
        import hashlib
        import json

        material = {
            "home_id": self.home_id,
            "devices": {
                device_id: {
                    "room_id": device["room_id"],
                    "available": device["available"],
                    "capabilities": {
                        capability: {
                            "value": state["value"],
                            "unit": state["unit"],
                            "occurred_at": state["occurred_at"],
                            "observed": state["observed"],
                        }
                        for capability, state in sorted(device["capabilities"].items())
                    },
                }
                for device_id, device in sorted(self.devices.items())
            },
            "rooms": {room: sorted(devices) for room, devices in sorted(self.rooms.items())},
        }
        encoded = json.dumps(material, sort_keys=True, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()


class TwinProjection:
    """Applies events to per-home state. Pure and deterministic."""

    def __init__(self) -> None:
        self._homes: dict[str, HomeState] = {}
        self._seen_events: OrderedDict[str, None] = OrderedDict()

    # ── queries ──

    @property
    def home_ids(self) -> list[str]:
        return sorted(self._homes)

    def home(self, home_id: str) -> HomeState | None:
        return self._homes.get(home_id)

    def device(self, home_id: str, device_id: str) -> DeviceState | None:
        home = self._homes.get(home_id)
        return home.devices.get(device_id) if home else None

    def snapshot(self, home_id: str, now: datetime) -> TwinSnapshot:
        home = self._homes.get(home_id) or HomeState(home_id=home_id)
        devices: dict[str, dict[str, Any]] = {}
        for device_id, device in home.devices.items():
            devices[device_id] = {
                "device_id": device_id,
                "room_id": device.room_id,
                "name": device.name,
                "available": device.available,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "capabilities": {
                    capability: {
                        "value": state.value,
                        "unit": state.unit,
                        "quality": state.quality,
                        "status": state.status_at(now).value,
                        "observed": state.observed,
                        "occurred_at": (
                            state.occurred_at.isoformat() if state.occurred_at else None
                        ),
                        "age_seconds": state.age_seconds(now),
                    }
                    for capability, state in sorted(device.capabilities.items())
                },
            }
        return TwinSnapshot(
            home_id=home_id,
            taken_at=now,
            devices=devices,
            rooms={
                room_id: sorted(room.device_ids) for room_id, room in sorted(home.rooms.items())
            },
            events_applied=home.events_applied,
        )

    # ── mutation ──

    def apply(self, envelope: EventEnvelope) -> bool:
        """Apply one event. Returns True if observable state changed."""
        event_id = str(envelope.event_id)
        if event_id in self._seen_events:
            return False  # duplicate delivery — inert (safety invariant 10)
        self._seen_events[event_id] = None
        if len(self._seen_events) > _SEEN_EVENT_CAPACITY:
            self._seen_events.popitem(last=False)

        home = self._homes.setdefault(envelope.home_id, HomeState(home_id=envelope.home_id))
        home.events_applied += 1
        if home.last_event_at is None or envelope.occurred_at > home.last_event_at:
            home.last_event_at = envelope.occurred_at

        device_id = envelope.subject.device_id
        if device_id is None:
            return False

        device = home.devices.get(device_id)
        if device is None:
            device = DeviceState(device_id=device_id)
            home.devices[device_id] = device
        changed = False

        room_id = envelope.subject.room_id
        if room_id and device.room_id != room_id:
            self._relocate(home, device, room_id)
            changed = True

        if envelope.event_type == "device.discovered":
            name = envelope.value if isinstance(envelope.value, str) else None
            if name and device.name != name:
                device.name = name
                changed = True
            return changed

        if envelope.event_type == "device.removed":
            home.devices.pop(device_id, None)
            for room in home.rooms.values():
                room.device_ids.discard(device_id)
            return True

        if device.last_seen is None or envelope.received_at > device.last_seen:
            device.last_seen = envelope.received_at

        capability = envelope.capability
        if capability is None:
            return changed

        if capability == "device.online":
            available = bool(envelope.value)
            if device.available != available:
                device.available = available
                changed = True

        existing = device.capabilities.get(capability)
        is_correction = bool(envelope.metadata.get(CORRECTION_FLAG))
        if (
            existing is not None
            and existing.occurred_at is not None
            and envelope.occurred_at <= existing.occurred_at
            and not is_correction
        ):
            # Older or same-instant update: the newer observation stands.
            return changed

        new_state = CapabilityState(
            capability=capability,
            value=envelope.value,
            unit=envelope.unit,
            quality=envelope.quality,
            occurred_at=envelope.occurred_at,
            received_at=envelope.received_at,
            last_event_id=event_id,
            observed=True,
        )
        if existing is None or _observable_difference(existing, new_state):
            changed = True
        device.capabilities[capability] = new_state
        return changed

    def apply_all(self, envelopes: list[EventEnvelope]) -> int:
        return sum(1 for envelope in envelopes if self.apply(envelope))

    def reset(self) -> None:
        """Drop all state — used before a rebuild from the event stream."""
        self._homes.clear()
        self._seen_events.clear()

    @staticmethod
    def _relocate(home: HomeState, device: DeviceState, room_id: str) -> None:
        if device.room_id:
            previous = home.rooms.get(device.room_id)
            if previous:
                previous.device_ids.discard(device.device_id)
        device.room_id = room_id
        room = home.rooms.setdefault(room_id, RoomState(room_id=room_id))
        room.device_ids.add(device.device_id)


def _observable_difference(old: CapabilityState, new: CapabilityState) -> bool:
    """True when the change is visible to a consumer (value or unit)."""
    return old.value != new.value or old.unit != new.unit or not old.observed
