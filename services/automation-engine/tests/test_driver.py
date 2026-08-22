"""Something runs the household's automations (ADR-009).

Before this driver, `AutomationEngine.evaluate` was reachable from the *test
run* button and from nothing else. A household could write an automation, watch
a dry run say it would fire, enable it, and wait forever — the third time in
this build that a correct component had no caller.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from syltra_automation_engine import AutomationEngine
from syltra_automation_engine.driver import AutomationDriver
from syltra_contracts import (
    Automation,
    AutomationAction,
    AutomationTrigger,
    TriggerKind,
)
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

HOME = "home_auto"
RIYADH = "Asia/Riyadh"
NOW = datetime(2026, 8, 20, 19, 0, tzinfo=ZoneInfo(RIYADH)).astimezone(UTC)


class Twin:
    def __init__(self, homes: dict[str, Any]) -> None:
        self._homes = homes

    @property
    def home_ids(self) -> list[str]:
        return sorted(self._homes)

    def home(self, home_id: str) -> Any:
        return self._homes.get(home_id)


def house() -> Any:
    return home(
        device("motion_living", "living_room", a=reading("occupancy.motion", True, NOW)),
        device("light_living", "living_room", a=reading("light.power", False, NOW)),
        home_id=HOME,
    )


def at_seven() -> Automation:
    return Automation(
        automation_id=uuid4(),
        home_id=HOME,
        name="Evening lights",
        owner="amal",
        trigger=AutomationTrigger(kind=TriggerKind.AT_TIME, at_hour=19, at_minute=0),
        actions=(
            AutomationAction(capability="light.power", value=True, device_id="light_living"),
        ),
    )


def driver(
    engine: AutomationEngine, changes: list[tuple[str, tuple[str, ...]]]
) -> AutomationDriver:
    d = AutomationDriver(
        Twin({HOME: house()}), engine, on_change=lambda h, r: changes.append((h, r))
    )
    d.scheduler.set_timezone(HOME, RIYADH)
    return d


@pytest.mark.asyncio
async def test_a_scheduled_automation_comes_due_on_the_household_clock() -> None:
    engine = AutomationEngine()
    engine.upsert(at_seven())
    changes: list[tuple[str, tuple[str, ...]]] = []

    assert await driver(engine, changes).run_once(NOW) == 1

    reasons = [r for _, group in changes for r in group]
    assert any(r.startswith("SCHEDULED_") for r in reasons)


@pytest.mark.asyncio
async def test_it_does_not_come_due_twice() -> None:
    engine = AutomationEngine()
    engine.upsert(at_seven())
    changes: list[tuple[str, tuple[str, ...]]] = []
    d = driver(engine, changes)

    await d.run_once(NOW)
    before = len(changes)
    await d.run_once(NOW + timedelta(seconds=30))
    scheduled = [r for _, group in changes[before:] for r in group if r.startswith("SCHEDULED_")]
    assert scheduled == []


@pytest.mark.asyncio
async def test_a_household_that_fails_does_not_stop_the_next() -> None:
    class Exploding(Twin):
        def home(self, home_id: str) -> Any:
            if home_id == "home_bad":
                msg = "unreadable"
                raise RuntimeError(msg)
            return super().home(home_id)

    engine = AutomationEngine()
    d = AutomationDriver(Exploding({HOME: house(), "home_bad": house()}), engine)
    assert await d.run_once(NOW) == 1


@pytest.mark.asyncio
async def test_the_loop_starts_and_stops_and_says_which() -> None:
    engine = AutomationEngine()
    d = AutomationDriver(Twin({HOME: house()}), engine, interval_seconds=0.01)
    await d.start()
    try:
        assert d.health.started
        assert d.health.is_healthy(datetime.now(tz=UTC), tolerance_seconds=30)
    finally:
        await d.stop()
    assert not d.health.started


def test_the_development_server_starts_an_automation_driver() -> None:
    """The wiring, checked rather than assumed.

    Remove it and every automation silently stops firing, with the whole suite
    still green — which is exactly how it was before this existed.
    """
    from syltra_api_gateway.devserver import build_platform

    platform = build_platform()
    assert platform.automation_driver is not None
    assert platform.automation_driver.scheduler.timezones, "the household's clock must be set"


def test_a_platform_with_no_automation_driver_reports_degraded() -> None:
    from syltra_api_gateway.openapi_export import _empty_platform

    platform = _empty_platform()
    assert platform.system_status()["components"]["automation_engine"] == "degraded"


# ── goals ride the same loop ──


async def test_the_driver_corrects_a_goal_that_is_not_holding() -> None:
    """A goal is checked on a clock rather than fired by an event — a hub that
    only reacted to readings would never notice a goal it broke by doing
    nothing."""
    from syltra_automation_engine import GoalRegistry
    from syltra_contracts import Goal, GoalComparison

    goals = GoalRegistry()
    goals.upsert(
        Goal(
            home_id=HOME,
            name="الصالة لا تتجاوز ٢٤",
            capability="environment.temperature",
            comparison=GoalComparison.AT_MOST,
            value=24,
            room_id="living_room",
            actions=(
                AutomationAction(
                    capability="climate.target_temperature", value=22, device_id="ac_living"
                ),
            ),
        )
    )

    dispatched: list[Any] = []

    class Dispatcher:
        async def dispatch_all(self, proposals: Any, now: Any = None) -> tuple[Any, ...]:
            dispatched.extend(proposals)
            return tuple(type("O", (), {"carried_out": True, "name": p.name})() for p in proposals)

    hot = home(
        device("temp_living", "living_room", a=reading("environment.temperature", 27.0, NOW)),
        home_id=HOME,
    )
    driver = AutomationDriver(
        Twin({HOME: hot}),
        AutomationEngine(),
        dispatcher=Dispatcher(),  # type: ignore[arg-type]
        goals=goals,
    )
    await driver.run_once(NOW)

    assert [p.action.capability for p in dispatched] == ["climate.target_temperature"]


async def test_the_driver_never_corrects_a_goal_it_cannot_measure() -> None:
    """Correcting a room nobody can see is guessing with somebody's air
    conditioning."""
    from syltra_automation_engine import GoalRegistry
    from syltra_contracts import Goal, GoalComparison

    goals = GoalRegistry()
    goals.upsert(
        Goal(
            home_id=HOME,
            name="غرفة بلا حسّاس",
            capability="environment.temperature",
            comparison=GoalComparison.AT_MOST,
            value=24,
            room_id="cellar",
            actions=(
                AutomationAction(
                    capability="climate.target_temperature", value=22, device_id="ac_cellar"
                ),
            ),
        )
    )

    dispatched: list[Any] = []

    class Dispatcher:
        async def dispatch_all(self, proposals: Any, now: Any = None) -> tuple[Any, ...]:
            dispatched.extend(proposals)
            return ()

    driver = AutomationDriver(
        Twin({HOME: house()}),
        AutomationEngine(),
        dispatcher=Dispatcher(),  # type: ignore[arg-type]
        goals=goals,
    )
    await driver.run_once(NOW)

    assert dispatched == []
