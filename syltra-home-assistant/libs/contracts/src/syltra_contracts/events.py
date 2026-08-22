"""Base event envelope (spec §11).

Every event on the SYLTRA bus uses this envelope. Contract rules enforced
here (spec §11.3):

- immutable UUID identifiers;
- incompatible schema versions are rejected;
- unknown optional fields are preserved during relay (``extra="allow"``);
- timestamps are timezone-aware (stored as UTC; original offset may travel
  in ``metadata``).

JSON Schema documents generated from these models land in
``contracts/jsonschema/`` in Phase 2 alongside per-event payload schemas.
"""

from datetime import datetime
from typing import Any, Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from syltra_contracts.enums import PrivacyClass

SCHEMA_VERSION: Final[str] = "1.0"

# Required event types (spec §11.2).
EVENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        "device.discovered",
        "device.removed",
        "device.availability.changed",
        "device.state.changed",
        "twin.state.updated",
        "context.updated",
        "routine.discovered",
        "preference.updated",
        "recommendation.created",
        "recommendation.expired",
        "policy.decision.created",
        "risk.state.changed",
        "action.requested",
        "action.dispatched",
        "action.succeeded",
        "action.failed",
        "action.cancelled",
        "manual.override.detected",
        "feedback.recorded",
        "model.trained",
        "model.activated",
        "model.rolled_back",
        "system.health.changed",
    }
)


class EventSource(BaseModel):
    """Producing service, hub instance, and transport protocol."""

    model_config = ConfigDict(extra="allow", frozen=True)

    service: str
    instance_id: str
    protocol: str


class EventSubject(BaseModel):
    """What the event is about. Fields are optional because not every event
    concerns a device (e.g. system.health.changed)."""

    model_config = ConfigDict(extra="allow", frozen=True)

    device_id: str | None = None
    entity_id: str | None = None
    room_id: str | None = None


class EventEnvelope(BaseModel):
    """Immutable envelope shared by all SYLTRA events (spec §11.1)."""

    model_config = ConfigDict(extra="allow", frozen=True)

    event_id: UUID
    event_type: str
    schema_version: str
    occurred_at: datetime
    received_at: datetime
    home_id: str
    correlation_id: UUID
    causation_id: UUID | None = None
    source: EventSource
    subject: EventSubject = EventSubject()
    capability: str | None = None
    value: Any = None
    unit: str | None = None
    quality: float = Field(default=1.0, ge=0.0, le=1.0)
    privacy_class: PrivacyClass = PrivacyClass.HOUSEHOLD_PRIVATE
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type")
    @classmethod
    def _known_event_type(cls, v: str) -> str:
        if v not in EVENT_TYPES:
            msg = f"unknown event_type {v!r}; contract types are fixed in spec §11.2"
            raise ValueError(msg)
        return v

    @field_validator("schema_version")
    @classmethod
    def _compatible_schema_version(cls, v: str) -> str:
        major = v.split(".", 1)[0]
        if major != SCHEMA_VERSION.split(".", 1)[0]:
            msg = f"incompatible schema_version {v!r}; this build speaks {SCHEMA_VERSION}"
            raise ValueError(msg)
        return v

    @field_validator("occurred_at", "received_at")
    @classmethod
    def _timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            msg = "timestamps must be timezone-aware (UTC storage, spec §7.4)"
            raise ValueError(msg)
        return v
