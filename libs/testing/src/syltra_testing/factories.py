"""Synthetic event envelope factories."""

import random
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from syltra_contracts import EventEnvelope, EventSource, EventSubject

BASE_TIME = datetime(2026, 8, 18, 12, 0, 0, tzinfo=UTC)
"""Fixed reference instant so tests never depend on the wall clock."""


def make_envelope(
    capability: str | None = "environment.temperature",
    value: Any = 27.4,
    *,
    home_id: str = "home_001",
    device_id: str | None = "device_001",
    entity_id: str | None = "sensor.synthetic",
    room_id: str | None = "living_room",
    occurred_at: datetime = BASE_TIME,
    received_at: datetime | None = None,
    event_type: str = "device.state.changed",
    unit: str | None = "C",
    quality: float = 1.0,
    event_id: UUID | None = None,
    correlation_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> EventEnvelope:
    """Build a valid, fully synthetic event envelope."""
    return EventEnvelope(
        event_id=event_id or uuid4(),
        event_type=event_type,
        schema_version="1.0",
        occurred_at=occurred_at,
        received_at=received_at or occurred_at,
        home_id=home_id,
        correlation_id=correlation_id or uuid4(),
        source=EventSource(
            service="edge-agent", instance_id="hub_synthetic", protocol="test"
        ),
        subject=EventSubject(device_id=device_id, entity_id=entity_id, room_id=room_id),
        capability=capability,
        value=value,
        unit=unit,
        quality=quality,
        metadata=metadata or {},
    )


_CAPABILITY_CYCLE: tuple[tuple[str, str | None], ...] = (
    ("environment.temperature", "C"),
    ("environment.humidity", "%"),
    ("occupancy.motion", None),
    ("light.power", None),
    ("safety.gas_alarm", None),
)


def make_sequence(
    count: int = 60,
    *,
    home_id: str = "home_001",
    seed: int = 20260818,
    devices: int = 4,
    start: datetime = BASE_TIME,
    step_seconds: int = 7,
) -> list[EventEnvelope]:
    """A deterministic, varied event sequence.

    Given the same ``seed`` the values are identical on every run and machine,
    which is what lets determinism tests compare state fingerprints.
    """
    # Seeded, reproducible RNG for synthetic fixtures. A cryptographic source
    # would defeat the purpose: determinism tests compare state fingerprints
    # across runs, which requires identical values from an identical seed.
    rng = random.Random(seed)  # noqa: S311  # nosec B311
    rooms = ["living_room", "kitchen", "bedroom", "hall"]
    events: list[EventEnvelope] = []
    for index in range(count):
        capability, unit = _CAPABILITY_CYCLE[index % len(_CAPABILITY_CYCLE)]
        if capability == "environment.temperature":
            value: Any = round(rng.uniform(18, 32), 2)
        elif capability == "environment.humidity":
            value = round(rng.uniform(20, 70), 1)
        elif capability == "safety.gas_alarm":
            value = False
        else:
            value = rng.choice([True, False])
        events.append(
            make_envelope(
                capability=capability,
                value=value,
                unit=unit,
                home_id=home_id,
                device_id=f"device_{index % devices}",
                room_id=rooms[index % len(rooms)],
                occurred_at=start + timedelta(seconds=index * step_seconds),
            )
        )
    return events
