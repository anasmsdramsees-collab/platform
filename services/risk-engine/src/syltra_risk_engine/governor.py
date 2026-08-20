"""Safety Governor (spec §22 Phase 6, §18).

The only component permitted to declare an emergency real, and the only one
permitted to authorize an emergency response. It is deliberately the simplest
module in the platform: a short list of deterministic rules over certified
alarm capabilities, with no dependency on any model, context inference, or
network service.

That simplicity is the design. Safety invariant 17 requires safety rules to be
testable without ML services running, and invariant 7 requires safety monitoring
to survive the loss of the Adaptive Engine. A governor that consulted a model —
even for a hint — would satisfy neither.

What the governor will not do:

- confirm on inference, however confident (invariants 6, 18);
- confirm on a stale reading (invariant 4);
- confirm on a replayed historical event (invariant 11);
- execute a response itself — it authorizes, and the Action Orchestrator
  executes under the same policy gate as everything else (invariant 2).
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from syltra_contracts import (
    CERTIFIED_ALARM_CAPABILITIES,
    EvidenceOrigin,
    RiskCategory,
    RiskEvidenceItem,
    RiskSeverity,
)
from syltra_digital_twin.core import HomeState, StateStatus

logger = logging.getLogger(__name__)

GOVERNOR_VERSION = "1.0.0"

MAX_EVENT_AGE = timedelta(minutes=5)
"""A reading older than this is history, not a live alarm (invariant 11)."""


@dataclass(frozen=True)
class ConfirmationRule:
    """One deterministic rule: a certified capability and what it means."""

    rule_id: str
    capability: str
    category: RiskCategory
    severity: RiskSeverity
    response: str
    """The approved response this confirmation authorizes, by name."""
    requires_two_sources: bool = False
    """Set where a single reading is not considered sufficient."""

    @property
    def reference(self) -> str:
        return f"rule:{self.rule_id}@{GOVERNOR_VERSION}"


CONFIRMATION_RULES: tuple[ConfirmationRule, ...] = (
    ConfirmationRule(
        rule_id="gas_confirmed",
        capability="safety.gas_alarm",
        category=RiskCategory.GAS,
        severity=RiskSeverity.CRITICAL,
        response="NOTIFY_AND_PREPARE_GAS_ISOLATION",
    ),
    ConfirmationRule(
        rule_id="smoke_confirmed",
        capability="safety.smoke_alarm",
        category=RiskCategory.SMOKE_FIRE,
        severity=RiskSeverity.CRITICAL,
        response="NOTIFY_AND_UNLOCK_EGRESS",
    ),
    ConfirmationRule(
        rule_id="heat_confirmed",
        capability="safety.heat_alarm",
        category=RiskCategory.SMOKE_FIRE,
        severity=RiskSeverity.CRITICAL,
        response="NOTIFY_AND_UNLOCK_EGRESS",
    ),
    ConfirmationRule(
        rule_id="co_confirmed",
        capability="safety.co_alarm",
        category=RiskCategory.CARBON_MONOXIDE,
        severity=RiskSeverity.CRITICAL,
        response="NOTIFY_AND_VENTILATE",
    ),
    ConfirmationRule(
        rule_id="water_leak_confirmed",
        capability="safety.water_leak",
        category=RiskCategory.WATER_LEAK,
        severity=RiskSeverity.HIGH,
        response="NOTIFY_AND_PREPARE_WATER_ISOLATION",
    ),
)


@dataclass(frozen=True)
class Confirmation:
    """A confirmed hazard and the response it authorizes."""

    rule: ConfirmationRule
    category: RiskCategory
    severity: RiskSeverity
    evidence: list[RiskEvidenceItem]
    reason_codes: list[str]
    room_id: str | None
    authorized_response: str
    confirmed_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def confirmed_by(self) -> str:
        return self.rule.reference


@dataclass
class GovernorAudit:
    occurred_at: datetime
    home_id: str
    action: str
    rule: str
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)


class SafetyGovernor:
    """Deterministic confirmation over certified alarm capabilities.

    Constructed with no model, no context engine, and no network client — the
    dependency list is the safety argument.
    """

    def __init__(
        self,
        rules: tuple[ConfirmationRule, ...] = CONFIRMATION_RULES,
        max_event_age: timedelta = MAX_EVENT_AGE,
        environment: str = "development",
    ) -> None:
        self._rules = rules
        self._max_event_age = max_event_age
        self._environment = environment
        self.audit: list[GovernorAudit] = []

    @property
    def version(self) -> str:
        return GOVERNOR_VERSION

    def evaluate(
        self, home_id: str, home: HomeState, now: datetime | None = None
    ) -> list[Confirmation]:
        """Check every certified alarm; confirm only what the rules permit."""
        moment = now or datetime.now(tz=UTC)
        confirmations: list[Confirmation] = []

        for rule in self._rules:
            triggered: list[RiskEvidenceItem] = []
            rejected: list[tuple[str, str]] = []

            for device_id, device in home.devices.items():
                state = device.capabilities.get(rule.capability)
                if state is None:
                    continue
                if state.value is not True:
                    continue

                status = state.status_at(moment)
                if status is not StateStatus.KNOWN:
                    # Safety invariant 4: a stale sensor value cannot confirm.
                    rejected.append((device_id, f"READING_{status.value}"))
                    continue

                if state.occurred_at is None:
                    rejected.append((device_id, "READING_UNDATED"))
                    continue

                age = moment - state.occurred_at
                if age > self._max_event_age:
                    # Safety invariant 11: replayed history cannot trigger live
                    # action. A reading whose freshness window is generous but
                    # whose absolute age is large is a replay, not an alarm.
                    rejected.append((device_id, "HISTORICAL_REPLAY_REJECTED"))
                    continue
                if age < -timedelta(seconds=30):
                    rejected.append((device_id, "READING_FROM_THE_FUTURE"))
                    continue

                triggered.append(
                    RiskEvidenceItem(
                        origin=EvidenceOrigin.CERTIFIED_ALARM,
                        capability=rule.capability,
                        value=True,
                        device_id=device_id,
                        room_id=device.room_id,
                        observed_at=state.occurred_at,
                        status="KNOWN",
                        note=f"certified {rule.capability} active",
                    )
                )

            for device_id, reason in rejected:
                self._audit(
                    home_id, "CONFIRMATION_REJECTED", rule.reference, reason,
                    {"device_id": device_id, "capability": rule.capability},
                )

            if not triggered:
                continue
            if rule.requires_two_sources and len(triggered) < 2:
                self._audit(
                    home_id, "CONFIRMATION_WITHHELD", rule.reference,
                    "rule requires two independent sources",
                    {"sources": len(triggered)},
                )
                continue

            confirmation = Confirmation(
                rule=rule,
                category=rule.category,
                severity=rule.severity,
                evidence=triggered,
                reason_codes=[
                    f"CERTIFIED_{rule.capability.split('.')[1].upper()}_ACTIVE",
                    "DETERMINISTIC_CONFIRMATION",
                ],
                room_id=triggered[0].room_id,
                authorized_response=rule.response,
                confirmed_at=moment,
                metadata={"sources": len(triggered), "environment": self._environment},
            )
            confirmations.append(confirmation)
            self._audit(
                home_id, "HAZARD_CONFIRMED", rule.reference,
                f"{rule.capability} active on {len(triggered)} device(s)",
                {
                    "category": rule.category.value,
                    "severity": rule.severity.value,
                    "authorized_response": rule.response,
                },
            )
            logger.warning(
                "SAFETY: %s confirmed for %s by %s → %s",
                rule.category.value, home_id, rule.reference, rule.response,
            )
        return confirmations

    def authorizes_response(self, confirmation: Confirmation, response: str) -> bool:
        """Whether a proposed response is the one this confirmation authorizes.

        Responses are named and fixed per rule. A confirmed gas alarm does not
        become a licence to operate arbitrary devices.
        """
        return confirmation.authorized_response == response

    def _audit(
        self, home_id: str, action: str, rule: str, reason: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.audit.append(
            GovernorAudit(
                occurred_at=datetime.now(tz=UTC),
                home_id=home_id,
                action=action,
                rule=rule,
                reason=reason,
                detail=detail or {},
            )
        )


def governor_dependencies() -> list[str]:
    """The governor's runtime dependencies, for the safety case.

    Deliberately introspectable: a test asserts this list stays empty of model,
    context and network components, so a future refactor that quietly couples
    the governor to the Adaptive Engine fails the safety suite.
    """
    import syltra_risk_engine.governor as module

    forbidden = {"model", "onnx", "sklearn", "adaptive", "context", "nats", "http"}
    imported = {name.lower() for name in dir(module)}
    return sorted(name for name in imported if any(f in name for f in forbidden))


CallableRule = Callable[[HomeState, datetime], bool]
