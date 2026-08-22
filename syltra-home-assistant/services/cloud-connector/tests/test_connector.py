"""The connector's job is to refuse (spec §14.11, §26).

Every test here is a gate holding. A cloud connector that exports correctly and
refuses nothing is the component this platform spent its whole build promising
not to have.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from syltra_cloud_connector import CloudConnector, Destination, ExportRefused

NOW = datetime(2026, 8, 20, 19, 42, 17, tzinfo=UTC)
HOME = "home_cloud"

INSTALLER = Destination(
    name="installer-diagnostics",
    purpose="Diagnosing a fault the installer was called about",
    allowed_fields=frozenset({"device_id", "capability", "status", "occurred_at"}),
    pseudonymise=frozenset({"device_id"}),
)


def connector() -> CloudConnector:
    c = CloudConnector()
    c.register_destination(INSTALLER)
    return c


def consented() -> CloudConnector:
    c = connector()
    c.enable(HOME, actor="amal", reason="installer is diagnosing the hub", now=NOW)
    c.grant_consent(HOME, INSTALLER.name, actor="amal", now=NOW)
    return c


def reading() -> dict[str, Any]:
    return {
        "device_id": "gas_kitchen",
        "capability": "safety.gas_alarm",
        "status": "KNOWN",
        "occurred_at": NOW,
        # None of these are allowed. They are here because this is exactly the
        # payload somebody would pass by accident.
        "room_id": "kitchen",
        "value": True,
        "resident": "amal",
    }


# ── gate 1: off, and off by default ──


def test_a_new_connector_exports_nothing_for_anybody() -> None:
    """§0 rule 4's cheapest proof: the thing is off."""
    c = connector()
    assert not c.is_enabled(HOME)
    with pytest.raises(ExportRefused, match="CLOUD_EXPORT_DISABLED"):
        c.record(HOME, INSTALLER.name, reading(), now=NOW)


def test_enabling_it_must_say_why() -> None:
    c = connector()
    with pytest.raises(ExportRefused, match="REASON_REQUIRED"):
        c.enable(HOME, actor="amal", reason="  ", now=NOW)


def test_disabling_drops_what_was_waiting() -> None:
    """Off means off, not "off until somebody turns it back on"."""
    c = consented()
    c.record(HOME, INSTALLER.name, reading(), now=NOW)
    assert c.pending(HOME, INSTALLER.name) == 1

    c.disable(HOME, actor="amal", reason="installer has finished", now=NOW)
    assert c.pending(HOME, INSTALLER.name) == 0


# ── gate 2: consent, per destination ──


def test_enabled_is_not_consented() -> None:
    """Turning the connector on is not agreeing to send anywhere in particular."""
    c = connector()
    c.enable(HOME, actor="amal", reason="installer visit", now=NOW)
    with pytest.raises(ExportRefused, match="NO_CONSENT"):
        c.record(HOME, INSTALLER.name, reading(), now=NOW)


def test_consent_to_one_destination_is_not_consent_to_another() -> None:
    manufacturer = Destination(
        name="manufacturer-telemetry",
        purpose="Product improvement",
        allowed_fields=frozenset({"capability"}),
    )
    c = consented()
    c.register_destination(manufacturer)
    with pytest.raises(ExportRefused, match="NO_CONSENT"):
        c.record(HOME, manufacturer.name, reading(), now=NOW)


def test_withdrawal_takes_effect_now_and_empties_the_queue() -> None:
    """Not "stop after the backlog clears"."""
    c = consented()
    c.record(HOME, INSTALLER.name, reading(), now=NOW)

    c.withdraw_consent(HOME, INSTALLER.name, actor="amal", now=NOW + timedelta(minutes=1))

    assert c.pending(HOME, INSTALLER.name) == 0
    with pytest.raises(ExportRefused, match="NO_CONSENT"):
        c.record(HOME, INSTALLER.name, reading(), now=NOW + timedelta(minutes=2))


def test_an_unknown_destination_is_refused_rather_than_created() -> None:
    c = consented()
    with pytest.raises(ExportRefused, match="UNKNOWN_DESTINATION"):
        c.record(HOME, "somewhere-else", reading(), now=NOW)


