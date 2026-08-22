"""Digital Twin projection tests (spec §14.2).

Covers the four Phase 2 acceptance criteria directly:
identical sequence ⇒ identical state, duplicate/out-of-order handling,
multi-home isolation, and rebuild after reset.
"""

import random
from datetime import timedelta
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from syltra_digital_twin.core import StateStatus, TwinProjection
from syltra_testing import BASE_TIME as BASE
from syltra_testing import make_envelope as envelope
from syltra_testing import make_sequence


def test_applies_a_reading_to_device_capability() -> None:
    twin = TwinProjection()
    assert twin.apply(envelope(value=27.4))
    device = twin.device("home_001", "device_001")
    assert device is not None
    state = device.capability("environment.temperature")
    assert state.value == 27.4
    assert state.unit == "C"
    assert state.observed
    assert state.status_at(BASE) is StateStatus.KNOWN


def test_unobserved_capability_is_unknown_not_false() -> None:
    # The distinction that keeps "no data" from being read as "no alarm".
    twin = TwinProjection()
    twin.apply(envelope())
    device = twin.device("home_001", "device_001")
    assert device is not None
    gas = device.capability("safety.gas_alarm")
    assert gas.observed is False
    assert gas.value is None
    assert gas.status_at(BASE) is StateStatus.UNKNOWN
    assert not gas.is_usable_for_decisions(BASE)


def test_observed_false_is_known_not_unknown() -> None:
    twin = TwinProjection()
    twin.apply(envelope(capability="safety.gas_alarm", value=False, unit=None))
    device = twin.device("home_001", "device_001")
    assert device is not None
    gas = device.capability("safety.gas_alarm")
    assert gas.value is False
    assert gas.observed
    assert gas.status_at(BASE) is StateStatus.KNOWN
    assert gas.is_usable_for_decisions(BASE)


def test_value_becomes_stale_after_its_freshness_window() -> None:
    twin = TwinProjection()
    twin.apply(envelope(capability="safety.gas_alarm", value=False, unit=None))
    device = twin.device("home_001", "device_001")
    assert device is not None
    gas = device.capability("safety.gas_alarm")
    # Gas alarm freshness is 120s.
    assert gas.status_at(BASE + timedelta(seconds=60)) is StateStatus.KNOWN
    assert gas.status_at(BASE + timedelta(seconds=200)) is StateStatus.STALE
    assert not gas.is_usable_for_decisions(BASE + timedelta(seconds=200))


@pytest.mark.safety
def test_stale_value_is_never_usable_for_decisions() -> None:
    # Safety invariant 4: a stale sensor value cannot confirm a risk.
    twin = TwinProjection()
    twin.apply(envelope(capability="safety.gas_alarm", value=True, unit=None))
    device = twin.device("home_001", "device_001")
    assert device is not None
    gas = device.capability("safety.gas_alarm")
    assert gas.value is True
    assert not gas.is_usable_for_decisions(BASE + timedelta(hours=1))


def test_duplicate_event_id_is_inert() -> None:
    twin = TwinProjection()
    event = envelope(value=21.0)
    assert twin.apply(event)
    assert not twin.apply(event)
    home = twin.home("home_001")
    assert home is not None
    assert home.events_applied == 1


def test_out_of_order_update_does_not_overwrite_newer_state() -> None:
    twin = TwinProjection()
    twin.apply(envelope(value=28.4, occurred_at=BASE))
    twin.apply(envelope(value=26.1, occurred_at=BASE - timedelta(minutes=10)))
    device = twin.device("home_001", "device_001")
    assert device is not None
    assert device.capability("environment.temperature").value == 28.4


def test_correction_event_may_supersede_newer_state() -> None:
    twin = TwinProjection()
    twin.apply(envelope(value=28.4, occurred_at=BASE))
    twin.apply(
        envelope(
            value=22.0,
            occurred_at=BASE - timedelta(minutes=10),
            metadata={"correction": True},
        )
    )
    device = twin.device("home_001", "device_001")
    assert device is not None
    assert device.capability("environment.temperature").value == 22.0


def test_homes_are_isolated() -> None:
    twin = TwinProjection()
    twin.apply(envelope(home_id="home_a", device_id="dev_a", value=20.0))
    twin.apply(envelope(home_id="home_b", device_id="dev_b", value=30.0))
    assert twin.device("home_a", "dev_b") is None
    assert twin.device("home_b", "dev_a") is None
    assert twin.snapshot("home_a", BASE).devices.keys() == {"dev_a"}
    assert twin.snapshot("home_b", BASE).devices.keys() == {"dev_b"}


def test_unknown_home_yields_empty_snapshot_not_an_error() -> None:
    snapshot = TwinProjection().snapshot("nonexistent", BASE)
    assert snapshot.devices == {}
    assert snapshot.rooms == {}


