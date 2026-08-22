"""Phase 1 integration tests: mock Home Assistant → Edge Agent → events.

These exercise the real service loop (connection, bootstrap, subscription,
normalization, publishing) against the mock Home Assistant boundary that spec
§24.3 permits. No physical devices and no household data are involved.
"""

import asyncio
from collections.abc import AsyncIterator

import pytest
from syltra_edge_agent import metrics
from syltra_simulator.harness import SimulationRun, wait_for
from syltra_simulator.scenarios import SCENARIOS


@pytest.fixture
async def run() -> AsyncIterator[SimulationRun]:
    simulation = SimulationRun()
    await simulation.start()
    try:
        yield simulation
    finally:
        await simulation.stop()


async def test_bootstrap_discovers_devices_and_seeds_states(run: SimulationRun) -> None:
    snapshot = run.service.registry_snapshot
    assert snapshot is not None
    assert len(snapshot.devices) >= 15
    assert any(d.device_id == "sim_ac_living" for d in snapshot.devices)
    # Devices are announced and current states seeded through the pipeline.
    assert any(e.event_type == "device.discovered" for _, e in run.events.normalized)
    assert run.events.capability_events("environment.temperature")


async def test_rooms_are_attached_from_the_area_registry(run: SimulationRun) -> None:
    temps = run.events.capability_events("environment.temperature")
    assert temps
    assert temps[0].subject.room_id == "living_room"


async def test_state_change_becomes_normalized_capability_event(run: SimulationRun) -> None:
    await run.ha.set_state("sensor.living_room_temperature", "29.5")
    await wait_for(
        lambda: any(
            e.value == 29.5 for e in run.events.capability_events("environment.temperature")
        )
    )
    event = next(
        e for e in run.events.capability_events("environment.temperature") if e.value == 29.5
    )
    assert event.unit == "°C"
    assert event.subject.entity_id == "sensor.living_room_temperature"
    assert event.subject.device_id == "sim_climate_sensor_living"
    assert event.home_id == "home_sim_001"
    assert event.quality == 1.0


async def test_every_normalized_event_has_a_raw_counterpart(run: SimulationRun) -> None:
    before_raw = len(run.events.raw)
    await run.ha.set_state("binary_sensor.living_room_motion", "on")
    await wait_for(lambda: len(run.events.raw) > before_raw)
    assert len(run.events.raw) > before_raw


async def test_invalid_event_reaches_dead_letter_with_reason_code(
    run: SimulationRun,
) -> None:
    await run.ha.emit_raw_event(
        {"entity_id": "sensor.living_room_temperature", "new_state": {"attributes": {}}}
    )
    await wait_for(lambda: len(run.events.deadletter) == 1)
    record = run.events.deadletter[0]
    assert record["reason_codes"] == ["MISSING_STATE"]
    assert record["payload"]["entity_id"] == "sensor.living_room_temperature"


async def test_non_numeric_sensor_value_reaches_dead_letter(run: SimulationRun) -> None:
    await run.ha.set_state("sensor.living_room_temperature", "quite warm")
    await wait_for(lambda: len(run.events.deadletter) >= 1)
    assert any(r["reason_codes"] == ["NON_NUMERIC_SENSOR_VALUE"] for r in run.events.deadletter)


async def test_duplicate_delivery_publishes_once(run: SimulationRun) -> None:
    await run.ha.set_state("binary_sensor.kitchen_leak", "on")
    # Wait for this specific transition, not merely "any leak event" — bootstrap
    # already seeded the initial 'off' reading.
    await wait_for(
        lambda: any(e.value is True for e in run.events.capability_events("safety.water_leak"))
    )
    baseline = len(run.events.capability_events("safety.water_leak"))
    for _ in range(3):
        await run.ha.emit_raw_event(
            {
                "entity_id": "binary_sensor.kitchen_leak",
                "new_state": run.ha._states["binary_sensor.kitchen_leak"],
            }
        )
    await asyncio.sleep(0.3)
    assert len(run.events.capability_events("safety.water_leak")) == baseline


async def test_unavailable_device_marked_then_recovers(run: SimulationRun) -> None:
    await run.ha.set_state("sensor.living_room_temperature", "unavailable")
    await wait_for(
        lambda: any(e.value is False for e in run.events.capability_events("device.online"))
    )
    offline = next(e for e in run.events.capability_events("device.online") if e.value is False)
    assert offline.event_type == "device.availability.changed"

    await run.ha.set_state("sensor.living_room_temperature", "26.8")
    await wait_for(
        lambda: any(
            e.value == 26.8 for e in run.events.capability_events("environment.temperature")
        )
    )


async def test_unmapped_entity_does_not_enter_normalized_stream(
    run: SimulationRun,
) -> None:
    await run.ha.set_state("camera.entrance", "idle")
    await asyncio.sleep(0.2)
    # camera.recording is mapped; an entity outside the model must not appear.
    assert not [e for _, e in run.events.normalized if e.capability == "media.state"]


async def test_agent_reconnects_after_home_assistant_restart(run: SimulationRun) -> None:
    assert run.service.connected
    before = metrics.RECONNECTS._value.get()
    await run.ha.restart_connections()
    # Reconnection can complete faster than a poll interval, so assert on the
    # reconnect counter rather than trying to observe the disconnected instant.
    await wait_for(lambda: metrics.RECONNECTS._value.get() > before, timeout=15.0)
    await wait_for(lambda: run.service.connected, timeout=15.0)

    # And the pipeline works again afterwards.
    await run.ha.set_state("sensor.living_room_temperature", "31.1")
    await wait_for(
        lambda: any(
            e.value == 31.1 for e in run.events.capability_events("environment.temperature")
        ),
        timeout=15.0,
    )


async def test_state_continuity_across_reconnect(run: SimulationRun) -> None:
    await run.ha.set_state("light.living_room", "on", {"brightness": 255})
    await wait_for(
        lambda: any(e.value is True for e in run.events.capability_events("light.power"))
    )
    await run.ha.restart_connections()
    await wait_for(lambda: run.service.connected, timeout=15.0)
    # Re-bootstrap re-seeds current state, so the twin can recover from the stream.
    await wait_for(
        lambda: (
            len([e for e in run.events.capability_events("light.power") if e.value is True]) >= 2
        ),
        timeout=15.0,
    )


@pytest.mark.parametrize("scenario_name", sorted(SCENARIOS))
async def test_scenarios_meet_their_expectations(run: SimulationRun, scenario_name: str) -> None:
    scenario = SCENARIOS[scenario_name]
    _, before_norm, before_dl = run.mark()
    await run.run_scenario(scenario)
    normalized = len(run.events.normalized) - before_norm
    deadletter = len(run.events.deadletter) - before_dl
    if "normalized" in scenario.expects:
        assert normalized >= scenario.expects["normalized"]
    if "deadletter" in scenario.expects:
        assert deadletter == scenario.expects["deadletter"]
