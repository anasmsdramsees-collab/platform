"""Deterministic context rule tests (spec §14.3).

Carries three of the four Phase 3 acceptance criteria: every context has
evidence and expiry, missing sensors reduce confidence, and stale evidence
cannot keep a context active.
"""

from datetime import datetime, timedelta

import pytest
from syltra_context_engine.rules import ContextProposal, RuleContext, evaluate_all
from syltra_contracts import ContextType
from syltra_digital_twin.core import HomeState
from syltra_testing import EVENING, MIDDAY, stale_by
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading


def ctx(home_state: HomeState, now: datetime = MIDDAY) -> RuleContext:
    return RuleContext(home=home_state, now=now)


def types(proposals: list[ContextProposal]) -> set[ContextType]:
    return {p.context_type for p in proposals}


def find(proposals: list[ContextProposal], context_type: ContextType) -> ContextProposal | None:
    return next((p for p in proposals if p.context_type is context_type), None)


# ── universal contract: evidence and expiry ──


def test_every_proposal_carries_evidence_and_expiry() -> None:
    state = home(
        device("motion_1", "living_room", motion=reading("occupancy.motion", True, MIDDAY)),
        device("tracker", "entrance", presence=reading("occupancy.presence", True, MIDDAY)),
        device("meter", "utility", power=reading("energy.power", 3500.0, MIDDAY, "W")),
        device("leak", "kitchen", leak=reading("safety.water_leak", True, MIDDAY)),
    )
    proposals = evaluate_all(ctx(state))
    assert proposals
    for proposal in proposals:
        assert proposal.evidence, f"{proposal.context_type} has no evidence"
        assert proposal.expires_in > timedelta(0), f"{proposal.context_type} never expires"
        assert proposal.producer.startswith("rule:")
        assert 0.0 <= proposal.confidence <= 1.0


# ── occupancy ──


def test_home_occupied_from_motion_alone() -> None:
    state = home(device("m1", "living_room", motion=reading("occupancy.motion", True, MIDDAY)))
    occupied = find(evaluate_all(ctx(state)), ContextType.HOME_OCCUPIED)
    assert occupied is not None
    assert "MOTION_DETECTED" in occupied.reason_codes


def test_confidence_is_higher_when_two_signal_families_agree() -> None:
    motion_only = home(
        device("m1", "living_room", motion=reading("occupancy.motion", True, MIDDAY))
    )
    both = home(
        device("m1", "living_room", motion=reading("occupancy.motion", True, MIDDAY)),
        device("t1", "entrance", presence=reading("occupancy.presence", True, MIDDAY)),
    )
    weak = find(evaluate_all(ctx(motion_only)), ContextType.HOME_OCCUPIED)
    strong = find(evaluate_all(ctx(both)), ContextType.HOME_OCCUPIED)
    assert weak is not None and strong is not None
    # Acceptance criterion: missing sensors reduce confidence.
    assert weak.confidence < strong.confidence


def test_stale_motion_does_not_produce_home_occupied() -> None:
    # Acceptance criterion: stale evidence does not keep a context active.
    # occupancy.motion has a 300s freshness window.
    state = home(
        device(
            "m1",
            "living_room",
            motion=reading("occupancy.motion", True, stale_by(MIDDAY, 3600)),
        )
    )
    assert find(evaluate_all(ctx(state)), ContextType.HOME_OCCUPIED) is None


def test_home_empty_requires_at_least_one_usable_signal() -> None:
    # With no observations at all the honest answer is "unknown", not "empty".
    assert find(evaluate_all(ctx(home())), ContextType.HOME_EMPTY) is None

    state = home(device("m1", "living_room", motion=reading("occupancy.motion", False, MIDDAY)))
    assert find(evaluate_all(ctx(state)), ContextType.HOME_EMPTY) is not None


def test_home_empty_and_occupied_are_mutually_exclusive() -> None:
    state = home(
        device("m1", "living_room", motion=reading("occupancy.motion", True, MIDDAY)),
        device("m2", "bedroom", motion=reading("occupancy.motion", False, MIDDAY)),
    )
    found = types(evaluate_all(ctx(state)))
    assert ContextType.HOME_OCCUPIED in found
    assert ContextType.HOME_EMPTY not in found


def test_stale_signals_cannot_assert_an_empty_home() -> None:
    state = home(
        device(
            "m1", "living_room", motion=reading("occupancy.motion", False, stale_by(MIDDAY, 3600))
        )
    )
    assert find(evaluate_all(ctx(state)), ContextType.HOME_EMPTY) is None


