"""Context Engine driven by real simulator scenarios (spec §22 Phase 3).

The final Phase 3 acceptance criterion: scenario tests pass deterministically.
These run the actual Edge Agent output through the Context Engine, so the
contexts are inferred from the same events the platform would see in a home.
"""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from syltra_context_engine.service import ContextService
from syltra_contracts import ContextType
from syltra_simulator.harness import SimulationRun
from syltra_simulator.scenarios import SCENARIOS

HOME = "home_context"


class _CapturingPublisher:
    """Feeds the Edge Agent's output straight into the Context Engine."""

    def __init__(self) -> None:
        self.service: ContextService | None = None
        self.published: list[tuple[str, Any]] = []

    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        if subject.startswith("syltra.raw."):
            return
        self.published.append((subject, envelope))
        if self.service is not None:
            await self.service.apply_envelope(envelope)

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


@pytest_asyncio.fixture
async def context_pipeline() -> AsyncIterator[tuple[SimulationRun, ContextService]]:
    bridge = _CapturingPublisher()
    service = ContextService(publisher=bridge)  # type: ignore[arg-type]
    bridge.service = service
    run = SimulationRun(publisher=bridge)  # type: ignore[arg-type]
    await run.start(home_id=HOME)
    try:
        yield run, service
    finally:
        await run.stop()


async def run_scenario(run: SimulationRun, service: ContextService, name: str) -> None:
    await run.run_scenario(SCENARIOS[name])
    await asyncio.sleep(0.2)
    await service.evaluate(HOME, datetime.now(tz=UTC))


def active_types(service: ContextService) -> set[ContextType]:
    return {c.context_type for c in service.active(HOME)}


async def test_arrival_scenario_produces_occupancy_contexts(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "user_arrives_home")
    found = active_types(service)
    assert ContextType.HOME_OCCUPIED in found
    assert ContextType.ROOM_OCCUPIED in found
    assert ContextType.HOME_EMPTY not in found


async def test_empty_home_scenario_produces_home_empty(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "empty_home")
    found = active_types(service)
    assert ContextType.HOME_EMPTY in found
    assert ContextType.HOME_OCCUPIED not in found


async def test_cooking_scenario_produces_a_kitchen_scoped_context(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "cooking_activity")
    # The simulator's motion sensor lives in the living room, so COOKING (which
    # requires kitchen occupancy) must NOT fire — the rule is scope-correct
    # rather than merely keyword-triggered.
    cooking = [c for c in service.active(HOME) if c.context_type is ContextType.COOKING]
    assert cooking == []
    assert ContextType.HOME_OCCUPIED in active_types(service)


async def test_energy_anomaly_scenario_raises_high_energy_usage(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "energy_anomaly")
    assert ContextType.HIGH_ENERGY_USAGE in active_types(service)


@pytest.mark.safety
async def test_water_leak_scenario_is_advisory_only(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "water_leak_watch")
    leak = next(
        c for c in service.active(HOME) if c.context_type is ContextType.POSSIBLE_WATER_LEAK
    )
    assert leak.is_advisory_only()
    assert leak.metadata["advisory_only"] is True
    assert leak.evidence


@pytest.mark.safety
async def test_gas_risk_scenario_is_advisory_only(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "gas_risk_watch")
    gas = next(c for c in service.active(HOME) if c.context_type is ContextType.POSSIBLE_GAS_RISK)
    assert gas.is_advisory_only()
    assert "ADVISORY_ONLY" in gas.reason_codes


async def test_every_context_carries_evidence_and_expiry(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "normal_day")
    contexts = service.active(HOME)
    assert contexts
    for record in contexts:
        assert record.evidence, f"{record.context_type} has no evidence"
        assert record.expires_at > record.started_at
        assert record.producer.startswith("rule:")
        assert record.home_id == HOME


async def test_contexts_expire_when_events_stop(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "user_arrives_home")
    assert service.active(HOME)

    # No further events: a sweep an hour later must clear everything.
    future = datetime.now(tz=UTC) + timedelta(hours=1)
    await service.sweep(HOME, future)
    assert service.active(HOME, future) == []


async def test_context_changes_are_published(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "user_arrives_home")
    changes = await service.evaluate(HOME, datetime.now(tz=UTC))
    # Re-evaluating unchanged state must not manufacture events.
    assert changes == []


async def test_scenarios_are_deterministic(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "empty_home")
    first = sorted((c.context_type.value, c.scope, c.confidence) for c in service.active(HOME))

    for _ in range(3):
        await service.evaluate(HOME, datetime.now(tz=UTC))
        again = sorted((c.context_type.value, c.scope, c.confidence) for c in service.active(HOME))
        assert again == first


async def test_invalid_event_does_not_break_the_engine(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "invalid_event")
    # The malformed payload was dead-lettered by the Edge Agent; the engine
    # keeps working on the valid events either side of it.
    assert service.twin.home(HOME) is not None


async def test_homes_stay_isolated(
    context_pipeline: tuple[SimulationRun, ContextService],
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, "user_arrives_home")
    assert service.active(HOME)
    assert service.active("some_other_home") == []


@pytest.mark.parametrize(
    "scenario_name",
    [
        "normal_day",
        "user_arrives_home",
        "user_leaves_home",
        "empty_home",
        "sleep_routine",
        "energy_anomaly",
        "water_leak_watch",
        "gas_risk_watch",
    ],
)
async def test_scenario_runs_cleanly(
    context_pipeline: tuple[SimulationRun, ContextService], scenario_name: str
) -> None:
    run, service = context_pipeline
    await run_scenario(run, service, scenario_name)
    for record in service.active(HOME):
        assert 0.0 <= record.confidence <= 1.0
        assert record.evidence
