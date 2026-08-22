"""Twin-state builders for rule and engine tests (spec §26: synthetic data only)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from syltra_digital_twin.core import CapabilityState, DeviceState, HomeState, RoomState

EVENING = datetime(2026, 8, 18, 23, 30, 0, tzinfo=UTC)
"""Inside the default quiet-hours window (22:00–07:00)."""

MIDDAY = datetime(2026, 8, 18, 13, 0, 0, tzinfo=UTC)
"""Outside quiet hours."""


def build_reading(
    capability: str,
    value: Any,
    at: datetime,
    unit: str | None = None,
) -> CapabilityState:
    return CapabilityState(
        capability=capability,
        value=value,
        unit=unit,
        quality=1.0,
        occurred_at=at,
        received_at=at,
        last_event_id=None,
        observed=True,
    )


def build_device(
    device_id: str,
    room_id: str | None = None,
    name: str | None = None,
    available: bool | None = True,
    **capabilities: CapabilityState,
) -> DeviceState:
    return DeviceState(
        device_id=device_id,
        room_id=room_id,
        name=name,
        available=available,
        capabilities={state.capability: state for state in capabilities.values()},
        last_seen=max(
            (s.received_at for s in capabilities.values() if s.received_at), default=None
        ),
    )


def build_home(*devices: DeviceState, home_id: str = "home_001") -> HomeState:
    state = HomeState(home_id=home_id)
    for d in devices:
        state.devices[d.device_id] = d
        if d.room_id:
            state.rooms.setdefault(d.room_id, RoomState(room_id=d.room_id)).device_ids.add(
                d.device_id
            )
    return state


def stale_by(base: datetime, seconds: float) -> datetime:
    """A timestamp far enough in the past to breach a freshness window."""
    return base - timedelta(seconds=seconds)
