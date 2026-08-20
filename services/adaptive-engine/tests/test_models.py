"""Baseline model tests (spec §14.4, Phase 4 acceptance).

Covers: training is reproducible, insufficient-data behavior is tested, and
models produce predictions rather than actions.
"""

from datetime import UTC, datetime, timedelta

import polars as pl
import pytest
from syltra_adaptive_engine.features import extract_events, validate_schema
from syltra_adaptive_engine.models import (
    BaselineModel,
    EnergyAnomalyModel,
    RoutineBaselineModel,
    TemperaturePreferenceModel,
)
from syltra_adaptive_engine.models.routine import MIN_ROUTINE_STRENGTH
from syltra_testing import (
    HISTORY_START,
    comfort_history,
    energy_history,
    routine_history,
    sparse_history,
)


def frame_from(events: list) -> pl.DataFrame:  # type: ignore[type-arg]
    frame = extract_events(events)
    validate_schema(frame)
    return frame


# ── insufficient data (Phase 4 acceptance) ──


@pytest.mark.parametrize(
    "model",
    [RoutineBaselineModel(), TemperaturePreferenceModel(), EnergyAnomalyModel()],
    ids=["routine", "temperature", "energy"],
)
def test_models_refuse_to_train_on_sparse_data(model: BaselineModel) -> None:
    # Spec §14.4: do not train until minimum sample and diversity requirements
    # are met. Refusal is explained, not silent.
    result = model.train(frame_from(sparse_history()))
    assert result.refused
    assert not model.fitted
    assert result.reason_codes
    assert "cannot train" in result.sufficiency.explain()


@pytest.mark.parametrize(
    "model",
    [RoutineBaselineModel(), TemperaturePreferenceModel(), EnergyAnomalyModel()],
    ids=["routine", "temperature", "energy"],
)
def test_models_refuse_to_train_on_empty_history(model: BaselineModel) -> None:
    result = model.train(frame_from([]))
    assert result.refused
    assert "NO_DATA" in result.reason_codes


def test_untrained_models_refuse_to_predict() -> None:
    # Each model has its own predict signature, so they are exercised directly
    # rather than through a parametrized loop that would erase the types.
    with pytest.raises(RuntimeError, match="has not been trained"):
        RoutineBaselineModel().predict(HISTORY_START)
    with pytest.raises(RuntimeError, match="has not been trained"):
        TemperaturePreferenceModel().predict(HISTORY_START)
    with pytest.raises(RuntimeError, match="has not been trained"):
        EnergyAnomalyModel().predict(1000.0)


def test_data_requiring_days_rejects_a_single_busy_day() -> None:
    # 200 events in one day is plenty of samples but no day diversity: a
    # routine cannot be established from a single day.
    busy_day = routine_history(days=1, noise_events=200)
    result = RoutineBaselineModel().train(frame_from(busy_day))
    assert result.refused
    assert "INSUFFICIENT_DAY_DIVERSITY" in result.reason_codes


# ── routine baseline ──


def test_routine_model_finds_the_planted_evening_pattern() -> None:
    model = RoutineBaselineModel()
    result = model.train(frame_from(routine_history(days=28, hour=18, minute=30)))
    assert result.trained
    assert result.metrics["strong_buckets"] >= 1

    evening = datetime(2026, 6, 29, 18, 30, tzinfo=UTC)  # a Monday at the routine slot
    prediction = model.predict(evening)
    assert prediction.value is True
    assert prediction.confidence >= MIN_ROUTINE_STRENGTH
    assert "REPEATED_USER_PATTERN" in prediction.reason_codes


def test_routine_model_does_not_claim_a_pattern_at_a_quiet_hour() -> None:
    model = RoutineBaselineModel()
    model.train(frame_from(routine_history(days=28, hour=18, minute=30, noise_events=0)))
    quiet = datetime(2026, 6, 29, 4, 0, tzinfo=UTC)
    prediction = model.predict(quiet)
    assert prediction.value is False
    assert "NO_ESTABLISHED_PATTERN" in prediction.reason_codes


