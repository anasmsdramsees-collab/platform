"""The loop that asks the risk engine to look at the house.

Everything else in this package was reachable only from a test. The governor,
the seven risk states and the gas isolation were all complete, tested, and
connected to a `RiskEngineService.evaluate` that nothing in the deployed stack
ever called — so a certified gas alarm would have sat in the twin, correct and
unread. This module is the caller that was missing.

## Why a timer

A push-based driver would be better: evaluate the moment a reading changes,
rather than up to `interval` seconds later. It is not what this is, for one
reason — an event-driven safety loop stops when events stop, and the failure
that matters most here is the one where nothing arrives at all. A timer that
finds a stale twin still runs, still reads a gas alarm latched from a minute
ago, and still closes the valve. A subscriber waiting for the next message
would wait forever and look healthy doing it.

The interval is therefore a latency budget, not a polling convenience. One
second is the default because that is the scale a gas leak deserves and the
work per pass is a dictionary walk over one household's devices.

## Why liveness is part of it

A safety loop that dies quietly is worse than one that was never built: the
console keeps rendering, the household keeps trusting it, and nothing is
watching the detectors. `last_completed_at` and `consecutive_failures` exist so
`/v1/health` can report a stalled driver as a fault rather than as silence, and
so the metric a dashboard alerts on has something to read.

## What it does not do

Decide anything. It hands the risk engine a home state and a clock, and the
determinism lives entirely downstream — same state, same time, same outcome,
whether this loop or a test made the call.
"""

import asyncio
import logging
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from syltra_contracts import ContextType

from syltra_risk_engine import metrics

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 1.0


class _Twin(Protocol):
    @property
    def home_ids(self) -> list[str]: ...

    def home(self, home_id: str) -> Any: ...


class _Contexts(Protocol):
    def active(self, home_id: str, now: datetime | None = ...) -> list[Any]: ...


class _Risk(Protocol):
    def evaluate(
        self,
        home_id: str,
        home: Any,
        now: datetime | None = ...,
        occupied: bool | None = ...,
        cooking: bool = ...,
    ) -> list[Any]: ...

    async def carry_out_confirmed_isolations(
        self, home_id: str, now: datetime | None = ...
    ) -> tuple[Any, ...]: ...


@dataclass
class RiskDriverHealth:
    """What a health endpoint needs to tell a stalled loop from a quiet one."""

    started: bool = False
    passes: int = 0
    last_completed_at: datetime | None = None
    consecutive_failures: int = 0
    last_error: str | None = None

    def is_healthy(self, now: datetime, tolerance_seconds: float) -> bool:
        """False when the loop has not completed a pass recently enough.

        A driver that has never completed one is unhealthy rather than
        unknown: before the first pass, nothing is watching the detectors.
        """
        if not self.started or self.last_completed_at is None:
            return False
        return (now - self.last_completed_at).total_seconds() <= tolerance_seconds


class RiskDriver:
    """Feeds the risk engine, on a timer, until stopped."""

    def __init__(
        self,
        twin: _Twin,
        risk: _Risk,
        contexts: _Contexts | None = None,
        interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
        on_change: Callable[[str, tuple[str, ...]], None] | None = None,
    ) -> None:
        self._twin = twin
        self._risk = risk
        self._contexts = contexts
        # Called when a pass actually changed something, so a live console
        # learns about a confirmed hazard in the same second rather than at the
        # next poll. A callback rather than an import: the risk engine must not
        # depend on the web layer to do its job.
        self._on_change = on_change
        self._interval = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self.health = RiskDriverHealth()

    # ── one pass, which is the whole behaviour ──

    async def run_once(self, now: datetime | None = None) -> int:
        """Evaluate every known home and carry out what that authorizes.

        Returns the number of homes examined. Failures are contained per home:
        one household whose evaluation raises must not stop the loop reaching
        the next one, because the next one may be the one with the gas alarm.
        """
        moment = now or datetime.now(tz=UTC)
        examined = 0
        for home_id in self._twin.home_ids:
            try:
                await self._examine(home_id, moment)
            except Exception:
                # Logged with the traceback and counted, never re-raised: this
                # loop stopping is a worse outcome than any single bad pass.
                logger.exception("SAFETY: risk evaluation failed for %s", home_id)
                metrics.DRIVER_FAILURES.labels(home_id=home_id).inc()
            else:
                examined += 1
        return examined

    async def _examine(self, home_id: str, now: datetime) -> None:
        state = self._twin.home(home_id)
        if state is None:
            return
        occupied, cooking = self._situation(home_id, now)
        changes = self._risk.evaluate(home_id, state, now, occupied=occupied, cooking=cooking)
        # Hints for the change feed. Some are real reason codes and some are
        # only "this part changed"; either way the console uses them to decide
        # what to re-read, not to show a person.
        changed = [f"RISK_{change.kind}" for change in changes]
        # Isolations are carried out in the same pass that confirmed them.
        # Deferring to the next tick would put a second of avoidable delay
        # between a certified gas reading and a closed valve.
        outcomes = await self._risk.carry_out_confirmed_isolations(home_id, now)
        for outcome in outcomes:
            metrics.ISOLATIONS.labels(
                capability=outcome.capability,
                verified=str(outcome.succeeded).lower(),
            ).inc()
            changed.append(outcome.reason_code)
        # Only when something happened. A quiet pass every second that told the
        # console to re-read would be the 15-second poll again, faster.
        if changed and self._on_change is not None:
            self._on_change(home_id, tuple(changed))

    def _situation(self, home_id: str, now: datetime) -> tuple[bool | None, bool]:
        """Occupancy and cooking, from context rather than from guesswork.

        `None` occupancy is deliberate when there is no context service: the
        risk rules distinguish "nobody home" from "unknown", and inventing
        `False` would tell them the house is empty on no evidence.
        """
        if self._contexts is None:
            return None, False
        active = {record.context_type for record in self._contexts.active(home_id, now)}
        occupied = ContextType.HOME_OCCUPIED in active or None
        return (True if occupied is True else None), ContextType.COOKING in active

    # ── the loop ──

    async def _loop(self) -> None:
        while True:
            started = datetime.now(tz=UTC)
            try:
                await self.run_once(started)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - the loop must survive anything
                self.health.consecutive_failures += 1
                self.health.last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("SAFETY: risk driver pass failed")
            else:
                self.health.passes += 1
                self.health.last_completed_at = datetime.now(tz=UTC)
                self.health.consecutive_failures = 0
                self.health.last_error = None
                metrics.DRIVER_PASSES.inc()
            await asyncio.sleep(self._interval)

    async def start(self) -> None:
        if self._task is not None:
            return
        # One pass before returning, so a caller that starts the driver and
        # immediately reports health does not report a loop that has not run.
        #
        # A first pass that fails must not stop the driver starting: refusing to
        # start leaves nothing watching at all, where starting unhealthy leaves
        # a loop that will retry and a health flag that says so.
        self.health.started = True
        try:
            await self.run_once()
        except Exception as exc:  # noqa: BLE001 - the loop must survive anything
            self.health.consecutive_failures += 1
            self.health.last_error = f"{type(exc).__name__}: {exc}"
            logger.exception("SAFETY: the risk driver's first pass failed")
        else:
            self.health.passes += 1
            self.health.last_completed_at = datetime.now(tz=UTC)
        self._task = asyncio.create_task(self._loop())
        logger.info("risk driver started, evaluating every %.1fs", self._interval)

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        self.health.started = False
        logger.info("risk driver stopped")

    async def __aenter__(self) -> "RiskDriver":
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()
