"""Context contracts (spec §14.3).

A context is an inference about the household — "someone is home", "the kitchen
is in use" — and every later service reads contexts rather than re-deriving
them. Because a context can influence an action, it must always carry the
evidence that produced it, a confidence, and an expiry: an inference that
outlives its evidence is worse than no inference at all.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContextType(StrEnum):
    """Initial contexts (spec §14.3). A closed vocabulary."""

    HOME_OCCUPIED = "HOME_OCCUPIED"
    HOME_EMPTY = "HOME_EMPTY"
    ROOM_OCCUPIED = "ROOM_OCCUPIED"
    SLEEPING = "SLEEPING"
    COOKING = "COOKING"
    ARRIVING = "ARRIVING"
    LEAVING = "LEAVING"
    QUIET_HOURS = "QUIET_HOURS"
    CHILD_PRESENT = "CHILD_PRESENT"
    HIGH_ENERGY_USAGE = "HIGH_ENERGY_USAGE"
    POSSIBLE_WATER_LEAK = "POSSIBLE_WATER_LEAK"
    POSSIBLE_GAS_RISK = "POSSIBLE_GAS_RISK"
    DEVICE_CONNECTIVITY_DEGRADED = "DEVICE_CONNECTIVITY_DEGRADED"


ADVISORY_ONLY_CONTEXTS: frozenset[ContextType] = frozenset(
    {ContextType.POSSIBLE_WATER_LEAK, ContextType.POSSIBLE_GAS_RISK}
)
"""Contexts that may raise awareness but can never confirm an emergency.

Safety invariants 6 and 18: confirmed emergency response follows deterministic
approved rules against certified alarm capabilities, never an inferred context.
The Risk Engine (Phase 6) may use these to enter WATCH or PRE_ALERT only.
"""


class EvidenceItem(BaseModel):
    """One observation supporting a context, with its provenance."""

    model_config = ConfigDict(extra="allow", frozen=True)

    device_id: str | None = None
    room_id: str | None = None
    capability: str
    value: Any = None
    observed_at: datetime | None = None
    status: str = "KNOWN"
    """Twin status of the observation: KNOWN, STALE or UNKNOWN."""
    event_id: UUID | None = None
    note: str | None = None

    @property
    def is_usable(self) -> bool:
        return self.status == "KNOWN"


class ContextRecord(BaseModel):
    """An active or expired context (spec §14.3 required fields)."""

    model_config = ConfigDict(extra="allow", frozen=True)

    context_id: UUID
    home_id: str
    context_type: ContextType
    scope: str
    """``home`` or ``room:{room_id}`` — the extent this context applies to."""
    started_at: datetime
    last_updated_at: datetime
    expires_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    producer: str
    """Rule id and version, or model name and version, that produced this."""
    reason_codes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("started_at", "last_updated_at", "expires_at")
    @classmethod
    def _timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            msg = "context timestamps must be timezone-aware (UTC storage)"
            raise ValueError(msg)
        return v

    @field_validator("evidence")
    @classmethod
    def _evidence_required(cls, v: list[EvidenceItem]) -> list[EvidenceItem]:
        # Spec §14.3: every context record must include evidence references.
        # An inference with no traceable basis cannot be explained to a user
        # or audited later, so it is rejected outright.
        if not v:
            msg = "a context must carry at least one evidence item"
            raise ValueError(msg)
        return v

    def is_active_at(self, now: datetime) -> bool:
        return now < self.expires_at

    def is_advisory_only(self) -> bool:
        return self.context_type in ADVISORY_ONLY_CONTEXTS

    @property
    def scope_room_id(self) -> str | None:
        return self.scope.removeprefix("room:") if self.scope.startswith("room:") else None


def home_scope() -> str:
    return "home"


def room_scope(room_id: str) -> str:
    return f"room:{room_id}"
