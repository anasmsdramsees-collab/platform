"""HomeAssistantDeviceGateway adapter tests against the mock HA boundary.

The adapter is the ONLY module permitted to translate canonical capabilities
into Home Assistant service calls (ADR-001). These tests exercise it through a
live connection so the translation is verified end to end, including the
round-trip state change the command produces.
"""

from collections.abc import AsyncIterator

import pytest
from syltra_contracts import CapabilityCommand
from syltra_edge_agent.gateway import HomeAssistantDeviceGateway
from syltra_simulator.harness import SimulationRun, wait_for


@pytest.fixture
async def gateway_pair() -> AsyncIterator[tuple[HomeAssistantDeviceGateway, SimulationRun]]:
    run = SimulationRun()
    await run.start()
    # 'pilot' exercises the non-blocked path; the development block has its own
    # dedicated safety tests in services/edge-agent/tests/test_gateway_safety.py.
    gateway = HomeAssistantDeviceGateway(run.service.client, run.service, "pilot")
    try:
        yield gateway, run
    finally:
        await run.stop()


async def test_list_devices_and_entities_come_from_the_registry(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, _ = gateway_pair
    devices = await gateway.list_devices()
    entities = await gateway.list_entities()
    assert any(d.device_id == "sim_light_living" for d in devices)
    assert any(e.entity_id == "light.living_room" for e in entities)
    # Vendor detail stays inside the adapter's inputs, not the contract types.
    living_light = next(d for d in devices if d.device_id == "sim_light_living")
    assert living_light.room_id == "living_room"
    assert "light.living_room" in living_light.entity_ids


async def test_get_state_returns_current_entity_state(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, run = gateway_pair
    await run.ha.set_state("sensor.living_room_temperature", "25.5")
    state = await gateway.get_state("sensor.living_room_temperature")
    assert state is not None
    assert state.state == "25.5"
    assert state.available


async def test_get_state_for_unknown_entity_is_none(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, _ = gateway_pair
    assert await gateway.get_state("sensor.does_not_exist") is None


async def test_registry_snapshot_is_available_after_bootstrap(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, _ = gateway_pair
    snapshot = await gateway.get_registry_snapshot()
    assert snapshot.devices and snapshot.entities and snapshot.states
    assert snapshot.taken_at.tzinfo is not None


async def test_light_power_command_reaches_the_device(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, run = gateway_pair
    result = await gateway.execute_capability_command(
        CapabilityCommand(device_id="sim_light_living", capability="light.power", value=True)
    )
    assert result.accepted
    await wait_for(
        lambda: any(e.value is True for e in run.events.capability_events("light.power"))
    )


async def test_light_power_false_maps_to_turn_off(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, run = gateway_pair
    await gateway.execute_capability_command(
        CapabilityCommand(device_id="sim_light_living", capability="light.power", value=True)
    )
    await wait_for(
        lambda: any(e.value is True for e in run.events.capability_events("light.power"))
    )
    await gateway.execute_capability_command(
        CapabilityCommand(device_id="sim_light_living", capability="light.power", value=False)
    )
    await wait_for(lambda: run.events.capability_events("light.power")[-1].value is False)


async def test_brightness_command_translates_to_percent(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, run = gateway_pair
    result = await gateway.execute_capability_command(
        CapabilityCommand(device_id="sim_light_living", capability="light.brightness", value=50)
    )
    assert result.accepted
    await wait_for(
        lambda: any(
            abs(float(e.value) - 50.0) < 1.0
            for e in run.events.capability_events("light.brightness")
        )
    )


async def test_climate_target_temperature_command(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, run = gateway_pair
    result = await gateway.execute_capability_command(
        CapabilityCommand(
            device_id="sim_ac_living", capability="climate.target_temperature", value=23.0
        )
    )
    assert result.accepted
    await wait_for(
        lambda: any(
            e.value == 23.0 for e in run.events.capability_events("climate.target_temperature")
        )
    )


async def test_cover_position_command(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, run = gateway_pair
    result = await gateway.execute_capability_command(
        CapabilityCommand(device_id="sim_curtain_living", capability="cover.position", value=30)
    )
    assert result.accepted
    await wait_for(
        lambda: any(e.value == 30.0 for e in run.events.capability_events("cover.position"))
    )


async def test_device_health_reports_online_and_battery(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, _ = gateway_pair
    health = await gateway.get_device_health("sim_motion_living")
    assert health is not None
    assert health.online
    assert health.battery_percent == 87.0


async def test_device_health_for_unknown_device_is_none(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, _ = gateway_pair
    assert await gateway.get_device_health("no_such_device") is None


async def test_state_change_subscription_yields_pushed_states(
    gateway_pair: tuple[HomeAssistantDeviceGateway, SimulationRun],
) -> None:
    gateway, _ = gateway_pair
    from syltra_contracts import EntityState

    stream = gateway.subscribe_state_changes()
    await gateway.push_state_change(EntityState(entity_id="light.living_room", state="on"))
    received = await anext(stream)
    assert received.entity_id == "light.living_room"
