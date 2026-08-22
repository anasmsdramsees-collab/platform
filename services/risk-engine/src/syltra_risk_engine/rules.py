"""Risk inference rules (spec §14.5).

These rules watch for *combinations* that ordinary single-sensor thresholds
miss — a gas alarm during cooking means something different from a gas alarm in
an empty house at 3am; water detected while the dishwasher runs is a different
story from water detected in a dry utility room.

Everything here is advisory. Each rule returns a `WATCH` or `PRE_ALERT`
proposal and nothing more; `CONFIRMED` is not in this module's vocabulary, and
the contract layer would refuse it anyway. The Safety Governor, in `governor.py`,
is the only component that confirms.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from syltra_contracts import (
    DEFAULT_PRE_ALERT_TTL,
    DEFAULT_WATCH_TTL,
    EvidenceOrigin,
    RiskCategory,
    RiskEvidenceItem,
    RiskSeverity,
    RiskState,
)
from syltra_digital_twin.core import HomeState, StateStatus

RISK_RULES_VERSION = "1.0.0"


@dataclass(frozen=True)
class RiskInput:
    """Everything a risk rule may read."""

    home: HomeState
    now: datetime
    occupied: bool | None = None
    """None when occupancy is unknown — deliberately not defaulted to False."""
    cooking: bool = False

    def readings(self, capability: str) -> list[tuple[str, Any, StateStatus, str | None]]:
        """(device_id, value, status, room_id) for every device with this capability."""
        found = []
        for device_id, device in self.home.devices.items():
            state = device.capabilities.get(capability)
            if state is None:
                continue
            found.append(
                (device_id, state.value, state.status_at(self.now), device.room_id)
            )
        return found

    def fresh(self, capability: str) -> list[tuple[str, Any, str | None]]:
        return [
            (device_id, value, room)
            for device_id, value, status, room in self.readings(capability)
            if status is StateStatus.KNOWN
        ]

    def stale_or_unknown(self, capability: str) -> list[str]:
        return [
            device_id
            for device_id, _, status, _ in self.readings(capability)
            if status is not StateStatus.KNOWN
        ]


@dataclass
class RiskProposal:
    """A rule's advisory output. Cannot express CONFIRMED by construction."""

    category: RiskCategory
    state: RiskState
    severity: RiskSeverity
    confidence: float
    evidence: list[RiskEvidenceItem]
    reason_codes: list[str]
    room_id: str | None = None
    ttl: timedelta = DEFAULT_WATCH_TTL
    producer: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Structural guarantee: a rule in this module physically cannot emit a
        # confirmed state, so a mistake here fails at construction rather than
        # reaching the case store.
        if self.state not in {RiskState.WATCH, RiskState.PRE_ALERT}:
            msg = (
                f"risk inference may propose WATCH or PRE_ALERT only, not "
                f"{self.state.value} (spec §22 Phase 6)"
            )
            raise ValueError(msg)


def _sensor(capability: str, device_id: str, value: Any, room: str | None,
            note: str) -> RiskEvidenceItem:
    return RiskEvidenceItem(
        origin=EvidenceOrigin.SENSOR_READING,
        capability=capability,
        value=value,
        device_id=device_id,
        room_id=room,
        status="KNOWN",
        note=note,
    )


def _inference(capability: str, value: Any, note: str) -> RiskEvidenceItem:
    return RiskEvidenceItem(
        origin=EvidenceOrigin.INFERENCE,
        capability=capability,
        value=value,
        status="KNOWN",
        note=note,
    )


Rule = Callable[[RiskInput], list[RiskProposal]]


# ── hazard watches ──


