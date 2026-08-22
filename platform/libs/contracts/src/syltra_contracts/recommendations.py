"""Recommendation contract (spec §15).

The single most important property of this type: **a recommendation is not a
command** (safety invariant 1). It names a target and a proposed value, but it
carries no dispatch mechanism and no authority. Turning one into an action
requires a `PolicyDecision` (Phase 5) and then an `ActionRequest` — three
distinct types, so no code path can shortcut from a model output to an actuator.

A recommendation also always expires. A stale recommendation cannot execute
(safety invariant 3), and the only way to guarantee that is for staleness to be
part of the recommendation itself rather than a check someone might forget.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from syltra_contracts.capability_definitions import CAPABILITY_DEFINITIONS


class RecommendationTarget(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    device_id: str
    capability: str
    room_id: str | None = None

    @field_validator("capability")
    @classmethod
    def _known_capability(cls, v: str) -> str:
        if v not in CAPABILITY_DEFINITIONS:
            msg = f"unknown capability {v!r}; recommendations address the canonical model only"
            raise ValueError(msg)
        return v


class ModelReference(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    name: str
    version: str


class Recommendation(BaseModel):
    """An advisory proposal produced by the Adaptive Engine (spec §15)."""

    model_config = ConfigDict(extra="allow", frozen=True)

    recommendation_id: UUID
    home_id: str
    recommendation_type: str
    created_at: datetime
    expires_at: datetime
    target: RecommendationTarget
    proposed_value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    reason_codes: list[str] = Field(min_length=1)
    evidence_event_ids: list[UUID] = Field(default_factory=list)
    model: ModelReference
    required_policy: str
    requires_user_approval: bool = True
    """Defaults to True: a recommendation is untrusted until policy says otherwise."""
    shadow: bool = False
    """True while the producing model is in SHADOW mode — recorded, never shown."""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("created_at", "expires_at")
    @classmethod
    def _timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            msg = "recommendation timestamps must be timezone-aware (UTC storage)"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def _must_expire_after_creation(self) -> "Recommendation":
        if self.expires_at <= self.created_at:
            msg = "a recommendation must expire after it is created"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _value_within_capability_domain(self) -> "Recommendation":
        # A model must not be able to propose a value the capability does not
        # accept — an out-of-range setpoint should fail here, long before it
        # reaches policy or a device.
        definition = CAPABILITY_DEFINITIONS[self.target.capability]
        if not definition.is_within_range(self.proposed_value):
            msg = (
                f"proposed value {self.proposed_value!r} is outside the declared domain "
                f"of {self.target.capability}"
            )
            raise ValueError(msg)
        return self

    def is_expired_at(self, now: datetime) -> bool:
        return now >= self.expires_at

    def is_actionable_at(self, now: datetime) -> bool:
        """Never a substitute for a policy decision.

        This only reports whether the recommendation is still live and out of
        shadow mode. Execution additionally requires an approved policy
        decision, a known target mapping and an audit record (spec §14.7).
        """
        return not self.shadow and not self.is_expired_at(now)
