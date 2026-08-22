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

## Evaluating is not acting

The first version of this file stopped at the proposal, which meant the loop ran
every two seconds for weeks and never turned on a light: `ActionOrchestrator`
had one caller in the whole platform, and it was a person pressing a control.
A `dispatcher` closes that gap. It stays optional — a hub that wants to watch
its automations without letting them act constructs the driver without one, and
that is exactly what the shadow phase of a pilot needs.

## Goals ride the same loop

A goal is checked on a clock rather than fired by an event, which would suggest
a third timer. It does not get one: each goal carries its own review interval
and this pass simply asks which are due. A hub has two loops — one at a gas
leak's pace and one at a household's — and a third would be a third thing that
can stop without anybody noticing.

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
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from syltra_automation_engine import metrics
from syltra_automation_engine.dispatcher import AutomationDispatcher
from syltra_automation_engine.engine import AutomationProposal
from syltra_automation_engine.goals import GoalRegistry, assess, with_manual_hold
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
        dispatcher: AutomationDispatcher | None = None,
        goals: GoalRegistry | None = None,
        manual_override: Callable[[str, str | None, str], bool] | None = None,
    ) -> None:
        self._twin = twin
        self._engine = engine
        self._contexts = contexts
        self.scheduler = scheduler or Scheduler()
        self._interval = interval_seconds
        self._on_change = on_change
        self._dispatcher = dispatcher
        self._goals = goals
        self._manual_override = manual_override
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
        proposals = tuple(getattr(result, "proposals", ()))
        changed = [f"AUTOMATION_{p.automation_id}" for p in proposals]

        # And then it happens. Without this the loop is a very thorough way of
        # deciding to do nothing.
        if proposals and self._dispatcher is not None:
            for outcome in await self._dispatcher.dispatch_all(proposals, now):
                metrics.DISPATCHES.labels(
                    outcome=outcome.outcome,
                    carried_out=str(outcome.carried_out).lower(),
                ).inc()
                logger.info(
                    "automation %s → %s %s%s",
                    outcome.name,
                    outcome.capability,
                    outcome.intended_value,
                    "" if outcome.carried_out else f" (not carried out: {outcome.outcome})",
                )

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

        changed.extend(await self._review_goals(home_id, state, now))

        if changed and self._on_change is not None:
            self._on_change(home_id, tuple(changed))

    async def _review_goals(self, home_id: str, state: Any, now: datetime) -> list[str]:
        """Ask each goal that is due whether it still holds, and act if it does not."""
        if self._goals is None:
            return []
        changed: list[str] = []
        for goal in self._goals.list_for(home_id):
            if not goal.enabled or not self._goals.due(goal, now):
                continue
            self._goals.mark_reviewed(goal, now)
            status = assess(goal, state, now)
            if self._manual_override is not None:
                status = with_manual_hold(
                    status,
                    goal,
                    lambda device_id, capability: bool(
                        self._manual_override(home_id, device_id, capability)  # type: ignore[misc]
                    ),
                )
            changed.append(f"GOAL_{goal.goal_id}")

            if not status.needs_correcting or not goal.actions:
                # Nothing to do, or nothing this goal is allowed to do about it.
                # A goal that only reports is a perfectly good goal.
                continue
            if not self._goals.may_correct(goal, now) or self._dispatcher is None:
                continue

            proposals = tuple(
                AutomationProposal(
                    automation_id=goal.goal_id,
                    home_id=home_id,
                    name=goal.name,
                    action=action,
                    triggered_at=now,
                    expires_at=now + timedelta(seconds=goal.review_seconds),
                    reason_codes=("GOAL_NOT_HOLDING",),
                )
                for action in goal.actions
            )
            outcomes = await self._dispatcher.dispatch_all(proposals, now)
            if any(outcome.carried_out for outcome in outcomes):
                # Marked only when something actually happened. A correction
                # policy refused is not a correction, and must not start the
                # clock that stops the next attempt.
                self._goals.mark_corrected(goal, now)
            logger.info(
                "goal %s not holding (%s vs %s) — corrected %d/%d",
                goal.name,
                status.measured,
                goal.value,
                sum(1 for o in outcomes if o.carried_out),
                len(outcomes),
            )
        return changed

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