def test_room_membership_tracks_device_moves() -> None:
    twin = TwinProjection()
    twin.apply(envelope(room_id="living_room"))
    twin.apply(envelope(room_id="bedroom", occurred_at=BASE + timedelta(minutes=1)))
    snapshot = twin.snapshot("home_001", BASE)
    assert snapshot.rooms["bedroom"] == ["device_001"]
    assert snapshot.rooms["living_room"] == []


def test_availability_is_unknown_until_observed() -> None:
    twin = TwinProjection()
    twin.apply(envelope())
    device = twin.device("home_001", "device_001")
    assert device is not None
    assert device.available is None  # not False


def test_availability_updates_from_device_online_capability() -> None:
    twin = TwinProjection()
    twin.apply(
        envelope(
            capability="device.online",
            value=False,
            unit=None,
            event_type="device.availability.changed",
        )
    )
    device = twin.device("home_001", "device_001")
    assert device is not None
    assert device.available is False


def test_device_removed_drops_it_from_state_and_rooms() -> None:
    twin = TwinProjection()
    twin.apply(envelope())
    twin.apply(
        envelope(
            capability=None,
            value=None,
            unit=None,
            event_type="device.removed",
            occurred_at=BASE + timedelta(minutes=1),
        )
    )
    assert twin.device("home_001", "device_001") is None
    assert twin.snapshot("home_001", BASE).rooms["living_room"] == []


def test_discovery_event_sets_the_device_name() -> None:
    twin = TwinProjection()
    twin.apply(
        envelope(
            capability=None, value="Living Room AC", unit=None, event_type="device.discovered"
        )
    )
    device = twin.device("home_001", "device_001")
    assert device is not None
    assert device.name == "Living Room AC"


def test_repeated_identical_value_reports_no_observable_change() -> None:
    twin = TwinProjection()
    twin.apply(envelope(value=21.0, occurred_at=BASE))
    changed = twin.apply(envelope(value=21.0, occurred_at=BASE + timedelta(minutes=1)))
    assert changed is False


# ── acceptance: determinism and rebuild ──


build_sequence = make_sequence


def test_identical_event_sequence_produces_identical_state() -> None:
    events = build_sequence()
    first, second = TwinProjection(), TwinProjection()
    first.apply_all(events)
    second.apply_all(events)
    assert (
        first.snapshot("home_001", BASE).fingerprint()
        == second.snapshot("home_001", BASE).fingerprint()
    )


def test_rebuild_after_reset_restores_the_same_state() -> None:
    events = build_sequence()
    twin = TwinProjection()
    twin.apply_all(events)
    before = twin.snapshot("home_001", BASE).fingerprint()

    twin.reset()
    assert twin.snapshot("home_001", BASE).devices == {}

    twin.apply_all(events)
    assert twin.snapshot("home_001", BASE).fingerprint() == before


def test_replaying_with_duplicates_yields_the_same_state() -> None:
    events = build_sequence()
    clean = TwinProjection()
    clean.apply_all(events)

    noisy = TwinProjection()
    noisy.apply_all([e for event in events for e in (event, event)])

    assert (
        noisy.snapshot("home_001", BASE).fingerprint()
        == clean.snapshot("home_001", BASE).fingerprint()
    )


@settings(max_examples=25, deadline=None)
@given(seed=st.integers(min_value=0, max_value=10_000))
def test_property_shuffled_delivery_converges_to_the_same_state(seed: int) -> None:
    """Delivery order must not change the final state.

    Events carry their own ``occurred_at``; the projection keeps the newest per
    capability, so a reordered stream converges on the same answer. This is what
    makes replay and redelivery safe.
    """
    events = build_sequence(40)
    ordered = TwinProjection()
    ordered.apply_all(events)

    shuffled = list(events)
    random.Random(seed).shuffle(shuffled)
    out_of_order = TwinProjection()
    out_of_order.apply_all(shuffled)

    assert (
        out_of_order.snapshot("home_001", BASE).fingerprint()
        == ordered.snapshot("home_001", BASE).fingerprint()
    )


def test_fingerprint_ignores_transport_artifacts_but_not_values() -> None:
    a = TwinProjection()
    b = TwinProjection()
    a.apply(envelope(value=21.0, event_id=uuid4(), received_at=BASE + timedelta(seconds=5)))
    b.apply(envelope(value=21.0, event_id=uuid4(), received_at=BASE + timedelta(seconds=99)))
    assert a.snapshot("home_001", BASE).fingerprint() == b.snapshot("home_001", BASE).fingerprint()

    c = TwinProjection()
    c.apply(envelope(value=21.5))
    assert c.snapshot("home_001", BASE).fingerprint() != a.snapshot("home_001", BASE).fingerprint()
