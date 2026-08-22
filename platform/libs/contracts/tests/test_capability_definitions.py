"""Capability definition tests (spec §10.3).

These lock in the safety-relevant attributes that later phases depend on:
a model must never be able to command a life-safety actuator, and stale data
must never support a decision.
"""

import pytest
from syltra_contracts import ALL_CAPABILITIES, SafetyClass
from syltra_contracts.capabilities import CRITICAL_ACTUATOR_CAPABILITIES, SENSOR_CAPABILITIES
from syltra_contracts.capability_definitions import (
    CAPABILITY_DEFINITIONS,
    Access,
    Confirmation,
    DataType,
    get_definition,
    is_writable,
)

pytestmark = pytest.mark.contract


def test_every_capability_has_a_definition() -> None:
    assert set(CAPABILITY_DEFINITIONS) == ALL_CAPABILITIES


def test_every_definition_declares_all_spec_fields() -> None:
    for definition in CAPABILITY_DEFINITIONS.values():
        assert isinstance(definition.data_type, DataType)
        assert isinstance(definition.access, Access)
        assert isinstance(definition.safety_class, SafetyClass)
        assert definition.freshness_seconds > 0
        assert isinstance(definition.reversible, bool)
        assert isinstance(definition.confirmation, Confirmation)


def test_sensors_are_read_only() -> None:
    for capability in SENSOR_CAPABILITIES:
        assert not is_writable(capability), f"{capability} must not be writable"


@pytest.mark.safety
def test_life_safety_actuators_require_deterministic_rules() -> None:
    # Safety invariant 18: critical rules use approved device capabilities, never
    # inferred or model output. Gas valves and breakers must be unreachable by
    # anything except a deterministic approved safety rule.
    for capability in ("valve.state", "breaker.state", "siren.state"):
        definition = get_definition(capability)
        assert definition.confirmation is Confirmation.DETERMINISTIC_SAFETY_RULE


@pytest.mark.safety
def test_no_critical_actuator_permits_unconfirmed_automation() -> None:
    # Safety invariant 13: locks, valves, breakers, sirens and garage doors use
    # separate policy classes — none may execute with Confirmation.NONE.
    for capability in CRITICAL_ACTUATOR_CAPABILITIES:
        definition = get_definition(capability)
        assert definition.confirmation is not Confirmation.NONE
        assert definition.safety_class is not SafetyClass.NON_CRITICAL
        assert definition.safety_class is not SafetyClass.COMFORT


@pytest.mark.safety
def test_alarm_sensors_have_tight_freshness_requirements() -> None:
    # Safety invariant 4: a stale sensor value cannot confirm a risk. Alarm
    # inputs must go stale quickly rather than linger as apparent truth.
    for capability in (
        "safety.smoke_alarm",
        "safety.heat_alarm",
        "safety.gas_alarm",
        "safety.co_alarm",
    ):
        assert get_definition(capability).freshness_seconds <= 120


@pytest.mark.safety
def test_life_safety_capabilities_are_fresher_than_comfort_ones() -> None:
    life_safety = max(
        d.freshness_seconds
        for d in CAPABILITY_DEFINITIONS.values()
        if d.safety_class is SafetyClass.LIFE_SAFETY_CRITICAL
    )
    comfort = min(
        d.freshness_seconds
        for d in CAPABILITY_DEFINITIONS.values()
        if d.safety_class is SafetyClass.COMFORT
    )
    assert life_safety <= comfort


def test_comfort_actuators_are_reversible() -> None:
    for capability in (
        "light.power",
        "light.brightness",
        "climate.target_temperature",
        "cover.position",
        "switch.power",
    ):
        assert get_definition(capability).reversible


def test_breaker_is_marked_irreversible() -> None:
    # Re-closing a breaker is not a safe automatic compensating action.
    assert get_definition("breaker.state").reversible is False


@pytest.mark.parametrize(
    ("capability", "value", "expected"),
    [
        ("climate.target_temperature", 23, True),
        ("climate.target_temperature", 5, False),  # below minimum
        ("climate.target_temperature", 45, False),  # above maximum
        ("light.brightness", 0, True),
        ("light.brightness", 101, False),
        ("light.power", True, True),
        ("light.power", 1, False),  # int is not a boolean
        ("environment.humidity", 50.5, True),
        ("climate.mode", "cool", True),
        ("climate.mode", "turbo", False),  # outside the enum
        ("lock.state", "locked", True),
        ("lock.state", "exploded", False),
    ],
)
def test_range_and_enum_validation(capability: str, value: object, expected: bool) -> None:
    assert get_definition(capability).is_within_range(value) is expected


def test_unknown_capability_lookup_raises() -> None:
    with pytest.raises(KeyError, match="unknown capability"):
        get_definition("vendor.magic")


def test_temperature_setpoint_range_is_habitable() -> None:
    # Guards against an automation being allowed to set a dangerous setpoint.
    definition = get_definition("climate.target_temperature")
    assert definition.minimum is not None and definition.minimum >= 16
    assert definition.maximum is not None and definition.maximum <= 30
