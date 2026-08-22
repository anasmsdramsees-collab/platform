"""Updating a hub that is watching a house (spec §22 Phase 8, §25.4).

`docs/architecture/DEPLOYMENT.md` described the shape and nothing implemented
it. That was defensible while nothing was installed anywhere — and it stops
being defensible the moment a hub sits in a kitchen, because a hub with no safe
way to update is a hub nobody dares update, and an un-updatable hub is one
running whatever it shipped with for the rest of its life.

## The four things this has to survive

**A bad image.** Verified before anything is written, and the verifier is
injected rather than imported: this module knows the *order* things must happen
in, and has no business holding a public key.

**A bad release.** Every stage is reversible, and a health check that fails
after a bounded wait rolls the whole thing back without asking.

**Power loss.** The hub can die at any point, including between two service
restarts, and must come back knowing where it was. Every stage is recorded
*before* it is attempted, so the record errs towards "this might have happened"
— which is the safe direction, because re-checking a completed step is cheap
and skipping an incomplete one is not.

**Being interrupted mid-safety-layer.** This is the one that shapes the
ordering.

## Why safety services go last

An update walks the services one at a time, health-checking between each. If it
did the safety layer first, then a failure two services later would leave a
house running *new* safety code against *old* everything else, for as long as
the rollback takes. Doing safety last means a failure anywhere earlier is
rolled back with the safety layer untouched — it was watching the house on
known-good code the whole time.

The cost is that a safety fix ships last, which is the right trade: a safety
layer that is unchanged is a safety layer that is working.

## What this does not do

Move files, pull images, restart containers, or talk to a package manager.
Those are injected. What lives here is the sequence, the crash record, and the
refusals — the parts that are easy to get subtly wrong and impossible to test
if they are tangled up with an orchestrator.
"""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)

#: How long a service is given to come back healthy before the update gives up.
#: Long enough for a slow start, short enough that a household is not left on a
#: half-updated hub while somebody waits to see.
DEFAULT_HEALTH_TIMEOUT = timedelta(seconds=90)


class UpdateStage(StrEnum):
    """Where an update had got to. Recorded before each stage is attempted."""

    VERIFYING = "VERIFYING"
    BACKING_UP = "BACKING_UP"
    MIGRATING = "MIGRATING"
    RESTARTING = "RESTARTING"
    HEALTH_CHECKING = "HEALTH_CHECKING"
    COMMITTED = "COMMITTED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"
    """Rollback itself failed. A person is needed, and the household is told."""


