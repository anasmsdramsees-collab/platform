"""Deterministic scenarios (spec §23).

Each scenario is a fixed sequence of steps against the mock Home Assistant
boundary; identical runs produce identical event sequences. Phase 1 ships the
scenarios the Edge Agent pipeline needs; the remaining spec §23 scenarios land
with the services that consume them (tracked in IMPLEMENTATION_STATUS.md).
"""

from dataclasses import dataclass, field
from datetime import timedelta
from enum import StrEnum
from typing import Any

from syltra_simulator.mock_ha import MockHomeAssistant


class StepKind(StrEnum):
    SET = "SET"                # normal state change
    DUPLICATE = "DUPLICATE"    # re-emit the entity's current state verbatim
    BACKDATED = "BACKDATED"    # emit with a timestamp older than current
    MALFORMED = "MALFORMED"    # structurally invalid payload → dead-letter
    OFFLINE = "OFFLINE"        # entity becomes unavailable
    RESTART = "RESTART"        # drop all connections (HA restart)


@dataclass(frozen=True)
class ScenarioStep:
    kind: StepKind
    entity_id: str = ""
    state: str = ""
    attributes: dict[str, Any] | None = None
    backdate_seconds: float = 0.0


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    steps: tuple[ScenarioStep, ...]
    expects: dict[str, int] = field(default_factory=dict)
    """Minimum expected pipeline outcomes, e.g. {"normalized": 5, "deadletter": 1}."""


async def apply_step(ha: MockHomeAssistant, step: ScenarioStep) -> None:
    if step.kind is StepKind.SET:
        await ha.set_state(step.entity_id, step.state, step.attributes)
    elif step.kind is StepKind.OFFLINE:
        await ha.set_state(step.entity_id, "unavailable")
    elif step.kind is StepKind.DUPLICATE:
        current = dict((await _current(ha, step.entity_id)))
        await ha.emit_raw_event(
            {"entity_id": step.entity_id, "old_state": None, "new_state": current}
        )
    elif step.kind is StepKind.BACKDATED:
        stamp = ha.advance_clock(0.0) - timedelta(seconds=step.backdate_seconds)
        await ha.set_state(step.entity_id, step.state, step.attributes, last_updated=stamp)
    elif step.kind is StepKind.MALFORMED:
        await ha.emit_raw_event(
            {"entity_id": step.entity_id, "new_state": {"attributes": {}, "state": None}}
        )
    elif step.kind is StepKind.RESTART:
        await ha.restart_connections()


async def _current(ha: MockHomeAssistant, entity_id: str) -> dict[str, Any]:
    states = ha._states  # noqa: SLF001 - simulator-internal accessor
    return states[entity_id]


