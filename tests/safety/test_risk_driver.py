"""Something asks the risk engine to look at the house (spec §20).

Before this driver existed, `RiskEngineService.evaluate` was called by the test
suite and by nothing else. Every safety test passed against a component the
product never invoked — which is the sharpest version of the pattern in
`docs/GAPS.md` §6: the code was checked against itself, and the check that was
missing was "does anything run this at all".

So these tests are mostly about the loop's failure behaviour, not its happy
path. A driver that works when everything works is not the interesting case.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from syltra_action_orchestrator import ActionOrchestrator, OrchestratorConfig
from syltra_contracts import CommandResult
from syltra_policy_safety import PolicyService
from syltra_risk_engine import IsolationDispatcher, RiskEngineService
from syltra_risk_engine.driver import RiskDriver, RiskDriverHealth
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

pytestmark = pytest.mark.safety

NOW = datetime(2026, 8, 20, 3, 40, tzinfo=UTC)
HOME = "home_driven"
OTHER = "home_quiet"


class Twin:
    """Just enough twin: named homes, and the state of each."""

    def __init__(self, homes: dict[str, Any]) -> None:
        self._homes = homes

    @property
    def home_ids(self) -> list[str]:
        return sorted(self._homes)

    def home(self, home_id: str) -> Any:
        return self._homes.get(home_id)


class ValveGateway:
    def __init__(self) -> None:
        self.state: dict[tuple[str, str], Any] = {("valve_main", "valve.state"): "open"}
        self.commands: list[Any] = []

    async def execute_capability_command(self, command: Any) -> CommandResult:
        self.commands.append(command)
        self.state[(command.device_id, command.capability)] = command.value
        return CommandResult(accepted=True)

    async def read(self, device_id: str, capability: str) -> Any:
        return self.state.get((device_id, capability))


def alarming(home_id: str = HOME, *, gas: bool = True):  # type: ignore[no-untyped-def]
    return home(
        device("gas_kitchen", "kitchen", a=reading("safety.gas_alarm", gas, NOW)),
        device("valve_main", "kitchen", a=reading("valve.state", "open", NOW)),
        home_id=home_id,
    )


def wired() -> tuple[RiskEngineService, ValveGateway]:
    gateway = ValveGateway()
    policy = PolicyService()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision=policy.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
    )
    risk = RiskEngineService(
        isolation=IsolationDispatcher(policy=policy, orchestrator=orchestrator)
    )
    return risk, gateway


# ── the thing that was missing ──


async def test_one_pass_finds_the_alarm_nobody_was_reading() -> None:
    risk, gateway = wired()
    driver = RiskDriver(Twin({HOME: alarming()}), risk)

    assert await driver.run_once(NOW) == 1

    assert risk.open_cases(HOME, NOW), "the gas alarm should have produced a case"
    assert await gateway.read("valve_main", "valve.state") == "closed"


async def test_a_quiet_house_is_examined_and_nothing_happens() -> None:
    risk, gateway = wired()
    driver = RiskDriver(Twin({HOME: alarming(gas=False)}), risk)

    assert await driver.run_once(NOW) == 1
    assert gateway.commands == []
    assert await gateway.read("valve_main", "valve.state") == "open"


# ── failure containment, which is why the loop is written this way ──


async def test_one_household_failing_does_not_stop_the_next_being_examined() -> None:
    """The next house may be the one with the gas alarm.

    A driver that gives up on the first exception is a driver that stops
    watching every home after the first one with a bad reading.
    """
    risk, gateway = wired()

    class Exploding(Twin):
        def home(self, home_id: str) -> Any:
            if home_id == OTHER:
                msg = "this household's state is unreadable"
                raise RuntimeError(msg)
            return super().home(home_id)

    # OTHER sorts before HOME, so the failure happens first.
    driver = RiskDriver(Exploding({HOME: alarming(), OTHER: alarming(OTHER)}), risk)

    assert await driver.run_once(NOW) == 1, "one home failed, one was examined"
    assert await gateway.read("valve_main", "valve.state") == "closed"


async def test_a_home_with_no_state_is_skipped_rather_than_crashing() -> None:
    risk, _ = wired()
    driver = RiskDriver(Twin({HOME: None}), risk)
    assert await driver.run_once(NOW) == 1


async def test_the_loop_survives_a_pass_that_raises() -> None:
    class Broken:
        @property
        def home_ids(self) -> list[str]:
            msg = "the twin is unavailable"
            raise RuntimeError(msg)

        def home(self, home_id: str) -> Any:
            return None

    risk, _ = wired()
    driver = RiskDriver(Broken(), risk, interval_seconds=0.01)

    # Starting must succeed even though the first pass cannot: refusing to
    # start would leave nothing watching, where starting unhealthy leaves a
    # loop that retries and a flag that says it is not working.
    await driver.start()
    try:
        assert driver.health.started
        assert driver.health.consecutive_failures >= 1
        assert driver.health.last_error is not None
        assert not driver.health.is_healthy(datetime.now(tz=UTC), tolerance_seconds=60)
        await asyncio.sleep(0.05)
        assert driver.health.consecutive_failures >= 2, "the loop should keep trying"
    finally:
        await driver.stop()


# ── liveness, because a stopped safety loop must not look like a quiet house ──


def test_a_driver_that_never_ran_is_unhealthy_rather_than_unknown() -> None:
    health = RiskDriverHealth()
    assert not health.is_healthy(NOW, tolerance_seconds=5)


def test_a_stalled_driver_reports_unhealthy() -> None:
    health = RiskDriverHealth(started=True, last_completed_at=NOW - timedelta(seconds=30))
    assert not health.is_healthy(NOW, tolerance_seconds=5)
    assert health.is_healthy(NOW - timedelta(seconds=27), tolerance_seconds=5)


async def test_starting_the_driver_completes_a_pass_before_reporting_health() -> None:
    """Otherwise a hub reports "watching" during the window before it is.

    Built at the wall clock rather than at NOW, because `start` runs its first
    pass against the real time — and a reading from hours ago is stale, which
    is the freshness rule working rather than a broken driver.
    """
    risk, gateway = wired()
    live = datetime.now(tz=UTC)
    state = home(
        device("gas_kitchen", "kitchen", a=reading("safety.gas_alarm", True, live)),
        device("valve_main", "kitchen", a=reading("valve.state", "open", live)),
        home_id=HOME,
    )
    driver = RiskDriver(Twin({HOME: state}), risk, interval_seconds=10)
    await driver.start()
    try:
        assert driver.health.started
        assert driver.health.last_completed_at is not None
        assert await gateway.read("valve_main", "valve.state") == "closed"
    finally:
        await driver.stop()


async def test_stopping_the_driver_is_visible() -> None:
    risk, _ = wired()
    driver = RiskDriver(Twin({HOME: alarming(gas=False)}), risk, interval_seconds=0.01)
    await driver.start()
    await driver.stop()
    assert not driver.health.started
    assert not driver.health.is_healthy(datetime.now(tz=UTC), tolerance_seconds=0.001)


# ── the driver decides nothing ──


async def test_occupancy_is_unknown_rather_than_false_without_a_context_service() -> None:
    """The rules distinguish an empty house from an unread one.

    Passing `False` on no evidence would tell the risk rules the household is
    out, which changes what several of them conclude.
    """
    seen: dict[str, Any] = {}

    class Recording(RiskEngineService):
        def evaluate(
            self,
            home_id: str,
            home: Any,
            now: Any = None,
            occupied: Any = None,
            cooking: Any = False,
        ) -> Any:
            seen["occupied"] = occupied
            seen["cooking"] = cooking
            return super().evaluate(home_id, home, now, occupied, cooking)

    driver = RiskDriver(Twin({HOME: alarming()}), Recording())
    await driver.run_once(NOW)
    assert seen["occupied"] is None
    assert seen["cooking"] is False


# ── the hub says when nothing is watching ──


def test_a_platform_with_no_driver_reports_the_risk_engine_degraded() -> None:
    """The state the product was in until this module existed.

    `"risk_engine": "ok"` was hard-coded, so a hub with nothing reading its
    detectors reported itself healthy. That is the worst possible thing for
    this particular field to have said.
    """
    from syltra_api_gateway.openapi_export import _empty_platform

    platform = _empty_platform()
    assert platform.risk_driver is None
    assert platform.system_status()["components"]["risk_engine"] == "degraded"


async def test_a_running_driver_reports_the_risk_engine_ok() -> None:
    from syltra_api_gateway.openapi_export import _empty_platform

    risk, _ = wired()
    platform = _empty_platform()
    driver = RiskDriver(Twin({}), risk, interval_seconds=10)
    object.__setattr__(platform, "risk_driver", driver)

    assert platform.system_status()["components"]["risk_engine"] == "degraded"
    await driver.start()
    try:
        assert platform.system_status()["components"]["risk_engine"] == "ok"
    finally:
        await driver.stop()
    assert platform.system_status()["components"]["risk_engine"] == "degraded"


def test_the_development_server_starts_a_driver() -> None:
    """The wiring, checked rather than assumed.

    Remove the driver from `build_platform` and the hub silently goes back to
    never looking at its detectors — with every safety test still passing,
    because they all call `evaluate` themselves.
    """
    from syltra_api_gateway.devserver import build_platform

    platform = build_platform()
    assert platform.risk_driver is not None
    assert platform.risk_driver._risk is platform.risk
    assert platform.risk_driver._twin is platform.twin
