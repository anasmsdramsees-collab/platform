"""Action Orchestrator tests (spec §14.7, Phase 5 acceptance).

Every Phase 5 acceptance criterion lands here: no action without a valid policy
decision, duplicates cause one action, manual override cancels a conflict,
expired actions do not run, verification works, and retry policy is tested.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from syltra_action_orchestrator import (
    ActionOrchestrator,
    DispatchMode,
    OrchestratorConfig,
    build_action_request,
)
from syltra_contracts import (
    ActionStatus,
    CommandResult,
    ModelReference,
    PolicyDecision,
    PolicyOutcome,
    Recommendation,
    RecommendationTarget,
    SafetyClass,
    compute_input_hash,
)

NOW = datetime(2026, 8, 18, 13, 0, tzinfo=UTC)


class FakeGateway:
    """A device gateway that records commands and can be made to misbehave."""

    def __init__(
        self,
        state: dict[tuple[str, str], Any] | None = None,
        accept: bool = True,
        apply_effect: bool = True,
        raise_times: int = 0,
        refuse_reason: str | None = None,
    ) -> None:
        self.state = state or {}
        self.commands: list[Any] = []
        self._accept = accept
        self._apply = apply_effect
        self._raise_times = raise_times
        self._refuse_reason = refuse_reason

    async def execute_capability_command(self, command: Any) -> CommandResult:
        self.commands.append(command)
        if self._raise_times > 0:
            self._raise_times -= 1
            msg = "simulated transport failure"
            raise TimeoutError(msg)
        if not self._accept:
            return CommandResult(accepted=False, reason=self._refuse_reason or "refused")
        if self._apply:
            self.state[(command.device_id, command.capability)] = command.value
        return CommandResult(accepted=True)

    async def read(self, device_id: str, capability: str) -> Any:
        return self.state.get((device_id, capability))


def recommendation(**overrides: object) -> Recommendation:
    payload: dict[str, object] = {
        "recommendation_id": uuid4(),
        "home_id": "home_001",
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


def decision(outcome: PolicyOutcome = PolicyOutcome.ALLOW, **overrides: object) -> PolicyDecision:
    payload: dict[str, object] = {
        "decision_id": uuid4(),
        "recommendation_id": uuid4(),
        "home_id": "home_001",
        "decision": outcome,
        "evaluated_at": NOW,
        "expires_at": NOW + timedelta(minutes=15),
        "reason_codes": ["WITHIN_POLICY"],
        "safety_class": SafetyClass.COMFORT,
        "input_hash": compute_input_hash({"x": 1}),
    }
    payload.update(overrides)
    return PolicyDecision.model_validate(payload)


def build(
    gateway: FakeGateway,
    decisions: dict[UUID, PolicyDecision],
    environment: str = "production",
    dispatch: DispatchMode = DispatchMode.ENABLED,
) -> ActionOrchestrator:
    return ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision=decisions.get,
        config=OrchestratorConfig(
            environment=environment, dispatch=dispatch, verify_delay_seconds=0.0
        ),
    )


def scenario(
    outcome: PolicyOutcome = PolicyOutcome.ALLOW,
    initial: Any = 27.0,
    environment: str = "production",
    dispatch: DispatchMode = DispatchMode.ENABLED,
    safety_class: SafetyClass = SafetyClass.COMFORT,
    **gateway_kwargs: Any,
) -> tuple[ActionOrchestrator, FakeGateway, Any]:
    gateway = FakeGateway(
        state={("ac_living", "climate.target_temperature"): initial}, **gateway_kwargs
    )
    approved = decision(outcome, safety_class=safety_class)
    orchestrator = build(gateway, {approved.decision_id: approved}, environment, dispatch)
    request = build_action_request(approved, recommendation(), NOW)
    return orchestrator, gateway, request


# ── acceptance: no action without a valid policy decision ──


@pytest.mark.safety
async def test_an_action_without_a_decision_on_record_never_dispatches() -> None:
    # Safety invariant 2, checked at dispatch time rather than trusted from
    # earlier in the pipeline.
    gateway = FakeGateway(state={("ac_living", "climate.target_temperature"): 27.0})
    orphan = decision()
    orchestrator = build(gateway, {})  # decision deliberately not registered
    request = build_action_request(orphan, recommendation(), NOW)

    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.FAILED
    assert "NO_POLICY_DECISION" in result.reason_codes
    assert gateway.commands == []


@pytest.mark.safety
@pytest.mark.parametrize(
    "outcome",
    [
        PolicyOutcome.DENY,
        PolicyOutcome.REQUIRE_USER_APPROVAL,
        PolicyOutcome.PREPARE_ONLY,
        PolicyOutcome.ESCALATE_TO_FIXED_SAFETY_RULE,
    ],
)
async def test_only_an_allow_decision_reaches_a_device(outcome: PolicyOutcome) -> None:
    orchestrator, gateway, request = scenario(outcome)
    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.FAILED
    assert "POLICY_DECISION_NOT_AUTHORIZING" in result.reason_codes
    assert gateway.commands == []


@pytest.mark.safety
async def test_an_expired_decision_authorizes_nothing() -> None:
    # Safety invariant 3.
    gateway = FakeGateway(state={("ac_living", "climate.target_temperature"): 27.0})
    stale = decision(expires_at=NOW + timedelta(minutes=1))
    orchestrator = build(gateway, {stale.decision_id: stale})
    request = build_action_request(stale, recommendation(), NOW, ttl_seconds=3600)

    result = await orchestrator.execute(request, now=NOW + timedelta(minutes=5))
    assert result.status is ActionStatus.FAILED
    assert gateway.commands == []


@pytest.mark.safety
async def test_a_decision_for_another_household_is_refused() -> None:
    gateway = FakeGateway(state={("ac_living", "climate.target_temperature"): 27.0})
    foreign = decision(home_id="home_other")
    orchestrator = build(gateway, {foreign.decision_id: foreign})
    request = build_action_request(foreign, recommendation(home_id="home_001"), NOW)

    result = await orchestrator.execute(request, now=NOW)
    assert "DECISION_HOME_MISMATCH" in result.reason_codes
    assert gateway.commands == []


# ── acceptance: expired actions do not run ──


@pytest.mark.safety
async def test_an_expired_action_never_dispatches() -> None:
    orchestrator, gateway, request = scenario()
    result = await orchestrator.execute(request, now=NOW + timedelta(hours=1))
    assert result.status is ActionStatus.EXPIRED
    assert "ACTION_EXPIRED" in result.reason_codes
    assert gateway.commands == []


# ── acceptance: duplicate requests cause one action ──


@pytest.mark.safety
async def test_a_duplicate_request_does_not_act_twice() -> None:
    # Safety invariant 10.
    orchestrator, gateway, request = scenario()
    first = await orchestrator.execute(request, now=NOW)
    second = await orchestrator.execute(request, now=NOW)

    assert first.status is ActionStatus.SUCCEEDED
    assert second.action_id == first.action_id
    assert len(gateway.commands) == 1
    assert any(e.action == "ACTION_DEDUPLICATED" for e in orchestrator.audit)


@pytest.mark.safety
async def test_the_same_decision_yields_the_same_idempotency_key() -> None:
    approved = decision()
    rec = recommendation()
    a = build_action_request(approved, rec, NOW)
    b = build_action_request(approved, rec, NOW + timedelta(seconds=30))
    assert a.idempotency_key == b.idempotency_key
    assert a.action_id != b.action_id  # distinct attempts, one intent


# ── acceptance: manual override cancels a conflict ──


@pytest.mark.safety
async def test_manual_override_cancels_a_pending_action() -> None:
    # Safety invariant 5: manual control cancels conflicting adaptive actions.
    orchestrator, gateway, request = scenario()
    orchestrator.register_pending(request, now=NOW)
    assert orchestrator.pending_keys() == [request.idempotency_key]

    # A person adjusts the same device before the action lands.
    cancelled = orchestrator.cancel_conflicting(
        "home_001", "ac_living", "climate.target_temperature"
    )
    assert cancelled == [request.idempotency_key]

    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.CANCELLED
    assert "MANUAL_OVERRIDE_DETECTED" in result.reason_codes
    assert gateway.commands == []


@pytest.mark.safety
async def test_manual_override_on_another_device_leaves_the_action_alone() -> None:
    orchestrator, _gateway, request = scenario()
    orchestrator.register_pending(request, now=NOW)
    orchestrator.cancel_conflicting("home_001", "light_kitchen", "light.power")
    assert orchestrator.pending_keys() == [request.idempotency_key]

    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.SUCCEEDED


# ── acceptance: result verification works ──


async def test_a_verified_action_succeeds() -> None:
    orchestrator, _gateway, request = scenario()
    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.SUCCEEDED
    assert result.observed_value == 23
    assert result.attempts[-1].verified
    assert "VERIFIED" in result.reason_codes


@pytest.mark.safety
async def test_an_unverified_action_fails_even_though_dispatch_succeeded() -> None:
    # An action is successful because the device reports what we asked for,
    # not because the call returned without error.
    orchestrator, gateway, request = scenario(apply_effect=False)
    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.FAILED
    assert "VERIFICATION_FAILED" in result.reason_codes
    assert gateway.commands  # it really did dispatch
    assert all(not a.verified for a in result.attempts)


async def test_an_action_already_in_the_expected_state_is_a_no_dispatch_success() -> None:
    orchestrator, gateway, request = scenario(initial=23)
    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.SUCCEEDED
    assert "ALREADY_IN_EXPECTED_STATE" in result.reason_codes
    assert gateway.commands == []


# ── acceptance: failure and retry policy ──


async def test_a_transient_failure_is_retried_and_can_succeed() -> None:
    orchestrator, _gateway, request = scenario(raise_times=1)
    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.SUCCEEDED
    assert result.attempt_count == 2
    assert result.attempts[0].failure_kind is not None
    assert result.attempts[0].failure_kind.retryable


@pytest.mark.safety
async def test_a_permanent_refusal_is_not_retried() -> None:
    # Spec §14.7: retry only safe retryable failures. Repeating a refusal
    # would re-send a command the integration already declined.
    orchestrator, gateway, request = scenario(accept=False, refuse_reason="UNSUPPORTED")
    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.FAILED
    assert result.attempt_count == 1
    assert len(gateway.commands) == 1


async def test_retries_are_bounded_by_max_attempts() -> None:
    orchestrator, _gateway, request = scenario(raise_times=99)
    bounded = request.model_copy(update={"max_attempts": 3})
    result = await orchestrator.execute(bounded, now=NOW)
    assert result.status is ActionStatus.FAILED
    assert result.attempt_count == 3


async def test_a_failed_reversible_action_is_compensated() -> None:
    gateway = FakeGateway(
        state={("ac_living", "climate.target_temperature"): 27.0}, apply_effect=False
    )
    approved = decision()
    orchestrator = build(gateway, {approved.decision_id: approved})
    request = build_action_request(approved, recommendation(), NOW, previous_value=27.0)

    result = await orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.FAILED
    # The last command restores the previous value.
    assert gateway.commands[-1].value == 27.0
    assert any(e.action == "ACTION_COMPENSATED" for e in orchestrator.audit)


# ── development safety block (invariant 16) ──


@pytest.mark.safety
@pytest.mark.parametrize("environment", ["development", "simulation"])
async def test_critical_actuators_are_blocked_in_development(environment: str) -> None:
    gateway = FakeGateway(state={("valve_main", "valve.state"): "open"})
    approved = decision(safety_class=SafetyClass.LIFE_SAFETY_CRITICAL)
    orchestrator = build(gateway, {approved.decision_id: approved}, environment)
    rec = recommendation(
        target=RecommendationTarget(device_id="valve_main", capability="valve.state"),
        proposed_value="closed",
    )
    request = build_action_request(approved, rec, NOW)

    result = await orchestrator.execute(request, now=NOW)
    assert "CRITICAL_ACTUATOR_BLOCKED_IN_DEVELOPMENT" in result.reason_codes
    assert gateway.commands == []


# ── audit ──


@pytest.mark.safety
async def test_every_action_leaves_an_audit_record() -> None:
    # Safety invariant 12: every sensitive action has an immutable audit trail.
    orchestrator, _, request = scenario()
    await orchestrator.execute(request, now=NOW)
    assert orchestrator.audit
    entry = orchestrator.audit[-1]
    assert entry.action.startswith("ACTION_")
    assert entry.actor and entry.reason
    assert entry.detail["capability"] == "climate.target_temperature"
    assert entry.detail["safety_class"] == "COMFORT"


async def test_refusals_are_audited_too() -> None:
    orchestrator, _, request = scenario(PolicyOutcome.DENY)
    await orchestrator.execute(request, now=NOW)
    assert any("ACTION_" in e.action for e in orchestrator.audit)


async def test_results_are_queryable_per_home() -> None:
    orchestrator, _, request = scenario()
    await orchestrator.execute(request, now=NOW)
    assert len(orchestrator.results("home_001")) == 1
    assert orchestrator.results("home_other") == []
    assert orchestrator.result_for(request.idempotency_key) is not None


# ── safety invariant 9: fail safe when the audit store is unreachable ──


def _failing_sink(entry: object) -> None:
    msg = "audit database unreachable"
    raise ConnectionError(msg)


@pytest.mark.safety
async def test_an_adaptive_action_will_not_run_untraceably() -> None:
    # Spec §18.9: loss of the database must fail safely and prevent
    # untraceable adaptive execution.
    gateway = FakeGateway(state={("ac_living", "climate.target_temperature"): 27.0})
    approved = decision()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision={approved.decision_id: approved}.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
        audit_sink=_failing_sink,
    )
    first = build_action_request(approved, recommendation(), NOW)
    # The first action runs and its audit write fails, marking the store down.
    await orchestrator.execute(first, now=NOW)
    assert orchestrator.audit_store_available is False

    # The next adaptive action is refused before reaching the device.
    commands_before = len(gateway.commands)
    second = build_action_request(approved, recommendation(), NOW, sequence=2)
    result = await orchestrator.execute(second, now=NOW)
    assert result.status is ActionStatus.FAILED
    assert "AUDIT_STORE_UNAVAILABLE" in result.reason_codes
    assert len(gateway.commands) == commands_before


@pytest.mark.safety
async def test_a_deterministic_safety_response_still_runs_without_the_audit_store() -> None:
    # Refusing to act on a confirmed hazard because a log is down would be the
    # more dangerous failure. Safety-origin actions are exempt.
    gateway = FakeGateway(state={("ac_living", "climate.target_temperature"): 27.0})
    approved = decision()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision={approved.decision_id: approved}.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
        audit_sink=_failing_sink,
    )
    orchestrator.audit_store_available = False

    safety_action = build_action_request(approved, recommendation(), NOW).model_copy(
        update={"origin": "safety"}
    )
    result = await orchestrator.execute(safety_action, now=NOW)
    assert result.status is ActionStatus.SUCCEEDED
    assert gateway.commands


@pytest.mark.safety
async def test_the_in_memory_trail_survives_a_sink_failure() -> None:
    # Losing the durable record must not also lose the outcome.
    gateway = FakeGateway(state={("ac_living", "climate.target_temperature"): 27.0})
    approved = decision()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision={approved.decision_id: approved}.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
        audit_sink=_failing_sink,
    )
    await orchestrator.execute(build_action_request(approved, recommendation(), NOW), now=NOW)
    assert orchestrator.audit


async def test_a_working_sink_receives_every_entry() -> None:
    written: list[object] = []
    gateway = FakeGateway(state={("ac_living", "climate.target_temperature"): 27.0})
    approved = decision()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision={approved.decision_id: approved}.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
        audit_sink=written.append,
    )
    await orchestrator.execute(build_action_request(approved, recommendation(), NOW), now=NOW)
    assert written
    assert orchestrator.audit_store_available is True


# ── observe-only: the switch a first pilot runs behind ──


@pytest.mark.safety
async def test_an_observing_hub_sends_nothing_to_a_device() -> None:
    # The guarantee a household is owed on day one in a real home: everything
    # else runs, and nothing is commanded.
    orchestrator, gateway, request = scenario(dispatch=DispatchMode.OBSERVE_ONLY)

    result = await orchestrator.execute(request)

    assert result.status is ActionStatus.FAILED
    assert "DISPATCH_DISABLED_OBSERVE_ONLY" in result.reason_codes
    assert gateway.commands == [], "an observing hub commanded a device"


@pytest.mark.safety
@pytest.mark.parametrize("safety_class", list(SafetyClass))
async def test_observe_only_holds_for_every_safety_class(safety_class: SafetyClass) -> None:
    # Not only the critical ones. The existing environment block covers
    # life-safety and safety-related capabilities; comfort was never blocked in
    # any environment, and a light switching itself on in a stranger's house on
    # night one is exactly the wrong first impression.
    orchestrator, gateway, request = scenario(
        dispatch=DispatchMode.OBSERVE_ONLY, safety_class=safety_class
    )
    result = await orchestrator.execute(request)
    assert "DISPATCH_DISABLED_OBSERVE_ONLY" in result.reason_codes
    assert gateway.commands == []


@pytest.mark.safety
async def test_observe_only_is_checked_before_anything_else() -> None:
    # Placed at the top of the one function every dispatch passes through, so
    # no earlier condition can reach a device first. Proven by handing it a
    # request that would otherwise fail for a *different* reason: the observe
    # refusal is what comes back.
    gateway = FakeGateway(state={("ac_living", "climate.target_temperature"): 27.0})
    approved = decision(PolicyOutcome.ALLOW)
    # No decision on record at all, which would normally be NO_POLICY_DECISION.
    orchestrator = build(gateway, {}, "production", DispatchMode.OBSERVE_ONLY)
    request = build_action_request(approved, recommendation(), NOW)

    result = await orchestrator.execute(request)

    assert "DISPATCH_DISABLED_OBSERVE_ONLY" in result.reason_codes
    assert "NO_POLICY_DECISION" not in result.reason_codes
    assert gateway.commands == []


@pytest.mark.safety
async def test_an_observing_hub_records_what_it_would_have_sent() -> None:
    # The point of a pilot week: read back everything SYLTRA wanted to do. A
    # refusal that did not say what was refused would make the mode useless.
    orchestrator, _, request = scenario(dispatch=DispatchMode.OBSERVE_ONLY)

    await orchestrator.execute(request)

    entries = [e for e in orchestrator.audit if "DISPATCH_DISABLED" in e.reason]
    assert entries, "the refusal was not recorded"
    detail = entries[0].detail
    assert detail["capability"] == "climate.target_temperature"
    assert detail["device_id"] == "ac_living"
    assert "value" in detail, "the value that was not sent is not recorded"
    assert detail["attempts"] == 0, "an observing hub made no attempt"


async def test_dispatch_is_enabled_by_default() -> None:
    # Observe-only is a deliberate choice, not a default that could silently
    # disable a home that was meant to be working.
    assert OrchestratorConfig().dispatch is DispatchMode.ENABLED