SCENARIOS: dict[str, Scenario] = {
    "normal_day": Scenario(
        name="normal_day",
        description="Compressed ordinary day: presence, motion, comfort changes",
        steps=(
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "on"),
            ScenarioStep(StepKind.SET, "sensor.living_room_temperature", "27.9"),
            ScenarioStep(StepKind.SET, "light.living_room", "on", {"brightness": 200}),
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "off"),
            ScenarioStep(StepKind.SET, "sensor.home_power", "870"),
            ScenarioStep(StepKind.SET, "climate.living_room", "cool", {"temperature": 23.0}),
            ScenarioStep(StepKind.SET, "cover.living_room_curtain", "closed",
                         {"current_position": 0}),
            ScenarioStep(StepKind.SET, "light.living_room", "off"),
        ),
        expects={"normalized": 8, "deadletter": 0},
    ),
    "user_arrives_home": Scenario(
        name="user_arrives_home",
        description="Arrival: presence, front door, entrance motion, light",
        steps=(
            ScenarioStep(StepKind.SET, "device_tracker.resident_phone", "home"),
            ScenarioStep(StepKind.SET, "binary_sensor.front_door", "on"),
            ScenarioStep(StepKind.SET, "binary_sensor.front_door", "off"),
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "on"),
            ScenarioStep(StepKind.SET, "light.living_room", "on", {"brightness": 150}),
        ),
        expects={"normalized": 5, "deadletter": 0},
    ),
    "user_leaves_home": Scenario(
        name="user_leaves_home",
        description="Departure: door cycle, presence away, quiet home",
        steps=(
            ScenarioStep(StepKind.SET, "binary_sensor.front_door", "on"),
            ScenarioStep(StepKind.SET, "binary_sensor.front_door", "off"),
            ScenarioStep(StepKind.SET, "device_tracker.resident_phone", "not_home"),
            ScenarioStep(StepKind.SET, "light.living_room", "off"),
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "off"),
        ),
        expects={"normalized": 5, "deadletter": 0},
    ),
    "duplicate_events": Scenario(
        name="duplicate_events",
        description="The same physical event delivered twice must publish once",
        steps=(
            ScenarioStep(StepKind.SET, "binary_sensor.kitchen_leak", "on"),
            ScenarioStep(StepKind.DUPLICATE, "binary_sensor.kitchen_leak"),
            ScenarioStep(StepKind.DUPLICATE, "binary_sensor.kitchen_leak"),
        ),
        expects={"normalized": 1, "duplicates": 2, "deadletter": 0},
    ),
    "out_of_order_events": Scenario(
        name="out_of_order_events",
        description="A late (older) reading arrives after a newer one",
        steps=(
            ScenarioStep(StepKind.SET, "sensor.living_room_temperature", "28.4"),
            ScenarioStep(StepKind.BACKDATED, "sensor.living_room_temperature", "26.1",
                         backdate_seconds=600),
        ),
        expects={"normalized": 2, "out_of_order": 1, "deadletter": 0},
    ),
    "device_offline": Scenario(
        name="device_offline",
        description="A device drops offline and recovers",
        steps=(
            ScenarioStep(StepKind.OFFLINE, "sensor.living_room_temperature"),
            ScenarioStep(StepKind.SET, "sensor.living_room_temperature", "27.2"),
        ),
        expects={"normalized": 2, "deadletter": 0},
    ),
    "sleep_routine": Scenario(
        name="sleep_routine",
        description="Evening wind-down: lights off, motion stops, room goes dark",
        steps=(
            ScenarioStep(StepKind.SET, "device_tracker.resident_phone", "home"),
            ScenarioStep(StepKind.SET, "binary_sensor.bedroom_window", "off"),
            ScenarioStep(StepKind.SET, "light.living_room", "off"),
            ScenarioStep(StepKind.SET, "light.bedroom", "off"),
            ScenarioStep(StepKind.SET, "sensor.living_room_illuminance", "2"),
            ScenarioStep(StepKind.SET, "cover.living_room_curtain", "closed",
                         {"current_position": 0}),
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "off"),
        ),
        expects={"normalized": 7, "deadletter": 0},
    ),
    "cooking_activity": Scenario(
        name="cooking_activity",
        description="Kitchen in use: motion plus appliance power draw",
        steps=(
            ScenarioStep(StepKind.SET, "device_tracker.resident_phone", "home"),
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "on"),
            ScenarioStep(StepKind.SET, "sensor.home_power", "1850"),
            ScenarioStep(StepKind.SET, "sensor.living_room_humidity", "62"),
        ),
        expects={"normalized": 4, "deadletter": 0},
    ),
    "empty_home": Scenario(
        name="empty_home",
        description="Everyone out: presence away, no motion, lights off",
        steps=(
            ScenarioStep(StepKind.SET, "binary_sensor.front_door", "on"),
            ScenarioStep(StepKind.SET, "binary_sensor.front_door", "off"),
            ScenarioStep(StepKind.SET, "device_tracker.resident_phone", "not_home"),
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "off"),
            ScenarioStep(StepKind.SET, "light.living_room", "off"),
        ),
        expects={"normalized": 5, "deadletter": 0},
    ),
    "energy_anomaly": Scenario(
        name="energy_anomaly",
        description="Whole-home power climbs well above normal",
        steps=(
            ScenarioStep(StepKind.SET, "sensor.home_power", "1200"),
            ScenarioStep(StepKind.SET, "sensor.home_power", "3400"),
            ScenarioStep(StepKind.SET, "sensor.home_power", "5200"),
        ),
        expects={"normalized": 3, "deadletter": 0},
    ),
    "water_leak_watch": Scenario(
        name="water_leak_watch",
        description="Leak detector wets — an advisory watch signal, never a confirmation",
        steps=(
            ScenarioStep(StepKind.SET, "binary_sensor.kitchen_leak", "on"),
        ),
        expects={"normalized": 1, "deadletter": 0},
    ),
    "gas_risk_watch": Scenario(
        name="gas_risk_watch",
        description="Gas alarm during cooking — advisory watch only",
        steps=(
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "on"),
            ScenarioStep(StepKind.SET, "sensor.home_power", "1900"),
            ScenarioStep(StepKind.SET, "binary_sensor.kitchen_gas", "on"),
        ),
        expects={"normalized": 3, "deadletter": 0},
    ),
    "sensor_stale": Scenario(
        name="sensor_stale",
        description="A sensor reports, then goes silent so its reading ages out",
        steps=(
            ScenarioStep(StepKind.SET, "sensor.living_room_temperature", "26.0"),
            ScenarioStep(StepKind.BACKDATED, "sensor.living_room_humidity", "45",
                         backdate_seconds=7200),
        ),
        expects={"normalized": 2, "deadletter": 0},
    ),
    "manual_temperature_override": Scenario(
        name="manual_temperature_override",
        description="Occupant sets the AC themselves; adaptive proposals must stand down",
        steps=(
            ScenarioStep(StepKind.SET, "sensor.living_room_temperature", "29.0"),
            ScenarioStep(StepKind.SET, "climate.living_room", "cool",
                         {"temperature": 20.0}),
            ScenarioStep(StepKind.SET, "sensor.living_room_temperature", "28.4"),
        ),
        expects={"normalized": 4, "deadletter": 0},
    ),
    "repeated_lighting_preference": Scenario(
        name="repeated_lighting_preference",
        description="The same evening lighting choice, repeated — routine material",
        steps=(
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "on"),
            ScenarioStep(StepKind.SET, "light.living_room", "on", {"brightness": 180}),
            ScenarioStep(StepKind.SET, "light.living_room", "off"),
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "off"),
        ),
        expects={"normalized": 6, "deadletter": 0},
    ),
    "water_leak_confirmed": Scenario(
        name="water_leak_confirmed",
        description="Certified leak detector active — the Safety Governor may confirm",
        steps=(
            ScenarioStep(StepKind.SET, "sensor.living_room_humidity", "58"),
            ScenarioStep(StepKind.SET, "binary_sensor.kitchen_leak", "on"),
        ),
        expects={"normalized": 2, "deadletter": 0},
    ),
    "gas_alarm_confirmed": Scenario(
        name="gas_alarm_confirmed",
        description="Certified gas alarm active in an unoccupied home",
        steps=(
            ScenarioStep(StepKind.SET, "device_tracker.resident_phone", "not_home"),
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "off"),
            ScenarioStep(StepKind.SET, "binary_sensor.kitchen_gas", "on"),
        ),
        expects={"normalized": 3, "deadletter": 0},
    ),
    "historical_event_replay": Scenario(
        name="historical_event_replay",
        description="A day-old alarm reading replayed — must never confirm",
        steps=(
            ScenarioStep(StepKind.BACKDATED, "binary_sensor.kitchen_gas", "on",
                         backdate_seconds=86400),
        ),
        expects={"normalized": 1, "deadletter": 0},
    ),
    "internet_outage": Scenario(
        name="internet_outage",
        description="Local control continues while the home is offline from the cloud",
        steps=(
            ScenarioStep(StepKind.SET, "binary_sensor.living_room_motion", "on"),
            ScenarioStep(StepKind.SET, "sensor.living_room_temperature", "27.5"),
            ScenarioStep(StepKind.SET, "binary_sensor.kitchen_leak", "on"),
            ScenarioStep(StepKind.SET, "light.living_room", "on", {"brightness": 120}),
        ),
        expects={"normalized": 5, "deadletter": 0},
    ),
    "device_failure_protection_gap": Scenario(
        name="device_failure_protection_gap",
        description="A safety sensor stops reporting, leaving a gap in protection",
        steps=(
            ScenarioStep(StepKind.SET, "binary_sensor.kitchen_gas", "off"),
            ScenarioStep(StepKind.OFFLINE, "binary_sensor.kitchen_gas"),
        ),
        expects={"normalized": 2, "deadletter": 0},
    ),
    "invalid_event": Scenario(
        name="invalid_event",
        description="Structurally invalid payload must reach the dead-letter stream",
        steps=(
            ScenarioStep(StepKind.MALFORMED, "sensor.living_room_temperature"),
            ScenarioStep(StepKind.SET, "sensor.living_room_temperature", "27.0"),
        ),
        expects={"normalized": 1, "deadletter": 1},
    ),
}
