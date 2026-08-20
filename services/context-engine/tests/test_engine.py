"""Context lifecycle tests (spec §14.3): overlap, expiry, material change."""

from datetime import datetime, timedelta

import pytest
from syltra_context_engine.engine import ChangeKind, ContextChange, ContextEngine
from syltra_contracts import ContextType
from syltra_digital_twin.core import HomeState
from syltra_testing import MIDDAY, stale_by
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading

HOME = "home_001"


def occupied_home(at: datetime = MIDDAY, motion: bool = True) -> HomeState:
    return home(
        device("m1", "living_room", motion=reading("occupancy.motion", motion, at)),
        device("t1", "entrance", presence=reading("occupancy.presence", motion, at)),
    )


def kinds(changes: list[ContextChange], context_type: ContextType) -> list[ChangeKind]:
    return [c.kind for c in changes if c.record.context_type is context_type]


def test_new_context_is_reported_as_started() -> None:
    engine = ContextEngine()
    changes = engine.evaluate(HOME, occupied_home(), MIDDAY)
    assert ChangeKind.STARTED in kinds(changes, ContextType.HOME_OCCUPIED)
    assert engine.get(HOME, ContextType.HOME_OCCUPIED, "home") is not None


def test_unchanged_state_publishes_nothing() -> None:
    # Spec §14.3: publish context updates only on material change.
    engine = ContextEngine()
    state = occupied_home()
    engine.evaluate(HOME, state, MIDDAY)
    second = engine.evaluate(HOME, state, MIDDAY + timedelta(seconds=30))
    assert second == []


def test_confidence_shift_is_a_material_change() -> None:
    engine = ContextEngine()
    engine.evaluate(HOME, occupied_home(), MIDDAY)

    # Losing the presence tracker drops confidence by more than the threshold.
    weaker = home(device("m1", "living_room", motion=reading("occupancy.motion", True, MIDDAY)))
    changes = engine.evaluate(HOME, weaker, MIDDAY + timedelta(seconds=30))
    assert ChangeKind.UPDATED in kinds(changes, ContextType.HOME_OCCUPIED)


def test_context_identity_is_preserved_across_updates() -> None:
    engine = ContextEngine()
    engine.evaluate(HOME, occupied_home(), MIDDAY)
    original = engine.get(HOME, ContextType.HOME_OCCUPIED, "home")
    assert original is not None

    weaker = home(device("m1", "living_room", motion=reading("occupancy.motion", True, MIDDAY)))
    engine.evaluate(HOME, weaker, MIDDAY + timedelta(seconds=30))
    updated = engine.get(HOME, ContextType.HOME_OCCUPIED, "home")
    assert updated is not None
    # Same continuing context: id and start time survive, updated time moves.
    assert updated.context_id == original.context_id
    assert updated.started_at == original.started_at
    assert updated.last_updated_at > original.last_updated_at


def test_context_ends_when_its_evidence_stops() -> None:
    engine = ContextEngine()
    engine.evaluate(HOME, occupied_home(), MIDDAY)
    later = MIDDAY + timedelta(seconds=30)
    changes = engine.evaluate(HOME, occupied_home(at=later, motion=False), later)
    assert ChangeKind.ENDED in kinds(changes, ContextType.HOME_OCCUPIED)
    assert engine.get(HOME, ContextType.HOME_OCCUPIED, "home") is None


def test_sweep_expires_contexts_when_sensors_go_silent() -> None:
    # The acceptance criterion that needs a timer: with no further events, a
    # context must age out rather than remain true forever.
    engine = ContextEngine()
    engine.evaluate(HOME, occupied_home(), MIDDAY)
    assert engine.active_contexts(HOME, MIDDAY)

    much_later = MIDDAY + timedelta(hours=1)
    expired = engine.sweep_expired(HOME, much_later)
    assert any(c.kind is ChangeKind.EXPIRED for c in expired)
    assert engine.active_contexts(HOME, much_later) == []


def test_active_contexts_exclude_expired_ones() -> None:
    engine = ContextEngine()
    engine.evaluate(HOME, occupied_home(), MIDDAY)
    assert engine.active_contexts(HOME, MIDDAY + timedelta(minutes=1))
    assert engine.active_contexts(HOME, MIDDAY + timedelta(hours=2)) == []