# ── gate 3: the allowlist ──


def test_only_allowlisted_fields_leave() -> None:
    """An allowlist omits the field somebody added last week; a denylist
    exports it."""
    exported = consented().record(HOME, INSTALLER.name, reading(), now=NOW)
    assert set(exported) <= INSTALLER.allowed_fields
    for leaked in ("room_id", "value", "resident"):
        assert leaked not in exported


def test_a_destination_allowing_nothing_is_refused_at_construction() -> None:
    with pytest.raises(ValueError, match="allows no fields"):
        Destination(name="empty", purpose="none", allowed_fields=frozenset())


def test_pseudonymising_a_field_that_cannot_leave_is_refused() -> None:
    """Usually a sign somebody expected the field to be allowed."""
    with pytest.raises(ValueError, match="pseudonymised but not allowed"):
        Destination(
            name="confused",
            purpose="diagnostics",
            allowed_fields=frozenset({"capability"}),
            pseudonymise=frozenset({"device_id"}),
        )


# ── gate 4: redaction ──


def test_a_device_becomes_a_pseudonym_that_is_stable_within_the_hub() -> None:
    c = consented()
    first = c.record(HOME, INSTALLER.name, reading(), now=NOW)
    second = c.record(HOME, INSTALLER.name, reading(), now=NOW)
    assert first["device_id"].startswith("anon_")
    assert "gas_kitchen" not in first["device_id"]
    # Stable, or a diagnostic cannot correlate two records from one device.
    assert first["device_id"] == second["device_id"]


def test_two_hubs_do_not_produce_the_same_pseudonym() -> None:
    """The salt never leaves, so nothing downstream can join across houses."""
    a, b = connector(), connector()
    b.salt = "another-hub"
    for c in (a, b):
        c.enable(HOME, actor="amal", reason="visit", now=NOW)
        c.grant_consent(HOME, INSTALLER.name, actor="amal", now=NOW)
    assert (
        a.record(HOME, INSTALLER.name, reading(), now=NOW)["device_id"]
        != b.record(HOME, INSTALLER.name, reading(), now=NOW)["device_id"]
    )


def test_a_timestamp_is_rounded_to_the_hour() -> None:
    """An exact time is a movement record. The hour is enough to diagnose."""
    exported = consented().record(HOME, INSTALLER.name, reading(), now=NOW)
    assert exported["occurred_at"].endswith("19:00:00+00:00")


# ── the boundary: bounded, and never in the way ──


def test_a_full_queue_drops_rather_than_grows() -> None:
    c = consented()
    c.queue_limit = 5
    for _ in range(50):
        c.record(HOME, INSTALLER.name, reading(), now=NOW)
    assert c.pending(HOME, INSTALLER.name) == 5


def test_draining_hands_over_and_empties() -> None:
    c = consented()
    c.record(HOME, INSTALLER.name, reading(), now=NOW)
    assert len(c.drain(HOME, INSTALLER.name)) == 1
    assert c.pending(HOME, INSTALLER.name) == 0
    assert c.drain(HOME, INSTALLER.name) == []


def test_nothing_here_can_reach_a_device_or_a_network() -> None:
    """The module plans an export; delivering one is somebody else's job.

    Checked on the parsed tree rather than the text, because this module's own
    docstring discusses uplinks and a substring search would report the
    explanation as the offence.
    """
    import ast
    import inspect

    from syltra_cloud_connector import connector as module

    tree = ast.parse(inspect.getsource(module))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    for forbidden in ("socket", "http", "httpx", "requests", "urllib", "nats", "aiohttp"):
        assert not any(name.startswith(forbidden) for name in imported), forbidden


# ── every change is on the record ──


def test_enabling_consenting_and_withdrawing_are_all_audited() -> None:
    c = consented()
    c.withdraw_consent(HOME, INSTALLER.name, actor="amal", now=NOW)
    actions = [entry["action"] for entry in c.audit]
    assert actions == [
        "CLOUD_EXPORT_ENABLED",
        "CLOUD_CONSENT_GRANTED",
        "CLOUD_CONSENT_WITHDRAWN",
    ]
