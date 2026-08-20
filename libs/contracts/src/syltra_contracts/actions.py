"""Action contracts (spec §17, §14.7).

An `ActionRequest` is the only object that can reach a device, and it cannot be
built without a `decision_id`. Spec §14.7 lists what no action may execute
without — an approved policy decision, a non-expired TTL, a known target
mapping, a valid safety class, a correlation ID, and an audit record — and the
first four are enforced by this type rather than by the code that uses it.

The idempotency key is derived, not supplied: the same recommendation acted on
twice produces the same key, so a duplicate request cannot become a second
device command (safety invariant 10).
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from syltra_contracts.capability_definitions import CAPABILITY_DEFINITIONS
from syltra_contracts.enums import SafetyClass


class ActionStatus(StrEnum):
    REQUESTED = "REQUESTED"
    DISPATCHED = "DISPATCHED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class FailureKind(StrEnum):
    """Whether a failure may be retried.

    Retrying a transport timeout is reasonable; retrying a refusal, an unknown
    target, or a policy violation is not — it would just repeat a command the
    system already established it should not send (spec §14.7: retry only safe
    retryable failures).
    """

    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"

    @property
    def retryable(self) -> bool:
        return self is FailureKind.TRANSIENT


class ExpectedState(BaseModel):
    """What the device must report for the action to count as successful."""

    model_config = ConfigDict(frozen=True)

    capability: str
    operator: str = "equals"
    value: Any

    @field_validator("operator")
    @classmethod
    def _known_operator(cls, v: str) -> str:
        allowed = {"equals", "not_equals", "greater_than", "less_than", "within"}
        if v not in allowed:
            msg = f"unknown verification operator {v!r}; expected one of {sorted(allowed)}"
            raise ValueError(msg)
        return v

    def is_satisfied_by(self, observed: Any, tolerance: float = 0.5) -> bool:
        """Whether an observed value meets this expectation.

        Numeric comparisons use a tolerance: a thermostat asked for 23.0 may
        report 22.9, and treating that as a failure would trigger pointless
        retries against a device that did exactly what it was told.
        """
        if observed is None:
            return False
        if self.operator == "equals":
            if isinstance(self.value, int | float) and isinstance(observed, int | float):
                if isinstance(self.value, bool) or isinstance(observed, bool):
                    return bool(observed) == bool(self.value)
                return abs(float(observed) - float(self.value)) <= tolerance
            return bool(observed == self.value)
        if self.operator == "not_equals":
            return bool(observed != self.value)
        if self.operator == "greater_than":
            return float(observed) > float(self.value)
        if self.operator == "less_than":
            return float(observed) < float(self.value)
        if self.operator == "within":
            low, high = self.value
            return float(low) <= float(observed) <= float(high)
        return False


class ActionTarget(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    device_id: str
    capability: str
    room_id: str | None = None

    @field_validator("capability")
    @classmethod
    def _known_capability(cls, v: str) -> str:
        if v not in CAPABILITY_DEFINITIONS:
            msg = f"unknown capability {v!r}; actions address the canonical model only"
            raise ValueError(msg)
        return v


def derive_idempotency_key(
    home_id: str, decision_id: UUID, capability: str, sequence: int = 1
) -> str:
    """Spec §17 format: ``home:decision:action_n``.

    Derived from the decision rather than generated per attempt, so a retried or
    redelivered request reuses the same key and the orchestrator can recognise
    it as the same intent.
    """
    return f"{home_id}:{decision_id}:{capability}:action_{sequence}"


class ActionRequest(BaseModel):
    """An authorized, time-bounded, verifiable device command (spec §17)."""

    model_config = ConfigDict(extra="allow", frozen=True)

    action_id: UUID
    idempotency_key: str
    decision_id: UUID
    """Required: no action exists without an approved policy decision."""
    home_id: str
    correlation_id: UUID
    target: ActionTarget
    value: Any
    expected_state: ExpectedState
    safety_class: SafetyClass
    created_at: datetime
    expires_at: datetime
    timeout_seconds: float = 10.0
    max_attempts: int = Field(default=2, ge=1, le=5)
    reversible: bool = True
    previous_value: Any = None
    """Captured before dispatch so a compensating action is possible."""
    origin: str = "adaptive"
    """``adaptive`` or ``manual`` — manual actions still pass through policy."""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at", "expires_at")
    @classmethod
    def _timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            msg = "action timestamps must be timezone-aware (UTC storage)"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def _expiry_follows_creation(self) -> "ActionRequest":
        if self.expires_at <= self.created_at:
            msg = "an action must expire after it is created"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _value_within_capability_domain(self) -> "ActionRequest":
        definition = CAPABILITY_DEFINITIONS[self.target.capability]
        if not definition.is_within_range(self.value):
            msg = (
                f"action value {self.value!r} is outside the declared domain of "
                f"{self.target.capability}"
            )
            raise ValueError(msg)
        return self

    def is_expired_at(self, now: datetime) -> bool:
        return now >= self.expires_at


class ActionAttempt(BaseModel):
    """One dispatch attempt, recorded whether it succeeded or not."""

    model_config = ConfigDict(extra="allow", frozen=True)

    attempt: int = Field(ge=1)
    started_at: datetime
    finished_at: datetime | None = None
    dispatched: bool = False
    verified: bool = False
    failure_kind: FailureKind | None = None
    reason: str | None = None


class ActionResult(BaseModel):
    """The complete, immutable outcome of an action (spec §14.7)."""

    model_config = ConfigDict(extra="allow", frozen=True)

    action_id: UUID
    idempotency_key: str
    decision_id: UUID
    home_id: str
    correlation_id: UUID
    status: ActionStatus
    attempts: list[ActionAttempt] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    observed_value: Any = None
    compensated: bool = False
    completed_at: datetime
    audit_recorded: bool = True

    @property
    def succeeded(self) -> bool:
        return self.status is ActionStatus.SUCCEEDED

    @property
    def attempt_count(self) -> int:
        return len(self.attempts)
