"""Home Assistant entity → normalized capability mapping (spec §10, §14.1).

The intelligence layer never sees vendor entity names; this module is the
translation boundary. Unmappable entities are *rejected* from the normalized
stream (still visible raw); structurally invalid events raise
``MappingError`` and go to the dead-letter stream with reason codes.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

from syltra_contracts import ALL_CAPABILITIES

UNAVAILABLE_STATES: Final[frozenset[str]] = frozenset({"unavailable"})
UNKNOWN_STATES: Final[frozenset[str]] = frozenset({"unknown"})


class MappingError(Exception):
    """Structurally invalid Home Assistant payload."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code


@dataclass(frozen=True)
class CapabilityReading:
    """One normalized observation extracted from an entity state."""

    capability: str
    value: bool | float | str | None
    unit: str | None = None

    def __post_init__(self) -> None:
        if self.capability not in ALL_CAPABILITIES:
            msg = f"unknown capability {self.capability!r}"
            raise ValueError(msg)


_SENSOR_DEVICE_CLASS_MAP: Final[dict[str, tuple[str, str | None]]] = {
    "temperature": ("environment.temperature", "C"),
    "humidity": ("environment.humidity", "%"),
    "illuminance": ("environment.illuminance", "lx"),
    "aqi": ("environment.air_quality", None),
    "power": ("energy.power", "W"),
    "current": ("energy.current", "A"),
    "voltage": ("energy.voltage", "V"),
    "energy": ("energy.consumption", "kWh"),
    "battery": ("device.battery", "%"),
}

_BINARY_DEVICE_CLASS_MAP: Final[dict[str, str]] = {
    "motion": "occupancy.motion",
    "occupancy": "occupancy.presence",
    "presence": "occupancy.presence",
    "door": "contact.open",
    "window": "contact.open",
    "opening": "contact.open",
    "garage_door": "contact.open",
    "moisture": "safety.water_leak",
    "gas": "safety.gas_alarm",
    "smoke": "safety.smoke_alarm",
    "carbon_monoxide": "safety.co_alarm",
    "heat": "safety.heat_alarm",
    "connectivity": "device.online",
}


def _parse_float(state: str) -> float | None:
    try:
        return float(state)
    except ValueError:
        return None


def map_ha_state(
    entity_id: str,
    state: str,
    attributes: Mapping[str, Any],
) -> list[CapabilityReading]:
    """Map one HA entity state onto zero or more capability readings.

    Returns ``[]`` for entities outside the canonical capability model
    (rejected mappings — raw stream only).
    """
    if "." not in entity_id:
        raise MappingError("INVALID_ENTITY_ID", f"malformed entity_id {entity_id!r}")
    domain = entity_id.split(".", 1)[0]

    if state in UNAVAILABLE_STATES:
        return [CapabilityReading("device.online", False)]
    if state in UNKNOWN_STATES:
        return []

    device_class = attributes.get("device_class")

    if domain == "sensor":
        mapped = _SENSOR_DEVICE_CLASS_MAP.get(str(device_class))
        if mapped is None:
            return []
        capability, default_unit = mapped
        value = _parse_float(state)
        if value is None:
            raise MappingError(
                "NON_NUMERIC_SENSOR_VALUE",
                f"{entity_id}: expected numeric state, got {state!r}",
            )
        unit = str(attributes.get("unit_of_measurement") or default_unit or "") or None
        return [CapabilityReading(capability, value, unit)]

    if domain == "binary_sensor":
        capability = _BINARY_DEVICE_CLASS_MAP.get(str(device_class), "")
        if not capability:
            return []
        return [CapabilityReading(capability, state == "on")]

    if domain == "device_tracker":
        return [CapabilityReading("occupancy.presence", state == "home")]

    if domain == "light":
        readings = [CapabilityReading("light.power", state == "on")]
        brightness = attributes.get("brightness")
        if isinstance(brightness, int | float):
            readings.append(
                CapabilityReading("light.brightness", round(float(brightness) / 255 * 100, 1), "%")
            )
        return readings

    if domain == "switch":
        return [CapabilityReading("switch.power", state == "on")]

    if domain == "climate":
        readings = [CapabilityReading("climate.mode", state)]
        target = attributes.get("temperature")
        if isinstance(target, int | float):
            readings.append(
                CapabilityReading("climate.target_temperature", float(target), "C")
            )
        return readings

    if domain == "cover":
        position = attributes.get("current_position")
        if isinstance(position, int | float):
            return [CapabilityReading("cover.position", float(position), "%")]
        if state in ("open", "closed"):
            return [CapabilityReading("cover.position", 100.0 if state == "open" else 0.0, "%")]
        return []

    if domain == "lock":
        return [CapabilityReading("lock.state", state)]

    if domain == "valve":
        return [CapabilityReading("valve.state", state)]

    if domain == "siren":
        return [CapabilityReading("siren.state", state)]

    if domain == "camera":
        return [CapabilityReading("camera.recording", state == "recording")]

    return []
