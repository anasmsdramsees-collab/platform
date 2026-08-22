"""Context contract tests (spec §14.3)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from syltra_contracts import (
    ADVISORY_ONLY_CONTEXTS,
    ContextRecord,
    ContextType,
    EvidenceItem,
    home_scope,
    room_scope,
)

pytestmark = pytest.mark.contract

NOW = datetime(2026, 8, 18, 20, 0, 0, tzinfo=UTC)


def evidence(status: str = "KNOWN") -> EvidenceItem:
    return EvidenceItem(
        device_id="dev_1",
        capability="occupancy.motion",
        value=True,
        observed_at=NOW,
        status=status,
    )


def record(**overrides: object) -> ContextRecord:
    payload: dict[str, object] = {
        "context_id": uuid4(),
        "home_id": "home_001",
        "context_type": ContextType.HOME_OCCUPIED,
        "scope": home_scope(),
        "started_at": NOW,
        "last_updated_at": NOW,
        "expires_at": NOW + timedelta(minutes=10),
        "confidence": 0.9,
        "evidence": [evidence()],
        "producer": "rule:home_occupied@1.0.0",
    }
    payload.update(overrides)
    return ContextRecord.model_validate(payload)


def test_context_types_match_spec_14_3() -> None:
    assert {c.value for c in ContextType} == {
        "HOME_OCCUPIED",
        "HOME_EMPTY",
        "ROOM_OCCUPIED",
        "SLEEPING",
        "COOKING",
        "ARRIVING",
        "LEAVING",
        "QUIET_HOURS",
        "CHILD_PRESENT",
        "HIGH_ENERGY_USAGE",
        "POSSIBLE_WATER_LEAK",
        "POSSIBLE_GAS_RISK",
        "DEVICE_CONNECTIVITY_DEGRADED",
    }


def test_record_carries_every_required_field() -> None:
    ctx = record()
    assert ctx.context_type is ContextType.HOME_OCCUPIED
    assert ctx.scope == "home"
    assert ctx.started_at and ctx.last_updated_at and ctx.expires_at
    assert 0.0 <= ctx.confidence <= 1.0
    assert ctx.evidence
    assert ctx.producer.startswith("rule:")


def test_context_without_evidence_is_rejected() -> None:
    # An inference with no traceable basis cannot be explained or audited.
    with pytest.raises(ValidationError, match="at least one evidence item"):
        record(evidence=[])


def test_confidence_must_be_a_probability() -> None:
    for bad in (-0.1, 1.1):
        with pytest.raises(ValidationError):
            record(confidence=bad)


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        record(expires_at=datetime(2026, 8, 18, 21, 0, 0))  # noqa: DTZ001


def test_expiry_controls_activity() -> None:
    ctx = record(expires_at=NOW + timedelta(minutes=5))
    assert ctx.is_active_at(NOW)
    assert ctx.is_active_at(NOW + timedelta(minutes=4))
    assert not ctx.is_active_at(NOW + timedelta(minutes=6))


def test_room_scope_round_trips() -> None:
    ctx = record(scope=room_scope("kitchen"), context_type=ContextType.ROOM_OCCUPIED)
    assert ctx.scope == "room:kitchen"
    assert ctx.scope_room_id == "kitchen"
    assert record().scope_room_id is None


def test_evidence_usability_follows_twin_status() -> None:
    assert evidence("KNOWN").is_usable
    assert not evidence("STALE").is_usable
    assert not evidence("UNKNOWN").is_usable


@pytest.mark.safety
def test_risk_contexts_are_marked_advisory_only() -> None:
    # Safety invariants 6 and 18: an inferred context can raise awareness but
    # must never stand in for a certified alarm.
    assert ADVISORY_ONLY_CONTEXTS == {
        ContextType.POSSIBLE_GAS_RISK,
        ContextType.POSSIBLE_WATER_LEAK,
    }
    assert record(context_type=ContextType.POSSIBLE_GAS_RISK).is_advisory_only()
    assert record(context_type=ContextType.POSSIBLE_WATER_LEAK).is_advisory_only()
    assert not record(context_type=ContextType.HOME_OCCUPIED).is_advisory_only()
