"""Backup round-trip against a real database (Phase 8 acceptance).

Spec §22 Phase 8: "database backup and restore pass". A backup that has only
been tested against a dictionary has not been tested — the failures that matter
(a table the collector does not know how to scope, a type JSON cannot carry, a
join that silently returns nothing) only appear against a real schema.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from syltra_operations import (
    HOUSEHOLD_TABLES,
    CollectionError,
    collect_home,
    create_backup,
    declared_tables,
    read_manifest,
    restore_backup,
    table_query,
)

from tests.integration.conftest import database_url

PASSPHRASE = "pilot-hub-restore-passphrase"
HOME = "home_backup_test"
OTHER_HOME = "home_backup_other"


class Session:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def execute(self, statement: str, parameters: dict[str, Any]) -> Any:
        return self._connection.execute(text(statement), parameters)


@pytest.fixture
def engine() -> Any:
    """A live database, or a skip with an accurate reason.

    Only a connection failure skips. A missing driver is a broken environment,
    not absent infrastructure, and must fail loudly — a skip for the wrong
    reason looks green while proving nothing.
    """
    from sqlalchemy.exc import OperationalError

    url = database_url().replace("postgresql+asyncpg", "postgresql+psycopg2")
    created = create_engine(url)  # ModuleNotFoundError here is a real failure
    try:
        with created.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"PostgreSQL not reachable ({type(exc).__name__}); run 'make up'")
    return created


@pytest.fixture
def seeded(engine: Any) -> Any:
    """Insert synthetic household data for two homes, then clean up."""
    now = datetime.now(tz=UTC)
    with engine.begin() as connection:
        for home in (HOME, OTHER_HOME):
            connection.execute(
                text(
                    "INSERT INTO homes (id, home_id, name, timezone, created_at) "
                    "VALUES (:id, :home_id, :name, 'UTC', :now)"
                ),
                {"id": uuid4(), "home_id": home, "name": f"{home} residence", "now": now},
            )
            connection.execute(
                text(
                    "INSERT INTO device_events (id, event_id, event_type, schema_version, "
                    "home_id, capability, quality, privacy_class, occurred_at, received_at, "
                    "event_metadata) VALUES (:id, :event_id, 'device.state.changed', '1.0', "
                    ":home_id, 'occupancy.motion', 1.0, 'HOUSEHOLD_PRIVATE', :now, :now, '{}')"
                ),
                {"id": uuid4(), "event_id": uuid4(), "home_id": home, "now": now},
            )
            connection.execute(
                text(
                    "INSERT INTO policy_decisions (id, decision_id, home_id, decision, "
                    "safety_class, policy_version, input_hash, reason_codes, evidence, "
                    "evaluated_at, expires_at) VALUES (:id, :decision_id, :home_id, 'DENY', "
                    "'COMFORT', '1.0.0', :hash, '[\"CONFIDENCE_BELOW_THRESHOLD\"]', '{}', "
                    ":now, :later)"
                ),
                {
                    "id": uuid4(),
                    "decision_id": uuid4(),
                    "home_id": home,
                    "hash": "a" * 64,
                    "now": now,
                    "later": now + timedelta(minutes=15),
                },
            )
    yield engine
    with engine.begin() as connection:
        for table in ("policy_decisions", "device_events", "homes"):
            connection.execute(text(f"TRUNCATE {table} CASCADE"))


# ── the collector knows the schema ──


def test_the_collector_covers_every_household_table() -> None:
    # If a table is added to HOUSEHOLD_TABLES without declaring how it is
    # scoped, a backup would silently omit it.
    assert set(declared_tables()) == set(HOUSEHOLD_TABLES)


def test_every_declared_query_runs_against_the_real_schema(engine: Any) -> None:
    # The failure this catches: a column renamed in a migration, or a join that
    # no longer matches. A dictionary-based test cannot see either.
    with engine.connect() as connection:
        for table in HOUSEHOLD_TABLES:
            connection.execute(text(table_query(table)), {"home_id": "nobody"})


def test_an_undeclared_table_is_refused() -> None:
    with pytest.raises(CollectionError, match="no declared home scoping"):
        table_query("some_future_table")


# ── collection ──


def test_collection_reads_real_rows(seeded: Any) -> None:
    with seeded.connect() as connection:
        result = collect_home(Session(connection), HOME)
    assert result.row_count >= 3
    assert len(result.tables) == len(HOUSEHOLD_TABLES)
    assert result.tables["homes"][0]["home_id"] == HOME
    assert result.tables["device_events"][0]["capability"] == "occupancy.motion"


@pytest.mark.safety
def test_collection_never_crosses_households(seeded: Any) -> None:
    # A hub may serve several homes; one household's backup must never contain
    # another's data.
    with seeded.connect() as connection:
        collected = collect_home(Session(connection), HOME)
    serialized = str(collected.as_payload())
    assert OTHER_HOME not in serialized
    assert f"{OTHER_HOME} residence" not in serialized


def test_collection_converts_types_json_can_carry(seeded: Any) -> None:
    # UUIDs and timestamps must survive the JSON round trip, or a restore
    # produces subtly different data.
    with seeded.connect() as connection:
        result = collect_home(Session(connection), HOME)
    row = result.tables["device_events"][0]
    assert isinstance(row["event_id"], str)
    assert isinstance(row["occurred_at"], str)
    datetime.fromisoformat(row["occurred_at"])  # parses


# ── the full round trip ──


def test_a_real_backup_restores_the_household(seeded: Any, tmp_path: Path) -> None:
    with seeded.connect() as connection:
        collected = collect_home(Session(connection), HOME)
    payload = collected.as_payload()

    destination = tmp_path / "hub.syltrabk"
    manifest = create_backup(payload, PASSPHRASE, destination, home_id=HOME)

    restored, restored_manifest = restore_backup(destination, PASSPHRASE)
    assert restored == payload
    assert restored_manifest.payload_sha256 == manifest.payload_sha256
    assert restored["homes"][0]["home_id"] == HOME
    assert restored["policy_decisions"][0]["decision"] == "DENY"


@pytest.mark.safety
def test_a_real_backup_holds_no_readable_household_data(seeded: Any, tmp_path: Path) -> None:
    with seeded.connect() as connection:
        payload = collect_home(Session(connection), HOME).as_payload()

    destination = tmp_path / "hub.syltrabk"
    create_backup(payload, PASSPHRASE, destination, home_id=HOME)

    raw = destination.read_bytes()
    for household in (b"occupancy.motion", b"residence", b"CONFIDENCE_BELOW_THRESHOLD"):
        assert household not in raw, f"{household!r} is readable in the backup"


def test_the_manifest_reports_what_was_collected(seeded: Any, tmp_path: Path) -> None:
    with seeded.connect() as connection:
        payload = collect_home(Session(connection), HOME).as_payload()

    destination = tmp_path / "hub.syltrabk"
    create_backup(payload, PASSPHRASE, destination, home_id=HOME, hub_id="hub_1")

    manifest = read_manifest(destination)
    assert manifest.home_id == HOME
    assert manifest.table_counts["device_events"] == 1
    assert manifest.table_counts["policy_decisions"] == 1
    # Row counts are metadata; the values themselves are not in the manifest.
    assert "occupancy.motion" not in str(manifest)


def test_an_empty_home_still_produces_a_valid_backup(engine: Any, tmp_path: Path) -> None:
    # A hub commissioned yesterday has almost no data. That must back up and
    # restore cleanly rather than producing an edge case at the worst moment.
    with engine.connect() as connection:
        payload = collect_home(Session(connection), "home_that_does_not_exist").as_payload()

    destination = tmp_path / "empty.syltrabk"
    create_backup(payload, PASSPHRASE, destination, home_id="home_that_does_not_exist")
    restored, _ = restore_backup(destination, PASSPHRASE)
    assert restored == payload
    assert all(rows == [] for rows in restored.values() if isinstance(rows, list))
