"""Event envelope contract tests (spec §11)."""

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError
from syltra_contracts import EVENT_TYPES, EventEnvelope

pytestmark = pytest.mark.contract

# The example envelope from spec §11.1, verbatim except for real UUIDs.
SPEC_EXAMPLE = {
    "event_id": "5f0d8ee0-56cf-4d34-9d5e-0c8a1a2b3c4d",
    "event_type": "device.state.changed",
    "schema_version": "1.0",
    "occurred_at": "2026-08-18T15:30:00.000Z",
    "received_at": "2026-08-18T15:30:00.100Z",
    "home_id": "home_001",
    "correlation_id": "6a1e9ff1-67d0-4e45-ae6f-1d9b2c3d4e5f",
    "causation_id": None,
    "source": {
        "service": "edge-agent",
        "instance_id": "hub_001",
        "protocol": "home_assistant_websocket",
    },
    "subject": {
        "device_id": "device_001",
        "entity_id": "sensor.living_room_temperature",
        "room_id": "living_room",
    },
    "capability": "environment.temperature",
    "value": 27.4,
    "unit": "C",
    "quality": 0.98,
    "privacy_class": "HOUSEHOLD_PRIVATE",
    "metadata": {},
}


def test_spec_example_parses() -> None:
    env = EventEnvelope.model_validate(SPEC_EXAMPLE)
    assert env.event_type == "device.state.changed"
    assert env.value == 27.4
    assert env.occurred_at.tzinfo is not None


def test_round_trip_preserves_unknown_optional_fields() -> None:
    # Spec §11.3: relays must preserve unknown optional fields.
    payload = dict(SPEC_EXAMPLE, future_field={"nested": True})
    env = EventEnvelope.model_validate(payload)
    dumped = json.loads(env.model_dump_json())
    assert dumped["future_field"] == {"nested": True}


def test_unknown_event_type_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown event_type"):
        EventEnvelope.model_validate(dict(SPEC_EXAMPLE, event_type="made.up.type"))


def test_incompatible_schema_version_rejected() -> None:
    with pytest.raises(ValidationError, match="incompatible schema_version"):
        EventEnvelope.model_validate(dict(SPEC_EXAMPLE, schema_version="2.0"))


def test_compatible_minor_version_accepted() -> None:
    env = EventEnvelope.model_validate(dict(SPEC_EXAMPLE, schema_version="1.3"))
    assert env.schema_version == "1.3"


def test_naive_timestamp_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        EventEnvelope.model_validate(dict(SPEC_EXAMPLE, occurred_at="2026-08-18T15:30:00"))


@pytest.mark.parametrize("quality", [-0.1, 1.1])
def test_quality_out_of_range_rejected(quality: float) -> None:
    with pytest.raises(ValidationError):
        EventEnvelope.model_validate(dict(SPEC_EXAMPLE, quality=quality))


def test_envelope_is_immutable() -> None:
    env = EventEnvelope.model_validate(SPEC_EXAMPLE)
    with pytest.raises(ValidationError):
        env.value = 99  # type: ignore[misc]


def test_all_required_event_types_present() -> None:
    assert len(EVENT_TYPES) == 23
    for required in (
        "device.state.changed",
        "twin.state.updated",
        "recommendation.created",
        "policy.decision.created",
        "risk.state.changed",
        "action.succeeded",
        "manual.override.detected",
        "model.rolled_back",
    ):
        assert required in EVENT_TYPES


@given(
    event_type=st.sampled_from(sorted(EVENT_TYPES)),
    quality=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    home_id=st.text(min_size=1, max_size=40),
)
def test_property_valid_envelopes_always_parse(
    event_type: str, quality: float, home_id: str
) -> None:
    now = datetime.now(tz=UTC)
    env = EventEnvelope(
        event_id=uuid4(),
        event_type=event_type,
        schema_version="1.0",
        occurred_at=now,
        received_at=now,
        home_id=home_id,
        correlation_id=uuid4(),
        source={"service": "test", "instance_id": "t", "protocol": "unit"},
        quality=quality,
    )
    assert EventEnvelope.model_validate_json(env.model_dump_json()) == env