def rule_gas_watch(inp: RiskInput) -> list[RiskProposal]:
    """A gas alarm reading raises a watch — never a confirmation.

    The Safety Governor confirms on the same reading; this rule exists so the
    household sees the situation developing and so context (cooking, occupancy)
    is attached before any response is considered.
    """
    active = [(d, v, r) for d, v, r in inp.fresh("safety.gas_alarm") if v is True]
    if not active:
        return []

    evidence = [
        _sensor("safety.gas_alarm", d, v, r, "gas alarm reading active")
        for d, v, r in active
    ]
    reason_codes = ["GAS_ALARM_READING", "ADVISORY_PENDING_CONFIRMATION"]
    severity = RiskSeverity.HIGH
    confidence = 0.8

    if inp.cooking:
        # Cooking makes a transient reading more plausible, so the watch is
        # raised with lower confidence — but it is never suppressed.
        reason_codes.append("COOKING_IN_PROGRESS")
        confidence = 0.6
        evidence.append(_inference("occupancy.motion", True, "kitchen activity"))
    if inp.occupied is False:
        # An alarm in an empty home has no innocent explanation.
        reason_codes.append("HOME_EMPTY")
        confidence = 0.9
        severity = RiskSeverity.CRITICAL

    return [
        RiskProposal(
            category=RiskCategory.GAS,
            state=RiskState.PRE_ALERT,
            severity=severity,
            confidence=confidence,
            evidence=evidence,
            reason_codes=reason_codes,
            room_id=active[0][2],
            ttl=DEFAULT_PRE_ALERT_TTL,
        )
    ]


def rule_water_leak_watch(inp: RiskInput) -> list[RiskProposal]:
    active = [(d, v, r) for d, v, r in inp.fresh("safety.water_leak") if v is True]
    if not active:
        return []
    return [
        RiskProposal(
            category=RiskCategory.WATER_LEAK,
            state=RiskState.PRE_ALERT,
            severity=RiskSeverity.HIGH if inp.occupied is False else RiskSeverity.MEDIUM,
            confidence=0.85,
            evidence=[
                _sensor("safety.water_leak", d, v, r, "leak detector wet")
                for d, v, r in active
            ],
            reason_codes=["LEAK_DETECTOR_READING", "ADVISORY_PENDING_CONFIRMATION"],
            room_id=active[0][2],
            ttl=DEFAULT_PRE_ALERT_TTL,
        )
    ]


def rule_smoke_watch(inp: RiskInput) -> list[RiskProposal]:
    proposals = []
    for capability, category in (
        ("safety.smoke_alarm", RiskCategory.SMOKE_FIRE),
        ("safety.heat_alarm", RiskCategory.SMOKE_FIRE),
        ("safety.co_alarm", RiskCategory.CARBON_MONOXIDE),
    ):
        active = [(d, v, r) for d, v, r in inp.fresh(capability) if v is True]
        if not active:
            continue
        proposals.append(
            RiskProposal(
                category=category,
                state=RiskState.PRE_ALERT,
                severity=RiskSeverity.CRITICAL,
                confidence=0.9,
                evidence=[
                    _sensor(capability, d, v, r, f"{capability} reading active")
                    for d, v, r in active
                ],
                reason_codes=[
                    f"{capability.split('.')[1].upper()}_READING",
                    "ADVISORY_PENDING_CONFIRMATION",
                ],
                room_id=active[0][2],
                ttl=DEFAULT_PRE_ALERT_TTL,
            )
        )
    return proposals


def rule_electrical_watch(inp: RiskInput) -> list[RiskProposal]:
    """Sustained high power in an empty home is worth watching.

    Spec §20.6 is explicit that anomaly output must never open a breaker on its
    own, so this stays a watch: it surfaces a suspicion, nothing more.
    """
    high = [
        (d, v, r)
        for d, v, r in inp.fresh("energy.power")
        if isinstance(v, int | float) and not isinstance(v, bool) and v > 5000
    ]
    if not high or inp.occupied is not False:
        return []
    return [
        RiskProposal(
            category=RiskCategory.ELECTRICAL,
            state=RiskState.WATCH,
            severity=RiskSeverity.MEDIUM,
            confidence=0.6,
            evidence=[
                _sensor("energy.power", d, v, r, "sustained high draw with home empty")
                for d, v, r in high
            ],
            reason_codes=["HIGH_POWER_WHILE_EMPTY", "NO_AUTOMATIC_BREAKER_ACTION"],
            metadata={"advisory_only": True},
        )
    ]


def rule_temperature_watch(inp: RiskInput) -> list[RiskProposal]:
    extreme = [
        (d, v, r)
        for d, v, r in inp.fresh("environment.temperature")
        if isinstance(v, int | float) and not isinstance(v, bool) and (v > 45 or v < 2)
    ]
    if not extreme:
        return []
    return [
        RiskProposal(
            category=RiskCategory.TEMPERATURE,
            state=RiskState.WATCH,
            severity=RiskSeverity.MEDIUM,
            confidence=0.75,
            evidence=[
                _sensor("environment.temperature", d, v, r, "temperature outside habitable range")
                for d, v, r in extreme
            ],
            reason_codes=["TEMPERATURE_OUT_OF_RANGE"],
            room_id=extreme[0][2],
        )
    ]


