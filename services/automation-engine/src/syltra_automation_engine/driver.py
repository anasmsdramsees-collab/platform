"""The loop that runs the household's automations.

Wiring the scheduler turned up the same thing wiring the risk engine did:
`AutomationEngine.evaluate` was reachable from one place, the *test run* button,
and from nothing else. A household could write an automation, watch a dry run
say it would fire, enable it, and wait forever. The engine was correct and
nobody asked it anything.

So this driver is deliberately shaped like `RiskDriver`, and the resemblance is
the point — a hub has exactly two things that must keep asking questions on a
timer, and they should fail, report and recover the same way. What differs is
what each one is allowed to do: this one can only reach NON_CRITICAL and COMFORT
capabilities, because `AutomationAction` refuses to be constructed with anything
else.

## Two kinds of trigger, one pass

State triggers need the house: a light on motion fires because a reading
changed. Time triggers need only the clock, and the `Scheduler` decides which
occurrences are owed. Both are settled in the same pass so a scheduled
automation and a state-driven one cannot disagree about what time it is.

## Why it is slower than the safety loop

Two seconds rather than one. Nothing here is life-safety: a light that comes on
two seconds late is a light that came on. The risk driver runs at a gas leak's
pace; this one runs at a household's.
"""

import asyncio
import logging
from collections.abc import Callable, Iterable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from syltra_automation_engine import metrics
from syltra_automation_engine.scheduler import Scheduler

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 2.0


class _Twin(Protocol):
    @property
    def home_ids(self) -> list[str]: ...

    def home(self, home_id: str) -> Any: ...


class _Contexts(Protocol):
    def active(self, home_id: str, now: datetime | None = ...) -> list[Any]: ...


class _Engine(Protocol):
    def list_for(self, home_id: str) -> list[Any]: ...

    # Spelled out rather than **kwargs, so a change to the engine's signature
    # fails here instead of at the first pass on a running hub.
    def evaluate(
        self,
        home_id: str,
        home: Any,
        now: datetime | None = ...,
        active_contexts: Iterable[str] = ...,
        started_contexts: Iterable[str] = ...,
        manual_override: Mapping[tuple[str, str], datetime] | None = ...,
        dry_run: bool = ...,
    ) -> Any: ...


@dataclass
class AutomationDriverHealth:
    started: bool = False
    passes: int = 0
    last_completed_at: datetime | None = None
    consecutive_failures: int = 0
    last_error: str | None = None

    def is_healthy(self, now: datetime, tolerance_seconds: float) -> bool:
        if not self.started or self.last_completed_at is None:
            return False
        return (now - self.last_completed_at).total_seconds() <= tolerance_seconds


class AutomationDriver:
    """Evaluates every household's automations, on a timer, until stopped."""

    def __init__(
        self,
        twin: _Twin,
        engine: _Engine,
        contexts: _Contexts | None = None,
        scheduler: Scheduler | None = None,
        interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
        on_change: Callable[[str, tuple[str, ...]], None] | None = None,
    ) -> None:
        self._twin = twin
        self._engine = engine
        self._contexts = contexts
        self.scheduler = scheduler or Scheduler()
        self._interval = interval_seconds
        self._on_change = on_change
        self._task: asyncio.Task[None] | None = None
        self.health = AutomationDriverHealth()

    async def run_once(self, now: datetime | None = None) -> int:
        moment = now or datetime.now(tz=UTC)
        examined = 0
        for home_id in self._twin.home_ids:
            try:
                await self._examine(home_id, moment)
            except Exception:
                # Contained per household for the same reason the risk driver
                # contains it: the next house is somebody else's evening.
                logger.exception("automation evaluation failed for %s", home_id)
            else:
                examined += 1
        return examined

    async def _examine(self, home_id: str, now: datetime) -> None:
        state = self._twin.home(home_id)
        if state is None:
            return

        active: tuple[str, ...] = ()
        started: tuple[str, ...] = ()
        if self._contexts is not None:
            records = self._contexts.active(home_id, now)
            active = tuple(str(record.context_type) for record in records)
            # A context that began within this pass counts as started. Anything
            # finer would need the context engine to say so, and inventing it
            # here would fire CONTEXT_STARTED automations on every tick that a
            # context happened to still be running.
            started = tuple(
                str(record.context_type)
                for record in records
                if (now - record.started_at).total_seconds() <= self._interval
            )

        result = self._engine.evaluate(
            home_id, state, now, active_contexts=active, started_contexts=started
        )
        # Hints for the change feed, not policy reason codes. The two look
        # alike and are different vocabularies: a reason code is translated and
        # shown to a household, while these only tell a console which part of
        # the screen to re-read. Named `changed` so the difference is visible
        # and so the reason-code translation check does not claim them.
        changed = [f"AUTOMATION_{p.automation_id}" for p in getattr(result, "proposals", ())]

        # Scheduled automations, decided by the clock rather than by the house.
        for occurrence in self.scheduler.due(home_id, self._engine.list_for(home_id), now):
            self.scheduler.mark_fired(occurrence)
            metrics.SCHEDULED_FIRINGS.labels(late=str(occurrence.was_late).lower()).inc()
            changed.append(f"SCHEDULED_{occurrence.fire_key}")
            logger.info(
                "scheduled automation %s due for %s%s",
                occurrence.automation_id,
                occurrence.fire_key,
                f" ({occurrence.late_by.total_seconds():.0f}s late)" if occurrence.was_late else "",
            )

        if changed and self._on_change is not None:
            self._on_change(home_id, tuple(changed))

    async def _loop(self) -> None:
        while True:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - the loop must survive anything
                self.health.consecutive_failures += 1
                self.health.last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("automation driver pass failed")
            else:
                self.health.passes += 1
                self.health.last_completed_at = datetime.now(tz=UTC)
                self.health.consecutive_failures = 0
                self.health.last_error = None
            await asyncio.sleep(self._interval)

    async def start(self) -> None:
        if self._task is not None:
            return
        self.health.started = True
        try:
            await self.run_once()
        except Exception as exc:  # noqa: BLE001
            self.health.consecutive_failures += 1
            self.health.last_error = f"{type(exc).__name__}: {exc}"
            logger.exception("the automation driver's first pass failed")
        else:
            self.health.passes += 1
            self.health.last_completed_at = datetime.now(tz=UTC)
        self._task = asyncio.create_task(self._loop())
        logger.info("automation driver started, evaluating every %.1fs", self._interval)

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        self.health.started = False
