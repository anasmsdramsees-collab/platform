"""Shadow-mode and lifecycle tests (spec §19.2, Phase 4 acceptance).

The headline acceptance criterion for this phase: **models never dispatch
actions**. These tests assert that structurally — by tracing every path a model
output can take and showing none of them reach a device.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from syltra_adaptive_engine.service import (
    AdaptiveEngineService,
    shadow_subject,
)
from syltra_contracts import (
    LearningMode,
    LearningModeTransitionError,
    Recommendation,
)
from syltra_eventing.subjects import recommendation_subject
from syltra_testing import comfort_history, routine_history, sparse_history

HOME = "home_001"
NOW = datetime(2026, 6, 25, 19, 0, tzinfo=UTC)


class _RecordingPublisher:
    def __init__(self) -> None:
        self.published: list[tuple[str, Any]] = []

    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        self.published.append((subject, envelope))

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None

    def subjects(self) -> list[str]:
        return [subject for subject, _ in self.published]


def trained_service(
    mode: LearningMode = LearningMode.SHADOW,
) -> tuple[AdaptiveEngineService, _RecordingPublisher]:
    publisher = _RecordingPublisher()
    service = AdaptiveEngineService(publisher)  # type: ignore[arg-type]
    for event in comfort_history(days=21) + routine_history(days=28, hour=19, minute=0):
        service.observe(event)
    service.train_home(HOME)
    if mode is not LearningMode.OBSERVE:
        # Climb the ladder one rung at a time, as the spec requires.
        for step in (LearningMode.SHADOW, LearningMode.RECOMMEND):
            if step.value == mode.value or _rank(step) <= _rank(mode):
                service.set_mode(HOME, step)
            if step is mode:
                break
    return service, publisher


def _rank(mode: LearningMode) -> int:
    order = [
        LearningMode.DISABLED,
        LearningMode.OBSERVE,
        LearningMode.SHADOW,
        LearningMode.RECOMMEND,
        LearningMode.APPROVAL_REQUIRED,
        LearningMode.AUTHORIZED_AUTOMATION,
    ]
    return order.index(mode) if mode in order else -1


# ── the headline acceptance criterion ──


@pytest.mark.safety
def test_models_never_dispatch_actions() -> None:
    # Phase 4 acceptance + safety invariant 1. The engine's only output type is
    # Recommendation, which exposes no execution surface, and the service has
    # no method that could reach a device.
    service, _ = trained_service()
    recommendations = service.build_recommendations(HOME, NOW)
    assert recommendations
    for recommendation in recommendations:
        assert isinstance(recommendation, Recommendation)
        for forbidden in ("execute", "dispatch", "call_service", "apply"):
            assert not hasattr(recommendation, forbidden)
    for forbidden in ("execute_action", "dispatch", "call_service", "control_device"):
        assert not hasattr(service, forbidden)


@pytest.mark.safety
async def test_shadow_recommendations_never_reach_the_live_subject() -> None:
    # Spec §19.2 SHADOW: predictions are generated without being shown or executed.
    service, publisher = trained_service(LearningMode.SHADOW)
    recommendations = service.build_recommendations(HOME, NOW)
    published = await service.publish_recommendations(HOME, recommendations)

    assert published == 0
    assert publisher.subjects()
    assert all(subject == shadow_subject(HOME) for subject in publisher.subjects())
    assert recommendation_subject(HOME) not in publisher.subjects()
    assert len(service.shadow_log) == len(recommendations)


@pytest.mark.safety
async def test_shadow_recommendations_are_marked_and_not_actionable() -> None:
    service, _ = trained_service(LearningMode.SHADOW)
    for recommendation in service.build_recommendations(HOME, NOW):
        assert recommendation.shadow is True
        assert not recommendation.is_actionable_at(NOW)


@pytest.mark.safety
async def test_observe_mode_publishes_nothing_actionable() -> None:
    service, publisher = trained_service(LearningMode.OBSERVE)
    recommendations = service.build_recommendations(HOME, NOW)
    published = await service.publish_recommendations(HOME, recommendations)
    assert published == 0
    assert recommendation_subject(HOME) not in publisher.subjects()


async def test_recommend_mode_publishes_to_the_live_subject() -> None:
    service, publisher = trained_service(LearningMode.RECOMMEND)
    recommendations = service.build_recommendations(HOME, NOW)
    published = await service.publish_recommendations(HOME, recommendations)
    assert published == len(recommendations)
    assert recommendation_subject(HOME) in publisher.subjects()


# ── lifecycle enforcement (spec §19.2) ──


@pytest.mark.safety
def test_a_home_cannot_skip_from_observe_to_authorized_automation() -> None:
    service = AdaptiveEngineService(_RecordingPublisher())  # type: ignore[arg-type]
    assert service.mode(HOME) is LearningMode.OBSERVE
    with pytest.raises(LearningModeTransitionError):
        service.set_mode(HOME, LearningMode.AUTHORIZED_AUTOMATION)
    assert service.mode(HOME) is LearningMode.OBSERVE


@pytest.mark.safety
def test_the_ladder_must_be_climbed_in_order() -> None:
    service = AdaptiveEngineService(_RecordingPublisher())  # type: ignore[arg-type]
    for step in (
        LearningMode.SHADOW,
        LearningMode.RECOMMEND,
        LearningMode.APPROVAL_REQUIRED,
        LearningMode.AUTHORIZED_AUTOMATION,
    ):
        service.set_mode(HOME, step)
    assert service.mode(HOME) is LearningMode.AUTHORIZED_AUTOMATION


@pytest.mark.safety
def test_a_suspended_home_cannot_return_directly_to_automation() -> None:
    service = AdaptiveEngineService(_RecordingPublisher())  # type: ignore[arg-type]
    for step in (LearningMode.SHADOW, LearningMode.RECOMMEND, LearningMode.SUSPENDED):
        service.set_mode(HOME, step)
    with pytest.raises(LearningModeTransitionError):
        service.set_mode(HOME, LearningMode.AUTHORIZED_AUTOMATION)
    service.set_mode(HOME, LearningMode.OBSERVE)  # recovery starts low
    assert service.mode(HOME) is LearningMode.OBSERVE


def test_modes_are_tracked_per_home() -> None:
    service = AdaptiveEngineService(_RecordingPublisher())  # type: ignore[arg-type]
    service.set_mode("home_a", LearningMode.SHADOW)
    assert service.mode("home_a") is LearningMode.SHADOW
    assert service.mode("home_b") is LearningMode.OBSERVE


# ── training and recommendations ──


def test_training_registers_versions_that_are_not_yet_serving() -> None:
    service, _ = trained_service()
    versions = service.registry.versions(HOME)
    assert versions
    for version in versions:
        assert version.feature_schema_version == "1.0"
        assert version.training_code_revision
        assert version.evaluation_metrics
        assert version.card.summary
    # Registered is not promoted: nothing serves until an operator says so.
    assert service.registry.active(HOME, "temperature_preference") is None


def test_training_refuses_and_explains_on_sparse_history() -> None:
    publisher = _RecordingPublisher()
    service = AdaptiveEngineService(publisher)  # type: ignore[arg-type]
    for event in sparse_history():
        service.observe(event)
    results = service.train_home(HOME)
    assert all(result.refused for result in results.values())
    assert service.registry.versions(HOME) == []


def test_recommendations_carry_reasons_model_and_expiry() -> None:
    service, _ = trained_service()
    for recommendation in service.build_recommendations(HOME, NOW):
        assert recommendation.reason_codes
        assert recommendation.model.name
        assert recommendation.expires_at > recommendation.created_at
        assert recommendation.requires_user_approval is True
        assert recommendation.metadata["feature_schema"] == "1.0"


@pytest.mark.safety
def test_recommended_setpoints_stay_inside_the_safe_range() -> None:
    service, _ = trained_service()
    for recommendation in service.build_recommendations(HOME, NOW):
        if recommendation.target.capability == "climate.target_temperature":
            assert 16.0 <= recommendation.proposed_value <= 30.0


def test_an_untrained_home_produces_no_recommendations() -> None:
    service = AdaptiveEngineService(_RecordingPublisher())  # type: ignore[arg-type]
    assert service.build_recommendations("empty_home", NOW) == []


def test_history_is_bounded() -> None:
    from syltra_adaptive_engine.service import HISTORY_LIMIT

    service = AdaptiveEngineService(_RecordingPublisher())  # type: ignore[arg-type]
    assert HISTORY_LIMIT > 0
    for event in comfort_history(days=21):
        service.observe(event)
    assert 0 < service.history_size(HOME) <= HISTORY_LIMIT


def test_recommendations_expire_within_the_contract_ttl() -> None:
    service, _ = trained_service()
    for recommendation in service.build_recommendations(HOME, NOW):
        assert recommendation.expires_at - recommendation.created_at <= timedelta(minutes=15)
