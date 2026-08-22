"""Updating a hub that is watching a house (spec §22 Phase 8, §25.4).

A hub with no safe way to update is a hub nobody dares update, and an
un-updatable hub runs whatever it shipped with for the rest of its life. So
almost none of this tests a successful update: it tests a bad signature, a
service that will not come back, a power cut between two restarts, and a
rollback that itself fails.
"""

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest
from syltra_operations import (
    Hub,
    ReleaseBundle,
    UpdateManager,
    UpdateRefused,
    UpdateStage,
)

NOW = datetime(2026, 8, 21, 22, 0, tzinfo=UTC)

SERVICES = ("digital-twin", "risk-engine", "context-engine", "policy-safety", "api-gateway")


class FakeHub:
    """A hub that does what the test tells it to and remembers what happened."""

    def __init__(
        self,
        *,
        verifies: bool = True,
        unhealthy: set[str] | None = None,
        restore_fails: bool = False,
        version: str = "1.0.0",
        restart_raises: str | None = None,
    ) -> None:
        self.restarted: list[str] = []
        self.migrated: list[str] = []
        self.restored: list[str] = []
        self.backed_up = 0
        self._verifies = verifies
        self._unhealthy = unhealthy or set()
        self._restore_fails = restore_fails
        self._version = version
        self._restart_raises = restart_raises

    def as_hub(self) -> Hub:
        return Hub(
            verify=lambda bundle: self._verifies,
            back_up=self._back_up,
            migrate=self.migrated.append,
            restart=self._restart,
            is_healthy=lambda service: service not in self._unhealthy,
            restore=self._restore,
            current_version=lambda: self._version,
        )

    def _back_up(self) -> str:
        self.backed_up += 1
        return "backup-1"

    def _restart(self, service: str) -> None:
        if service == self._restart_raises:
            msg = f"{service} refused to start"
            raise RuntimeError(msg)
        self.restarted.append(service)

    def _restore(self, backup: str) -> None:
        if self._restore_fails:
            msg = "the backup could not be read"
            raise RuntimeError(msg)
        self.restored.append(backup)


def bundle(**overrides: Any) -> ReleaseBundle:
    values: dict[str, Any] = {
        "version": "1.1.0",
        "services": SERVICES,
        "signature": "valid",
    }
    values.update(overrides)
    return ReleaseBundle(**values)


# ── the ordering, which is the safety property ──


def test_safety_services_are_restarted_last() -> None:
    """A failure two services in must not leave the house running new safety
    code against old everything else while the rollback runs.

    Safety last means a failure anywhere earlier is rolled back with the safety
    layer untouched — it was watching on known-good code the whole time.
    """
    hub = FakeHub()
    manager = UpdateManager(hub.as_hub())
    manager.apply(bundle(), now=NOW)

    safety = {"risk-engine", "policy-safety", "edge-agent"}
    positions = [i for i, s in enumerate(hub.restarted) if s in safety]
    ordinary = [i for i, s in enumerate(hub.restarted) if s not in safety]
    assert positions and ordinary
    assert min(positions) > max(ordinary), hub.restarted


def test_a_bundle_asking_to_go_safety_first_is_reordered_not_obeyed() -> None:
    """The bundle says what to install; the hub decides what order is safe."""
    hub = FakeHub()
    manager = UpdateManager(hub.as_hub())
    manager.apply(bundle(services=("risk-engine", "digital-twin")), now=NOW)
    assert hub.restarted == ["digital-twin", "risk-engine"]


def test_order_is_stable_within_each_group() -> None:
    manager = UpdateManager(FakeHub().as_hub())
    assert manager.install_order(SERVICES) == [
        "digital-twin",
        "context-engine",
        "api-gateway",
        "risk-engine",
        "policy-safety",
    ]


# ── nothing is written until the signature holds ──


def test_an_unsigned_bundle_never_reaches_the_disk() -> None:
    """§25.4: an unverified bundle is not a slow update, it is a compromised hub."""
    hub = FakeHub(verifies=False)
    manager = UpdateManager(hub.as_hub())

    record = manager.apply(bundle(), now=NOW)

    assert record.stage is UpdateStage.FAILED
    assert hub.backed_up == 0
    assert hub.migrated == []
    assert hub.restarted == []


def test_a_release_refuses_to_install_over_too_old_a_version() -> None:
    """Migrations are not guaranteed to compose, so a hub too far back needs
    the intermediate release rather than a hopeful jump."""
    hub = FakeHub(version="0.9.0")
    manager = UpdateManager(hub.as_hub())

    record = manager.apply(bundle(minimum_version="1.0.0"), now=NOW)

    assert record.stage is UpdateStage.FAILED
    assert "older than the minimum" in record.detail
    assert hub.restarted == []


# ── failure rolls everything back ──


