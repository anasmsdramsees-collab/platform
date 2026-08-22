"""Registry lifecycle and ONNX artifact tests (spec §19, §7.5).

Phase 4 acceptance: inference output is validated, and model rollback works.
Safety invariants 14 and 15: a model cannot raise its own permission level, and
a version cannot activate without evaluation and explicit promotion.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
from syltra_adaptive_engine.features import extract_events
from syltra_adaptive_engine.models import TemperaturePreferenceModel
from syltra_adaptive_engine.onnx_export import (
    InferenceOutputError,
    OnnxExportError,
    OnnxPredictor,
    export_estimator,
)
from syltra_adaptive_engine.registry import (
    ModelRegistry,
    PromotionRefused,
    RollbackUnavailable,
    build_card,
)
from syltra_contracts import ModelCard, ModelStatus, ModelType, ModelVersion, TrainingWindow
from syltra_testing import comfort_history

NOW = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)


def window() -> TrainingWindow:
    return TrainingWindow(
        start=NOW - timedelta(days=21), end=NOW, sample_count=200, distinct_days=21
    )


def card() -> ModelCard:
    return build_card(
        ModelType.TEMPERATURE_PREFERENCE,
        summary="Comfort preference baseline",
        limitations="Small local sample; extrapolation is clamped.",
        training_data="21 days of local setpoint changes.",
        evaluation="Mean absolute error against held-in data.",
    )


def register(
    registry: ModelRegistry,
    version: str,
    metrics: dict[str, float] | None = None,
    home_id: str = "home_001",
) -> ModelVersion:
    return registry.register(
        home_id=home_id,
        name="temperature_preference",
        version=version,
        model_type=ModelType.TEMPERATURE_PREFERENCE,
        feature_schema_version="1.0",
        training_code_revision="abc1234",
        training_window=window(),
        evaluation_metrics=metrics or {"mae": 0.5},
        card=card(),
    )


# ── registration and promotion ──


def test_registered_versions_do_not_serve_until_promoted() -> None:
    registry = ModelRegistry()
    record = register(registry, "1.0.0")
    assert record.status is ModelStatus.TRAINED
    assert registry.active("home_001", "temperature_preference") is None


@pytest.mark.safety
def test_promotion_is_an_explicit_recorded_act() -> None:
    # Safety invariant 15: no activation without evaluation and explicit promotion.
    registry = ModelRegistry()
    register(registry, "1.0.0")
    promoted = registry.promote("home_001", "temperature_preference", "1.0.0")
    assert promoted.status is ModelStatus.ACTIVE
    assert promoted.promoted_at is not None
    assert any(e.action == "MODEL_ACTIVATED" for e in registry.audit)


@pytest.mark.safety
def test_a_version_failing_its_evaluation_gate_cannot_serve() -> None:
    # "Evaluated" must mean "evaluated and passed".
    registry = ModelRegistry()
    register(registry, "1.0.0", metrics={"mae": 4.0})  # far worse than the 1.5 °C gate
    with pytest.raises(PromotionRefused, match="promotion gate"):
        registry.promote("home_001", "temperature_preference", "1.0.0")
    assert registry.active("home_001", "temperature_preference") is None
    assert any(e.action == "MODEL_PROMOTION_REFUSED" for e in registry.audit)


@pytest.mark.safety
def test_a_version_missing_the_gate_metric_cannot_serve() -> None:
    registry = ModelRegistry()
    register(registry, "1.0.0", metrics={"unrelated_metric": 1.0})
    with pytest.raises(PromotionRefused):
        registry.promote("home_001", "temperature_preference", "1.0.0")


def test_promoting_an_unknown_version_is_refused() -> None:
    registry = ModelRegistry()
    with pytest.raises(PromotionRefused, match="no version"):
        registry.promote("home_001", "temperature_preference", "9.9.9")


def test_promotion_is_idempotent() -> None:
    registry = ModelRegistry()
    register(registry, "1.0.0")
    first = registry.promote("home_001", "temperature_preference", "1.0.0")
    second = registry.promote("home_001", "temperature_preference", "1.0.0")
    assert first.model_id == second.model_id


def test_promoting_a_new_version_retires_the_previous_one() -> None:
    registry = ModelRegistry()
    register(registry, "1.0.0")
    registry.promote("home_001", "temperature_preference", "1.0.0")
    register(registry, "1.1.0")
    registry.promote("home_001", "temperature_preference", "1.1.0")

    active = registry.active("home_001", "temperature_preference")
    assert active is not None
    assert active.version == "1.1.0"
    assert active.rollback_target == "1.0.0"
    previous = registry.get("home_001", "temperature_preference", "1.0.0")
    assert previous is not None
    assert previous.status is ModelStatus.ROLLED_BACK


# ── rollback and suspension (Phase 4 acceptance) ──


def test_rollback_restores_the_previous_version() -> None:
    registry = ModelRegistry()
    register(registry, "1.0.0")
    registry.promote("home_001", "temperature_preference", "1.0.0")
    register(registry, "1.1.0")
    registry.promote("home_001", "temperature_preference", "1.1.0")

    restored = registry.rollback(
        "home_001", "temperature_preference", reason="regression in comfort"
    )
    assert restored.version == "1.0.0"
    assert restored.status is ModelStatus.ACTIVE
    active = registry.active("home_001", "temperature_preference")
    assert active is not None and active.version == "1.0.0"
    assert any(e.action == "MODEL_ROLLED_BACK" for e in registry.audit)


def test_rollback_without_a_predecessor_is_refused() -> None:
    registry = ModelRegistry()
    register(registry, "1.0.0")
    registry.promote("home_001", "temperature_preference", "1.0.0")
    with pytest.raises(RollbackUnavailable, match="no rollback target"):
        registry.rollback("home_001", "temperature_preference")


def test_rollback_without_an_active_version_is_refused() -> None:
    registry = ModelRegistry()
    register(registry, "1.0.0")
    with pytest.raises(RollbackUnavailable, match="no active version"):
        registry.rollback("home_001", "temperature_preference")


@pytest.mark.safety
def test_suspension_withdraws_a_model_without_needing_a_replacement() -> None:
    # Spec §19.4: suspend on drift, degradation or a safety event.
    registry = ModelRegistry()
    register(registry, "1.0.0")
    registry.promote("home_001", "temperature_preference", "1.0.0")
    suspended = registry.suspend(
        "home_001", "temperature_preference", reason="required sensors went stale"
    )
    assert suspended.status is ModelStatus.SUSPENDED
    assert registry.active("home_001", "temperature_preference") is None
    assert any(e.action == "MODEL_SUSPENDED" for e in registry.audit)


@pytest.mark.safety
def test_registries_are_isolated_per_home() -> None:
    # Spec §14.4: per-home models. One household's model must never serve another.
    registry = ModelRegistry()
    register(registry, "1.0.0", home_id="home_a")
    registry.promote("home_a", "temperature_preference", "1.0.0")
    assert registry.active("home_a", "temperature_preference") is not None
    assert registry.active("home_b", "temperature_preference") is None
    assert registry.versions("home_b") == []


def test_every_lifecycle_act_is_audited() -> None:
    registry = ModelRegistry()
    register(registry, "1.0.0")
    registry.promote("home_001", "temperature_preference", "1.0.0")
    register(registry, "1.1.0")
    registry.promote("home_001", "temperature_preference", "1.1.0")
    registry.rollback("home_001", "temperature_preference")

    actions = [e.action for e in registry.audit]
    assert actions.count("MODEL_REGISTERED") == 2
    assert actions.count("MODEL_ACTIVATED") == 2
    assert actions.count("MODEL_ROLLED_BACK") == 1
    for event in registry.audit:
        assert event.actor and event.reason and event.home_id


def test_model_cards_carry_the_shared_safety_language() -> None:
    generated = build_card(ModelType.ROUTINE_BASELINE, "s", "l", "t", "e")
    assert "never an actuator command" in generated.intended_use
    assert "life-safety" in generated.out_of_scope_use
    assert "locks, valves, breakers" in generated.out_of_scope_use
    assert "never leaves the hub" in generated.ethical_and_safety_notes


# ── ONNX export and inference ──


@pytest.fixture
def fitted_model() -> TemperaturePreferenceModel:
    model = TemperaturePreferenceModel()
    model.train(extract_events(comfort_history(days=21)))
    return model


def test_export_produces_a_verified_artifact(
    fitted_model: TemperaturePreferenceModel, tmp_path: Path
) -> None:
    features, _ = fitted_model.build_design_matrix(extract_events(comfort_history(days=21)))
    artifact = export_estimator(fitted_model.estimator, features, tmp_path / "comfort.onnx")
    assert artifact.path.is_file()
    assert len(artifact.sha256) == 64
    assert artifact.feature_count == 4
    # Round-trip equivalence is verified during export, not assumed.
    assert artifact.max_round_trip_error < 1e-4


def test_exported_artifact_matches_the_estimator(
    fitted_model: TemperaturePreferenceModel, tmp_path: Path
) -> None:
    frame = extract_events(comfort_history(days=21))
    features, _ = fitted_model.build_design_matrix(frame)
    artifact = export_estimator(fitted_model.estimator, features, tmp_path / "m.onnx")

    predictor = OnnxPredictor(artifact.path, expected_features=4)
    served = predictor.predict(features[:10])
    assert fitted_model.estimator is not None
    direct = fitted_model.estimator.predict(features[:10])
    assert np.allclose(served, direct, atol=1e-4)


def test_export_rejects_an_empty_sample(tmp_path: Path) -> None:
    with pytest.raises(OnnxExportError, match="non-empty 2-D array"):
        export_estimator(object(), np.empty((0, 4)), tmp_path / "x.onnx")


def test_loading_a_missing_artifact_is_refused(tmp_path: Path) -> None:
    with pytest.raises(OnnxExportError, match="no ONNX artifact"):
        OnnxPredictor(tmp_path / "absent.onnx")


def test_inference_rejects_a_wrong_feature_count(
    fitted_model: TemperaturePreferenceModel, tmp_path: Path
) -> None:
    features, _ = fitted_model.build_design_matrix(extract_events(comfort_history(days=21)))
    artifact = export_estimator(fitted_model.estimator, features, tmp_path / "m.onnx")
    predictor = OnnxPredictor(artifact.path, expected_features=4)
    with pytest.raises(InferenceOutputError, match="features"):
        predictor.predict(np.zeros((2, 7)))


def test_inference_rejects_non_finite_input(
    fitted_model: TemperaturePreferenceModel, tmp_path: Path
) -> None:
    features, _ = fitted_model.build_design_matrix(extract_events(comfort_history(days=21)))
    artifact = export_estimator(fitted_model.estimator, features, tmp_path / "m.onnx")
    predictor = OnnxPredictor(artifact.path, expected_features=4)
    with pytest.raises(InferenceOutputError, match="NaN or infinity"):
        predictor.predict(np.array([[np.nan, 0.0, 0.0, 24.0]]))


def test_inference_accepts_a_single_row(
    fitted_model: TemperaturePreferenceModel, tmp_path: Path
) -> None:
    features, _ = fitted_model.build_design_matrix(extract_events(comfort_history(days=21)))
    artifact = export_estimator(fitted_model.estimator, features, tmp_path / "m.onnx")
    predictor = OnnxPredictor(artifact.path, expected_features=4)
    result = predictor.predict(np.array([0.5, 0.8, 0.0, 25.0]))
    assert result.shape == (1,)
    assert np.isfinite(result).all()


def test_artifact_digest_is_stable(
    fitted_model: TemperaturePreferenceModel, tmp_path: Path
) -> None:
    features, _ = fitted_model.build_design_matrix(extract_events(comfort_history(days=21)))
    artifact = export_estimator(fitted_model.estimator, features, tmp_path / "m.onnx")
    predictor = OnnxPredictor(artifact.path)
    assert predictor.sha256 == artifact.sha256
