"""Pilot operations tests (spec §22 Phase 8, §26).

Three Phase 8 acceptance criteria live here: database backup and restore pass,
the platform recovers after service restart, and household deletion actually
deletes.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from syltra_operations import (
    HOUSEHOLD_TABLES,
    BackupError,
    BackupIntegrityError,
    ServiceState,
    SupervisedService,
    Watchdog,
    create_backup,
    delete_home,
    diagnostic_bundle,
    export_home,
    looks_encrypted,
    pseudonymize,
    read_manifest,
    redact_for_diagnostics,
    restore_backup,
)
from syltra_operations.backup import MAGIC

PASSPHRASE = "correct-horse-battery-staple"
NOW = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)


def household_payload() -> dict[str, Any]:
    """Synthetic household data (spec §26: synthetic only)."""
    return {
        "homes": [{"home_id": "home_001", "name": "Al Noor residence"}],
        "device_events": [
            {"capability": "occupancy.motion", "value": True, "room_id": "bedroom"},
            {"capability": "environment.temperature", "value": 27.4},
        ],
        "user_feedback": [{"kind": "REJECT", "actor": "occupant"}],
    }


# ── backup and restore ──


def test_a_backup_round_trips_exactly(tmp_path: Path) -> None:
    payload = household_payload()
    destination = tmp_path / "hub.syltrabk"
    manifest = create_backup(payload, PASSPHRASE, destination, home_id="home_001")

    restored, restored_manifest = restore_backup(destination, PASSPHRASE)
    assert restored == payload
    assert restored_manifest.payload_sha256 == manifest.payload_sha256
    assert restored_manifest.home_id == "home_001"


# The manifest keys `backup info` is allowed to read without a passphrase.
# An exact set, not a substring scan: this fails when a *new* field appears,
# which is how household data would actually get into the manifest.
MANIFEST_KEYS = {
    "created_at",
    "format",
    "home_id",
    "hub_id",
    "payload_sha256",
    "schema_version",
    "table_counts",
}


def _split_backup(destination: Path) -> tuple[dict[str, Any], bytes]:
    """The readable manifest and the encrypted body, separately."""
    body = destination.read_bytes()
    length = int.from_bytes(body[len(MAGIC) : len(MAGIC) + 4], "big")
    manifest = json.loads(body[len(MAGIC) + 4 : len(MAGIC) + 4 + length])
    return manifest, body[len(MAGIC) + 4 + length :]


@pytest.mark.safety
def test_household_data_never_reaches_disk_in_the_clear(tmp_path: Path) -> None:
    # A hub backup contains when people are home, when they sleep, which rooms
    # they use. There is no plaintext branch in create_backup, and this proves
    # it at the byte level.
    #
    # The ciphertext is scanned, not the whole file. The manifest is readable by
    # design — `backup info` reads it without a passphrase — so scanning the
    # file as one blob conflates two different guarantees, and did so badly:
    # `created_at` is an ISO timestamp, and roughly one run in six hundred puts
    # `27.4` in its seconds field, which a search for the household temperature
    # reported as a leak. The encryption was never at fault; the canary was.
    destination = tmp_path / "hub.syltrabk"
    create_backup(household_payload(), PASSPHRASE, destination, home_id="home_001")

    _, ciphertext = _split_backup(destination)
    for secret in (b"Al Noor residence", b"occupancy.motion", b"bedroom", b"27.4"):
        assert secret not in ciphertext, f"{secret!r} is readable in the backup body"
    assert looks_encrypted(destination)


def test_the_readable_manifest_carries_no_household_data(tmp_path: Path) -> None:
    # The other half of the guarantee, and the one a substring scan could not
    # give: the manifest's shape is fixed, so anything household-specific
    # arriving in it shows up as a new key rather than as a string someone
    # thought to search for.
    destination = tmp_path / "hub.syltrabk"
    create_backup(household_payload(), PASSPHRASE, destination, home_id="home_001")

    manifest, _ = _split_backup(destination)
    assert set(manifest) == MANIFEST_KEYS, "an unreviewed field reached the readable manifest"
    # Identifiers, never names or readings.
    assert manifest["home_id"] == "home_001"
    assert "Al Noor" not in json.dumps(manifest)
    # Row counts are metadata; the rows themselves are not.
    assert set(manifest["table_counts"]) == {"device_events", "homes", "user_feedback"}
    assert all(isinstance(count, int) for count in manifest["table_counts"].values())


def test_two_backups_of_the_same_data_are_not_byte_identical(tmp_path: Path) -> None:
    # A fresh nonce every time. Without it, an observer who saw two backups
    # could tell whether anything changed between them — and identical
    # ciphertext would mean the "encryption" was a fixed transform.
    first = tmp_path / "one.syltrabk"
    second = tmp_path / "two.syltrabk"
    create_backup(household_payload(), PASSPHRASE, first, home_id="home_001")
    create_backup(household_payload(), PASSPHRASE, second, home_id="home_001")
    assert _split_backup(first)[1] != _split_backup(second)[1]


def test_the_wrong_passphrase_is_refused(tmp_path: Path) -> None:
    destination = tmp_path / "hub.syltrabk"
    create_backup(household_payload(), PASSPHRASE, destination, home_id="home_001")
    with pytest.raises(BackupIntegrityError):
        restore_backup(destination, "not-the-right-passphrase")


@pytest.mark.safety
def test_a_tampered_backup_is_refused(tmp_path: Path) -> None:
    # AES-GCM authenticates: altered ciphertext fails rather than restoring
    # subtly wrong data into a home.
    destination = tmp_path / "hub.syltrabk"
    create_backup(household_payload(), PASSPHRASE, destination, home_id="home_001")

    body = bytearray(destination.read_bytes())
    body[-1] ^= 0xFF
    destination.write_bytes(bytes(body))

    with pytest.raises(BackupIntegrityError):
        restore_backup(destination, PASSPHRASE)


@pytest.mark.safety
def test_a_swapped_manifest_is_refused(tmp_path: Path) -> None:
    # The manifest is authenticated additional data, so it cannot be edited to
    # misrepresent which home or when a backup came from.
    destination = tmp_path / "hub.syltrabk"
    create_backup(household_payload(), PASSPHRASE, destination, home_id="home_001")

    body = destination.read_bytes()
    manifest_length = int.from_bytes(body[9:13], "big")
    manifest = bytearray(body[13 : 13 + manifest_length])
    manifest[manifest.index(b"home_001")] = ord("H")  # alter the home id
    destination.write_bytes(body[:13] + bytes(manifest) + body[13 + manifest_length :])

    with pytest.raises(BackupIntegrityError):
        restore_backup(destination, PASSPHRASE)


def test_the_manifest_is_readable_without_the_passphrase(tmp_path: Path) -> None:
    # An operator must be able to see what a backup is before restoring it.
    destination = tmp_path / "hub.syltrabk"
    create_backup(household_payload(), PASSPHRASE, destination, home_id="home_001", hub_id="hub_1")
    manifest = read_manifest(destination)
    assert manifest.home_id == "home_001"
    assert manifest.hub_id == "hub_1"
    assert manifest.table_counts["device_events"] == 2


def test_the_manifest_carries_no_household_data(tmp_path: Path) -> None:
    destination = tmp_path / "hub.syltrabk"
    create_backup(household_payload(), PASSPHRASE, destination, home_id="home_001")
    manifest = read_manifest(destination)
    serialized = str(manifest)
    for household in ("Al Noor residence", "bedroom", "27.4"):
        assert household not in serialized


def test_a_weak_passphrase_is_refused(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="at least"):
        create_backup(household_payload(), "short", tmp_path / "x", home_id="home_001")


def test_a_non_backup_file_is_rejected(tmp_path: Path) -> None:
    stray = tmp_path / "notes.txt"
    stray.write_text("this is not a backup")
    with pytest.raises(BackupError, match="not a SYLTRA backup"):
        restore_backup(stray, PASSPHRASE)


def test_backups_are_owner_readable_only(tmp_path: Path) -> None:
    destination = tmp_path / "hub.syltrabk"
    create_backup(household_payload(), PASSPHRASE, destination, home_id="home_001")
    assert destination.stat().st_mode & 0o077 == 0


def test_two_backups_of_the_same_data_differ(tmp_path: Path) -> None:
    # Fresh salt and nonce each time: identical plaintext must not produce
    # identical ciphertext, or an observer learns when nothing changed.
    payload = household_payload()
    first = tmp_path / "a.syltrabk"
    second = tmp_path / "b.syltrabk"
    create_backup(payload, PASSPHRASE, first, home_id="home_001")
    create_backup(payload, PASSPHRASE, second, home_id="home_001")
    assert first.read_bytes() != second.read_bytes()


# ── privacy: export and deletion (spec §26) ──


class FakeStore:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], list[dict[str, Any]]] = {
            ("device_events", "home_001"): [{"x": 1}, {"x": 2}],
            ("homes", "home_001"): [{"home_id": "home_001"}],
            ("user_feedback", "home_001"): [{"kind": "ACCEPT"}],
            ("device_events", "home_002"): [{"x": 9}],
        }

    def read(self, table: str, home_id: str) -> list[dict[str, Any]]:
        return list(self.rows.get((table, home_id), []))

    def delete(self, table: str, home_id: str) -> int:
        removed = len(self.rows.pop((table, home_id), []))
        return removed


def test_export_returns_every_household_table() -> None:
    store = FakeStore()
    bundle = export_home("home_001", store.read)
    assert set(bundle.tables) == set(HOUSEHOLD_TABLES)
    assert bundle.record_count == 4


@pytest.mark.safety
def test_deletion_actually_deletes_and_verifies() -> None:
    # Spec §26: provide user and home deletion. A deletion that reports success
    # without checking is a promise, not a fact.
    store = FakeStore()
    report = delete_home("home_001", store.delete, store.read)
    assert report.complete
    assert report.total_deleted == 4
    assert export_home("home_001", store.read).record_count == 0


@pytest.mark.safety
def test_deleting_one_home_leaves_another_untouched() -> None:
    store = FakeStore()
    delete_home("home_001", store.delete, store.read)
    assert export_home("home_002", store.read).record_count == 1


def test_an_incomplete_deletion_is_reported_as_incomplete() -> None:
    store = FakeStore()

    def stubborn_delete(table: str, home_id: str) -> int:
        # Simulate a table that refuses to clear.
        return 0 if table == "device_events" else store.delete(table, home_id)

    report = delete_home("home_001", stubborn_delete, store.read)
    assert not report.complete
    assert report.remaining["device_events"] == 2


# ── diagnostics redaction (spec §26) ──


@pytest.mark.safety
def test_diagnostics_carry_no_secrets_or_identifiers() -> None:
    payload = {
        "home_id": "home_001",
        "token": "secret-token",
        "devices": [{"device_id": "ac_living", "room_id": "bedroom", "value": 23}],
        "nested": {"password": "hunter2", "capability": "climate.mode"},
    }
    bundle = diagnostic_bundle(payload, salt="fixed-salt")
    text = str(bundle)
    for sensitive in ("home_001", "secret-token", "ac_living", "bedroom", "hunter2"):
        assert sensitive not in text, f"{sensitive} leaked into diagnostics"
    # Non-identifying detail survives, or the bundle is useless.
    assert "climate.mode" in text
    assert "23" in text


def test_pseudonyms_are_stable_within_a_bundle_but_not_across_them() -> None:
    # Support can correlate events inside one bundle without being able to
    # build a mapping across bundles.
    assert pseudonymize("ac_living", "salt-a") == pseudonymize("ac_living", "salt-a")
    assert pseudonymize("ac_living", "salt-a") != pseudonymize("ac_living", "salt-b")
    assert pseudonymize("ac_living", "salt-a") != pseudonymize("light_living", "salt-a")


def test_redaction_handles_nested_structures() -> None:
    payload = {"a": [{"b": {"token": "x", "device_id": "d"}}]}
    result = redact_for_diagnostics(payload, "salt")
    assert result["a"][0]["b"]["token"] == "**REDACTED**"
    assert result["a"][0]["b"]["device_id"].startswith("id_")


# ── watchdog (spec §22 Phase 8) ──


def build_watchdog(
    healthy: dict[str, bool], restart_raises: bool = False
) -> tuple[Watchdog, list[str], list[tuple[str, str]]]:
    restarted: list[str] = []
    alerts: list[tuple[str, str]] = []

    def probe(name: str) -> bool:
        return healthy.get(name, True)

    def restart(name: str) -> None:
        if restart_raises:
            msg = "restart failed"
            raise RuntimeError(msg)
        restarted.append(name)
        healthy[name] = True

    watchdog = Watchdog(
        services=(
            SupervisedService("risk-engine", critical=True, failure_threshold=3),
            SupervisedService("adaptive-engine", failure_threshold=3),
        ),
        probe=probe,
        restart=restart,
        alert=lambda name, message: alerts.append((name, message)),
    )
    return watchdog, restarted, alerts


def test_a_healthy_service_is_left_alone() -> None:
    watchdog, restarted, _ = build_watchdog({})
    for status in watchdog.check_all(NOW):
        assert status.state is ServiceState.HEALTHY
    assert restarted == []


def test_a_single_missed_probe_does_not_trigger_a_restart() -> None:
    # One missed probe is usually a busy moment, not a crash.
    watchdog, restarted, _ = build_watchdog({"adaptive-engine": False})
    status = watchdog.check("adaptive-engine", NOW)
    assert status.state is ServiceState.DEGRADED
    assert restarted == []


def test_repeated_failures_trigger_a_restart() -> None:
    watchdog, restarted, _ = build_watchdog({"adaptive-engine": False})
    for _ in range(3):
        watchdog.check("adaptive-engine", NOW)
    assert restarted == ["adaptive-engine"]


@pytest.mark.safety
def test_a_crashed_safety_service_raises_an_alert_not_just_a_log() -> None:
    # A crashed governor stops monitoring silently — the worst way for a safety
    # component to fail. The household must be told.
    watchdog, restarted, alerts = build_watchdog({"risk-engine": False})
    for _ in range(3):
        watchdog.check("risk-engine", NOW)
    assert restarted == ["risk-engine"]
    assert any("unmonitored" in message for _, message in alerts)


def test_recovery_clears_the_failure_count() -> None:
    healthy = {"adaptive-engine": False}
    watchdog, _, _ = build_watchdog(healthy)
    watchdog.check("adaptive-engine", NOW)
    healthy["adaptive-engine"] = True
    status = watchdog.check("adaptive-engine", NOW)
    assert status.state is ServiceState.HEALTHY
    assert status.consecutive_failures == 0


@pytest.mark.safety
def test_the_watchdog_stops_thrashing_and_escalates() -> None:
    # Restarting forever helps nobody; the failure must become visible.
    healthy = {"adaptive-engine": False}
    watchdog, _, alerts = build_watchdog(healthy)
    service = watchdog.statuses["adaptive-engine"].service
    for attempt in range(service.restart_budget + 1):
        healthy["adaptive-engine"] = False
        for _ in range(service.failure_threshold):
            watchdog.check("adaptive-engine", NOW + timedelta(minutes=attempt))

    status = watchdog.statuses["adaptive-engine"]
    assert status.state is ServiceState.FAILED
    assert any("manual intervention" in message for _, message in alerts)


def test_a_failing_restart_marks_the_service_failed() -> None:
    watchdog, _, alerts = build_watchdog({"adaptive-engine": False}, restart_raises=True)
    for _ in range(3):
        watchdog.check("adaptive-engine", NOW)
    assert watchdog.statuses["adaptive-engine"].state is ServiceState.FAILED
    assert alerts


def test_a_raising_probe_counts_as_a_failure() -> None:
    def probe(name: str) -> bool:
        msg = "connection refused"
        raise ConnectionError(msg)

    watchdog = Watchdog(
        services=(SupervisedService("edge-agent", failure_threshold=2),),
        probe=probe,
        restart=lambda name: None,
    )
    watchdog.check("edge-agent", NOW)
    status = watchdog.statuses["edge-agent"]
    assert status.consecutive_failures == 1
    assert status.last_error == "ConnectionError"


def test_unhealthy_services_are_listed() -> None:
    watchdog, _, _ = build_watchdog({"adaptive-engine": False})
    watchdog.check_all(NOW)
    assert watchdog.unhealthy() == ["adaptive-engine"]


# ── collector query safety ──


@pytest.mark.safety
def test_query_building_refuses_a_non_identifier_table() -> None:
    # The allowlist is the primary defence; this is the second one. Even if a
    # hostile name reached _HOME_COLUMN, it could not produce injectable SQL.
    from syltra_operations import CollectionError
    from syltra_operations.collector import _assert_identifier

    for hostile in ("devices; DROP TABLE homes", "devices--", "1=1", "Devices", ""):
        with pytest.raises(CollectionError, match="not a valid SQL identifier"):
            _assert_identifier(hostile)


@pytest.mark.safety
def test_the_home_id_is_always_a_bound_parameter() -> None:
    # The one caller-supplied value never reaches the SQL string.
    from syltra_operations import HOUSEHOLD_TABLES, table_query

    for table in HOUSEHOLD_TABLES:
        query = table_query(table)
        assert ":home_id" in query
        assert "'" not in query


@pytest.mark.safety
def test_an_unknown_table_is_refused_before_any_sql_is_built() -> None:
    from syltra_operations import CollectionError, table_query

    with pytest.raises(CollectionError, match="no declared home scoping"):
        table_query("homes; DROP TABLE audit_events")
