"""Full capability definitions (spec §10.3).

Every canonical capability declares data type, unit, allowed range or enum,
access mode, safety class, freshness requirement, reversibility, and the
confirmation level required before it may be written. Downstream services read
these rather than hardcoding assumptions:

- the Digital Twin uses ``freshness_seconds`` to mark a value stale;
- the Policy and Safety Service uses ``safety_class`` and ``confirmation``;
- the Action Orchestrator uses ``reversible`` to decide compensating actions.

Vendor and Home Assistant mappings live with the adapter that owns them
(``services/edge-agent/mapping.py``), keeping this module vendor-neutral.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from syltra_contracts.capabilities import ACTUATOR_CAPABILITIES, ALL_CAPABILITIES
from syltra_contracts.enums import SafetyClass


class DataType(StrEnum):
    BOOLEAN = "BOOLEAN"
    NUMBER = "NUMBER"
    ENUM = "ENUM"
    STRING = "STRING"


class Access(StrEnum):
    READ = "READ"
    WRITE = "WRITE"
    READ_WRITE = "READ_WRITE"


class Confirmation(StrEnum):
    """How much authority a write to this capability requires (spec §10.3)."""

    NONE = "NONE"
    """Automatic execution permitted within policy limits."""
    USER_APPROVAL = "USER_APPROVAL"
    """An explicit human approval per action."""
    DETERMINISTIC_SAFETY_RULE = "DETERMINISTIC_SAFETY_RULE"
    """Never model-driven: only an approved fixed safety rule may command it."""


@dataclass(frozen=True)
class CapabilityDefinition:
    capability: str
    data_type: DataType
    access: Access
    safety_class: SafetyClass
    freshness_seconds: float
    """Beyond this age a value is stale and cannot support a decision."""
    reversible: bool
    confirmation: Confirmation
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    allowed_values: tuple[str, ...] = ()

    def is_within_range(self, value: Any) -> bool:
        """True if ``value`` satisfies this capability's declared domain."""
        if self.data_type is DataType.BOOLEAN:
            return isinstance(value, bool)
        if self.data_type is DataType.NUMBER:
            if isinstance(value, bool) or not isinstance(value, int | float):
                return False
            if self.minimum is not None and value < self.minimum:
                return False
            return not (self.maximum is not None and value > self.maximum)
        if self.data_type is DataType.ENUM:
            return isinstance(value, str) and (
                not self.allowed_values or value in self.allowed_values
            )
        return isinstance(value, str)


def _sensor(
    capability: str,
    data_type: DataType,
    safety_class: SafetyClass,
    freshness_seconds: float,
    unit: str | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
) -> CapabilityDefinition:
    return CapabilityDefinition(
        capability=capability,
        data_type=data_type,
        access=Access.READ,
        safety_class=safety_class,
        freshness_seconds=freshness_seconds,
        reversible=True,  # reading changes nothing
        confirmation=Confirmation.NONE,
        unit=unit,
        minimum=minimum,
        maximum=maximum,
    )


