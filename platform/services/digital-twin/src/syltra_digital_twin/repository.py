"""Persistence for the twin (spec §13.1).

Two separate concerns, deliberately:

- ``device_events`` is the append-only history. Writes are idempotent via the
  unique constraint on ``event_id`` — a redelivered event is skipped, not
  duplicated, which is how safety invariant 10 survives a broker retry.
- ``device_current_states`` is the current-value projection, upserted per
  device capability, kept strictly separate from history.

Replay reads history back in ``occurred_at`` order so the twin can rebuild
deterministically after a reset or restart.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from syltra_contracts import EventEnvelope, EventSource, EventSubject
from syltra_digital_twin.core import TwinProjection
from syltra_digital_twin.models import (
    Device,
    DeviceCurrentState,
    DeviceEvent,
    Home,
    Room,
    TwinCheckpoint,
)


class TwinRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── append-only history ──

    async def append_event(self, envelope: EventEnvelope) -> bool:
        """Store an event. Returns False if it was already stored (idempotent)."""
        statement = (
            insert(DeviceEvent)
            .values(
                event_id=envelope.event_id,
                event_type=envelope.event_type,
                schema_version=envelope.schema_version,
                home_id=envelope.home_id,
                device_id=envelope.subject.device_id,
                entity_id=envelope.subject.entity_id,
                room_id=envelope.subject.room_id,
                capability=envelope.capability,
                value={"v": envelope.value},
                unit=envelope.unit,
                quality=envelope.quality,
                privacy_class=str(envelope.privacy_class),
                correlation_id=envelope.correlation_id,
                causation_id=envelope.causation_id,
                occurred_at=envelope.occurred_at,
                received_at=envelope.received_at,
                event_metadata=dict(envelope.metadata),
            )
            .on_conflict_do_nothing(index_elements=[DeviceEvent.event_id])
            .returning(DeviceEvent.id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def read_events(
        self, home_id: str, limit: int | None = None
    ) -> list[EventEnvelope]:
        """Replay stored history in deterministic order.

        Ordered by ``(occurred_at, event_id)`` so the sequence is stable even
        when two events share a timestamp — without the tiebreak, a rebuild
        could differ between runs.
        """
        statement = (
            select(DeviceEvent)
            .where(DeviceEvent.home_id == home_id)
            .order_by(DeviceEvent.occurred_at, DeviceEvent.event_id)
        )
        if limit is not None:
            statement = statement.limit(limit)
        rows = (await self._session.execute(statement)).scalars().all()
        return [_to_envelope(row) for row in rows]

    async def count_events(self, home_id: str) -> int:
        statement = select(DeviceEvent).where(DeviceEvent.home_id == home_id)
        return len((await self._session.execute(statement)).scalars().all())

    # ── current state projection ──

    async def upsert_current_states(self, home_id: str, twin: TwinProjection) -> int:
        """Persist the twin's current state for one home. Returns rows written."""
        home_state = twin.home(home_id)
        if home_state is None:
            return 0
        home = await self._ensure_home(home_id)
        now = datetime.now(tz=UTC)
        written = 0
        for device_id, device_state in home_state.devices.items():
            device = await self._ensure_device(home, device_id, device_state.room_id)
            device.available = device_state.available
            device.last_seen_at = device_state.last_seen
            if device_state.name:
                device.name = device_state.name
            for capability, state in device_state.capabilities.items():
                statement = (
                    insert(DeviceCurrentState)
                    .values(
                        home_uuid=home.id,
                        device_uuid=device.id,
                        capability=capability,
                        value={"v": state.value},
                        unit=state.unit,
                        quality=state.quality,
                        status=state.status_at(now).value,
                        occurred_at=state.occurred_at,
                        received_at=state.received_at,
                        last_event_id=UUID(state.last_event_id)
                        if state.last_event_id
                        else None,
                    )
                    .on_conflict_do_update(
                        index_elements=[
                            DeviceCurrentState.device_uuid,
                            DeviceCurrentState.capability,
                        ],
                        set_={
                            "value": {"v": state.value},
                            "unit": state.unit,
                            "quality": state.quality,
                            "status": state.status_at(now).value,
                            "occurred_at": state.occurred_at,
                            "received_at": state.received_at,
                            "last_event_id": UUID(state.last_event_id)
                            if state.last_event_id
                            else None,
                        },
                    )
                )
                await self._session.execute(statement)
                written += 1
        return written

    async def save_checkpoint(
        self, home_id: str, events_applied: int, fingerprint: str, sequence: int = 0
    ) -> None:
        statement = (
            insert(TwinCheckpoint)
            .values(
                home_id=home_id,
                stream_sequence=sequence,
                events_applied=events_applied,
                fingerprint=fingerprint,
                updated_at=datetime.now(tz=UTC),
            )
            .on_conflict_do_update(
                index_elements=[TwinCheckpoint.home_id],
                set_={
                    "stream_sequence": sequence,
                    "events_applied": events_applied,
                    "fingerprint": fingerprint,
                    "updated_at": datetime.now(tz=UTC),
                },
            )
        )
        await self._session.execute(statement)

    async def get_checkpoint(self, home_id: str) -> TwinCheckpoint | None:
        statement = select(TwinCheckpoint).where(TwinCheckpoint.home_id == home_id)
        return (await self._session.execute(statement)).scalar_one_or_none()

    # ── helpers ──

    async def _ensure_home(self, home_id: str) -> Home:
        statement = select(Home).where(Home.home_id == home_id)
        home = (await self._session.execute(statement)).scalar_one_or_none()
        if home is None:
            home = Home(home_id=home_id, created_at=datetime.now(tz=UTC))
            self._session.add(home)
            await self._session.flush()
        return home

    async def _ensure_room(self, home: Home, room_id: str) -> Room:
        statement = select(Room).where(Room.home_uuid == home.id, Room.room_id == room_id)
        room = (await self._session.execute(statement)).scalar_one_or_none()
        if room is None:
            room = Room(home_uuid=home.id, room_id=room_id, name=room_id)
            self._session.add(room)
            await self._session.flush()
        return room

    async def _ensure_device(
        self, home: Home, device_id: str, room_id: str | None
    ) -> Device:
        statement = select(Device).where(
            Device.home_uuid == home.id, Device.device_id == device_id
        )
        device = (await self._session.execute(statement)).scalar_one_or_none()
        if device is None:
            device = Device(home_uuid=home.id, device_id=device_id)
            self._session.add(device)
            await self._session.flush()
        if room_id:
            room = await self._ensure_room(home, room_id)
            device.room_uuid = room.id
        return device


