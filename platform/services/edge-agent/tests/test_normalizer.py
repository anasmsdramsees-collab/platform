"""Normalizer tests: envelopes, duplicates, ordering, freshness (spec §14.1)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from syltra_edge_agent.mapping import MappingError
from syltra_edge_agent.normalizer import StateChangeNormalizer

BASE = datetime(2026, 8, 18, 12, 0, 0, tzinfo=UTC)


def make_normalizer() -> StateChangeNormalizer:
    return StateChangeNormalizer(
        home_id="home_test",
        hub_id="hub_test",
        device_id_for=lambda e: f"device_{e.split('.', 1)[1]}",
        room_id_for=lambda _e: "living_room",
    )


def event(
    entity_id: str = "sensor.living_room_temperature",
    state: str = "27.4",
    at: datetime = BASE,
    attributes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "entity_id": entity_id,
        "new_state": {
            "entity_id": entity_id,
            "state": state,
            "attributes": attributes
            if attributes is not None
            else {"device_class": "temperature"},
            "last_updated": at.isoformat(),
        },
    }


def test_produces_raw_and_normalized_envelopes() -> None:
    outcome = make_normalizer().normalize(event())
    assert outcome.raw_envelope is not None
    assert outcome.raw_envelope.capability is None
    assert len(outcome.envelopes) == 1
    assert outcome.envelopes[0].capability == "environment.temperature"
    assert outcome.envelopes[0].value == 27.4
    # No unit_of_measurement attribute → the capability's default unit applies.
    assert outcome.envelopes[0].unit == "C"


def test_raw_and_normalized_share_a_correlation_id() -> None:
    outcome = make_normalizer().normalize(event())
    assert outcome.raw_envelope is not None
    assert outcome.envelopes[0].correlation_id == outcome.raw_envelope.correlation_id


def test_duplicate_delivery_is_suppressed() -> None:
    n = make_normalizer()
    first = n.normalize(event())
    second = n.normalize(event())
    assert not first.duplicate
    assert second.duplicate
    assert second.envelopes == []
    assert "DUPLICATE_EVENT" in second.reason_codes


def test_same_value_at_a_later_time_is_not_a_duplicate() -> None:
    n = make_normalizer()
    n.normalize(event(at=BASE))
    later = n.normalize(event(at=BASE + timedelta(seconds=30)))
    assert not later.duplicate


def test_out_of_order_event_is_flagged_and_downgraded() -> None:
    n = make_normalizer()
    n.normalize(event(state="28.4", at=BASE))
    late = n.normalize(event(state="26.1", at=BASE - timedelta(minutes=10)))
    assert late.out_of_order
    assert "OUT_OF_ORDER_EVENT" in late.reason_codes
    # Still published (history matters) but with reduced quality and a marker.
    assert late.envelopes[0].quality == 0.5
    assert late.envelopes[0].metadata["out_of_order"] is True


def test_in_order_events_keep_full_quality() -> None:
    n = make_normalizer()
    n.normalize(event(state="27.0", at=BASE))
    nxt = n.normalize(event(state="27.5", at=BASE + timedelta(seconds=60)))
    assert not nxt.out_of_order
    assert nxt.envelopes[0].quality == 1.0


def test_freshness_is_recorded_in_metadata() -> None:
    outcome = make_normalizer().normalize(event(at=datetime.now(tz=UTC)))
    assert outcome.raw_envelope is not None
    assert outcome.raw_envelope.metadata["freshness_ms"] >= 0.0


def test_unmapped_entity_publishes_raw_only() -> None:
    outcome = make_normalizer().normalize(
        event(entity_id="media_player.tv", state="playing", attributes={})
    )
    assert outcome.unmapped
    assert outcome.raw_envelope is not None
    assert outcome.envelopes == []


def test_unavailable_entity_becomes_availability_event() -> None:
    outcome = make_normalizer().normalize(event(state="unavailable"))
    assert outcome.envelopes[0].event_type == "device.availability.changed"
    assert outcome.envelopes[0].capability == "device.online"
    assert outcome.envelopes[0].value is False


def test_entity_removal_is_treated_as_unavailable() -> None:
    outcome = make_normalizer().normalize(
        {"entity_id": "sensor.living_room_temperature", "new_state": None}
    )
    assert outcome.envelopes[0].capability == "device.online"


@pytest.mark.parametrize(
    "payload",
    [
        {"new_state": {"state": "on"}},
        {"entity_id": "", "new_state": {"state": "on"}},
        {"entity_id": "sensor.a", "new_state": {"state": None, "attributes": {}}},
    ],
)
def test_structurally_invalid_payloads_raise(payload: dict[str, Any]) -> None:
    with pytest.raises(MappingError):
        make_normalizer().normalize(payload)


def test_naive_timestamps_are_treated_as_utc() -> None:
    payload = event()
    payload["new_state"]["last_updated"] = "2026-08-18T12:00:00"
    outcome = make_normalizer().normalize(payload)
    assert outcome.raw_envelope is not None
    assert outcome.raw_envelope.occurred_at.tzinfo is not None


@given(count=st.integers(min_value=2, max_value=40))
def test_property_repeated_identical_delivery_publishes_once(count: int) -> None:
    n = make_normalizer()
    published = 0
    for _ in range(count):
        outcome = n.normalize(event())
        published += len(outcome.envelopes)
    assert published == 1
