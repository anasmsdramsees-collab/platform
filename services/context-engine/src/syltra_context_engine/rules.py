"""Deterministic context rules (spec §14.3).

Every rule is a pure function of twin state plus the evaluation time. No
machine learning participates here — spec §14.3 requires deterministic rules
*before* ML inference, so that context remains explainable and available when
model services are down (safety invariant 7).

Confidence is not decorative. Each rule starts from a base confidence and
**loses** confidence for evidence that is missing or stale, so a context built
on half-observed sensors is visibly weaker than one built on fresh ones. Expiry
is derived from the evidence itself: a context can never outlive the freshness
window of the observations that justify it.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Any

from syltra_contracts import ContextType, EvidenceItem, home_scope, room_scope
from syltra_contracts.capability_definitions import freshness_seconds
from syltra_digital_twin.core import DeviceState, HomeState, StateStatus

RULES_VERSION = "1.0.0"

# Quiet hours are a household preference; these defaults are overridable per
# home in configuration (Phase 7 exposes them in the console).
DEFAULT_QUIET_START = time(22, 0)
DEFAULT_QUIET_END = time(7, 0)

_MISSING_EVIDENCE_PENALTY = 0.25
"""Confidence lost per required capability that is unobserved or stale."""

_MIN_CONFIDENCE = 0.1


@dataclass(frozen=True)
class Observation:
    """A twin reading resolved for rule use, carrying its usability."""

    device_id: str
    room_id: str | None
    capability: str
    value: Any
    observed_at: datetime | None
    status: StateStatus

    @property
    def usable(self) -> bool:
        return self.status is StateStatus.KNOWN

    def to_evidence(self, note: str | None = None) -> EvidenceItem:
        return EvidenceItem(
            device_id=self.device_id,
            room_id=self.room_id,
            capability=self.capability,
            value=self.value,
            observed_at=self.observed_at,
            status=self.status.value,
            note=note,
        )


@dataclass
class ContextProposal:
    """A rule's output before the engine turns it into a record."""

    context_type: ContextType
    scope: str
    confidence: float
    evidence: list[EvidenceItem]
    expires_in: timedelta
    reason_codes: list[str] = field(default_factory=list)
    producer: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleContext:
    """Everything a rule may read. Deliberately narrow and side-effect free."""

    home: HomeState
    now: datetime
    quiet_start: time = DEFAULT_QUIET_START
    quiet_end: time = DEFAULT_QUIET_END

    def observations(self, capability: str) -> list[Observation]:
        """All readings of a capability across the home, fresh or not."""
        found: list[Observation] = []
        for device_id, device in self.home.devices.items():
            state = device.capabilities.get(capability)
            if state is None:
                continue
            found.append(
                Observation(
                    device_id=device_id,
                    room_id=device.room_id,
                    capability=capability,
                    value=state.value,
                    observed_at=state.occurred_at,
                    status=state.status_at(self.now),
                )
            )
        return found

    def usable(self, capability: str) -> list[Observation]:
        return [o for o in self.observations(capability) if o.usable]

    def usable_in_room(self, capability: str, room_id: str) -> list[Observation]:
        return [o for o in self.usable(capability) if o.room_id == room_id]

    def rooms(self) -> list[str]:
        return sorted(self.home.rooms)

    def devices_in_room(self, room_id: str) -> list[tuple[str, DeviceState]]:
        return [
            (device_id, device)
            for device_id, device in self.home.devices.items()
            if device.room_id == room_id
        ]

    def most_recent(self, capability: str) -> Observation | None:
        candidates = [o for o in self.usable(capability) if o.observed_at is not None]
        if not candidates:
            return None
        return max(candidates, key=lambda o: o.observed_at or self.now)


def _confidence(base: float, required: int, present: int) -> float:
    """Degrade confidence for each required signal that is missing or stale."""
    missing = max(required - present, 0)
    return round(max(base - missing * _MISSING_EVIDENCE_PENALTY, _MIN_CONFIDENCE), 3)


