"""Normalized capability registry (spec §10).

Intelligence services must never depend on vendor entity names; they address
devices only through these capability identifiers. Full capability
*definitions* (type, unit, range, access, safety class, freshness,
reversibility, confirmation level, vendor and Home Assistant mappings) are
introduced in Phase 1 with the Edge Agent's mapping layer; this module fixes
the identifier vocabulary they must draw from.
"""

from typing import Final

SENSOR_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {
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
)

ACTUATOR_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {
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
)

ALL_CAPABILITIES: Final[frozenset[str]] = SENSOR_CAPABILITIES | ACTUATOR_CAPABILITIES

# Actuators that must always sit behind separate, stricter policy classes
# (safety invariant 13) and are blocked as real targets in development and
# simulation environments (safety invariant 16).
CRITICAL_ACTUATOR_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {
        "lock.state",
        "valve.state",
        "breaker.state",
        "siren.state",
        "garage.state",
    }
)


def is_known_capability(capability: str) -> bool:
    """Return True if the identifier belongs to the canonical registry."""
    return capability in ALL_CAPABILITIES
