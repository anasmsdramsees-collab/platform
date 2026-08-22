"""Capability registry must match spec §10.1/§10.2 exactly."""

import pytest
from syltra_contracts import (
    ACTUATOR_CAPABILITIES,
    ALL_CAPABILITIES,
    SENSOR_CAPABILITIES,
    is_known_capability,
)
from syltra_contracts.capabilities import CRITICAL_ACTUATOR_CAPABILITIES

pytestmark = pytest.mark.contract

SPEC_SENSORS = {
    "occupancy.motion",
    "occupancy.presence",
    "contact.open",
    "environment.temperature",
    "environment.humidity",
    "environment.illuminance",
    "environment.air_quality",
    "safety.smoke_alarm",
    "safety.heat_alarm",
    "safety.gas_alarm",
    "safety.co_alarm",
    "safety.water_leak",
    "energy.power",
    "energy.current",
    "energy.voltage",
    "energy.consumption",
    "device.online",
    "device.battery",
}

SPEC_ACTUATORS = {
    "light.power",
    "light.brightness",
    "switch.power",
    "climate.mode",
    "climate.target_temperature",
    "cover.position",
    "lock.state",
    "valve.state",
    "breaker.state",
    "siren.state",
    "garage.state",
    "camera.recording",
    "notification.send",
}


def test_sensor_capabilities_match_spec() -> None:
    assert SENSOR_CAPABILITIES == SPEC_SENSORS


def test_actuator_capabilities_match_spec() -> None:
    assert ACTUATOR_CAPABILITIES == SPEC_ACTUATORS


def test_registry_is_disjoint_and_complete() -> None:
    assert SENSOR_CAPABILITIES.isdisjoint(ACTUATOR_CAPABILITIES)
    assert ALL_CAPABILITIES == SPEC_SENSORS | SPEC_ACTUATORS


def test_lookup_helper() -> None:
    assert is_known_capability("climate.target_temperature")
    assert not is_known_capability("vendor.magic_mode")


@pytest.mark.safety
def test_critical_actuators_are_a_subset_of_actuators() -> None:
    # Locks, gas valves, breakers, sirens, and garage doors carry separate
    # policy classes (safety invariant 13) and must all be known actuators.
    assert CRITICAL_ACTUATOR_CAPABILITIES <= ACTUATOR_CAPABILITIES
    assert {
        "lock.state",
        "valve.state",
        "breaker.state",
        "siren.state",
        "garage.state",
    } == CRITICAL_ACTUATOR_CAPABILITIES
