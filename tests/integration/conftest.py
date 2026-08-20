"""Integration test fixtures requiring real infrastructure.

Tests that need PostgreSQL or NATS skip cleanly when the development stack is
not running, so `make test` stays useful on a machine without Docker while
`make test-integration` exercises the real thing.

Credentials come from the environment only (spec §0 rule 8, §25.3). There are
deliberately no literal password fallbacks here: a default password in a
checked-in file is still a password in the repository, and it would also let a
misconfigured run connect somewhere unintended instead of failing loudly.
"""

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _required_secret(name: str) -> str:
    """Read a credential from the environment, or skip with a clear reason."""
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"{name} is not set; source your .env or run 'make up' first")
    return value


def database_url() -> str:
    user = os.environ.get("POSTGRES_USER", "syltra")
    password = _required_secret("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    database = os.environ.get("POSTGRES_DB", "syltra")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


def nats_url() -> str:
    return os.environ.get("NATS_URL", "nats://localhost:4222")


@pytest_asyncio.fixture
async def nats_connection() -> AsyncIterator[object]:
    """A live NATS connection, or a clean skip when the stack is not running."""
    import contextlib

    import nats

    try:
        nc = await nats.connect(
            nats_url(),
            user=os.environ.get("NATS_USER", "syltra"),
            password=_required_secret("NATS_PASSWORD"),
            connect_timeout=3,
            allow_reconnect=False,
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"NATS unavailable ({exc.__class__.__name__}); run 'make up'")
    try:
        yield nc
    finally:
        with contextlib.suppress(Exception):
            await nc.close()


@pytest_asyncio.fixture
async def db_sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Session factory against the development database.

    Truncates the tables this suite owns before each test so runs are
    independent. `device_events` and `audit_events` are append-only, so
    TRUNCATE (which bypasses row triggers) is the only legitimate reset —
    and it is confined to the development database.
    """
    from sqlalchemy import text

    engine = create_async_engine(database_url())
    try:
        async with engine.begin() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - environment dependent
        await engine.dispose()
        pytest.skip(f"PostgreSQL unavailable ({exc.__class__.__name__}); run 'make up'")

    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE device_events, device_current_states, device_capabilities, "
                "device_vendor_mappings, device_entities, devices, room_relationships, "
                "rooms, twin_checkpoints, hubs, homes, audit_events, "
                "system_health_events RESTART IDENTITY CASCADE"
            )
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()