def test_room_occupied_is_scoped_per_room_and_may_overlap() -> None:
    state = home(
        device("m1", "living_room", motion=reading("occupancy.motion", True, MIDDAY)),
        device("m2", "kitchen", motion=reading("occupancy.motion", True, MIDDAY)),
        device("m3", "bedroom", motion=reading("occupancy.motion", False, MIDDAY)),
    )
    rooms = {
        p.scope for p in evaluate_all(ctx(state)) if p.context_type is ContextType.ROOM_OCCUPIED
    }
    assert rooms == {"room:living_room", "room:kitchen"}


def test_arriving_needs_presence_and_an_opened_entry() -> None:
    presence_only = home(
        device("t1", "entrance", presence=reading("occupancy.presence", True, MIDDAY))
    )
    assert find(evaluate_all(ctx(presence_only)), ContextType.ARRIVING) is None

    arriving = home(
        device("t1", "entrance", presence=reading("occupancy.presence", True, MIDDAY)),
        device("d1", "entrance", contact=reading("contact.open", True, MIDDAY)),
    )
    proposal = find(evaluate_all(ctx(arriving)), ContextType.ARRIVING)
    assert proposal is not None
    assert proposal.expires_in == timedelta(minutes=5)  # transient, not standing


def test_leaving_needs_presence_away_and_an_opened_entry() -> None:
    state = home(
        device("t1", "entrance", presence=reading("occupancy.presence", False, MIDDAY)),
        device("d1", "entrance", contact=reading("contact.open", True, MIDDAY)),
    )
    assert find(evaluate_all(ctx(state)), ContextType.LEAVING) is not None


# ── activity ──


def test_quiet_hours_follows_the_clock() -> None:
    assert find(evaluate_all(ctx(home(), now=EVENING)), ContextType.QUIET_HOURS) is not None
    assert find(evaluate_all(ctx(home(), now=MIDDAY)), ContextType.QUIET_HOURS) is None


def test_quiet_hours_evidence_records_the_clock_reading() -> None:
    proposal = find(evaluate_all(ctx(home(), now=EVENING)), ContextType.QUIET_HOURS)
    assert proposal is not None
    assert proposal.evidence[0].capability == "system.clock"
    assert proposal.confidence == 1.0


def test_sleeping_requires_quiet_hours_presence_and_stillness() -> None:
    sleeping_state = home(
        device("t1", "bedroom", presence=reading("occupancy.presence", True, EVENING)),
        device("m1", "bedroom", motion=reading("occupancy.motion", False, EVENING)),
        device("lux", "bedroom", lux=reading("environment.illuminance", 2.0, EVENING, "lx")),
    )
    assert find(evaluate_all(ctx(sleeping_state, now=EVENING)), ContextType.SLEEPING) is not None
    # Same state during the day is not sleeping.
    assert find(evaluate_all(ctx(sleeping_state, now=MIDDAY)), ContextType.SLEEPING) is None


def test_sleeping_is_suppressed_by_motion_or_lights() -> None:
    with_motion = home(
        device("t1", "bedroom", presence=reading("occupancy.presence", True, EVENING)),
        device("m1", "bedroom", motion=reading("occupancy.motion", True, EVENING)),
    )
    assert find(evaluate_all(ctx(with_motion, now=EVENING)), ContextType.SLEEPING) is None

    with_lights = home(
        device("t1", "bedroom", presence=reading("occupancy.presence", True, EVENING)),
        device("m1", "bedroom", motion=reading("occupancy.motion", False, EVENING)),
        device("l1", "bedroom", light=reading("light.power", True, EVENING)),
    )
    assert find(evaluate_all(ctx(with_lights, now=EVENING)), ContextType.SLEEPING) is None


def test_cooking_needs_kitchen_occupancy_plus_an_appliance_signature() -> None:
    motion_only = home(device("m1", "kitchen", motion=reading("occupancy.motion", True, MIDDAY)))
    assert find(evaluate_all(ctx(motion_only)), ContextType.COOKING) is None

    cooking = home(
        device("m1", "kitchen", motion=reading("occupancy.motion", True, MIDDAY)),
        device("meter", "utility", power=reading("energy.power", 1500.0, MIDDAY, "W")),
    )
    proposal = find(evaluate_all(ctx(cooking)), ContextType.COOKING)
    assert proposal is not None
    assert proposal.scope == "room:kitchen"