def _expiry_from(capabilities: list[str], floor: timedelta = timedelta(minutes=1)) -> timedelta:
    """A context lives no longer than its shortest-lived evidence."""
    windows = [freshness_seconds(c) for c in capabilities]
    shortest = min(windows) if windows else 300.0
    return max(timedelta(seconds=shortest), floor)


Rule = Callable[[RuleContext], list[ContextProposal]]


# ── occupancy ──


def rule_home_occupied(ctx: RuleContext) -> list[ContextProposal]:
    """Someone is home: recent motion, or a presence tracker reporting home."""
    motion = [o for o in ctx.usable("occupancy.motion") if o.value is True]
    presence = [o for o in ctx.usable("occupancy.presence") if o.value is True]
    if not motion and not presence:
        return []

    evidence = [o.to_evidence("motion detected") for o in motion]
    evidence += [o.to_evidence("presence tracker at home") for o in presence]
    reason_codes = []
    if motion:
        reason_codes.append("MOTION_DETECTED")
    if presence:
        reason_codes.append("PRESENCE_TRACKER_HOME")

    # Two independent signal families agreeing is stronger than one.
    present_families = int(bool(motion)) + int(bool(presence))
    return [
        ContextProposal(
            context_type=ContextType.HOME_OCCUPIED,
            scope=home_scope(),
            confidence=_confidence(0.95, required=2, present=present_families),
            evidence=evidence,
            expires_in=_expiry_from(["occupancy.motion", "occupancy.presence"]),
            reason_codes=reason_codes,
        )
    ]


def rule_home_empty(ctx: RuleContext) -> list[ContextProposal]:
    """Nobody home: every usable occupancy signal says absent.

    Requires at least one usable signal — with no observations at all the
    honest answer is "unknown", not "empty". Asserting an empty home on missing
    data could later authorize actions that assume nobody is present.
    """
    motion = ctx.usable("occupancy.motion")
    presence = ctx.usable("occupancy.presence")
    signals = motion + presence
    if not signals:
        return []
    if any(o.value is True for o in signals):
        return []

    present_families = int(bool(motion)) + int(bool(presence))
    return [
        ContextProposal(
            context_type=ContextType.HOME_EMPTY,
            scope=home_scope(),
            confidence=_confidence(0.9, required=2, present=present_families),
            evidence=[o.to_evidence("no occupancy signal") for o in signals],
            expires_in=_expiry_from(["occupancy.motion", "occupancy.presence"]),
            reason_codes=["NO_MOTION", "NO_PRESENCE"],
        )
    ]


def rule_room_occupied(ctx: RuleContext) -> list[ContextProposal]:
    """Per-room occupancy — overlapping contexts, one per active room."""
    proposals: list[ContextProposal] = []
    for room_id in ctx.rooms():
        motion = [
            o for o in ctx.usable_in_room("occupancy.motion", room_id) if o.value is True
        ]
        if not motion:
            continue
        proposals.append(
            ContextProposal(
                context_type=ContextType.ROOM_OCCUPIED,
                scope=room_scope(room_id),
                confidence=_confidence(0.9, required=1, present=1),
                evidence=[o.to_evidence(f"motion in {room_id}") for o in motion],
                expires_in=_expiry_from(["occupancy.motion"]),
                reason_codes=["ROOM_MOTION_DETECTED"],
            )
        )
    return proposals


def rule_arriving(ctx: RuleContext) -> list[ContextProposal]:
    """Arrival: presence turned home and an entry contact opened recently."""
    presence = [o for o in ctx.usable("occupancy.presence") if o.value is True]
    contacts = [o for o in ctx.usable("contact.open") if o.value is True]
    if not presence or not contacts:
        return []
    return [
        ContextProposal(
            context_type=ContextType.ARRIVING,
            scope=home_scope(),
            confidence=_confidence(0.8, required=2, present=2),
            evidence=[o.to_evidence("presence home") for o in presence]
            + [o.to_evidence("entry opened") for o in contacts],
            # Arrival is a transient moment, not a standing condition.
            expires_in=timedelta(minutes=5),
            reason_codes=["PRESENCE_ARRIVED", "ENTRY_OPENED"],
        )
    ]


