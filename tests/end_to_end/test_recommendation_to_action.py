"""End-to-end chain (spec §24.4, Phase 5 acceptance).

Runs the full path the spec describes:

    Recommendation → Policy → Action → device → verification → Feedback

against the real simulator devices behind the mock Home Assistant boundary, so
the chain is exercised end to end rather than through mocks at each seam.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from syltra_action_orchestrator import (
    ActionOrchestrator,
    OrchestratorConfig,
    build_action_request,
)
from syltra_contracts import (
    ActionStatus,
    CommandResult,
    FeedbackKind,
    FeedbackSource,
    ModelReference,
    PolicyOutcome,
    Recommendation,
    RecommendationTarget,
)
from syltra_feedback_service import FeedbackService
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_simulator.mock_ha import MockHomeAssistant

HOME = "home_e2e"
NOW = datetime(2026, 8, 18, 13, 0, tzinfo=UTC)

# Simulator entities, and the capability each expresses.
AC = ("sim_ac_living", "climate.target_temperature", "climate.living_room")
LIGHT = ("sim_light_living", "light.power", "light.living_room")
CURTAIN = ("sim_curtain_living", "cover.position", "cover.living_room_curtain")


class SimulatorGateway:
    """Drives the mock Home Assistant through capability commands."""

    def __init__(self, mock: MockHomeAssistant) -> None:
        self._mock = mock
        self._entities = {
            AC[0]: AC[2],
            LIGHT[0]: LIGHT[2],
            CURTAIN[0]: CURTAIN[2],
        }
        self.commands: list[Any] = []

    async def execute_capability_command(self, command: Any) -> CommandResult:
        self.commands.append(command)
        entity = self._entities.get(command.device_id)
        if entity is None:
            return CommandResult(accepted=False, reason="UNKNOWN_TARGET_MAPPING")
        if command.capability == "climate.target_temperature":
            await self._mock.set_state(entity, "cool", {"temperature": float(command.value)})
        elif command.capability == "light.power":
            await self._mock.set_state(entity, "on" if command.value else "off")
        elif command.capability == "cover.position":
            position = float(command.value)
            await self._mock.set_state(
                entity,
                "open" if position > 0 else "closed",
                {"current_position": position},
            )
        else:
            return CommandResult(accepted=False, reason="UNSUPPORTED_CAPABILITY_COMMAND")
        return CommandResult(accepted=True)

    async def read(self, device_id: str, capability: str) -> Any:
        entity = self._entities.get(device_id)
        if entity is None:
            return None
        state = self._mock._states.get(entity)
        if state is None:
            return None
        if capability == "climate.target_temperature":
            return state["attributes"].get("temperature")
        if capability == "light.power":
            return state["state"] == "on"
        if capability == "cover.position":
            return state["attributes"].get("current_position")
        return None


@dataclass
class Chain:
    """The assembled pipeline under test, named rather than positional."""

    mock: MockHomeAssistant
    gateway: SimulatorGateway
    policy: PolicyService
    orchestrator: ActionOrchestrator
    feedback: FeedbackService


@pytest_asyncio.fixture
async def chain() -> AsyncIterator[Chain]:
    mock = MockHomeAssistant(start_time=NOW)
    await mock.start()
    gateway = SimulatorGateway(mock)
    policy = PolicyService()
    policy.set_policy(
        HOME,
        HomePolicy(unattended_automation=True, require_approval_below=0.0),
    )
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision=policy.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
    )
    feedback = FeedbackService()
    try:
        yield Chain(mock, gateway, policy, orchestrator, feedback)
    finally:
        await mock.stop()


def recommendation(
    device_id: str, capability: str, value: Any, **overrides: Any
) -> Recommendation:
    payload: dict[str, Any] = {
        "recommendation_id": uuid4(),
        "home_id": HOME,
        "recommendation_type": "climate.precondition",
        "created_at": NOW,
        "expires_at": NOW + timedelta(minutes=15),
        "target": RecommendationTarget(device_id=device_id, capability=capability),
        "proposed_value": value,
        "confidence": 0.9,
        "reason_codes": ["REPEATED_USER_PATTERN"],
        "model": ModelReference(name="temperature_preference", version="1.0.0"),
        "required_policy": "COMFORT_AUTOMATION",
        "requires_user_approval": False,
    }
    payload.update(overrides)
    return Recommendation.model_validate(payload)


async def run_chain(chain: Chain, rec: Recommendation, now: datetime = NOW) -> tuple[Any, Any]:
    current = await chain.gateway.read(rec.target.device_id, rec.target.capability)
    decision = chain.policy.evaluate(rec, now=now, twin_value=current, twin_status="KNOWN")
    if decision.decision is not PolicyOutcome.ALLOW:
        return decision, None
    request = build_action_request(decision, rec, now, previous_value=current)
    result = await chain.orchestrator.execute(request, now=now)
    return decision, result


# ── the three comfort actions (Phase 5 deliverable) ──


async def test_air_conditioning_setpoint_end_to_end(chain: Chain) -> None:
    decision, result = await run_chain(chain, recommendation(AC[0], AC[1], 23))
    assert decision.decision is PolicyOutcome.ALLOW
    assert result.status is ActionStatus.SUCCEEDED
    assert await chain.gateway.read(AC[0], AC[1]) == 23


async def test_lighting_end_to_end(chain: Chain) -> None:
    rec = recommendation(LIGHT[0], LIGHT[1], True, recommendation_type="lighting.routine")
    decision, result = await run_chain(chain, rec)
    assert decision.decision is PolicyOutcome.ALLOW
    assert result.status is ActionStatus.SUCCEEDED
    assert await chain.gateway.read(LIGHT[0], LIGHT[1]) is True


async def test_curtain_end_to_end(chain: Chain) -> None:
    rec = recommendation(CURTAIN[0], CURTAIN[1], 40.0, recommendation_type="cover.privacy")
    decision, result = await run_chain(chain, rec)
    assert decision.decision is PolicyOutcome.ALLOW
    assert result.status is ActionStatus.SUCCEEDED
    assert await chain.gateway.read(CURTAIN[0], CURTAIN[1]) == 40.0


# ── acceptance criteria over the whole chain ──


@pytest.mark.safety
async def test_no_action_without_a_valid_policy_decision(chain: Chain) -> None:
    denied = recommendation(AC[0], AC[1], 23, confidence=0.05)
    decision, result = await run_chain(chain, denied)
    assert decision.decision is PolicyOutcome.DENY
    assert result is None
    assert chain.gateway.commands == []
    # The device is untouched.
    assert await chain.gateway.read(AC[0], AC[1]) == 24.0


@pytest.mark.safety
async def test_duplicate_requests_produce_one_device_command(chain: Chain) -> None:
    rec = recommendation(AC[0], AC[1], 23)
    current = await chain.gateway.read(AC[0], AC[1])
    decision = chain.policy.evaluate(rec, now=NOW, twin_value=current, twin_status="KNOWN")
    request = build_action_request(decision, rec, NOW, previous_value=current)

    first = await chain.orchestrator.execute(request, now=NOW)
    second = await chain.orchestrator.execute(request, now=NOW)
    assert first.status is ActionStatus.SUCCEEDED
    assert second.action_id == first.action_id
    assert len(chain.gateway.commands) == 1


@pytest.mark.safety
async def test_manual_override_stops_the_chain(chain: Chain) -> None:
    # Safety invariant 5 across the whole pipeline: a person adjusted the AC a
    # moment ago, so the adaptive proposal must not override them.
    chain.policy.record_manual_change(HOME, AC[0], AC[1], NOW - timedelta(minutes=1))
    decision, result = await run_chain(chain, recommendation(AC[0], AC[1], 23))
    assert decision.decision is PolicyOutcome.DENY
    assert "USER_CONTROL_TAKES_PRECEDENCE" in decision.reason_codes
    assert result is None
    assert chain.gateway.commands == []


@pytest.mark.safety
async def test_an_expired_recommendation_never_reaches_a_device(
    chain: Chain,
) -> None:
    decision, _result = await run_chain(
        chain, recommendation(AC[0], AC[1], 23), now=NOW + timedelta(hours=1)
    )
    assert decision.decision is PolicyOutcome.DENY
    assert chain.gateway.commands == []


@pytest.mark.safety
async def test_result_verification_reflects_the_real_device(chain: Chain) -> None:
    _, result = await run_chain(chain, recommendation(AC[0], AC[1], 23))
    # Verified against the simulator's own reported state, not our intent.
    assert result.observed_value == 23
    assert result.attempts[-1].verified


# ── approval flow ──


@pytest.mark.safety
async def test_an_untrusted_home_requires_approval_before_acting(
    chain: Chain,
) -> None:
    chain.policy.set_policy(HOME, HomePolicy())  # default: not yet trusted
    rec = recommendation(AC[0], AC[1], 23)
    current = await chain.gateway.read(AC[0], AC[1])
    pending = chain.policy.evaluate(rec, now=NOW, twin_value=current, twin_status="KNOWN")
    assert pending.decision is PolicyOutcome.REQUIRE_USER_APPROVAL

    # Nothing may execute on the pending decision itself.
    blocked = build_action_request(pending, rec, NOW, previous_value=current)
    refused = await chain.orchestrator.execute(blocked, now=NOW)
    assert refused.status is ActionStatus.FAILED
    assert chain.gateway.commands == []

    # After a human approves, a fresh decision authorizes execution.
    approved = chain.policy.approve(pending.decision_id, actor="occupant", now=NOW)
    request = build_action_request(approved, rec, NOW, previous_value=current)
    result = await chain.orchestrator.execute(request, now=NOW)
    assert result.status is ActionStatus.SUCCEEDED
    assert await chain.gateway.read(AC[0], AC[1]) == 23


# ── feedback closes the loop ──


async def test_feedback_from_the_household_lowers_standing(chain: Chain) -> None:
    rec = recommendation(AC[0], AC[1], 23)
    chain.feedback.register_recommendation(rec)
    _, result = await run_chain(chain, rec)
    assert result.status is ActionStatus.SUCCEEDED

    chain.feedback.record(
        HOME, rec.recommendation_id, FeedbackKind.UNDO, action_id=result.action_id, now=NOW
    )
    assert chain.feedback.adjustment_for(HOME, "climate.precondition") < 1.0


@pytest.mark.safety
async def test_our_own_write_does_not_become_household_feedback(
    chain: Chain,
) -> None:
    # Spec §14.8 loop-breaker, end to end: the simulator reports the value we
    # just wrote, and that echo must not be read as the household agreeing.
    rec = recommendation(AC[0], AC[1], 23)
    chain.feedback.register_recommendation(rec)
    _, _result = await run_chain(chain, rec)
    chain.feedback.note_automation_write(HOME, AC[0], AC[1], NOW)

    source = chain.feedback.classify_state_change(HOME, AC[0], AC[1], NOW + timedelta(seconds=2))
    assert source is FeedbackSource.AUTOMATION_ECHO

    before = chain.feedback.adjustment_for(HOME, "climate.precondition")
    chain.feedback.record(HOME, rec.recommendation_id, FeedbackKind.ACCEPT, source=source, now=NOW)
    assert chain.feedback.adjustment_for(HOME, "climate.precondition") == before


async def test_never_repeat_feeds_back_into_policy(chain: Chain) -> None:
    # The household's refusal must actually stop future proposals.
    rec = recommendation(AC[0], AC[1], 23)
    chain.feedback.register_recommendation(rec)
    chain.feedback.record(HOME, rec.recommendation_id, FeedbackKind.NEVER_REPEAT, now=NOW)
    for suppressed in chain.feedback.suppressed_types(HOME):
        chain.policy.suppress(HOME, suppressed)

    decision, result = await run_chain(chain, recommendation(AC[0], AC[1], 22))
    assert decision.decision is PolicyOutcome.DENY
    assert "SUPPRESSED_BY_USER" in decision.reason_codes
    assert result is None


# ── audit across the chain ──


@pytest.mark.safety
async def test_the_chain_leaves_a_complete_audit_trail(chain: Chain) -> None:
    # Safety invariant 12: every sensitive action is traceable end to end.
    rec = recommendation(AC[0], AC[1], 23)
    chain.feedback.register_recommendation(rec)
    decision, result = await run_chain(chain, rec)
    chain.feedback.record(HOME, rec.recommendation_id, FeedbackKind.ACCEPT, now=NOW)

    assert any(e["action"] == "POLICY_DECISION_CREATED" for e in chain.policy.audit)
    assert any(e.action == "ACTION_SUCCEEDED" for e in chain.orchestrator.audit)
    assert any(e["action"] == "FEEDBACK_RECORDED" for e in chain.feedback.audit)
    # The correlation id threads recommendation → decision → action.
    assert result.correlation_id == rec.recommendation_id
    assert decision.recommendation_id == rec.recommendation_id
    assert result.decision_id == decision.decision_id
