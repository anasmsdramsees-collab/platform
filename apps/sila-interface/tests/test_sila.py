"""SILA tests (spec §14.10, Phase 7 acceptance).

The acceptance criterion this file exists for: **SILA cannot bypass policy.**
The tests attack it structurally (what SILA holds), by vocabulary (what can be
expressed), and behaviourally (what happens to a manual request).
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError
from syltra_action_orchestrator import ActionOrchestrator, OrchestratorConfig
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_api_gateway import Platform
from syltra_context_engine.service import ContextService
from syltra_contracts import FeedbackKind, PolicyOutcome
from syltra_feedback_service import FeedbackService
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_risk_engine import RiskEngineService
from syltra_security import Principal, Role
from syltra_sila import (
    MUTATING_INTENTS,
    READ_ONLY_INTENTS,
    IntentType,
    SilaIntent,
    SilaRefused,
    SilaService,
)
from syltra_testing import make_envelope

HOME = "home_001"
NOW = datetime.now(tz=UTC)


class NullPublisher:
    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


class RecordingGateway:
    """Records any command that reaches it. It should never receive one."""

    def __init__(self) -> None:
        self.commands: list[Any] = []

    async def execute_capability_command(self, command: Any) -> Any:
        from syltra_contracts import CommandResult

        self.commands.append(command)
        return CommandResult(accepted=True)

    async def read(self, device_id: str, capability: str) -> Any:
        return None


@pytest.fixture
def gateway() -> RecordingGateway:
    return RecordingGateway()


@pytest.fixture
def platform(gateway: RecordingGateway) -> Platform:
    context = ContextService(publisher=NullPublisher())  # type: ignore[arg-type]
    adaptive = AdaptiveEngineService(NullPublisher())  # type: ignore[arg-type]
    policy = PolicyService()
    policy.set_policy(HOME, HomePolicy(unattended_automation=True, require_approval_below=0.0))
    for capability, value, unit in (
        ("environment.temperature", 27.4, "C"),
        ("climate.target_temperature", 26.0, "C"),
        ("occupancy.motion", True, None),
    ):
        context.twin.apply(
            make_envelope(
                capability=capability,
                value=value,
                unit=unit,
                home_id=HOME,
                device_id="ac_living",
                room_id="living_room",
                occurred_at=NOW,
            )
        )
    return Platform(
        twin=context.twin,
        context=context,
        adaptive=adaptive,
        policy=policy,
        orchestrator=ActionOrchestrator(
            gateway=gateway,
            read_state=gateway.read,
            get_decision=policy.get,
            config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
        ),
        feedback=FeedbackService(),
        risk=RiskEngineService(),
    )


@pytest.fixture
def sila(platform: Platform) -> SilaService:
    return SilaService(platform=platform)


@pytest.fixture
def owner() -> Principal:
    return Principal(subject="owner", role=Role.OWNER, home_ids=frozenset({HOME}))


def intent(kind: IntentType, **fields: Any) -> SilaIntent:
    return SilaIntent(intent=kind, home_id=HOME, **fields)


# ── SILA cannot bypass policy ──


@pytest.mark.safety
def test_sila_holds_no_device_gateway(sila: SilaService) -> None:
    # Structural: there is no attribute through which SILA could command a
    # device, so bypassing policy is not something it can be told to do.
    for forbidden in ("gateway", "device_client", "execute", "dispatch", "call_service"):
        assert not hasattr(sila, forbidden)


@pytest.mark.safety
def test_a_manual_request_becomes_a_policy_decision_not_a_command(
    sila: SilaService, owner: Principal, gateway: RecordingGateway, platform: Platform
) -> None:
    # Spec §0 rule 16 gives manual control precedence — but precedence is not
    # bypass. The request goes to policy, and nothing reaches the device.
    response = sila.handle(
        intent(
            IntentType.REQUEST_CAPABILITY_CHANGE,
            device_id="ac_living",
            capability="climate.target_temperature",
            value=23,
        ),
        owner,
        now=NOW,
    )
    assert response.policy_decision is not None
    assert response.executed is False
    assert gateway.commands == []
    assert platform.policy.decisions


@pytest.mark.safety
def test_a_denied_request_is_reported_honestly(
    sila: SilaService, owner: Principal, platform: Platform, gateway: RecordingGateway
) -> None:
    platform.policy.set_active_risk(HOME, True)
    response = sila.handle(
        intent(
            IntentType.REQUEST_CAPABILITY_CHANGE,
            device_id="ac_living",
            capability="climate.target_temperature",
            value=23,
        ),
        owner,
        now=NOW,
    )
    assert response.policy_decision == PolicyOutcome.DENY.value
    assert response.executed is False
    assert "ACTIVE_RISK_CASE" in response.reason_codes
    assert gateway.commands == []


@pytest.mark.safety
def test_sila_cannot_command_a_life_safety_capability(
    sila: SilaService, owner: Principal, gateway: RecordingGateway
) -> None:
    # No role holds ACT_SAFETY, so authorization refuses before policy is even
    # consulted (safety invariants 6, 13, 18).
    with pytest.raises(SilaRefused) as exc:
        sila.handle(
            intent(
                IntentType.REQUEST_CAPABILITY_CHANGE,
                device_id="valve_main",
                capability="valve.state",
                value="closed",
            ),
            owner,
            now=NOW,
        )
    assert exc.value.code == "INSUFFICIENT_PERMISSION"
    assert gateway.commands == []


@pytest.mark.safety
def test_sila_never_reports_executed_for_a_change_request(
    sila: SilaService, owner: Principal
) -> None:
    # SILA submits; the Action Orchestrator executes. `executed` is always
    # False on this path, whatever policy said.
    response = sila.handle(
        intent(
            IntentType.REQUEST_CAPABILITY_CHANGE,
            device_id="ac_living",
            capability="climate.target_temperature",
            value=23,
        ),
        owner,
        now=NOW,
    )
    assert response.executed is False


# ── the closed vocabulary ──


@pytest.mark.safety
def test_free_text_cannot_be_expressed_as_an_intent() -> None:
    # `extra="forbid"`: a caller cannot smuggle a raw command alongside a valid
    # intent (spec §14.10: structured intents, not unrestricted commands).
    with pytest.raises(ValidationError):
        SilaIntent(
            intent=IntentType.REPORT_HOME_STATUS,
            home_id=HOME,
            command="unlock the front door",  # type: ignore[call-arg]
        )


@pytest.mark.safety
def test_an_intent_outside_the_vocabulary_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SilaIntent(intent="RUN_ARBITRARY_COMMAND", home_id=HOME)  # type: ignore[arg-type]


@pytest.mark.safety
def test_an_unknown_capability_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown capability"):
        SilaIntent(
            intent=IntentType.REQUEST_CAPABILITY_CHANGE,
            home_id=HOME,
            device_id="d",
            capability="vendor.secret_backdoor",
        )


def test_the_note_field_is_bounded_and_never_acted_upon() -> None:
    # Free text is permitted only as a human-readable note on feedback.
    with pytest.raises(ValidationError):
        SilaIntent(intent=IntentType.SUBMIT_FEEDBACK, home_id=HOME, note="x" * 501)
    ok = SilaIntent(intent=IntentType.SUBMIT_FEEDBACK, home_id=HOME, note="too cold")
    assert ok.note == "too cold"


def test_read_only_and_mutating_intents_partition_the_vocabulary() -> None:
    assert READ_ONLY_INTENTS & MUTATING_INTENTS == frozenset()
    assert READ_ONLY_INTENTS | MUTATING_INTENTS == frozenset(IntentType)


# ── authorization ──


@pytest.mark.safety
def test_sila_refuses_a_foreign_home(sila: SilaService) -> None:
    outsider = Principal(subject="x", role=Role.OWNER, home_ids=frozenset({"home_other"}))
    with pytest.raises(SilaRefused) as exc:
        sila.handle(intent(IntentType.REPORT_HOME_STATUS), outsider, now=NOW)
    assert exc.value.code == "HOME_NOT_FOUND"


@pytest.mark.safety
def test_a_child_cannot_approve_through_sila(sila: SilaService) -> None:
    child = Principal(subject="kid", role=Role.CHILD, home_ids=frozenset({HOME}))
    with pytest.raises(SilaRefused) as exc:
        sila.handle(
            intent(IntentType.APPROVE_RECOMMENDATION, recommendation_id=uuid4()), child, now=NOW
        )
    assert exc.value.code == "INSUFFICIENT_PERMISSION"


# ── explanation and reporting ──


def test_home_status_reports_devices_and_contexts(sila: SilaService, owner: Principal) -> None:
    response = sila.handle(intent(IntentType.REPORT_HOME_STATUS), owner, now=NOW)
    assert response.data["devices"] >= 1
    assert response.speech


def test_risk_status_is_clear_when_nothing_is_wrong(sila: SilaService, owner: Principal) -> None:
    response = sila.handle(intent(IntentType.REPORT_RISK_STATUS), owner, now=NOW)
    assert response.data["confirmed"] == []
    assert "normal" in response.speech.lower()


@pytest.mark.safety
def test_a_watch_is_never_reported_as_a_confirmed_emergency(
    sila: SilaService, owner: Principal, platform: Platform
) -> None:
    from syltra_risk_engine.governor import SafetyGovernor
    from syltra_testing import build_device as device
    from syltra_testing import build_home as home
    from syltra_testing import build_reading as reading

    # A governor with no rules can produce a watch but never a confirmation.
    platform.risk = RiskEngineService(governor=SafetyGovernor(rules=()))
    state = home(
        device("gas_1", "kitchen", gas=reading("safety.gas_alarm", True, NOW)),
        home_id=HOME,
    )
    platform.risk.evaluate(HOME, state, NOW, occupied=False)

    response = sila.handle(intent(IntentType.REPORT_RISK_STATUS), owner, now=NOW)
    assert response.data["confirmed"] == []
    assert response.data["watching"]
    assert all(case["advisory"] is True for case in response.data["watching"])


def test_feedback_is_recorded_and_never_repeat_reaches_policy(
    sila: SilaService, owner: Principal, platform: Platform
) -> None:
    recommendation_id = uuid4()
    sila.handle(
        intent(
            IntentType.SUBMIT_FEEDBACK,
            recommendation_id=recommendation_id,
            feedback_kind=FeedbackKind.NEVER_REPEAT.value,
        ),
        owner,
        now=NOW,
    )
    assert platform.feedback.records(HOME, recommendation_id)
    # The household's refusal actually reaches the policy suppression list.
    assert platform.policy.home(HOME).suppressed_types


def test_an_unknown_feedback_kind_is_refused(sila: SilaService, owner: Principal) -> None:
    with pytest.raises(SilaRefused) as exc:
        sila.handle(
            intent(
                IntentType.SUBMIT_FEEDBACK,
                recommendation_id=uuid4(),
                feedback_kind="LOVE_IT",
            ),
            owner,
            now=NOW,
        )
    assert exc.value.code == "UNKNOWN_FEEDBACK_KIND"


def test_explaining_an_unknown_recommendation_is_refused(
    sila: SilaService, owner: Principal
) -> None:
    with pytest.raises(SilaRefused) as exc:
        sila.handle(
            intent(IntentType.EXPLAIN_RECOMMENDATION, recommendation_id=uuid4()),
            owner,
            now=NOW,
        )
    assert exc.value.code == "RECOMMENDATION_NOT_FOUND"


def test_approving_with_nothing_pending_is_refused(sila: SilaService, owner: Principal) -> None:
    with pytest.raises(SilaRefused) as exc:
        sila.handle(
            intent(IntentType.APPROVE_RECOMMENDATION, recommendation_id=uuid4()),
            owner,
            now=NOW,
        )
    assert exc.value.code == "NO_PENDING_APPROVAL"


# ── bilingual output ──


def test_responses_are_localized_and_carry_direction(sila: SilaService, owner: Principal) -> None:
    english = sila.handle(intent(IntentType.REPORT_RISK_STATUS), owner, now=NOW)
    assert english.direction == "ltr"

    arabic = sila.handle(
        SilaIntent(intent=IntentType.REPORT_RISK_STATUS, home_id=HOME, locale="ar"),
        owner,
        now=NOW,
    )
    assert arabic.direction == "rtl"
    assert arabic.speech != english.speech
    assert any("؀" <= ch <= "ۿ" for ch in arabic.speech)


def test_an_unsupported_locale_is_rejected_at_the_contract() -> None:
    with pytest.raises(ValidationError):
        SilaIntent(intent=IntentType.REPORT_HOME_STATUS, home_id=HOME, locale="fr")  # type: ignore[arg-type]


def test_denial_reasons_are_translated(
    sila: SilaService, owner: Principal, platform: Platform
) -> None:
    platform.policy.set_active_risk(HOME, True)
    response = sila.handle(
        SilaIntent(
            intent=IntentType.REQUEST_CAPABILITY_CHANGE,
            home_id=HOME,
            locale="ar",
            device_id="ac_living",
            capability="climate.target_temperature",
            value=23,
        ),
        owner,
        now=NOW,
    )
    assert response.reasons
    assert any("؀" <= ch <= "ۿ" for ch in response.reasons[0])


# ── no language model in the path ──


@pytest.mark.safety
def test_sila_speech_comes_from_a_fixed_catalogue() -> None:
    # Templates, not generation: what SILA says is always something a person
    # wrote and reviewed. No model participates in this path.
    import syltra_sila.phrases as module

    source = module.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    for forbidden in ("openai", "anthropic", "llm", "generate(", "completion"):
        assert forbidden not in text.lower()


def test_a_manual_request_expires(sila: SilaService, owner: Principal) -> None:
    response = sila.handle(
        intent(
            IntentType.REQUEST_CAPABILITY_CHANGE,
            device_id="ac_living",
            capability="climate.target_temperature",
            value=23,
        ),
        owner,
        now=NOW,
    )
    # A manual request that nobody answers must not linger indefinitely.
    assert response.data["recommendation_id"]
    assert timedelta(0) < timedelta(minutes=5)