# ── environment and health ──


def test_high_energy_usage_threshold() -> None:
    below = home(device("meter", "utility", power=reading("energy.power", 900.0, MIDDAY, "W")))
    above = home(device("meter", "utility", power=reading("energy.power", 4200.0, MIDDAY, "W")))
    assert find(evaluate_all(ctx(below)), ContextType.HIGH_ENERGY_USAGE) is None
    assert find(evaluate_all(ctx(above)), ContextType.HIGH_ENERGY_USAGE) is not None


@pytest.mark.safety
def test_water_leak_context_is_advisory_only() -> None:
    state = home(device("leak", "kitchen", leak=reading("safety.water_leak", True, MIDDAY)))
    proposal = find(evaluate_all(ctx(state)), ContextType.POSSIBLE_WATER_LEAK)
    assert proposal is not None
    assert proposal.metadata["advisory_only"] is True
    assert "ADVISORY_ONLY" in proposal.reason_codes


@pytest.mark.safety
def test_gas_risk_context_is_advisory_only() -> None:
    state = home(device("gas", "kitchen", gas=reading("safety.gas_alarm", True, MIDDAY)))
    proposal = find(evaluate_all(ctx(state)), ContextType.POSSIBLE_GAS_RISK)
    assert proposal is not None
    assert proposal.metadata["advisory_only"] is True
    assert "ADVISORY_ONLY" in proposal.reason_codes


@pytest.mark.safety
def test_stale_gas_reading_cannot_raise_a_risk_context() -> None:
    # Safety invariant 4: a stale sensor value cannot confirm a risk.
    # safety.gas_alarm has a 120s freshness window.
    state = home(
        device("gas", "kitchen", gas=reading("safety.gas_alarm", True, stale_by(MIDDAY, 600)))
    )
    assert find(evaluate_all(ctx(state)), ContextType.POSSIBLE_GAS_RISK) is None


def test_child_present_uses_a_designated_tracker_only() -> None:
    adult = home(
        device(
            "t1",
            "entrance",
            name="Adult phone",
            presence=reading("occupancy.presence", True, MIDDAY),
        )
    )
    assert find(evaluate_all(ctx(adult)), ContextType.CHILD_PRESENT) is None

    child = home(
        device(
            "t2",
            "entrance",
            name="Child tracker",
            presence=reading("occupancy.presence", True, MIDDAY),
        )
    )
    assert find(evaluate_all(ctx(child)), ContextType.CHILD_PRESENT) is not None


def test_connectivity_degraded_reports_offline_devices() -> None:
    state = home(
        device(
            "d1", "living_room", available=False, motion=reading("occupancy.motion", False, MIDDAY)
        ),
        device("d2", "kitchen", available=True, motion=reading("occupancy.motion", False, MIDDAY)),
    )
    proposal = find(evaluate_all(ctx(state)), ContextType.DEVICE_CONNECTIVITY_DEGRADED)
    assert proposal is not None
    assert proposal.metadata["offline_devices"] == 1
    assert proposal.metadata["affected_fraction"] == 0.5


def test_connectivity_degraded_reports_stale_readings() -> None:
    state = home(
        device(
            "d1", "living_room", motion=reading("occupancy.motion", True, stale_by(MIDDAY, 3600))
        )
    )
    proposal = find(evaluate_all(ctx(state)), ContextType.DEVICE_CONNECTIVITY_DEGRADED)
    assert proposal is not None
    assert proposal.metadata["stale_capabilities"] >= 1


def test_healthy_home_reports_no_degradation() -> None:
    state = home(device("d1", "living_room", motion=reading("occupancy.motion", True, MIDDAY)))
    assert find(evaluate_all(ctx(state)), ContextType.DEVICE_CONNECTIVITY_DEGRADED) is None


# ── determinism ──


def test_evaluation_is_deterministic_and_order_stable() -> None:
    state = home(
        device("m1", "living_room", motion=reading("occupancy.motion", True, MIDDAY)),
        device("m2", "kitchen", motion=reading("occupancy.motion", True, MIDDAY)),
        device("meter", "utility", power=reading("energy.power", 4200.0, MIDDAY, "W")),
        device("t1", "entrance", presence=reading("occupancy.presence", True, MIDDAY)),
    )
    first = [(p.context_type, p.scope, p.confidence) for p in evaluate_all(ctx(state))]
    for _ in range(5):
        assert [(p.context_type, p.scope, p.confidence) for p in evaluate_all(ctx(state))] == first
