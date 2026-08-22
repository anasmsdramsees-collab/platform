"""Feedback Service tests (spec §14.8)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from syltra_contracts import (
    FeedbackKind,
    FeedbackSource,
    ModelReference,
    Recommendation,
    RecommendationTarget,
)
from syltra_feedback_service import SUSPEND_BELOW, FeedbackService

NOW = datetime(2026, 8, 18, 13, 0, tzinfo=UTC)
HOME = "home_001"
REC_TYPE = "climate.precondition"


def recommendation() -> Recommendation:
    return Recommendation(
        recommendation_id=uuid4(),
        home_id=HOME,
        recommendation_type=REC_TYPE,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=15),
        target=RecommendationTarget(
            device_id="ac_living", capability="climate.target_temperature"
        ),
        proposed_value=23,
        confidence=0.9,
        reason_codes=["REPEATED_USER_PATTERN"],
        model=ModelReference(name="temperature_preference", version="1.0.0"),
        required_policy="COMFORT_AUTOMATION",
    )


def service_with_recommendation() -> tuple[FeedbackService, Recommendation]:
    service = FeedbackService()
    rec = recommendation()
    service.register_recommendation(rec)
    return service, rec


# ── recording ──


def test_all_six_responses_are_recordable() -> None:
    service, rec = service_with_recommendation()
    for kind in FeedbackKind:
        record = service.record(HOME, rec.recommendation_id, kind, now=NOW)
        assert record.kind is kind
    assert len(service.records(HOME)) == len(FeedbackKind)


def test_feedback_is_linked_to_its_recommendation_and_action() -> None:
    service, rec = service_with_recommendation()
    action_id = uuid4()
    record = service.record(
        HOME, rec.recommendation_id, FeedbackKind.ACCEPT, action_id=action_id, now=NOW
    )
    assert record.recommendation_id == rec.recommendation_id
    assert record.action_id == action_id
    assert service.records(HOME, rec.recommendation_id) == [record]


def test_every_response_is_audited() -> None:
    service, rec = service_with_recommendation()
    service.record(HOME, rec.recommendation_id, FeedbackKind.REJECT, now=NOW)
    entry = service.audit[-1]
    assert entry["action"] == "FEEDBACK_RECORDED"
    assert entry["kind"] == "REJECT"
    assert entry["recommendation_type"] == REC_TYPE


# ── confidence adjustment ──


def test_acceptance_raises_standing_and_rejection_lowers_it() -> None:
    service, rec = service_with_recommendation()
    baseline = service.adjustment_for(HOME, REC_TYPE)

    service.record(HOME, rec.recommendation_id, FeedbackKind.REJECT, now=NOW)
    lowered = service.adjustment_for(HOME, REC_TYPE)
    assert lowered < baseline

    for _ in range(5):
        service.record(HOME, rec.recommendation_id, FeedbackKind.ACCEPT, now=NOW)
    assert service.adjustment_for(HOME, REC_TYPE) > lowered


def test_trust_is_slow_to_earn_and_quick_to_lose() -> None:
    # A household that says no has told us more than one that clicked yes.
    service, rec = service_with_recommendation()
    service.record(HOME, rec.recommendation_id, FeedbackKind.REJECT, now=NOW)
    after_one_rejection = service.adjustment_for(HOME, REC_TYPE)
    service.record(HOME, rec.recommendation_id, FeedbackKind.ACCEPT, now=NOW)
    after_one_acceptance = service.adjustment_for(HOME, REC_TYPE)
    assert after_one_acceptance < 1.0
    assert (1.0 - after_one_rejection) > (after_one_acceptance - after_one_rejection)


def test_an_undo_costs_more_than_a_rejection() -> None:
    # The household let it happen, saw the result, and reversed it.
    rejecting = FeedbackService()
    undoing = FeedbackService()
    rec = recommendation()
    for service in (rejecting, undoing):
        service.register_recommendation(rec)
    rejecting.record(HOME, rec.recommendation_id, FeedbackKind.REJECT, now=NOW)
    undoing.record(HOME, rec.recommendation_id, FeedbackKind.UNDO, now=NOW)
    assert undoing.adjustment_for(HOME, REC_TYPE) < rejecting.adjustment_for(HOME, REC_TYPE)


def test_not_now_is_about_timing_and_does_not_change_standing() -> None:
    service, rec = service_with_recommendation()
    before = service.adjustment_for(HOME, REC_TYPE)
    service.record(HOME, rec.recommendation_id, FeedbackKind.NOT_NOW, now=NOW)
    assert service.adjustment_for(HOME, REC_TYPE) == before
    assert service.standing(HOME, REC_TYPE).deferred == 1


def test_modify_records_the_value_the_household_wanted() -> None:
    service, rec = service_with_recommendation()
    service.record(HOME, rec.recommendation_id, FeedbackKind.MODIFY, modified_value=21.5, now=NOW)
    assert service.preferred_values(HOME, REC_TYPE) == [21.5]
    # Partial agreement: penalised, but less than an outright rejection.
    assert 0.9 < service.adjustment_for(HOME, REC_TYPE) < 1.0


def test_adjustment_is_bounded() -> None:
    service, rec = service_with_recommendation()
    for _ in range(50):
        service.record(HOME, rec.recommendation_id, FeedbackKind.ACCEPT, now=NOW)
    assert service.adjustment_for(HOME, REC_TYPE) <= 1.0
    for _ in range(50):
        service.record(HOME, rec.recommendation_id, FeedbackKind.REJECT, now=NOW)
    assert service.adjustment_for(HOME, REC_TYPE) >= 0.0


# ── suppression and suspension ──


@pytest.mark.safety
def test_never_repeat_suppresses_the_type_permanently() -> None:
    service, rec = service_with_recommendation()
    service.record(HOME, rec.recommendation_id, FeedbackKind.NEVER_REPEAT, now=NOW)
    assert REC_TYPE in service.suppressed_types(HOME)
    assert service.standing(HOME, REC_TYPE).suppressed
    # Later acceptances do not quietly revive it.
    service.record(HOME, rec.recommendation_id, FeedbackKind.ACCEPT, now=NOW)
    assert REC_TYPE in service.suppressed_types(HOME)


@pytest.mark.safety
def test_repeated_rejection_marks_a_type_for_suspension() -> None:
    # Spec §19.4: suspend after repeated rejection or undo.
    service, rec = service_with_recommendation()
    for _ in range(5):
        service.record(HOME, rec.recommendation_id, FeedbackKind.REJECT, now=NOW)
    assert service.adjustment_for(HOME, REC_TYPE) < SUSPEND_BELOW
    assert REC_TYPE in service.types_needing_suspension(HOME)


def test_a_healthy_type_is_not_marked_for_suspension() -> None:
    service, rec = service_with_recommendation()
    for _ in range(3):
        service.record(HOME, rec.recommendation_id, FeedbackKind.ACCEPT, now=NOW)
    assert service.types_needing_suspension(HOME) == frozenset()


def test_acceptance_rate_is_reported() -> None:
    service, rec = service_with_recommendation()
    assert service.standing(HOME, REC_TYPE).acceptance_rate is None
    for kind in (FeedbackKind.ACCEPT, FeedbackKind.ACCEPT, FeedbackKind.REJECT):
        service.record(HOME, rec.recommendation_id, kind, now=NOW)
    assert service.standing(HOME, REC_TYPE).acceptance_rate == pytest.approx(0.667, abs=0.01)


# ── the feedback loop-breaker ──


@pytest.mark.safety
def test_an_automation_echo_is_recorded_but_never_teaches_preference() -> None:
    # Spec §14.8: prevent feedback loops caused by automation-generated state
    # changes. Without this the platform would treat its own writes as the
    # household agreeing with it, and reinforce its guesses indefinitely.
    service, rec = service_with_recommendation()
    before = service.adjustment_for(HOME, REC_TYPE)
    service.record(
        HOME,
        rec.recommendation_id,
        FeedbackKind.ACCEPT,
        source=FeedbackSource.AUTOMATION_ECHO,
        now=NOW,
    )
    assert service.adjustment_for(HOME, REC_TYPE) == before
    assert service.standing(HOME, REC_TYPE).accepted == 0
    # Still recorded for audit.
    assert len(service.records(HOME)) == 1
    assert service.audit[-1]["teaches_preference"] is False


@pytest.mark.safety
def test_a_change_right_after_our_own_write_is_classified_as_an_echo() -> None:
    service = FeedbackService()
    service.note_automation_write(HOME, "ac_living", "climate.target_temperature", NOW)
    assert (
        service.classify_state_change(
            HOME, "ac_living", "climate.target_temperature", NOW + timedelta(seconds=5)
        )
        is FeedbackSource.AUTOMATION_ECHO
    )


@pytest.mark.safety
def test_a_later_change_is_classified_as_a_person() -> None:
    # Once the echo window closes, a change is the household acting.
    service = FeedbackService()
    service.note_automation_write(HOME, "ac_living", "climate.target_temperature", NOW)
    assert (
        service.classify_state_change(
            HOME, "ac_living", "climate.target_temperature", NOW + timedelta(minutes=10)
        )
        is FeedbackSource.USER
    )


def test_a_change_to_an_untouched_device_is_a_person() -> None:
    service = FeedbackService()
    assert (
        service.classify_state_change(HOME, "light_kitchen", "light.power", NOW)
        is FeedbackSource.USER
    )


def test_system_feedback_does_not_teach_preference() -> None:
    service, rec = service_with_recommendation()
    before = service.adjustment_for(HOME, REC_TYPE)
    service.record(
        HOME,
        rec.recommendation_id,
        FeedbackKind.NOT_NOW,
        source=FeedbackSource.SYSTEM,
        now=NOW,
    )
    assert service.adjustment_for(HOME, REC_TYPE) == before


# ── isolation ──


def test_homes_are_isolated() -> None:
    service, rec = service_with_recommendation()
    service.record(HOME, rec.recommendation_id, FeedbackKind.NEVER_REPEAT, now=NOW)
    assert service.suppressed_types(HOME) == {REC_TYPE}
    assert service.suppressed_types("home_other") == frozenset()
    assert service.adjustment_for("home_other", REC_TYPE) == 1.0


def test_unknown_recommendation_still_records_under_an_explicit_type() -> None:
    service = FeedbackService()
    record = service.record(
        HOME, uuid4(), FeedbackKind.REJECT, recommendation_type="lighting.routine", now=NOW
    )
    assert record.kind is FeedbackKind.REJECT
    assert service.adjustment_for(HOME, "lighting.routine") < 1.0
