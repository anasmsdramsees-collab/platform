"""Who owns time in this platform (spec §2.3, ADR-009).

"Turn the lights on at 7pm" looked like a small feature and is not. It needs an
answer to a question nothing else in the platform had to answer: **whose clock?**

## The answer

The household's. A person who asks for 7pm means 7pm on the clock in their
kitchen — in June and in December, before and after the country changes its
offset, and regardless of what the hub's system timezone happens to be.

So a schedule is stored as a wall-clock time plus an IANA timezone, and the
firing instant is computed from those at the moment it is needed. The
alternative — converting to UTC when the automation is saved — bakes in an
offset that stops being true, and an automation saved in winter fires an hour
wrong all summer.

Every recorded instant is UTC. Only the *intent* is local.

## Firing once, and only once

The hard part is not "has 7pm passed". It is "has 7pm passed **and I have not
already run for this 7pm**", across:

- a hub that restarts at 18:59 and comes back at 19:01;
- a clock corrected forwards by NTP, skipping over 19:00 entirely;
- a clock corrected backwards, making 19:00 arrive twice;
- a daylight-saving jump where 19:00 does not exist, or exists twice.

The mechanism is a **fire key**: the local date and time an occurrence belongs
to, `2026-08-20T19:00`, recorded per automation once it has run. Comparing keys
rather than timestamps makes every case above fall out:

- a restart re-derives the same key and finds it already recorded;
- a clock jumped forwards past 19:00 still finds the 19:00 key unfired, so a
  skipped occurrence runs late rather than never — for a light that is right,
  and this module says so out loud rather than leaving it as an accident;
- a clock moved backwards re-derives a key already recorded, and nothing runs
  twice;
- a doubled hour has one key, so it fires once.

## What it will not do

Fire an occurrence from the distant past. A hub restored from a backup, or
switched on after a fortnight away, must not run a fortnight of missed evening
routines in one burst. `catch_up_window` bounds how late an occurrence may run,
and anything older is recorded as skipped, with a reason.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from syltra_contracts import Automation, TriggerKind

logger = logging.getLogger(__name__)

#: How late a missed occurrence may still run. Longer than a restart or a
#: clock correction, far shorter than a holiday.
DEFAULT_CATCH_UP = timedelta(minutes=15)

DEFAULT_TIMEZONE = "UTC"


class UnknownTimezone(ValueError):
    """The household named a timezone this machine does not have."""


@dataclass(frozen=True)
class Occurrence:
    """One scheduled firing, named by the local time it belongs to."""

    automation_id: str
    fire_key: str
    local: datetime
    at: datetime
    late_by: timedelta

    @property
    def was_late(self) -> bool:
        return self.late_by > timedelta(seconds=1)


@dataclass
class Scheduler:
    """Decides which scheduled automations are due, and only once each."""

    timezones: dict[str, str] = field(default_factory=dict)
    catch_up_window: timedelta = DEFAULT_CATCH_UP
    _fired: dict[str, set[str]] = field(default_factory=dict)
    #: Occurrences that were too old to run, kept so a household can be told
    #: its evening routine did not happen rather than left to notice.
    skipped: list[tuple[str, str, str]] = field(default_factory=list)

    def set_timezone(self, home_id: str, name: str) -> None:
        try:
            ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            msg = f"{name!r} is not a timezone this hub knows"
            raise UnknownTimezone(msg) from exc
        self.timezones[home_id] = name

    def zone(self, home_id: str) -> ZoneInfo:
        return ZoneInfo(self.timezones.get(home_id, DEFAULT_TIMEZONE))

    # ── deciding what is due ──

    def due(
        self, home_id: str, automations: list[Automation], now: datetime
    ) -> list[Occurrence]:
        """Scheduled automations whose time has come and not yet been served."""
        moment = now.astimezone(UTC)
        local_now = moment.astimezone(self.zone(home_id))
        due: list[Occurrence] = []

        for automation in automations:
            if automation.trigger.kind is not TriggerKind.AT_TIME:
                continue
            if not automation.enabled:
                continue
            occurrence = self._latest_occurrence(home_id, automation, local_now)
            if occurrence is None:
                continue
            already = self._fired.setdefault(str(automation.automation_id), set())
            if occurrence.fire_key in already:
                continue
            if occurrence.late_by > self.catch_up_window:
                # Recorded as fired so it cannot run later, and recorded as
                # skipped so somebody can see that it did not.
                already.add(occurrence.fire_key)
                self.skipped.append(
                    (str(automation.automation_id), occurrence.fire_key, "TOO_LATE_TO_RUN")
                )
                logger.info(
                    "scheduled automation %s skipped %s: %.0fs late",
                    automation.automation_id,
                    occurrence.fire_key,
                    occurrence.late_by.total_seconds(),
                )
                continue
            due.append(occurrence)
        return due

    def mark_fired(self, occurrence: Occurrence) -> None:
        """Record an occurrence as served, so nothing serves it again."""
        self._fired.setdefault(occurrence.automation_id, set()).add(occurrence.fire_key)

    def has_fired(self, automation_id: str, fire_key: str) -> bool:
        return fire_key in self._fired.get(automation_id, set())

    # ── the arithmetic ──

    def _latest_occurrence(
        self, home_id: str, automation: Automation, local_now: datetime
    ) -> Occurrence | None:
        """The most recent occurrence at or before `local_now`, if any."""
        trigger = automation.trigger
        assert trigger.at_hour is not None and trigger.at_minute is not None  # noqa: S101
        wanted = time(trigger.at_hour, trigger.at_minute)
        allowed = set(trigger.weekdays) if trigger.weekdays else set(range(7))

        # Walk back at most a week: any occurrence older than that is beyond
        # any catch-up window worth having.
        for days_back in range(8):
            day: date = (local_now - timedelta(days=days_back)).date()
            if day.weekday() not in allowed:
                continue
            local = datetime.combine(day, wanted, tzinfo=local_now.tzinfo)
            if local > local_now:
                continue
            return Occurrence(
                automation_id=str(automation.automation_id),
                # The key is the local wall-clock time, which is what the
                # household asked for and what stays stable across an offset
                # change.
                fire_key=local.strftime("%Y-%m-%dT%H:%M"),
                local=local,
                at=local.astimezone(UTC),
                late_by=local_now - local,
            )
        return None
