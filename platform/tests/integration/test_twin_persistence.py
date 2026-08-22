"""Digital Twin persistence and rebuild against real PostgreSQL (spec §14.2).

These carry the Phase 2 acceptance criteria that only a real database can
prove: append-only history, idempotent storage, and deterministic rebuild.
"""

from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from syltra_digital_twin.core import TwinProjection
from syltra_digital_twin.repository import TwinRepository, rebuild_from_history
from syltra_testing import BASE_TIME, make_envelope, make_sequence


async def test_event_is_appended_and_readable(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    envelope = make_envelope(value=24.5)
    async with db_sessions() as session:
        repository = TwinRepository(session)
        assert await repository.append_event(envelope) is True
        await session.commit()

    async with db_sessions() as session:
        stored = await TwinRepository(session).read_events("home_001")
    assert len(stored) == 1
    assert stored[0].event_id == envelope.event_id
    assert stored[0].value == 24.5
    assert stored[0].capability == "environment.temperature"
    assert stored[0].occurred_at == envelope.occurred_at


async def test_duplicate_event_is_not_stored_twice(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    # The unique constraint on event_id is the persistence-level guard behind
    # safety invariant 10 — a broker redelivery cannot double-apply.
    envelope = make_envelope()
    async with db_sessions() as session:
        repository = TwinRepository(session)
        assert await repository.append_event(envelope) is True
        assert await repository.append_event(envelope) is False
        await session.commit()

    async with db_sessions() as session:
        assert await TwinRepository(session).count_events("home_001") == 1


@pytest.mark.safety
async def test_stored_events_cannot_be_modified_or_deleted(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    # Safety invariant 12: every sensitive action has an immutable audit trail.
    # Immutability is enforced by the database, not by convention.
    async with db_sessions() as session:
        await TwinRepository(session).append_event(make_envelope())
        await session.commit()

    async with db_sessions() as session:
        with pytest.raises(Exception, match="append-only"):
            await session.execute(text("UPDATE device_events SET quality = 0.1"))
        await session.rollback()

    async with db_sessions() as session:
        with pytest.raises(Exception, match="append-only"):
            await session.execute(text("DELETE FROM device_events"))
        await session.rollback()

    async with db_sessions() as session:
        assert await TwinRepository(session).count_events("home_001") == 1


async def test_current_state_is_persisted_separately_from_history(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    twin = TwinProjection()
    events = [
        make_envelope(value=21.0, occurred_at=BASE_TIME),
        make_envelope(value=22.0, occurred_at=BASE_TIME + timedelta(minutes=5)),
        make_envelope(value=23.0, occurred_at=BASE_TIME + timedelta(minutes=10)),
    ]
    async with db_sessions() as session:
        repository = TwinRepository(session)
        for event in events:
            await repository.append_event(event)
            twin.apply(event)
        await repository.upsert_current_states("home_001", twin)
        await session.commit()

    async with db_sessions() as session:
        # Three events in history, one current-state row holding only the latest.
        assert await TwinRepository(session).count_events("home_001") == 3
        rows = (
            await session.execute(
                text("SELECT capability, value, status FROM device_current_states")
            )
        ).all()
    assert len(rows) == 1
    assert rows[0].capability == "environment.temperature"
    assert rows[0].value == {"v": 23.0}


async def test_rebuild_from_history_reproduces_state(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    events = make_sequence(50)
    live = TwinProjection()
    async with db_sessions() as session:
        repository = TwinRepository(session)
        for event in events:
            await repository.append_event(event)
            live.apply(event)
        await session.commit()
    expected = live.snapshot("home_001", BASE_TIME).fingerprint()

    # A cold service starting from an empty projection must land on the same state.
    async with db_sessions() as session:
        rebuilt = await rebuild_from_history(TwinRepository(session), "home_001")
    assert rebuilt.snapshot("home_001", BASE_TIME).fingerprint() == expected


async def test_rebuild_is_stable_across_repeated_runs(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessions() as session:
        repository = TwinRepository(session)
        for event in make_sequence(40):
            await repository.append_event(event)
        await session.commit()

    fingerprints = set()
    for _ in range(3):
        async with db_sessions() as session:
            twin = await rebuild_from_history(TwinRepository(session), "home_001")
        fingerprints.add(twin.snapshot("home_001", BASE_TIME).fingerprint())
    assert len(fingerprints) == 1


async def test_replay_order_is_deterministic_for_identical_timestamps(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    # Events sharing an instant must still replay in a stable order, or a
    # rebuild could differ between runs.
    same_instant = [
        make_envelope(value=v, occurred_at=BASE_TIME, device_id=f"device_{i}")
        for i, v in enumerate([20.0, 21.0, 22.0, 23.0])
    ]
    async with db_sessions() as session:
        repository = TwinRepository(session)
        for event in same_instant:
            await repository.append_event(event)
        await session.commit()

    orders = []
    for _ in range(3):
        async with db_sessions() as session:
            stored = await TwinRepository(session).read_events("home_001")
        orders.append([str(e.event_id) for e in stored])
    assert orders[0] == orders[1] == orders[2]


async def test_homes_remain_isolated_in_storage(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessions() as session:
        repository = TwinRepository(session)
        for event in make_sequence(10, home_id="home_a", seed=1):
            await repository.append_event(event)
        for event in make_sequence(6, home_id="home_b", seed=2):
            await repository.append_event(event)
        await session.commit()

    async with db_sessions() as session:
        repository = TwinRepository(session)
        assert await repository.count_events("home_a") == 10
        assert await repository.count_events("home_b") == 6
        home_a_events = await repository.read_events("home_a")
    assert {e.home_id for e in home_a_events} == {"home_a"}


async def test_checkpoint_records_progress_and_fingerprint(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    twin = TwinProjection()
    events = make_sequence(12)
    async with db_sessions() as session:
        repository = TwinRepository(session)
        for event in events:
            await repository.append_event(event)
            twin.apply(event)
        snapshot = twin.snapshot("home_001", BASE_TIME)
        await repository.save_checkpoint(
            "home_001", snapshot.events_applied, snapshot.fingerprint()
        )
        await session.commit()

    async with db_sessions() as session:
        checkpoint = await TwinRepository(session).get_checkpoint("home_001")
    assert checkpoint is not None
    assert checkpoint.events_applied == len(events)
    assert checkpoint.fingerprint == twin.snapshot("home_001", BASE_TIME).fingerprint()


async def test_checkpoint_upsert_is_idempotent(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessions() as session:
        repository = TwinRepository(session)
        await repository.save_checkpoint("home_001", 1, "abc")
        await repository.save_checkpoint("home_001", 2, "def")
        await session.commit()

    async with db_sessions() as session:
        checkpoint = await TwinRepository(session).get_checkpoint("home_001")
    assert checkpoint is not None
    assert checkpoint.events_applied == 2
