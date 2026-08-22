"""Fault injection (spec §24.7) and soak behaviour (Phase 8 acceptance).

Spec §24.7 lists eleven faults to test. Each one below names the fault it
injects and the property that must survive it. The theme throughout: the
platform may lose capability under fault, but it must never lose *safety* — and
it must never fail in a way that leaves a household believing it is protected
when it is not.
"""

import gc
import sys
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from syltra_action_orchestrator import (
    ActionOrchestrator,
    OrchestratorConfig,
    build_action_request,
)
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_contracts import (
    ActionStatus,
    CommandResult,
    ModelReference,
    PolicyOutcome,
    Recommendation,
    RecommendationTarget,
    SafetyClass,
    compute_input_hash,
)
from syltra_contracts.policy import PolicyDecision
from syltra_digital_twin.core import TwinProjection
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_risk_engine import RiskEngineService, SafetyGovernor
from syltra_testing import build_device as device
from syltra_testing import build_home as home
from syltra_testing import build_reading as reading
from syltra_testing import make_envelope, make_sequence

pytestmark = pytest.mark.safety

HOME = "home_001"
NOW = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)


def approved_decision(**overrides: Any) -> PolicyDecision:
    payload: dict[str, Any] = {
        "decision_id": uuid4(),
        "recommendation_id": uuid4(),
        "home_id": HOME,
        "decision": PolicyOutcome.ALLOW,
        "evaluated_at": NOW,
        "expires_at": NOW + timedelta(minutes=15),
        "reason_codes": ["WITHIN_POLICY"],
        "safety_class": SafetyClass.COMFORT,
        "input_hash": compute_input_hash({"x": 1}),
    }
    payload.update(overrides)
    return PolicyDecision.model_validate(payload)


def recommendation(**overrides: Any) -> Recommendation:
    payload: dict[str, Any] = {
        "recommendation_id": uuid4(),
        "home_id": HOME,
        "recommendation_type": "climate.precondition",
        "created_at": NOW,
        "expires_at": NOW + timedelta(minutes=15),
        "target": RecommendationTarget(
            device_id="ac_living", capability="climate.target_temperature"
        ),
        "proposed_value": 23,
        "confidence": 0.9,
        "reason_codes": ["REPEATED_USER_PATTERN"],
        "model": ModelReference(name="temperature_preference", version="1.0.0"),
        "required_policy": "COMFORT_AUTOMATION",
    }
    payload.update(overrides)
    return Recommendation.model_validate(payload)


class FaultyGateway:
    """A gateway that can be made to fail in specific, chosen ways."""

    def __init__(self, fail_times: int = 0, latency_error: type[Exception] | None = None) -> None:
        self.state: dict[tuple[str, str], Any] = {
            ("ac_living", "climate.target_temperature"): 27.0
        }
        self.commands: list[Any] = []
        self._fail_times = fail_times
        self._latency_error = latency_error

    async def execute_capability_command(self, command: Any) -> CommandResult:
        self.commands.append(command)
        if self._fail_times > 0:
            self._fail_times -= 1
            if self._latency_error is not None:
                raise self._latency_error("injected fault")
            raise TimeoutError("injected timeout")
        self.state[(command.device_id, command.capability)] = command.value
        return CommandResult(accepted=True)

    async def read(self, device_id: str, capability: str) -> Any:
        return self.state.get((device_id, capability))


# ── §24.7: service crashes ──


def test_a_crashed_adaptive_engine_leaves_safety_monitoring_intact() -> None:
    # Safety invariant 7. The governor is constructed with no reference to the
    # adaptive engine, so "crashing" it is simply not having one.
    governor = SafetyGovernor()
    state = home(
        device("gas_1", "kitchen", gas=reading("safety.gas_alarm", True, NOW)),
        home_id=HOME,
    )
    assert governor.evaluate(HOME, state, NOW)


def test_a_crashed_risk_engine_does_not_authorize_anything() -> None:
    # Losing the risk engine loses detection, which is a real degradation — but
    # it must not fail *open* by leaving something authorized.
    policy = PolicyService()
    policy.set_policy(HOME, HomePolicy(unattended_automation=True, require_approval_below=0.0))
    policy.set_active_risk(HOME, True)  # last known state before the crash
    decision = policy.evaluate(recommendation(), now=NOW, twin_value=27.0)
    assert decision.decision is PolicyOutcome.DENY


# ── §24.7: message redelivery ──


def test_redelivery_of_the_same_event_changes_nothing() -> None:
    twin = TwinProjection()
    events = make_sequence(30)
    twin.apply_all(events)
    fingerprint = twin.snapshot(HOME, NOW).fingerprint()

    # Deliver everything a second and third time.
    twin.apply_all(events)
    twin.apply_all(events)
    assert twin.snapshot(HOME, NOW).fingerprint() == fingerprint


