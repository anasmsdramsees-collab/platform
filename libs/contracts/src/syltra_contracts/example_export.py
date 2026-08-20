"""Worked contract examples (spec §8: `contracts/examples/`).

The JSON Schemas say what a document *may* contain. They do not show what one
actually looks like, and a schema alone leaves an integrator guessing at how the
documents relate — which id appears in which other record, what a reason code
reads like, how a decision references the recommendation it decided on.

So these are not twenty unrelated blobs. They are one evening in one synthetic
home, told once through every contract it touches:

    a motion reading arrives  → a context opens
    the model proposes 23 °C  → policy allows it
    the action is dispatched  → the device confirms
    the resident says "yes"   → feedback records it

Every id is shared across the documents that reference it, so following
`recommendation_id` from the recommendation to the decision to the feedback
record works the way it would on a running hub.

They are generated from the same models the runtime validates with, and a test
re-validates each one and fails the build if the checked-in copies drift. An
example that a schema change silently invalidated is worse than no example.

The home is invented (spec §0 rule 15: synthetic data only in development). The
reason codes are not: every one is a code some service really emits and the
gateway can translate, checked by the same test that guards the live API.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from syltra_contracts.actions import ActionRequest, ActionResult, ActionTarget, ExpectedState
from syltra_contracts.contexts import ContextRecord, ContextType, EvidenceItem
from syltra_contracts.deadletter import DeadLetterRecord
from syltra_contracts.enums import PolicyOutcome, RiskCategory, RiskState, SafetyClass
from syltra_contracts.events import SCHEMA_VERSION, EventEnvelope, EventSource
from syltra_contracts.feedback import FeedbackKind, FeedbackRecord, FeedbackSource
from syltra_contracts.gateway import (
    CapabilityCommand,
    DeviceInfo,
    EntityInfo,
    EntityState,
    RegistrySnapshot,
)
from syltra_contracts.models_registry import ModelCard, ModelType, ModelVersion, TrainingWindow
from syltra_contracts.policy import PolicyDecision
from syltra_contracts.recommendations import ModelReference, Recommendation, RecommendationTarget
from syltra_contracts.risk import EvidenceOrigin, RiskCase, RiskEvidenceItem, RiskSeverity

# One evening, fixed so the files regenerate byte-identically.
EVENING = datetime(2026, 8, 20, 19, 30, tzinfo=UTC)
HOME = "home_example"

# Shared identifiers. The point of the examples is that these repeat.
EVENT_ID = UUID("11111111-1111-4111-8111-111111111111")
CORRELATION_ID = UUID("22222222-2222-4222-8222-222222222222")
CONTEXT_ID = UUID("33333333-3333-4333-8333-333333333333")
RECOMMENDATION_ID = UUID("44444444-4444-4444-8444-444444444444")
DECISION_ID = UUID("55555555-5555-4555-8555-555555555555")
ACTION_ID = UUID("66666666-6666-4666-8666-666666666666")
FEEDBACK_ID = UUID("77777777-7777-4777-8777-777777777777")
MODEL_ID = UUID("88888888-8888-4888-8888-888888888888")
CASE_ID = UUID("99999999-9999-4999-8999-999999999999")
DEADLETTER_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

IDEMPOTENCY_KEY = f"{HOME}:ac_living:climate.target_temperature:{int(EVENING.timestamp())}"

_MOTION = EvidenceItem(
    device_id="motion_living",
    room_id="living_room",
    capability="occupancy.motion",
    value=True,
    observed_at=EVENING - timedelta(seconds=40),
    status="KNOWN",
    event_id=EVENT_ID,
)

_MODEL_CARD = ModelCard(
    summary="Predicts the temperature this household chooses at this hour.",
    intended_use="Proposing a comfort setpoint for review. Advisory only.",
    out_of_scope_use=(
        "Any safety decision, any life-safety actuator, and any home other than "
        "the one it was trained on."
    ),
    training_data="21 days of this home's own thermostat changes. No data leaves the hub.",
    evaluation="Held-out final 5 days; mean absolute error 0.6 °C.",
    limitations=(
        "Cold-starts for the first three weeks and after a household change. "
        "Suspended automatically when drift is detected."
    ),
    ethical_and_safety_notes=(
        "Output is a recommendation, never an action. Policy and the Safety "
        "Governor stand between this model and any device."
    ),
)


def build_examples() -> dict[str, BaseModel]:
    """One instance per contract, all describing the same evening."""
    return {
        "event-envelope": EventEnvelope(
            event_id=EVENT_ID,
            event_type="device.state.changed",
            schema_version=SCHEMA_VERSION,
            occurred_at=EVENING - timedelta(seconds=40),
            received_at=EVENING - timedelta(seconds=39),
            home_id=HOME,
            correlation_id=CORRELATION_ID,
            source=EventSource(
                service="edge-agent", instance_id="hub_example", protocol="home-assistant"
            ),
            device_id="motion_living",
            room_id="living_room",
            capability="occupancy.motion",
            value=True,
        ),
        "context-record": ContextRecord(
            context_id=CONTEXT_ID,
            home_id=HOME,
            context_type=ContextType.ROOM_OCCUPIED,
            scope="room:living_room",
            started_at=EVENING - timedelta(seconds=40),
            last_updated_at=EVENING,
            expires_at=EVENING + timedelta(minutes=5),
            confidence=0.9,
            producer="context-engine",
            evidence=[_MOTION],
            reason_codes=["ROOM_MOTION_DETECTED"],
        ),
        "evidence-item": _MOTION,
        "recommendation": Recommendation(
            recommendation_id=RECOMMENDATION_ID,
            home_id=HOME,
            recommendation_type="climate.precondition",
            created_at=EVENING,
            expires_at=EVENING + timedelta(minutes=15),
            target=RecommendationTarget(
                device_id="ac_living",
                capability="climate.target_temperature",
                room_id="living_room",
            ),
            proposed_value=23.0,
            confidence=0.83,
            reason_codes=["REPEATED_USER_PATTERN"],
            model=ModelReference(name="temperature_preference", version="1.0.0"),
            required_policy="COMFORT_AUTOMATION",
            requires_user_approval=False,
        ),
        "policy-decision": PolicyDecision(
            decision_id=DECISION_ID,
            home_id=HOME,
            decision=PolicyOutcome.ALLOW,
            evaluated_at=EVENING,
            expires_at=EVENING + timedelta(minutes=15),
            reason_codes=["WITHIN_POLICY"],
            safety_class=SafetyClass.COMFORT,
            input_hash="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            recommendation_id=RECOMMENDATION_ID,
        ),
        "action-request": ActionRequest(
            action_id=ACTION_ID,
            idempotency_key=IDEMPOTENCY_KEY,
            decision_id=DECISION_ID,
            home_id=HOME,
            correlation_id=CORRELATION_ID,
            target=ActionTarget(
                device_id="ac_living",
                capability="climate.target_temperature",
                room_id="living_room",
            ),
            value=23.0,
            expected_state=ExpectedState(capability="climate.target_temperature", value=23.0),
            safety_class=SafetyClass.COMFORT,
            created_at=EVENING,
            expires_at=EVENING + timedelta(minutes=2),
            previous_value=26.0,
        ),
        "action-result": ActionResult(
            action_id=ACTION_ID,
            idempotency_key=IDEMPOTENCY_KEY,
            decision_id=DECISION_ID,
            home_id=HOME,
            correlation_id=CORRELATION_ID,
            status="SUCCEEDED",
            completed_at=EVENING + timedelta(seconds=3),
            verified=True,
            observed_value=23.0,
        ),
        "feedback-record": FeedbackRecord(
            feedback_id=FEEDBACK_ID,
            home_id=HOME,
            recommendation_id=RECOMMENDATION_ID,
            kind=FeedbackKind.ACCEPT,
            recorded_at=EVENING + timedelta(seconds=20),
            source=FeedbackSource.USER,
        ),
        "capability-command": CapabilityCommand(
            device_id="ac_living",
            capability="climate.target_temperature",
            value=23.0,
        ),
        "device-info": DeviceInfo(
            device_id="ac_living",
            name="Living room air conditioner",
            manufacturer="Example",
            model="AC-1",
            room_id="living_room",
            entity_ids=["climate.living_room"],
        ),
        "entity-info": EntityInfo(
            entity_id="climate.living_room",
            device_id="ac_living",
            capability="climate.target_temperature",
            room_id="living_room",
        ),
        "entity-state": EntityState(
            entity_id="climate.living_room",
            state="cool",
            attributes={"temperature": 23.0},
            last_updated=EVENING + timedelta(seconds=3),
            available=True,
        ),
        "registry-snapshot": RegistrySnapshot(
            taken_at=EVENING,
            devices=[
                DeviceInfo(
                    device_id="ac_living",
                    name="Living room air conditioner",
                    room_id="living_room",
                    entity_ids=["climate.living_room"],
                )
            ],
            entities=[
                EntityInfo(
                    entity_id="climate.living_room",
                    device_id="ac_living",
                    capability="climate.target_temperature",
                    room_id="living_room",
                )
            ],
            states=[EntityState(entity_id="climate.living_room", state="cool")],
        ),
        "model-version": ModelVersion(
            model_id=MODEL_ID,
            home_id=HOME,
            name="temperature_preference",
            version="1.0.0",
            model_type=ModelType.TEMPERATURE_PREFERENCE,
            feature_schema_version="1.0",
            training_code_revision="0000000000000000000000000000000000000000",
            training_window=TrainingWindow(
                start=EVENING - timedelta(days=21),
                end=EVENING,
                sample_count=177,
                distinct_days=22,
            ),
            evaluation_metrics={"mean_absolute_error_celsius": 0.6},
            created_at=EVENING,
            card=_MODEL_CARD,
        ),
        "model-card": _MODEL_CARD,
        # The two below did not happen on this evening. A quiet house produces
        # no risk case and no dead letter, and an example set that only shows
        # the happy path teaches half the contract.
        "risk-case": RiskCase(
            case_id=CASE_ID,
            home_id=HOME,
            category=RiskCategory.WATER_LEAK,
            state=RiskState.WATCH,
            severity=RiskSeverity.LOW,
            confidence=0.4,
            opened_at=EVENING + timedelta(hours=2),
            last_updated_at=EVENING + timedelta(hours=2),
            evidence=[
                RiskEvidenceItem(
                    origin=EvidenceOrigin.SENSOR_READING,
                    capability="environment.humidity",
                    value=78.0,
                    device_id="humidity_bath",
                    room_id="bathroom",
                    observed_at=EVENING + timedelta(hours=2),
                    status="KNOWN",
                    note="Inference only. WATCH cannot act; only a certified alarm confirms.",
                )
            ],
            reason_codes=["ADVISORY_PENDING_CONFIRMATION"],
            producer="risk-engine",
        ),
        "risk-evidence-item": RiskEvidenceItem(
            origin=EvidenceOrigin.CERTIFIED_ALARM,
            capability="safety.water_leak",
            value=True,
            device_id="leak_kitchen",
            room_id="kitchen",
            observed_at=EVENING + timedelta(hours=2),
            status="KNOWN",
            note="A certified alarm is the only evidence that can confirm a hazard.",
        ),
        "deadletter-record": DeadLetterRecord(
            deadletter_id=DEADLETTER_ID,
            service="edge-agent",
            occurred_at=EVENING + timedelta(minutes=1),
            reason_codes=["UNMAPPED_ENTITY"],
            error="Entity sensor.unmapped_thing maps to no known device or capability.",
            subject="syltra.device.state.changed",
            home_id=HOME,
        ),
    }


def examples_directory(root: Path) -> Path:
    return root / "contracts" / "examples" / f"v{SCHEMA_VERSION}"


def write_examples(root: Path) -> list[Path]:
    """Write every example under ``root``; returns the paths written."""
    target = examples_directory(root)
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, instance in build_examples().items():
        document: dict[str, Any] = instance.model_dump(mode="json")
        path = target / f"{name}.example.json"
        path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def main() -> None:  # pragma: no cover - thin CLI wrapper
    root = Path(__file__).resolve().parents[4]
    for path in write_examples(root):
        print(f"wrote {path.relative_to(root)}")


if __name__ == "__main__":  # pragma: no cover
    main()
