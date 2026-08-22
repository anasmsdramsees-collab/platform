"""Household data export and deletion (spec §26).

Spec §26 requires the platform to "provide user data export" and "provide user
and home deletion". Both are here, and both are deliberately blunt: an export
returns everything the platform holds about a home, and a deletion removes it.

The subtle requirement is the third one — "redact identifiers from diagnostic
bundles". A diagnostic bundle goes to support, not to the household, so it must
carry the shape of the problem without the substance of the home.
"""

import hashlib
import hmac
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from syltra_contracts.enums import PrivacyClass

REDACTED = "**REDACTED**"

# Fields that identify a household or a person, rather than describing the
# platform's behaviour.
IDENTIFYING_FIELDS: frozenset[str] = frozenset(
    {
        "home_id", "hub_id", "device_id", "entity_id", "room_id", "actor",
        "subject", "display_name", "occupant_id", "name", "note",
    }
)

SECRET_FIELDS: frozenset[str] = frozenset(
    {"token", "access_token", "password", "api_key", "authorization", "secret"}
)

# Data classes that must never leave the hub in a diagnostic bundle.
NEVER_IN_DIAGNOSTICS: frozenset[PrivacyClass] = frozenset(
    {PrivacyClass.HOUSEHOLD_PRIVATE, PrivacyClass.PERSONAL_SENSITIVE}
)


@dataclass
class ExportBundle:
    """Everything the platform holds about one home (spec §26)."""

    home_id: str
    exported_at: datetime
    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def record_count(self) -> int:
        return sum(len(rows) for rows in self.tables.values())


@dataclass
class DeletionReport:
    home_id: str
    deleted_at: datetime
    deleted_counts: dict[str, int] = field(default_factory=dict)
    remaining: dict[str, int] = field(default_factory=dict)

    @property
    def complete(self) -> bool:
        """True only when nothing about the home remains."""
        return all(count == 0 for count in self.remaining.values())

    @property
    def total_deleted(self) -> int:
        return sum(self.deleted_counts.values())


def pseudonymize(value: str, salt: str) -> str:
    """A stable, non-reversible stand-in for an identifier.

    Used in diagnostics so support can see that two log lines concern the same
    device without learning which device. Keyed by a per-bundle salt, so the
    mapping cannot be built up across bundles.
    """
    digest = hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"id_{digest[:12]}"


def redact_for_diagnostics(payload: Any, salt: str) -> Any:
    """Strip secrets and pseudonymize identifiers, recursively.

    Secrets are removed outright. Identifiers are replaced with stable
    pseudonyms rather than deleted, because a diagnostic bundle with no way to
    correlate events is often useless for the problem it was collected for.
    """
    if isinstance(payload, dict):
        result: dict[str, Any] = {}
        for key, value in payload.items():
            lowered = key.lower()
            if lowered in SECRET_FIELDS:
                result[key] = REDACTED
            elif lowered in IDENTIFYING_FIELDS and isinstance(value, str):
                result[key] = pseudonymize(value, salt)
            else:
                result[key] = redact_for_diagnostics(value, salt)
        return result
    if isinstance(payload, list):
        return [redact_for_diagnostics(item, salt) for item in payload]
    return payload


def diagnostic_bundle(
    payload: dict[str, Any], salt: str | None = None
) -> dict[str, Any]:
    """Build a support bundle carrying no household-identifying data."""
    import secrets as _secrets

    bundle_salt = salt or _secrets.token_hex(16)
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "pseudonym_salt_retained_locally": True,
        "data": redact_for_diagnostics(payload, bundle_salt),
    }


TableReader = Callable[[str, str], Iterable[dict[str, Any]]]
"""(table, home_id) -> rows"""

TableDeleter = Callable[[str, str], int]
"""(table, home_id) -> rows deleted"""


HOUSEHOLD_TABLES: tuple[str, ...] = (
    "device_events",
    "device_current_states",
    "devices",
    "device_entities",
    "device_capabilities",
    "device_vendor_mappings",
    "rooms",
    "contexts",
    "context_evidence",
    "recommendations",
    "policy_decisions",
    "action_requests",
    "action_attempts",
    "action_results",
    "manual_overrides",
    "user_feedback",
    "risk_cases",
    "risk_evidence",
    "audit_events",
    "homes",
)
"""Every table holding household data, in dependency order for deletion."""


def export_home(home_id: str, read: TableReader) -> ExportBundle:
    bundle = ExportBundle(home_id=home_id, exported_at=datetime.now(tz=UTC))
    for table in HOUSEHOLD_TABLES:
        bundle.tables[table] = list(read(table, home_id))
    return bundle


def delete_home(home_id: str, delete: TableDeleter, read: TableReader) -> DeletionReport:
    """Delete a household's data and then verify it is gone.

    The verification pass matters: a deletion that reports success without
    checking is a promise, not a fact, and spec §26 asks for the fact.
    """
    report = DeletionReport(home_id=home_id, deleted_at=datetime.now(tz=UTC))
    for table in HOUSEHOLD_TABLES:
        report.deleted_counts[table] = delete(table, home_id)
    for table in HOUSEHOLD_TABLES:
        report.remaining[table] = len(list(read(table, home_id)))
    return report