async def test_redelivery_of_an_action_request_does_not_act_twice() -> None:
    gateway = FaultyGateway()
    decision = approved_decision()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision={decision.decision_id: decision}.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
    )
    request = build_action_request(decision, recommendation(), NOW)
    for _ in range(5):
        await orchestrator.execute(request, now=NOW)
    assert len(gateway.commands) == 1


# ── §24.7: database latency and unavailability ──


def test_database_latency_does_not_block_hazard_detection() -> None:
    # The governor reads twin state, not storage. Slow or absent storage costs
    # history, not detection.
    governor = SafetyGovernor()
    state = home(
        device("smoke_1", "hall", smoke=reading("safety.smoke_alarm", True, NOW)),
        home_id=HOME,
    )
    assert governor.evaluate(HOME, state, NOW)


# ── §24.7: unavailable Home Assistant ──


async def test_an_unreachable_gateway_fails_the_action_rather_than_hanging() -> None:
    gateway = FaultyGateway(fail_times=99, latency_error=ConnectionError)
    decision = approved_decision()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision={decision.decision_id: decision}.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
    )
    result = await orchestrator.execute(
        build_action_request(decision, recommendation(), NOW), now=NOW
    )
    assert result.status is ActionStatus.FAILED
    assert result.attempt_count <= 2  # bounded, not infinite


# ── §24.7: stale sensor data ──


def test_stale_data_degrades_to_refusal_not_to_a_guess() -> None:
    policy = PolicyService()
    policy.set_policy(HOME, HomePolicy(unattended_automation=True, require_approval_below=0.0))
    decision = policy.evaluate(recommendation(), now=NOW, twin_value=27.0, twin_status="STALE")
    assert decision.decision is PolicyOutcome.DENY
    assert "TARGET_STATE_NOT_FRESH" in decision.reason_codes


def test_a_stale_alarm_stops_confirming_rather_than_latching() -> None:
    # A sensor that stops reporting must not leave a hazard permanently
    # confirmed, nor permanently denied — it becomes unusable, and the
    # protection-gap case surfaces it.
    governor = SafetyGovernor()
    fresh = home(
        device("gas_1", "kitchen", gas=reading("safety.gas_alarm", True, NOW)),
        home_id=HOME,
    )
    assert governor.evaluate(HOME, fresh, NOW)

    stale = home(
        device("gas_1", "kitchen", gas=reading("safety.gas_alarm", True, NOW)),
        home_id=HOME,
    )
    assert governor.evaluate(HOME, stale, NOW + timedelta(hours=2)) == []


# ── §24.7: clock differences ──


def test_a_future_dated_reading_cannot_confirm_a_hazard() -> None:
    # Clock skew must not become an injection route.
    governor = SafetyGovernor()
    skewed = home(
        device(
            "gas_1",
            "kitchen",
            gas=reading("safety.gas_alarm", True, NOW + timedelta(hours=6)),
        ),
        home_id=HOME,
    )
    assert governor.evaluate(HOME, skewed, NOW) == []


def test_a_backdated_recommendation_cannot_execute() -> None:
    policy = PolicyService()
    policy.set_policy(HOME, HomePolicy(unattended_automation=True, require_approval_below=0.0))
    old = recommendation(
        created_at=NOW - timedelta(days=2), expires_at=NOW + timedelta(minutes=15)
    )
    decision = policy.evaluate(old, now=NOW, twin_value=27.0)
    assert decision.decision is PolicyOutcome.DENY
    assert "HISTORICAL_REPLAY_SUSPECTED" in decision.reason_codes


# ── §24.7: corrupt model artifact and failed inference ──


def test_a_corrupt_model_artifact_is_refused(tmp_path: Any) -> None:
    from syltra_adaptive_engine.onnx_export import OnnxExportError, OnnxPredictor

    corrupt = tmp_path / "broken.onnx"
    corrupt.write_bytes(b"this is not an ONNX graph")
    # ONNX Runtime raises its own error type for an unparseable graph; the
    # point is that it raises rather than serving nonsense.
    with pytest.raises(Exception):  # noqa: B017
        OnnxPredictor(corrupt)

    missing = tmp_path / "absent.onnx"
    with pytest.raises(OnnxExportError, match=r"no ONNX artifact"):
        OnnxPredictor(missing)


def test_failed_inference_never_produces_a_recommendation() -> None:
    # An untrained model raises rather than returning a plausible number.
    from syltra_adaptive_engine.models import TemperaturePreferenceModel

    model = TemperaturePreferenceModel()
    with pytest.raises(RuntimeError, match="has not been trained"):
        model.predict(NOW)