def test_routine_recency_weighting_favours_recent_behaviour() -> None:
    # An old pattern that stopped should score lower than a current one.
    # 14 days each keeps the combined history above the training minimums.
    old = routine_history(days=14, hour=18, start=HISTORY_START, noise_events=0)
    recent = routine_history(
        days=14, hour=20, start=HISTORY_START + timedelta(days=40), noise_events=0
    )
    model = RoutineBaselineModel()
    model.train(frame_from(old + recent))

    # routine_history plants events at :30, so query the same buckets.
    at_recent = model.predict(datetime(2026, 7, 13, 20, 30, tzinfo=UTC))
    at_old = model.predict(datetime(2026, 7, 13, 18, 30, tzinfo=UTC))
    assert at_recent.confidence > at_old.confidence


def test_routine_bucket_labels_are_readable() -> None:
    assert RoutineBaselineModel.describe_bucket(0) == "Mon 00:00"
    assert RoutineBaselineModel.describe_bucket(37) == "Mon 18:30"


def test_routine_training_is_reproducible() -> None:
    events = routine_history()
    first, second = RoutineBaselineModel(), RoutineBaselineModel()
    a = first.train(frame_from(events))
    b = second.train(frame_from(events))
    assert a.parameters == b.parameters
    assert a.metrics == b.metrics


def test_routine_rejects_invalid_decay() -> None:
    for bad in (0.0, -0.1, 1.5):
        with pytest.raises(ValueError, match="decay must fall"):
            RoutineBaselineModel(decay=bad)


# ── temperature preference ──


def test_temperature_model_learns_the_planted_relationship() -> None:
    model = TemperaturePreferenceModel()
    result = model.train(frame_from(comfort_history(days=21)))
    assert result.trained
    # The synthetic household lowers the setpoint as it warms; a useful model
    # should track that within a degree or so.
    assert result.metrics["mae"] < 1.0

    warm = model.predict(datetime(2026, 6, 20, 19, 0, tzinfo=UTC), indoor_temperature=28.0)
    cool = model.predict(datetime(2026, 6, 20, 19, 0, tzinfo=UTC), indoor_temperature=20.0)
    assert warm.value < cool.value


@pytest.mark.safety
def test_temperature_predictions_are_clamped_to_the_safe_range() -> None:
    # Even a badly extrapolating model cannot propose an unsafe setpoint.
    model = TemperaturePreferenceModel()
    model.train(frame_from(comfort_history(days=21)))
    for indoor in (-40.0, 0.0, 60.0, 200.0):
        prediction = model.predict(datetime(2026, 6, 20, 12, 0, tzinfo=UTC), indoor)
        assert 16.0 <= prediction.value <= 30.0


def test_temperature_confidence_reflects_fit_quality() -> None:
    model = TemperaturePreferenceModel()
    model.train(frame_from(comfort_history(days=21)))
    prediction = model.predict(datetime(2026, 6, 20, 19, 0, tzinfo=UTC), 25.0)
    assert 0.0 <= prediction.confidence <= 1.0
    assert prediction.detail["residual_std"] >= 0.0


def test_temperature_training_is_reproducible() -> None:
    events = comfort_history()
    a = TemperaturePreferenceModel().train(frame_from(events))
    b = TemperaturePreferenceModel().train(frame_from(events))
    assert a.parameters == b.parameters
    assert a.metrics == b.metrics


def test_temperature_feature_order_is_pinned() -> None:
    from syltra_adaptive_engine.models.temperature_preference import FEATURE_COLUMNS

    model = TemperaturePreferenceModel()
    result = model.train(frame_from(comfort_history()))
    assert result.parameters["feature_columns"] == list(FEATURE_COLUMNS)


# ── energy anomaly ──


def test_energy_model_establishes_a_robust_baseline() -> None:
    model = EnergyAnomalyModel()
    result = model.train(frame_from(energy_history(days=10)))
    assert result.trained
    assert 500 < result.metrics["median"] < 700
    assert result.metrics["mad"] > 0


def test_energy_model_flags_a_clear_spike() -> None:
    model = EnergyAnomalyModel()
    model.train(frame_from(energy_history(days=10)))
    prediction = model.predict(6000.0)
    assert prediction.value is True
    assert "ENERGY_ABOVE_BASELINE" in prediction.reason_codes
    assert prediction.confidence > 0


def test_energy_model_accepts_normal_readings() -> None:
    model = EnergyAnomalyModel()
    model.train(frame_from(energy_history(days=10)))
    prediction = model.predict(620.0)
    assert prediction.value is False
    assert "WITHIN_BASELINE" in prediction.reason_codes