def test_a_service_that_will_not_come_back_rolls_the_update_back() -> None:
    hub = FakeHub(unhealthy={"context-engine"})
    manager = UpdateManager(hub.as_hub())

    record = manager.apply(bundle(), now=NOW)

    assert record.stage is UpdateStage.ROLLED_BACK
    assert hub.restored == ["backup-1"]
    # It stopped where it failed rather than carrying on through the safety layer.
    assert "risk-engine" not in hub.restarted


def test_a_service_that_raises_on_restart_rolls_back_too() -> None:
    hub = FakeHub(restart_raises="context-engine")
    manager = UpdateManager(hub.as_hub())

    record = manager.apply(bundle(), now=NOW)

    assert record.stage is UpdateStage.ROLLED_BACK
    assert hub.restored == ["backup-1"]


def test_a_backup_is_taken_before_anything_is_migrated() -> None:
    """Otherwise there is nothing to roll back to."""
    hub = FakeHub(unhealthy={"digital-twin"})
    manager = UpdateManager(hub.as_hub())
    manager.apply(bundle(), now=NOW)
    assert hub.backed_up == 1
    assert hub.restored == ["backup-1"]


def test_a_failed_rollback_is_the_loudest_outcome_there_is() -> None:
    """A hub that failed to roll back is running an unknown mixture.

    FAILED rather than ROLLED_BACK, because the difference is whether a person
    has to go and look.
    """
    hub = FakeHub(unhealthy={"digital-twin"}, restore_fails=True)
    manager = UpdateManager(hub.as_hub())

    record = manager.apply(bundle(), now=NOW)

    assert record.stage is UpdateStage.FAILED
    assert "rollback failed" in record.detail


# ── power loss ──


def test_a_hub_that_died_before_any_change_recovers_without_restoring() -> None:
    hub = FakeHub()
    manager = UpdateManager(hub.as_hub())
    manager.record = _interrupted_at(UpdateStage.BACKING_UP)

    record = manager.recover()

    assert record is not None
    assert record.stage is UpdateStage.ROLLED_BACK
    assert hub.restored == [], "nothing had changed, so nothing needed restoring"


def test_a_hub_that_died_between_two_restarts_rolls_back() -> None:
    """It cannot know how much of the stage completed, and the only state it
    can be sure of is the one it started from."""
    hub = FakeHub()
    manager = UpdateManager(hub.as_hub())
    manager.record = _interrupted_at(UpdateStage.RESTARTING)

    record = manager.recover()

    assert record is not None
    assert record.stage is UpdateStage.ROLLED_BACK
    assert hub.restored == ["latest"]


def test_a_hub_that_died_during_a_health_check_still_rolls_back() -> None:
    """Deliberately generous: it may have completed the restart it was
    checking, and a redundant rollback is cheaper than a wrong assumption."""
    hub = FakeHub()
    manager = UpdateManager(hub.as_hub())
    manager.record = _interrupted_at(UpdateStage.HEALTH_CHECKING)
    assert manager.recover() is not None
    assert hub.restored == ["latest"]


def test_a_finished_update_needs_no_recovery() -> None:
    manager = UpdateManager(FakeHub().as_hub())
    manager.record = _interrupted_at(UpdateStage.COMMITTED)
    assert manager.recover() is None


def test_a_second_update_is_refused_while_one_is_unfinished() -> None:
    manager = UpdateManager(FakeHub().as_hub())
    manager.record = _interrupted_at(UpdateStage.RESTARTING)
    with pytest.raises(UpdateRefused, match="UPDATE_IN_FLIGHT"):
        manager.apply(bundle(), now=NOW)


def test_the_stage_is_recorded_before_it_is_attempted() -> None:
    """A record written afterwards is a record a power cut erases.

    Checked by watching what the record says at the instant a service is asked
    to restart — the moment a hub is most likely to lose power.
    """
    seen: list[str] = []
    hub = FakeHub()
    manager = UpdateManager(hub.as_hub())

    # Wrapped on the Hub the manager actually holds. Patching the FakeHub
    # afterwards would change nothing: `as_hub` captured the bound method when
    # it was built, which is its own small lesson about testing through seams
    # rather than around them.
    restart = manager.hub.restart

    def watching(service: str) -> None:
        assert manager.record is not None
        seen.append(manager.record.stage.value)
        restart(service)

    manager.hub = replace(manager.hub, restart=watching)
    manager.apply(bundle(), now=NOW)

    assert seen and set(seen) == {UpdateStage.RESTARTING.value}


# ── the happy path, briefly ──


def test_a_clean_update_commits() -> None:
    hub = FakeHub()
    manager = UpdateManager(hub.as_hub())

    record = manager.apply(bundle(), now=NOW)

    assert record.stage is UpdateStage.COMMITTED
    assert hub.migrated == ["1.1.0"]
    assert len(hub.restarted) == len(SERVICES)
    assert hub.restored == []
    assert manager.status()["updating"] is False


def _interrupted_at(stage: UpdateStage) -> Any:
    from syltra_operations import UpdateRecord

    return UpdateRecord(version="1.1.0", stage=stage, started_at=NOW, updated_at=NOW)