def rule_leaving(ctx: RuleContext) -> list[ContextProposal]:
    """Departure: presence away while an entry contact was just opened."""
    presence = [o for o in ctx.usable("occupancy.presence") if o.value is False]
    contacts = [o for o in ctx.usable("contact.open") if o.value is True]
    if not presence or not contacts:
        return []
    return [
        ContextProposal(
            context_type=ContextType.LEAVING,
            scope=home_scope(),
            confidence=_confidence(0.8, required=2, present=2),
            evidence=[o.to_evidence("presence away") for o in presence]
            + [o.to_evidence("entry opened") for o in contacts],
            expires_in=timedelta(minutes=5),
            reason_codes=["PRESENCE_AWAY", "ENTRY_OPENED"],
        )
    ]


# ── activity ──


def rule_quiet_hours(ctx: RuleContext) -> list[ContextProposal]:
    """Household quiet hours — a time rule, so it needs no sensor evidence.

    Its evidence is the clock itself, recorded explicitly so the context still
    satisfies the "must carry evidence" contract honestly.
    """
    local = ctx.now.timetz()
    start, end = ctx.quiet_start, ctx.quiet_end
    within = (
        (start <= local.replace(tzinfo=None) or local.replace(tzinfo=None) < end)
        if start > end  # window crosses midnight
        else (start <= local.replace(tzinfo=None) < end)
    )
    if not within:
        return []
    return [
        ContextProposal(
            context_type=ContextType.QUIET_HOURS,
            scope=home_scope(),
            confidence=1.0,  # a clock reading is not uncertain
            evidence=[
                EvidenceItem(
                    capability="system.clock",
                    # The window, not the instant. An instantaneous timestamp
                    # here would differ on every evaluation, so the engine's
                    # material-change check would republish this context
                    # continuously for as long as quiet hours lasted.
                    value=f"{start.isoformat()}-{end.isoformat()}",
                    observed_at=ctx.now,
                    status="KNOWN",
                    note=f"within quiet hours {start}–{end}",
                )
            ],
            expires_in=timedelta(minutes=15),
            reason_codes=["WITHIN_QUIET_HOURS"],
        )
    ]


def rule_sleeping(ctx: RuleContext) -> list[ContextProposal]:
    """Sleeping: quiet hours, someone home, bedroom quiet and dark.

    Deliberately conservative — a false SLEEPING context would suppress
    lighting and notifications a waking household may need.
    """
    if not rule_quiet_hours(ctx):
        return []
    presence = [o for o in ctx.usable("occupancy.presence") if o.value is True]
    if not presence:
        return []

    # No motion anywhere in the last freshness window.
    motion = ctx.usable("occupancy.motion")
    if any(o.value is True for o in motion):
        return []

    illuminance = [o for o in ctx.usable("environment.illuminance")]
    dark = [o for o in illuminance if isinstance(o.value, int | float) and o.value < 10]
    lights_on = [o for o in ctx.usable("light.power") if o.value is True]
    if lights_on:
        return []

    evidence = [o.to_evidence("occupant home") for o in presence]
    evidence += [o.to_evidence("no motion") for o in motion]
    evidence += [o.to_evidence("dark") for o in dark]

    present_signals = 1 + int(bool(motion)) + int(bool(dark))
    return [
        ContextProposal(
            context_type=ContextType.SLEEPING,
            scope=home_scope(),
            confidence=_confidence(0.85, required=3, present=present_signals),
            evidence=evidence,
            expires_in=_expiry_from(["occupancy.motion", "environment.illuminance"]),
            reason_codes=["QUIET_HOURS", "NO_MOTION", "LIGHTS_OFF"],
        )
    ]