# ── system health ──


def rule_sensor_health_watch(inp: RiskInput) -> list[RiskProposal]:
    """Safety sensors that have gone stale or unknown.

    This is the risk case nobody thinks to look for: the home is quiet not
    because it is safe, but because the sensors that would tell us otherwise
    have stopped reporting. Safety invariant 4 makes stale data unusable, which
    means a stale smoke detector is a *gap in protection*, and the household
    deserves to know.
    """
    degraded: list[RiskEvidenceItem] = []
    for capability in (
        "safety.smoke_alarm",
        "safety.heat_alarm",
        "safety.gas_alarm",
        "safety.co_alarm",
        "safety.water_leak",
    ):
        for device_id, value, status, room in inp.readings(capability):
            if status is StateStatus.KNOWN:
                continue
            degraded.append(
                RiskEvidenceItem(
                    origin=EvidenceOrigin.SYSTEM_HEALTH,
                    capability=capability,
                    value=value,
                    device_id=device_id,
                    room_id=room,
                    status=status.value,
                    note="safety sensor not reporting fresh data",
                )
            )
    if not degraded:
        return []
    return [
        RiskProposal(
            category=RiskCategory.DEVICE_FAILURE,
            state=RiskState.WATCH,
            severity=RiskSeverity.HIGH,
            confidence=1.0,  # this is an observation about our own data, not a guess
            evidence=degraded[:20],
            reason_codes=["SAFETY_SENSOR_NOT_REPORTING", "PROTECTION_GAP"],
            metadata={"degraded_sensors": len(degraded)},
        )
    ]


def rule_connectivity_watch(inp: RiskInput) -> list[RiskProposal]:
    offline = [
        RiskEvidenceItem(
            origin=EvidenceOrigin.SYSTEM_HEALTH,
            capability="device.online",
            value=False,
            device_id=device_id,
            room_id=device.room_id,
            status="KNOWN",
            note="device unavailable",
        )
        for device_id, device in inp.home.devices.items()
        if device.available is False
    ]
    if not offline:
        return []
    fraction = len(offline) / max(len(inp.home.devices), 1)
    return [
        RiskProposal(
            category=RiskCategory.CONNECTIVITY,
            state=RiskState.WATCH,
            severity=RiskSeverity.HIGH if fraction > 0.5 else RiskSeverity.LOW,
            confidence=1.0,
            evidence=offline[:20],
            reason_codes=["DEVICES_OFFLINE"],
            metadata={"offline_fraction": round(fraction, 3)},
        )
    ]


def rule_intrusion_watch(inp: RiskInput) -> list[RiskProposal]:
    """An entry opening while the home is believed empty."""
    if inp.occupied is not False:
        return []
    opened = [(d, v, r) for d, v, r in inp.fresh("contact.open") if v is True]
    if not opened:
        return []
    return [
        RiskProposal(
            category=RiskCategory.INTRUSION,
            state=RiskState.PRE_ALERT,
            severity=RiskSeverity.HIGH,
            confidence=0.7,
            evidence=[
                _sensor("contact.open", d, v, r, "entry opened while home believed empty")
                for d, v, r in opened
            ],
            reason_codes=["ENTRY_OPENED_WHILE_EMPTY"],
            room_id=opened[0][2],
            ttl=DEFAULT_PRE_ALERT_TTL,
        )
    ]


ALL_RULES: dict[str, Rule] = {
    "gas_watch": rule_gas_watch,
    "water_leak_watch": rule_water_leak_watch,
    "smoke_watch": rule_smoke_watch,
    "electrical_watch": rule_electrical_watch,
    "temperature_watch": rule_temperature_watch,
    "sensor_health_watch": rule_sensor_health_watch,
    "connectivity_watch": rule_connectivity_watch,
    "intrusion_watch": rule_intrusion_watch,
}


def evaluate_all(inp: RiskInput) -> list[RiskProposal]:
    proposals: list[RiskProposal] = []
    for rule_id, rule in ALL_RULES.items():
        for proposal in rule(inp):
            proposal.producer = f"rule:{rule_id}@{RISK_RULES_VERSION}"
            proposals.append(proposal)
    return proposals