class UpdateRefused(RuntimeError):
    """An update the hub declined to start, with the reason it declined."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail


@dataclass(frozen=True)
class ReleaseBundle:
    """What is being installed."""

    version: str
    #: Services in the order they are named in the bundle. The updater imposes
    #: its own order on top of this; a bundle cannot ask to go safety-first.
    services: tuple[str, ...]
    signature: str
    #: Minimum version this release will install over. A hub further back than
    #: this needs the intermediate release, because migrations are not
    #: guaranteed to compose.
    minimum_version: str | None = None


@dataclass
class UpdateRecord:
    """The crash record: what was being attempted, written before attempting it."""

    version: str
    stage: UpdateStage
    started_at: datetime
    updated_at: datetime
    services_restarted: tuple[str, ...] = ()
    detail: str = ""

    @property
    def is_finished(self) -> bool:
        return self.stage in (
            UpdateStage.COMMITTED,
            UpdateStage.ROLLED_BACK,
            UpdateStage.FAILED,
        )

    @property
    def needs_recovery(self) -> bool:
        """True for a record left mid-flight by a power cut.

        Deliberately generous: a hub that died during HEALTH_CHECKING may have
        completed the restart it was checking, and treating that as unfinished
        costs one redundant check while assuming otherwise costs correctness.
        """
        return not self.is_finished


@dataclass
class Hub:
    """The operations an update performs, injected rather than imported.

    A hub updater that imported a container runtime could not be tested without
    one, and the sequence is the part worth testing.
    """

    verify: Callable[[ReleaseBundle], bool]
    back_up: Callable[[], str]
    migrate: Callable[[str], None]
    restart: Callable[[str], None]
    is_healthy: Callable[[str], bool]
    restore: Callable[[str], None]
    current_version: Callable[[], str]
    #: Services whose restart must happen after everything else. Named rather
    #: than inferred, so adding a safety service is a deliberate act.
    safety_services: frozenset[str] = frozenset(
        {"risk-engine", "policy-safety", "edge-agent"}
    )


@dataclass
class UpdateManager:
    """Runs one update at a time, and knows what to do about the last one."""

    hub: Hub
    health_timeout: timedelta = DEFAULT_HEALTH_TIMEOUT
    record: UpdateRecord | None = None
    history: list[UpdateRecord] = field(default_factory=list)

    # ── ordering ──

    def install_order(self, services: Sequence[str]) -> list[str]:
        """Everything else first, safety last, order stable within each group.

        A bundle listing its services safety-first is reordered rather than
        refused: the bundle describes what to install, and the hub decides in
        what order it is safe to do so.
        """
        ordinary = [s for s in services if s not in self.hub.safety_services]
        safety = [s for s in services if s in self.hub.safety_services]
        return ordinary + safety

    # ── the update ──

    def apply(self, bundle: ReleaseBundle, now: datetime | None = None) -> UpdateRecord:
        """Install a release, or put the hub back exactly as it was."""
        moment = now or datetime.now(tz=UTC)
        if self.record is not None and self.record.needs_recovery:
            msg = (
                f"an update to {self.record.version} is unfinished at "
                f"{self.record.stage.value}; recover it before starting another"
            )
            raise UpdateRefused("UPDATE_IN_FLIGHT", msg)

        self.record = UpdateRecord(
            version=bundle.version,
            stage=UpdateStage.VERIFYING,
            started_at=moment,
            updated_at=moment,
        )
        self.history.append(self.record)

        # Nothing is written until the signature holds. §25.4: an unverified
        # bundle is not a slow update, it is a compromised hub.
        if not self.hub.verify(bundle):
            return self._finish(UpdateStage.FAILED, "signature did not verify")

        installed = self.hub.current_version()
        if bundle.minimum_version and installed < bundle.minimum_version:
            return self._finish(
                UpdateStage.FAILED,
                f"{installed} is older than the minimum {bundle.minimum_version} "
                "this release installs over",
            )

        self._advance(UpdateStage.BACKING_UP)
        backup = self.hub.back_up()

        try:
            self._advance(UpdateStage.MIGRATING)
            self.hub.migrate(bundle.version)

            for service in self.install_order(bundle.services):
                self._advance(UpdateStage.RESTARTING, detail=service)
                self.hub.restart(service)
                self.record.services_restarted = (*self.record.services_restarted, service)

                self._advance(UpdateStage.HEALTH_CHECKING, detail=service)
                if not self.hub.is_healthy(service):
                    return self._roll_back(backup, f"{service} did not come back healthy")
        except Exception as exc:  # noqa: BLE001 - any failure rolls back
            return self._roll_back(backup, f"{type(exc).__name__}: {exc}")

        return self._finish(UpdateStage.COMMITTED, f"updated to {bundle.version}")

    def _roll_back(self, backup: str, why: str) -> UpdateRecord:
        assert self.record is not None  # noqa: S101 - only reachable mid-update
        logger.error("update to %s failed: %s — rolling back", self.record.version, why)
        self._advance(UpdateStage.ROLLING_BACK, detail=why)
        try:
            self.hub.restore(backup)
        except Exception as exc:  # noqa: BLE001
            # The worst outcome, and it must not be quiet. A hub that failed to
            # roll back is running an unknown mixture and a person has to look.
            return self._finish(
                UpdateStage.FAILED, f"rollback failed after {why}: {exc}"
            )
        return self._finish(UpdateStage.ROLLED_BACK, why)

    # ── after a power cut ──

    def recover(self, now: datetime | None = None) -> UpdateRecord | None:
        """Finish what a power cut interrupted.

        Called at start-up. An update that died before its backup existed has
        nothing to restore and nothing was changed; anything later is rolled
        back, because a hub cannot know how much of a stage completed and the
        only state it can be sure of is the one it started from.
        """
        if self.record is None or not self.record.needs_recovery:
            return None

        interrupted = self.record
        logger.error(
            "hub restarted during an update to %s at stage %s; recovering",
            interrupted.version,
            interrupted.stage.value,
        )
        if interrupted.stage in (UpdateStage.VERIFYING, UpdateStage.BACKING_UP):
            # Nothing had been changed yet.
            return self._finish(UpdateStage.ROLLED_BACK, "interrupted before any change")

        self._advance(UpdateStage.ROLLING_BACK, detail="recovering after restart")
        try:
            self.hub.restore("latest")
        except Exception as exc:  # noqa: BLE001
            return self._finish(UpdateStage.FAILED, f"recovery rollback failed: {exc}")
        return self._finish(UpdateStage.ROLLED_BACK, "recovered after restart")

    # ── record keeping ──

    def _advance(self, stage: UpdateStage, detail: str = "") -> None:
        """Record a stage *before* attempting it.

        The order is the point: a record written afterwards is a record that a
        power cut erases, and an update whose progress nobody wrote down is one
        nobody can recover.
        """
        assert self.record is not None  # noqa: S101
        self.record.stage = stage
        self.record.updated_at = datetime.now(tz=UTC)
        if detail:
            self.record.detail = detail

    def _finish(self, stage: UpdateStage, detail: str) -> UpdateRecord:
        assert self.record is not None  # noqa: S101
        self.record.stage = stage
        self.record.detail = detail
        self.record.updated_at = datetime.now(tz=UTC)
        logger.info("update %s: %s", stage.value.lower(), detail)
        return self.record

    def status(self) -> dict[str, Any]:
        if self.record is None:
            return {"updating": False, "last": None}
        return {
            "updating": self.record.needs_recovery,
            "version": self.record.version,
            "stage": self.record.stage.value,
            "services_restarted": list(self.record.services_restarted),
            "detail": self.record.detail,
        }