def _to_envelope(row: DeviceEvent) -> EventEnvelope:
    """Reconstruct a contract envelope from stored history."""
    value: Any = row.value.get("v") if isinstance(row.value, dict) else None
    return EventEnvelope(
        event_id=row.event_id,
        event_type=row.event_type,
        schema_version=row.schema_version,
        occurred_at=row.occurred_at,
        received_at=row.received_at,
        home_id=row.home_id,
        correlation_id=row.correlation_id or row.event_id,
        causation_id=row.causation_id,
        source=EventSource(service="digital-twin", instance_id="replay", protocol="database"),
        subject=EventSubject(
            device_id=row.device_id, entity_id=row.entity_id, room_id=row.room_id
        ),
        capability=row.capability,
        value=value,
        unit=row.unit,
        quality=row.quality,
        privacy_class=row.privacy_class,
        metadata=dict(row.event_metadata or {}),
    )


async def rebuild_from_history(
    repository: TwinRepository, home_id: str, into: TwinProjection | None = None
) -> TwinProjection:
    """Rebuild a twin purely from stored events (spec §14.2 acceptance)."""
    twin = into or TwinProjection()
    twin.reset()
    events: Sequence[EventEnvelope] = await repository.read_events(home_id)
    twin.apply_all(list(events))
    return twin