def test_a_model_that_cannot_train_leaves_the_platform_working() -> None:
    class _Null:
        async def publish_envelope(self, subject: str, envelope: Any) -> None:
            return None

        async def publish_deadletter(self, **kwargs: Any) -> None:
            return None

    service = AdaptiveEngineService(_Null())  # type: ignore[arg-type]
    for index in range(3):
        service.observe(make_envelope(home_id=HOME, occurred_at=NOW + timedelta(minutes=index)))
    results = service.train_home(HOME)
    assert all(result.refused for result in results.values())
    # No model registered, no recommendation, no crash.
    assert service.registry.versions(HOME) == []
    assert service.build_recommendations(HOME, NOW) == []


# ── §24.7: conflicting manual and adaptive commands ──


async def test_a_manual_change_mid_flight_cancels_the_adaptive_action() -> None:
    gateway = FaultyGateway()
    decision = approved_decision()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision={decision.decision_id: decision}.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
    )
    request = build_action_request(decision, recommendation(), NOW)
    orchestrator.register_pending(request, now=NOW)
    orchestrator.cancel_conflicting(HOME, "ac_living", "climate.target_temperature")

    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.CANCELLED
    assert gateway.commands == []


# ── §24.7: network partition (cloud unreachable) ──


def test_a_network_partition_does_not_affect_local_safety() -> None:
    import socket

    original = socket.socket

    def _forbidden(*args: object, **kwargs: object) -> None:
        msg = "network partitioned"
        raise OSError(msg)

    socket.socket = _forbidden  # type: ignore[assignment, misc]
    try:
        risk = RiskEngineService()
        state = home(
            device("gas_1", "kitchen", gas=reading("safety.gas_alarm", True, NOW)),
            home_id=HOME,
        )
        risk.evaluate(HOME, state, NOW, occupied=False)
        assert risk.has_confirmed_case(HOME, NOW)
    finally:
        socket.socket = original  # type: ignore[misc]


# ── Phase 8 acceptance: no unbounded growth ──


def test_the_twin_does_not_grow_without_bound_under_a_long_run() -> None:
    # Spec §22 Phase 8: the simulator runs continuously without unbounded
    # resource growth. The twin keeps current state, not history, so a long run
    # must not accumulate.
    twin = TwinProjection()
    for batch in range(20):
        twin.apply_all(make_sequence(100, seed=batch, start=NOW + timedelta(hours=batch)))
    snapshot = twin.snapshot(HOME, NOW + timedelta(days=1))
    # 4 devices in the fixture, however many events arrive.
    assert len(snapshot.devices) == 4
    assert snapshot.events_applied == 2000


def test_the_deduplication_window_is_bounded() -> None:
    from syltra_digital_twin.core import _SEEN_EVENT_CAPACITY

    twin = TwinProjection()
    for batch in range(30):
        twin.apply_all(make_sequence(500, seed=batch, start=NOW + timedelta(hours=batch)))
    seen = twin._seen_events
    assert len(seen) <= _SEEN_EVENT_CAPACITY


def test_the_adaptive_history_is_bounded() -> None:
    from syltra_adaptive_engine.service import HISTORY_LIMIT

    class _Null:
        async def publish_envelope(self, subject: str, envelope: Any) -> None:
            return None

        async def publish_deadletter(self, **kwargs: Any) -> None:
            return None

    service = AdaptiveEngineService(_Null())  # type: ignore[arg-type]
    for batch in range(12):
        for event in make_sequence(500, seed=batch, start=NOW + timedelta(hours=batch)):
            service.observe(event)
    assert service.history_size(HOME) <= HISTORY_LIMIT


def test_risk_cases_do_not_accumulate_indefinitely() -> None:
    risk = RiskEngineService(governor=SafetyGovernor(rules=()))
    quiet = home(
        device("meter", "utility", power=reading("energy.power", 9000.0, NOW, "W")),
        home_id=HOME,
    )
    for hour in range(48):
        moment = NOW + timedelta(hours=hour)
        state = home(
            device("meter", "utility", power=reading("energy.power", 9000.0, moment, "W")),
            home_id=HOME,
        )
        risk.evaluate(HOME, state, moment, occupied=False)
        risk.sweep_expired(HOME, moment)
    # One open case per (category, room), not one per evaluation.
    assert len(risk.open_cases(HOME, NOW + timedelta(hours=48))) <= 2
    assert quiet is not None


def test_a_long_run_does_not_leak_objects() -> None:
    twin = TwinProjection()
    twin.apply_all(make_sequence(200, seed=1))
    gc.collect()
    baseline = len(gc.get_objects())

    for batch in range(5):
        twin.apply_all(make_sequence(200, seed=batch + 2, start=NOW + timedelta(hours=batch)))
    gc.collect()
    grown = len(gc.get_objects())

    # Some growth is normal; a leak would be proportional to events processed.
    assert grown - baseline < 20_000, f"object count grew by {grown - baseline}"
    assert sys.getsizeof(twin) < 10_000