def test_expiry_never_outlives_the_evidence_freshness() -> None:
    engine = ContextEngine()
    engine.evaluate(HOME, occupied_home(), MIDDAY)
    record = engine.get(HOME, ContextType.HOME_OCCUPIED, "home")
    assert record is not None
    # occupancy.motion has a 300s freshness window; the context may not outlive it.
    assert record.expires_at <= MIDDAY + timedelta(seconds=300)


def test_overlapping_contexts_coexist() -> None:
    engine = ContextEngine()
    state = home(
        device("m1", "kitchen", motion=reading("occupancy.motion", True, MIDDAY)),
        device("t1", "entrance", presence=reading("occupancy.presence", True, MIDDAY)),
        device("meter", "utility", power=reading("energy.power", 4200.0, MIDDAY, "W")),
    )
    engine.evaluate(HOME, state, MIDDAY)
    active = {(c.context_type, c.scope) for c in engine.active_contexts(HOME, MIDDAY)}
    assert (ContextType.HOME_OCCUPIED, "home") in active
    assert (ContextType.ROOM_OCCUPIED, "room:kitchen") in active
    assert (ContextType.COOKING, "room:kitchen") in active
    assert (ContextType.HIGH_ENERGY_USAGE, "home") in active


def test_room_contexts_are_independent() -> None:
    engine = ContextEngine()
    both = home(
        device("m1", "kitchen", motion=reading("occupancy.motion", True, MIDDAY)),
        device("m2", "bedroom", motion=reading("occupancy.motion", True, MIDDAY)),
    )
    engine.evaluate(HOME, both, MIDDAY)

    later = MIDDAY + timedelta(seconds=30)
    kitchen_only = home(
        device("m1", "kitchen", motion=reading("occupancy.motion", True, later)),
        device("m2", "bedroom", motion=reading("occupancy.motion", False, later)),
    )
    engine.evaluate(HOME, kitchen_only, later)
    scopes = {
        c.scope
        for c in engine.active_contexts(HOME, later)
        if c.context_type is ContextType.ROOM_OCCUPIED
    }
    assert scopes == {"room:kitchen"}


def test_homes_are_isolated() -> None:
    engine = ContextEngine()
    engine.evaluate("home_a", occupied_home(), MIDDAY)
    assert engine.active_contexts("home_a", MIDDAY)
    assert engine.active_contexts("home_b", MIDDAY) == []


def test_every_active_context_satisfies_the_contract() -> None:
    engine = ContextEngine()
    state = home(
        device("m1", "kitchen", motion=reading("occupancy.motion", True, MIDDAY)),
        device("t1", "entrance", presence=reading("occupancy.presence", True, MIDDAY)),
        device("meter", "utility", power=reading("energy.power", 4200.0, MIDDAY, "W")),
        device("leak", "kitchen", leak=reading("safety.water_leak", True, MIDDAY)),
    )
    engine.evaluate(HOME, state, MIDDAY)
    for record in engine.active_contexts(HOME, MIDDAY):
        assert record.evidence
        assert record.expires_at > record.started_at
        assert record.producer.startswith("rule:")
        assert 0.0 <= record.confidence <= 1.0
        assert record.home_id == HOME


@pytest.mark.safety
def test_stale_evidence_cannot_sustain_a_risk_context() -> None:
    # Safety invariant 4, at the lifecycle level: the context is created while
    # the alarm reading is fresh, then must disappear once it goes stale.
    engine = ContextEngine()
    fresh = home(device("gas", "kitchen", gas=reading("safety.gas_alarm", True, MIDDAY)))
    engine.evaluate(HOME, fresh, MIDDAY)
    assert engine.get(HOME, ContextType.POSSIBLE_GAS_RISK, "home") is not None

    later = MIDDAY + timedelta(minutes=10)
    stale = home(
        device("gas", "kitchen", gas=reading("safety.gas_alarm", True, stale_by(later, 600)))
    )
    engine.evaluate(HOME, stale, later)
    assert engine.get(HOME, ContextType.POSSIBLE_GAS_RISK, "home") is None


def test_change_ordering_is_deterministic() -> None:
    state = home(
        device("m1", "kitchen", motion=reading("occupancy.motion", True, MIDDAY)),
        device("t1", "entrance", presence=reading("occupancy.presence", True, MIDDAY)),
        device("meter", "utility", power=reading("energy.power", 4200.0, MIDDAY, "W")),
    )
    signatures = []
    for _ in range(5):
        engine = ContextEngine()
        changes = engine.evaluate(HOME, state, MIDDAY)
        signatures.append([(c.kind, c.record.context_type, c.record.scope) for c in changes])
    assert all(s == signatures[0] for s in signatures)