CAPABILITY_DEFINITIONS: Final[dict[str, CapabilityDefinition]] = {
    d.capability: d
    for d in (
        # ── sensors (§10.1) ──
        _sensor("occupancy.motion", DataType.BOOLEAN, SafetyClass.NON_CRITICAL, 300),
        _sensor("occupancy.presence", DataType.BOOLEAN, SafetyClass.NON_CRITICAL, 600),
        _sensor("contact.open", DataType.BOOLEAN, SafetyClass.SECURITY_SENSITIVE, 900),
        _sensor(
            "environment.temperature", DataType.NUMBER, SafetyClass.COMFORT, 900, "C", -50, 100
        ),
        _sensor("environment.humidity", DataType.NUMBER, SafetyClass.COMFORT, 900, "%", 0, 100),
        _sensor(
            "environment.illuminance", DataType.NUMBER, SafetyClass.COMFORT, 900, "lx", 0, 200000
        ),
        _sensor("environment.air_quality", DataType.NUMBER, SafetyClass.COMFORT, 900, None, 0, 500),
        _sensor("safety.smoke_alarm", DataType.BOOLEAN, SafetyClass.LIFE_SAFETY_CRITICAL, 120),
        _sensor("safety.heat_alarm", DataType.BOOLEAN, SafetyClass.LIFE_SAFETY_CRITICAL, 120),
        _sensor("safety.gas_alarm", DataType.BOOLEAN, SafetyClass.LIFE_SAFETY_CRITICAL, 120),
        _sensor("safety.co_alarm", DataType.BOOLEAN, SafetyClass.LIFE_SAFETY_CRITICAL, 120),
        _sensor("safety.water_leak", DataType.BOOLEAN, SafetyClass.SAFETY_RELATED, 300),
        _sensor("energy.power", DataType.NUMBER, SafetyClass.NON_CRITICAL, 300, "W", 0, 100000),
        _sensor("energy.current", DataType.NUMBER, SafetyClass.NON_CRITICAL, 300, "A", 0, 1000),
        _sensor("energy.voltage", DataType.NUMBER, SafetyClass.NON_CRITICAL, 300, "V", 0, 1000),
        _sensor(
            "energy.consumption", DataType.NUMBER, SafetyClass.NON_CRITICAL, 3600, "kWh", 0, None
        ),
        _sensor("device.online", DataType.BOOLEAN, SafetyClass.NON_CRITICAL, 600),
        _sensor("device.battery", DataType.NUMBER, SafetyClass.NON_CRITICAL, 86400, "%", 0, 100),
        # ── actuators (§10.2) ──
        CapabilityDefinition(
            "light.power", DataType.BOOLEAN, Access.READ_WRITE, SafetyClass.COMFORT,
            900, True, Confirmation.NONE,
        ),
        CapabilityDefinition(
            "light.brightness", DataType.NUMBER, Access.READ_WRITE, SafetyClass.COMFORT,
            900, True, Confirmation.NONE, unit="%", minimum=0, maximum=100,
        ),
        CapabilityDefinition(
            "switch.power", DataType.BOOLEAN, Access.READ_WRITE, SafetyClass.COMFORT,
            900, True, Confirmation.NONE,
        ),
        CapabilityDefinition(
            "climate.mode", DataType.ENUM, Access.READ_WRITE, SafetyClass.COMFORT,
            900, True, Confirmation.NONE,
            allowed_values=("off", "cool", "heat", "auto", "dry", "fan_only"),
        ),
        CapabilityDefinition(
            "climate.target_temperature", DataType.NUMBER, Access.READ_WRITE, SafetyClass.COMFORT,
            900, True, Confirmation.NONE, unit="C", minimum=16, maximum=30,
        ),
        CapabilityDefinition(
            "cover.position", DataType.NUMBER, Access.READ_WRITE, SafetyClass.COMFORT,
            900, True, Confirmation.NONE, unit="%", minimum=0, maximum=100,
        ),
        # Security- and safety-critical actuators: separate policy classes
        # (safety invariant 13) and never model-commanded (invariant 18).
        CapabilityDefinition(
            "lock.state", DataType.ENUM, Access.READ_WRITE, SafetyClass.SECURITY_SENSITIVE,
            300, True, Confirmation.USER_APPROVAL,
            allowed_values=("locked", "unlocked", "locking", "unlocking", "jammed"),
        ),
        CapabilityDefinition(
            "valve.state", DataType.ENUM, Access.READ_WRITE, SafetyClass.LIFE_SAFETY_CRITICAL,
            120, True, Confirmation.DETERMINISTIC_SAFETY_RULE,
            allowed_values=("open", "closed", "opening", "closing"),
        ),
        CapabilityDefinition(
            "breaker.state", DataType.ENUM, Access.READ_WRITE, SafetyClass.LIFE_SAFETY_CRITICAL,
            120, False, Confirmation.DETERMINISTIC_SAFETY_RULE,
            allowed_values=("on", "off", "tripped"),
        ),
        CapabilityDefinition(
            "siren.state", DataType.ENUM, Access.READ_WRITE, SafetyClass.SAFETY_RELATED,
            120, True, Confirmation.DETERMINISTIC_SAFETY_RULE,
            allowed_values=("on", "off"),
        ),
        CapabilityDefinition(
            "garage.state", DataType.ENUM, Access.READ_WRITE, SafetyClass.SECURITY_SENSITIVE,
            300, True, Confirmation.USER_APPROVAL,
            allowed_values=("open", "closed", "opening", "closing", "stopped"),
        ),
        CapabilityDefinition(
            "camera.recording", DataType.BOOLEAN, Access.READ_WRITE,
            SafetyClass.SECURITY_SENSITIVE, 300, True, Confirmation.USER_APPROVAL,
        ),
        CapabilityDefinition(
            "notification.send", DataType.STRING, Access.WRITE, SafetyClass.NON_CRITICAL,
            60, False, Confirmation.NONE,
        ),
    )
}


def get_definition(capability: str) -> CapabilityDefinition:
    """Look up a capability definition, or raise for an unknown capability."""
    try:
        return CAPABILITY_DEFINITIONS[capability]
    except KeyError:
        msg = f"unknown capability {capability!r}"
        raise KeyError(msg) from None


def freshness_seconds(capability: str) -> float:
    return get_definition(capability).freshness_seconds


def is_writable(capability: str) -> bool:
    return get_definition(capability).access in (Access.WRITE, Access.READ_WRITE)


# Every canonical capability must have a definition — enforced by tests, and
# asserted here so an incomplete registry fails at import rather than at runtime.
_MISSING = ALL_CAPABILITIES - set(CAPABILITY_DEFINITIONS)
if _MISSING:  # pragma: no cover - guarded by tests
    msg = f"capabilities without definitions: {sorted(_MISSING)}"
    raise RuntimeError(msg)

WRITABLE_CAPABILITIES: Final[frozenset[str]] = frozenset(
    c for c in ACTUATOR_CAPABILITIES if is_writable(c)
)