def rule_cooking(ctx: RuleContext) -> list[ContextProposal]:
    """Cooking: kitchen occupied plus a heat or power signature.

    Note this is an *activity* inference, never a safety conclusion — a gas
    reading here contributes context, not an alarm.
    """
    proposals: list[ContextProposal] = []
    for room_id in ctx.rooms():
        if "kitchen" not in room_id.lower():
            continue
        motion = [
            o for o in ctx.usable_in_room("occupancy.motion", room_id) if o.value is True
        ]
        if not motion:
            continue
        power = [
            o
            for o in ctx.usable("energy.power")
            if isinstance(o.value, int | float) and o.value > 800
        ]
        humidity = [
            o
            for o in ctx.usable_in_room("environment.humidity", room_id)
            if isinstance(o.value, int | float) and o.value > 55
        ]
        if not power and not humidity:
            continue

        evidence = [o.to_evidence("kitchen motion") for o in motion]
        evidence += [o.to_evidence("elevated power draw") for o in power]
        evidence += [o.to_evidence("elevated humidity") for o in humidity]
        present = 1 + int(bool(power)) + int(bool(humidity))
        proposals.append(
            ContextProposal(
                context_type=ContextType.COOKING,
                scope=room_scope(room_id),
                confidence=_confidence(0.8, required=3, present=present),
                evidence=evidence,
                expires_in=_expiry_from(["occupancy.motion", "energy.power"]),
                reason_codes=["KITCHEN_OCCUPIED", "APPLIANCE_ACTIVITY"],
            )
        )
    return proposals


# ── environment and health ──


def rule_high_energy_usage(ctx: RuleContext) -> list[ContextProposal]:
    """Whole-home power above a configured threshold."""
    high = [
        o
        for o in ctx.usable("energy.power")
        if isinstance(o.value, int | float) and o.value > 3000
    ]
    if not high:
        return []
    return [
        ContextProposal(
            context_type=ContextType.HIGH_ENERGY_USAGE,
            scope=home_scope(),
            confidence=_confidence(0.9, required=1, present=1),
            evidence=[o.to_evidence("power above threshold") for o in high],
            expires_in=_expiry_from(["energy.power"]),
            reason_codes=["POWER_ABOVE_THRESHOLD"],
        )
    ]


def rule_possible_water_leak(ctx: RuleContext) -> list[ContextProposal]:
    """ADVISORY ONLY (safety invariant 6).

    Raises awareness from a certified leak detector reading. It does not
    confirm a leak and cannot trigger any action; the Risk Engine may use it to
    enter WATCH or PRE_ALERT, and only deterministic rules against the
    certified capability may confirm.
    """
    wet = [o for o in ctx.usable("safety.water_leak") if o.value is True]
    if not wet:
        return []
    return [
        ContextProposal(
            context_type=ContextType.POSSIBLE_WATER_LEAK,
            scope=home_scope(),
            confidence=_confidence(0.9, required=1, present=1),
            evidence=[o.to_evidence("leak detector wet") for o in wet],
            expires_in=_expiry_from(["safety.water_leak"]),
            reason_codes=["LEAK_DETECTOR_ACTIVE", "ADVISORY_ONLY"],
            metadata={"advisory_only": True},
        )
    ]


def rule_possible_gas_risk(ctx: RuleContext) -> list[ContextProposal]:
    """ADVISORY ONLY (safety invariants 6 and 18).

    Combines a certified gas-alarm reading with context. Confirmed emergency
    response remains deterministic and rule-based; this context never
    substitutes for it.
    """
    alarms = [o for o in ctx.usable("safety.gas_alarm") if o.value is True]
    if not alarms:
        return []
    cooking = rule_cooking(ctx)
    evidence = [o.to_evidence("gas alarm active") for o in alarms]
    reason_codes = ["GAS_ALARM_ACTIVE", "ADVISORY_ONLY"]
    if cooking:
        evidence += cooking[0].evidence
        reason_codes.append("COOKING_IN_PROGRESS")
    return [
        ContextProposal(
            context_type=ContextType.POSSIBLE_GAS_RISK,
            scope=home_scope(),
            confidence=_confidence(0.95, required=1, present=1),
            evidence=evidence,
            expires_in=_expiry_from(["safety.gas_alarm"]),
            reason_codes=reason_codes,
            metadata={"advisory_only": True},
        )
    ]


