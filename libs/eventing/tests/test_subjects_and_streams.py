"""Subject builders and stream policy (spec §12)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from syltra_eventing import (
    STREAM_SPECS,
    deadletter_subject,
    normalized_device_subject,
    raw_device_subject,
    sanitize_token,
    system_health_subject,
)
from syltra_eventing.subjects import (
    action_request_subject,
    policy_decision_subject,
    recommendation_subject,
    risk_state_subject,
    twin_updated_subject,
)

pytestmark = pytest.mark.contract


def test_subjects_match_spec_shape() -> None:
    assert raw_device_subject("home_001", "d1") == "syltra.raw.home.home_001.device.d1"
    assert (
        normalized_device_subject("home_001", "d1") == "syltra.normalized.home.home_001.device.d1"
    )
    assert twin_updated_subject("home_001") == "syltra.twin.home.home_001.updated"
    assert recommendation_subject("home_001") == "syltra.ai.home.home_001.recommendation"
    assert risk_state_subject("home_001") == "syltra.risk.home.home_001.state"
    assert policy_decision_subject("home_001") == "syltra.policy.home.home_001.decision"
    assert action_request_subject("home_001") == "syltra.action.home.home_001.request"
    assert system_health_subject("hub_001") == "syltra.system.hub.hub_001.health"
    assert deadletter_subject("edge-agent") == "syltra.deadletter.edge-agent"


def test_entity_ids_with_dots_are_sanitized() -> None:
    # HA entity ids contain dots, which would otherwise create subject levels.
    subject = raw_device_subject("home_001", "sensor.living_room_temperature")
    assert subject.count(".") == 5
    assert subject.endswith("sensor_living_room_temperature")


def test_wildcards_cannot_be_injected() -> None:
    assert "*" not in raw_device_subject("home_001", "a*b")
    assert ">" not in raw_device_subject("home_001", "a>b")
    assert sanitize_token("a*b") == "a_b"


def test_raw_retention_is_shorter_than_derived() -> None:
    by_name = {s.name: s for s in STREAM_SPECS}
    assert by_name["SYLTRA_RAW"].max_age < by_name["SYLTRA_NORMALIZED"].max_age
    assert by_name["SYLTRA_NORMALIZED"].max_age < by_name["SYLTRA_DERIVED"].max_age


def test_every_subject_family_is_covered_by_exactly_one_stream() -> None:
    subjects = [
        raw_device_subject("h", "d"),
        normalized_device_subject("h", "d"),
        twin_updated_subject("h"),
        recommendation_subject("h"),
        risk_state_subject("h"),
        policy_decision_subject("h"),
        action_request_subject("h"),
        system_health_subject("hub"),
        deadletter_subject("svc"),
    ]
    for subject in subjects:
        matches = [
            spec.name
            for spec in STREAM_SPECS
            for pattern in spec.subjects
            if subject.startswith(pattern.removesuffix(">"))
        ]
        assert len(matches) == 1, f"{subject} matched {matches}"


def test_identifier_without_alphanumerics_is_rejected() -> None:
    # Such identifiers would all collapse onto one placeholder token and route
    # distinct devices onto the same subject.
    for identifier in ("*", ">", "...", ":", "   "):
        with pytest.raises(ValueError, match="cannot form a NATS subject token"):
            sanitize_token(identifier)


# Identifiers carrying at least one alphanumeric character — the documented
# contract for sanitize_token.
_identifiers = st.text(min_size=1, max_size=30).filter(lambda s: any(c.isalnum() for c in s))


@given(home_id=_identifiers, device_id=_identifiers)
def test_property_subjects_have_fixed_depth(home_id: str, device_id: str) -> None:
    subject = normalized_device_subject(home_id, device_id)
    assert len(subject.split(".")) == 6
    assert "*" not in subject and ">" not in subject
