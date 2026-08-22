"""Scheduled triggers, and the clock problems they drag in (ADR-009, §2.3).

"At 7pm" is a small feature with a large tail. Almost every test here is a
clock behaving badly: a hub that restarts across the hour, an NTP correction in
either direction, a daylight-saving jump, and a hub switched on after a
fortnight away.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from syltra_automation_engine.scheduler import Scheduler, UnknownTimezone
from syltra_contracts import (
    Automation,
    AutomationAction,
    AutomationTrigger,
    TriggerKind,
)

HOME = "home_clock"
RIYADH = "Asia/Riyadh"
DUBLIN = "Europe/Dublin"  # observes daylight saving; Riyadh does not


def evening(hour: int = 19, minute: int = 0, weekdays: tuple[int, ...] = ()) -> Automation:
    return Automation(
        automation_id=uuid4(),
        home_id=HOME,
        name="Evening lights",
        owner="amal",
        trigger=AutomationTrigger(
            kind=TriggerKind.AT_TIME, at_hour=hour, at_minute=minute, weekdays=weekdays
        ),
        actions=(AutomationAction(capability="light.power", value=True, device_id="light_1"),),
    )


def scheduler(zone: str = RIYADH) -> Scheduler:
    s = Scheduler()
    s.set_timezone(HOME, zone)
    return s


def utc(zone_local: str) -> datetime:
    """A UTC instant written as a Riyadh wall-clock time, for readability."""
    from zoneinfo import ZoneInfo

    return datetime.fromisoformat(zone_local).replace(tzinfo=ZoneInfo(RIYADH)).astimezone(UTC)


# ── the household's clock, not the hub's ──


def test_seven_pm_means_seven_pm_where_the_household_lives() -> None:
    s = scheduler()
    automation = evening()
    due = s.due(HOME, [automation], utc("2026-08-20T19:00"))
    assert len(due) == 1
    assert due[0].fire_key == "2026-08-20T19:00"


def test_nothing_is_due_before_the_time_arrives() -> None:
    s = scheduler()
    assert s.due(HOME, [evening()], utc("2026-08-20T18:59")) == []


def test_an_unknown_timezone_is_refused_rather_than_silently_ignored() -> None:
    s = Scheduler()
    with pytest.raises(UnknownTimezone):
        s.set_timezone(HOME, "Mars/Olympus_Mons")


def test_a_disabled_automation_is_never_due() -> None:
    s = scheduler()
    off = evening().model_copy(update={"enabled": False})
    assert s.due(HOME, [off], utc("2026-08-20T19:30")) == []


# ── firing once, across every way a clock misbehaves ──


def test_it_does_not_fire_twice_in_the_same_evening() -> None:
    s = scheduler()
    automation = evening()
    first = s.due(HOME, [automation], utc("2026-08-20T19:00"))
    s.mark_fired(first[0])
    assert s.due(HOME, [automation], utc("2026-08-20T19:05")) == []


def test_a_restart_across_the_hour_still_fires_once() -> None:
    """The hub goes down at 18:59 and comes back at 19:01.

    Re-deriving the key rather than remembering a timestamp is what makes this
    work: the same occurrence produces the same key on both sides of a restart.
    """
    s = scheduler()
    automation = evening()
    assert s.due(HOME, [automation], utc("2026-08-20T18:59")) == []
    due = s.due(HOME, [automation], utc("2026-08-20T19:01"))
    assert len(due) == 1
    s.mark_fired(due[0])
    assert s.due(HOME, [automation], utc("2026-08-20T19:02")) == []


def test_a_clock_corrected_backwards_does_not_run_it_again() -> None:
    """NTP moves the clock from 19:05 back to 18:58, then forwards again."""
    s = scheduler()
    automation = evening()
    s.mark_fired(s.due(HOME, [automation], utc("2026-08-20T19:05"))[0])
    assert s.due(HOME, [automation], utc("2026-08-20T18:58")) == []
    assert s.due(HOME, [automation], utc("2026-08-20T19:06")) == []


def test_a_clock_jumped_over_the_time_still_runs_it_late() -> None:
    """A correction skips 18:58 straight to 19:04.

    For a light, running four minutes late is better than not running, and this
    is the deliberate choice rather than an accident of the implementation.
    """
    s = scheduler()
    due = s.due(HOME, [evening()], utc("2026-08-20T19:04"))
    assert len(due) == 1
    assert due[0].was_late


def test_an_occurrence_older_than_the_catch_up_window_is_skipped_and_recorded() -> None:
    """A hub switched on after a fortnight must not run a fortnight of evenings.

    Recorded rather than dropped: the household should be able to see that its
    routine did not happen.
    """
    s = scheduler()
    automation = evening()
    assert s.due(HOME, [automation], utc("2026-08-21T02:00")) == []
    assert s.skipped and s.skipped[0][2] == "TOO_LATE_TO_RUN"
    # And it stays skipped rather than firing at the next check.
    assert s.due(HOME, [automation], utc("2026-08-21T02:01")) == []


# ── daylight saving, where a wall clock and a duration disagree ──


def test_a_timezone_that_changes_offset_still_fires_at_the_local_time() -> None:
    """Dublin is UTC+1 in August and UTC+0 in December.

    Converting to UTC when the automation was saved would bake in the summer
    offset and fire an hour wrong all winter. The key stays the local time, so
    both fire at 19:00 as asked.
    """
    from zoneinfo import ZoneInfo

    s = Scheduler()
    s.set_timezone(HOME, DUBLIN)
    automation = evening()

    summer = datetime(2026, 8, 20, 19, 0, tzinfo=ZoneInfo(DUBLIN)).astimezone(UTC)
    winter = datetime(2026, 12, 20, 19, 0, tzinfo=ZoneInfo(DUBLIN)).astimezone(UTC)

    assert s.due(HOME, [automation], summer)[0].fire_key == "2026-08-20T19:00"
    assert s.due(HOME, [automation], winter)[0].fire_key == "2026-12-20T19:00"
    # The two instants really are a different offset apart.
    assert summer.hour != winter.hour


# ── which days ──


def test_weekdays_restrict_which_days_it_may_fire() -> None:
    s = scheduler()
    # 2026-08-20 is a Thursday (weekday 3); allow Monday and Tuesday only.
    weekday_only = evening(weekdays=(0, 1))
    assert s.due(HOME, [weekday_only], utc("2026-08-20T19:00")) == []


def test_an_empty_weekday_set_means_every_day() -> None:
    s = scheduler()
    assert len(s.due(HOME, [evening()], utc("2026-08-20T19:00"))) == 1


def test_the_previous_allowed_day_is_the_one_that_could_be_due() -> None:
    """On a Thursday morning, the occurrence that might still be owed is
    Wednesday evening's — not one from a day the schedule excludes."""
    s = Scheduler()
    s.set_timezone(HOME, RIYADH)
    s.catch_up_window = timedelta(hours=24)
    wednesdays = evening(weekdays=(2,))
    due = s.due(HOME, [wednesdays], utc("2026-08-20T08:00"))
    assert len(due) == 1
    assert due[0].fire_key == "2026-08-19T19:00"
