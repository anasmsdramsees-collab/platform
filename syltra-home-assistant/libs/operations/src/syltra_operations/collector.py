"""Household data collection for backup and export (spec §22 Phase 8, §26).

Reads every table holding household data. The two callers want the same rows for
different reasons — a backup encrypts them, an export hands them to the
household — so they share one collector rather than drifting apart.

Two properties matter more than speed:

- **Completeness.** A backup that silently omits a table is worse than no
  backup, because it will be discovered during a restore. The collector works
  from `HOUSEHOLD_TABLES` and fails loudly on a table it cannot read.
- **Scoping.** Every query is filtered to one home. A backup of one household
  must never contain another's data, even on a hub that serves several.
"""

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from syltra_operations.privacy import HOUSEHOLD_TABLES

logger = logging.getLogger(__name__)


class CollectionError(RuntimeError):
    """A household table could not be read.

    Raised rather than skipped: a backup missing a table is a backup that will
    fail when someone needs it.
    """


class Rows(Protocol):
    """The slice of a database cursor the collector needs."""

    def keys(self) -> Sequence[str]: ...

    def fetchall(self) -> Sequence[Sequence[Any]]: ...


class Connection(Protocol):
    def execute(self, statement: str, parameters: dict[str, Any]) -> Rows: ...


# How each table is scoped to a home. Most carry `home_id` directly; the rest
# are reached through the home they belong to, and are listed explicitly so a
# new table cannot be added without deciding how it is scoped.
_HOME_COLUMN: dict[str, str] = {
    "homes": "home_id",
    "rooms": "__via_home_uuid__",
    "devices": "__via_home_uuid__",
    "device_entities": "__via_device__",
    "device_capabilities": "__via_device__",
    "device_vendor_mappings": "__via_device__",
    "device_current_states": "__via_home_uuid__",
    "device_events": "home_id",
    "contexts": "home_id",
    "context_evidence": "__via_context__",
    "recommendations": "home_id",
    "policy_decisions": "home_id",
    "action_requests": "home_id",
    "action_attempts": "__via_action__",
    "action_results": "home_id",
    "manual_overrides": "home_id",
    "user_feedback": "home_id",
    "risk_cases": "home_id",
    "risk_evidence": "__via_risk_case__",
    "audit_events": "home_id",
}

_INDIRECT_SQL: dict[str, str] = {
    "__via_home_uuid__": (
        "SELECT t.* FROM {table} t "
        "JOIN homes h ON h.id = t.home_uuid WHERE h.home_id = :home_id"
    ),
    "__via_device__": (
        "SELECT t.* FROM {table} t "
        "JOIN devices d ON d.id = t.device_uuid "
        "JOIN homes h ON h.id = d.home_uuid WHERE h.home_id = :home_id"
    ),
    "__via_context__": (
        "SELECT t.* FROM {table} t "
        "JOIN contexts c ON c.context_id = t.context_id WHERE c.home_id = :home_id"
    ),
    "__via_action__": (
        "SELECT t.* FROM {table} t "
        "JOIN action_requests a ON a.action_id = t.action_id WHERE a.home_id = :home_id"
    ),
    "__via_risk_case__": (
        "SELECT t.* FROM {table} t "
        "JOIN risk_cases r ON r.case_id = t.case_id WHERE r.home_id = :home_id"
    ),
}


_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


def _assert_identifier(name: str) -> None:
    """Refuse anything that is not a plain lowercase SQL identifier."""
    if not _IDENTIFIER.match(name):
        msg = f"{name!r} is not a valid SQL identifier"
        raise CollectionError(msg)


def _json_safe(value: Any) -> Any:
    """Convert a database value to something JSON can carry losslessly."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def table_query(table: str) -> str:
    """The scoped SELECT for one household table.

    Table and column names cannot be bound as parameters, so they are
    interpolated. Two things make that safe, and neither relies on the caller:

    1. ``table`` must be a **key of `_HOME_COLUMN`** — a module constant. A name
       that is not already in that dictionary raises before any SQL is built.
    2. The name and the resolved column are re-checked against a strict
       identifier pattern immediately before interpolation, so even a future
       edit that added a hostile-looking key to the constant could not produce
       injectable SQL.

    The home id itself is always a bound parameter, never interpolated.
    """
    column = _HOME_COLUMN.get(table)
    if column is None:
        msg = (
            f"{table} has no declared home scoping; add it to _HOME_COLUMN so a "
            "backup cannot silently omit or over-collect it"
        )
        raise CollectionError(msg)

    if column.startswith("__via_"):
        _assert_identifier(table)
        return _INDIRECT_SQL[column].format(table=table)

    _assert_identifier(table)
    _assert_identifier(column)
    # Both names are allowlist-derived and identifier-checked above; the only
    # caller-supplied value (home_id) is a bound parameter.
    return f"SELECT * FROM {table} WHERE {column} = :home_id"  # noqa: S608  # nosec B608


def read_table(connection: Connection, table: str, home_id: str) -> list[dict[str, Any]]:
    """Read one table, scoped to one home."""
    try:
        result = connection.execute(table_query(table), {"home_id": home_id})
        columns = list(result.keys())
        return [
            {column: _json_safe(value) for column, value in zip(columns, row, strict=True)}
            for row in result.fetchall()
        ]
    except CollectionError:
        raise
    except Exception as exc:
        msg = f"could not read {table} for {home_id}: {type(exc).__name__}"
        raise CollectionError(msg) from exc


@dataclass
class CollectionResult:
    home_id: str
    collected_at: datetime
    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return sum(len(rows) for rows in self.tables.values())

    def as_payload(self) -> dict[str, Any]:
        return {
            "schema": "syltra-household-v1",
            "home_id": self.home_id,
            "collected_at": self.collected_at.isoformat(),
            **self.tables,
        }


def collect_home(connection: Connection, home_id: str) -> CollectionResult:
    """Read every household table for one home.

    Every table in `HOUSEHOLD_TABLES` is attempted; a failure raises rather than
    producing a quietly partial backup.
    """
    result = CollectionResult(home_id=home_id, collected_at=datetime.now(tz=UTC))
    for table in HOUSEHOLD_TABLES:
        rows = read_table(connection, table, home_id)
        result.tables[table] = rows
        logger.debug("collected %d rows from %s", len(rows), table)

    missing = set(HOUSEHOLD_TABLES) - set(result.tables)
    if missing:  # pragma: no cover - defensive; the loop covers every table
        msg = f"collection incomplete: {sorted(missing)}"
        raise CollectionError(msg)
    return result


def declared_tables() -> tuple[str, ...]:
    """Tables the collector knows how to scope — asserted against
    `HOUSEHOLD_TABLES` by a test, so the two cannot drift apart."""
    return tuple(_HOME_COLUMN)
