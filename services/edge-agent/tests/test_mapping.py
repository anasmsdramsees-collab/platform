"""Entity → capability mapping tests (spec §10, §14.1)."""

import pytest
from syltra_contracts import ALL_CAPABILITIES
from syltra_edge_agent.mapping import CapabilityReading, MappingError, map_ha_state


def _caps(readings: list[CapabilityReading]) -> set[str]:
    return {r.capability for r in readings}


@pytest.mark.parametrize(
    ("entity_id", "state", "attributes", "capability", "value"),
    [
        ("sensor.a", "27.4", {"device_class": "temperature"}, "environment.temperature", 27.4),
        ("sensor.b", "41", {"device_class": "humidity"}, "environment.humidity", 41.0),
        ("sensor.c", "180", {"device_class": "illuminance"}, "environment.illuminance", 180.0),
        ("sensor.d", "640", {"device_class": "power"}, "energy.power", 640.0),
        ("sensor.e", "87", {"device_class": "battery"}, "device.battery", 87.0),
        ("binary_sensor.f", "on", {"device_class": "motion"}, "occupancy.motion", True),
        ("binary_sensor.g", "off", {"device_class": "motion"}, "occupancy.motion", False),
        ("binary_sensor.h", "on", {"device_class": "door"}, "contact.open", True),
        ("binary_sensor.i", "on", {"device_class": "gas"}, "safety.gas_alarm", True),
        ("binary_sensor.j", "on", {"device_class": "moisture"}, "safety.water_leak", True),
        ("binary_sensor.k", "on", {"device_class": "smoke"}, "safety.smoke_alarm", True),
        ("device_tracker.l", "home", {}, "occupancy.presence", True),
        ("device_tracker.m", "not_home", {}, "occupancy.presence", False),
        ("switch.n", "on", {}, "switch.power", True),
        ("lock.o", "locked", {}, "lock.state", "locked"),
        ("valve.p", "open", {}, "valve.state", "open"),
        ("camera.q", "recording", {}, "camera.recording", True),
    ],
)
def test_single_capability_mappings(
    entity_id: str,
    state: str,
    attributes: dict[str, object],
    capability: str,
    value: object,
) -> None:
    readings = map_ha_state(entity_id, state, attributes)
    assert len(readings) == 1
    assert readings[0].capability == capability
    assert readings[0].value == value


def test_light_maps_power_and_brightness_as_percent() -> None:
    readings = map_ha_state("light.a", "on", {"brightness": 255})
    assert _caps(readings) == {"light.power", "light.brightness"}
    brightness = next(r for r in readings if r.capability == "light.brightness")
    assert brightness.value == 100.0
    assert brightness.unit == "%"


def test_climate_maps_mode_and_target_temperature() -> None:
    readings = map_ha_state("climate.a", "cool", {"temperature": 23.0})
    assert _caps(readings) == {"climate.mode", "climate.target_temperature"}


def test_cover_position_from_attribute_and_from_state() -> None:
    assert map_ha_state("cover.a", "open", {"current_position": 40})[0].value == 40.0
    assert map_ha_state("cover.a", "closed", {})[0].value == 0.0


def test_unavailable_state_becomes_device_offline() -> None:
    readings = map_ha_state("sensor.a", "unavailable", {"device_class": "temperature"})
    assert readings[0].capability == "device.online"
    assert readings[0].value is False


def test_unknown_state_produces_no_reading() -> None:
    assert map_ha_state("sensor.a", "unknown", {"device_class": "temperature"}) == []


def test_entity_outside_capability_model_is_rejected_not_invented() -> None:
    # An unmapped entity yields no readings — it must never be forced into a
    # capability the intelligence layer would then trust.
    assert map_ha_state("sensor.a", "42", {"device_class": "pressure"}) == []
    assert map_ha_state("media_player.tv", "playing", {}) == []


def test_non_numeric_sensor_value_is_invalid() -> None:
    with pytest.raises(MappingError) as exc:
        map_ha_state("sensor.a", "warm", {"device_class": "temperature"})
    assert exc.value.reason_code == "NON_NUMERIC_SENSOR_VALUE"


def test_malformed_entity_id_is_invalid() -> None:
    with pytest.raises(MappingError) as exc:
        map_ha_state("no_domain", "on", {})
    assert exc.value.reason_code == "INVALID_ENTITY_ID"


def test_every_mapping_result_is_a_canonical_capability() -> None:
    samples: list[tuple[str, str, dict[str, object]]] = [
        ("sensor.a", "1", {"device_class": "temperature"}),
        ("binary_sensor.b", "on", {"device_class": "motion"}),
        ("light.c", "on", {"brightness": 128}),
        ("climate.d", "cool", {"temperature": 22}),
        ("cover.e", "open", {"current_position": 50}),
    ]
    for entity_id, state, attributes in samples:
        for reading in map_ha_state(entity_id, state, attributes):
            assert reading.capability in ALL_CAPABILITIES