def rule_child_present(ctx: RuleContext) -> list[ContextProposal]:
    """Child presence, from an explicitly configured occupant tracker.

    Never inferred from biometrics or cameras (spec §3 non-goals): it relies on
    a device the household has designated, recorded in device metadata.
    """
    proposals: list[ContextProposal] = []
    for device_id, device in ctx.home.devices.items():
        if not (device.name or "").lower().startswith("child"):
            continue
        state = device.capabilities.get("occupancy.presence")
        if state is None or state.status_at(ctx.now) is not StateStatus.KNOWN:
            continue
        if state.value is not True:
            continue
        proposals.append(
            ContextProposal(
                context_type=ContextType.CHILD_PRESENT,
                scope=home_scope(),
                confidence=_confidence(0.85, required=1, present=1),
                evidence=[
                    EvidenceItem(
                        device_id=device_id,
                        room_id=device.room_id,
                        capability="occupancy.presence",
                        value=True,
                        observed_at=state.occurred_at,
                        status="KNOWN",
                        note="designated child presence tracker",
                    )
                ],
                expires_in=_expiry_from(["occupancy.presence"]),
                reason_codes=["CHILD_TRACKER_HOME"],
            )
        )
    return proposals


def rule_connectivity_degraded(ctx: RuleContext) -> list[ContextProposal]:
    """Devices offline or reporting stale data.

    This context is what later phases consult before trusting the twin: a
    degraded home should not be driving confident automation.
    """
    offline: list[EvidenceItem] = []
    stale: list[EvidenceItem] = []
    for device_id, device in ctx.home.devices.items():
        if device.available is False:
            offline.append(
                EvidenceItem(
                    device_id=device_id,
                    room_id=device.room_id,
                    capability="device.online",
                    value=False,
                    observed_at=device.last_seen,
                    status="KNOWN",
                    note="device unavailable",
                )
            )
        for capability, state in device.capabilities.items():
            if state.status_at(ctx.now) is StateStatus.STALE:
                stale.append(
                    EvidenceItem(
                        device_id=device_id,
                        room_id=device.room_id,
                        capability=capability,
                        value=state.value,
                        observed_at=state.occurred_at,
                        status="STALE",
                        note="reading past its freshness window",
                    )
                )
    if not offline and not stale:
        return []

    total_devices = max(len(ctx.home.devices), 1)
    affected = len({e.device_id for e in offline + stale})
    severity = affected / total_devices
    return [
        ContextProposal(
            context_type=ContextType.DEVICE_CONNECTIVITY_DEGRADED,
            scope=home_scope(),
            confidence=round(min(0.6 + severity * 0.4, 1.0), 3),
            evidence=(offline + stale)[:50],  # bounded: a full outage is not a payload
            expires_in=timedelta(minutes=10),
            reason_codes=["DEVICES_OFFLINE"] if offline else ["STALE_READINGS"],
            metadata={
                "offline_devices": len({e.device_id for e in offline}),
                "stale_capabilities": len(stale),
                "affected_fraction": round(severity, 3),
            },
        )
    ]


ALL_RULES: dict[str, Rule] = {
    "home_occupied": rule_home_occupied,
    "home_empty": rule_home_empty,
    "room_occupied": rule_room_occupied,
    "arriving": rule_arriving,
    "leaving": rule_leaving,
    "quiet_hours": rule_quiet_hours,
    "sleeping": rule_sleeping,
    "cooking": rule_cooking,
    "high_energy_usage": rule_high_energy_usage,
    "possible_water_leak": rule_possible_water_leak,
    "possible_gas_risk": rule_possible_gas_risk,
    "child_present": rule_child_present,
    "connectivity_degraded": rule_connectivity_degraded,
}


def evaluate_all(ctx: RuleContext) -> list[ContextProposal]:
    """Run every rule in a stable order; contexts may overlap."""
    proposals: list[ContextProposal] = []
    for rule_id, rule in ALL_RULES.items():
        for proposal in rule(ctx):
            proposal.producer = f"rule:{rule_id}@{RULES_VERSION}"
            proposals.append(proposal)
    return proposals