def test_robust_baseline_is_not_dragged_by_training_spikes() -> None:
    # The point of median/MAD: spikes in the history must not raise the
    # baseline enough to mask later spikes.
    clean = EnergyAnomalyModel()
    clean.train(frame_from(energy_history(days=10, spikes=0)))
    contaminated = EnergyAnomalyModel()
    contaminated.train(frame_from(energy_history(days=10, spikes=8)))

    assert abs(contaminated.parameters["median"] - clean.parameters["median"]) < 50
    assert contaminated.predict(6000.0).value is True


def test_flat_history_does_not_produce_infinite_scores() -> None:
    from syltra_testing import make_envelope

    flat = [
        make_envelope(
            capability="energy.power",
            value=500.0,
            unit="W",
            occurred_at=HISTORY_START + timedelta(hours=i),
        )
        for i in range(120)
    ]
    model = EnergyAnomalyModel()
    model.train(frame_from(flat))
    score = model.score(500.0)
    assert score == 0.0
    assert model.predict(500.0).value is False


@pytest.mark.safety
def test_energy_prediction_is_marked_advisory_and_names_contributors() -> None:
    # Spec §20.6: never open a breaker on anomaly-model output alone.
    model = EnergyAnomalyModel()
    model.train(frame_from(energy_history(days=10)))
    prediction = model.predict(6000.0, contributors=["ac_living", "water_heater"])
    assert prediction.detail["advisory_only"] is True
    assert prediction.detail["suspected_contributors"] == ["ac_living", "water_heater"]


@pytest.mark.safety
def test_no_model_exposes_an_execution_path() -> None:
    # Safety invariant 1, structurally: models predict, they never dispatch.
    for model in (RoutineBaselineModel(), TemperaturePreferenceModel(), EnergyAnomalyModel()):
        for forbidden in ("execute", "dispatch", "call_service", "act", "apply_action"):
            assert not hasattr(model, forbidden)


def test_energy_rejects_invalid_threshold() -> None:
    for bad in (0.0, -1.0):
        with pytest.raises(ValueError, match="threshold must be positive"):
            EnergyAnomalyModel(threshold=bad)


def test_energy_training_is_reproducible() -> None:
    events = energy_history()
    a = EnergyAnomalyModel().train(frame_from(events))
    b = EnergyAnomalyModel().train(frame_from(events))
    assert a.parameters == b.parameters
    assert a.metrics == b.metrics


# ── per-capability data shortfalls (regression) ──


def test_energy_model_refuses_a_history_with_no_power_readings() -> None:
    # Regression: an ample history of *other* capabilities once satisfied the
    # global data requirement, so the model reported itself trained while
    # holding no baseline at all — and would have crashed on first predict().
    history = comfort_history(days=21)  # setpoints and temperatures, no power
    model = EnergyAnomalyModel()
    result = model.train(frame_from(history))
    assert result.refused
    assert "INSUFFICIENT_POWER_SAMPLES" in result.reason_codes
    assert not model.fitted
    with pytest.raises(RuntimeError, match="has not been trained"):
        model.predict(6000.0)


def test_temperature_model_refuses_a_history_with_no_setpoint_changes() -> None:
    history = energy_history(days=10)  # power only, no setpoints
    model = TemperaturePreferenceModel()
    result = model.train(frame_from(history))
    assert result.refused
    assert "INSUFFICIENT_SETPOINT_SAMPLES" in result.reason_codes
    assert not model.fitted


def test_routine_model_refuses_a_history_with_no_activations() -> None:
    history = energy_history(days=10)  # no light.power events at all
    model = RoutineBaselineModel()
    result = model.train(frame_from(history))
    assert result.refused
    assert "NO_CAPABILITY_ACTIVATIONS" in result.reason_codes
    assert not model.fitted


def test_a_refused_model_is_never_registered_as_a_version() -> None:
    from syltra_adaptive_engine.service import AdaptiveEngineService

    class _Null:
        async def publish_envelope(self, subject: str, envelope: object) -> None:
            return None

        async def publish_deadletter(self, **kwargs: object) -> None:
            return None

    service = AdaptiveEngineService(_Null())  # type: ignore[arg-type]
    for event in comfort_history(days=21):
        service.observe(event)
    results = service.train_home("home_001")

    assert results["energy_anomaly"].refused
    registered = {v.name for v in service.registry.versions("home_001")}
    assert "energy_anomaly" not in registered
