"""Relational model for spec §13.

Data rules enforced here (spec §13.1):

- UUID primary keys for domain objects;
- database constraints for valid values and state transitions;
- unique constraints supporting idempotency (one row per event id);
- immutable events kept append-only (no update path in code, enforced by a
  trigger in the migration);
- current state kept separate from event history;
- actor, reason and source recorded for sensitive changes (audit_events).

Phase 8 completes the model: contexts, recommendations, policy decisions,
actions, feedback and risk cases. Decisions, actions and risk cases are
append-only in the same way `device_events` is — a record of what the platform
decided is only worth having if it cannot be quietly rewritten.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Home(Base):
    __tablename__ = "homes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    home_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    rooms: Mapped[list["Room"]] = relationship(back_populates="home")
    devices: Mapped[list["Device"]] = relationship(back_populates="home")


class Hub(Base):
    __tablename__ = "hubs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    hub_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    home_uuid: Mapped[UUID] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"))
    software_version: Mapped[str | None] = mapped_column(String(64))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (UniqueConstraint("home_uuid", "room_id", name="uq_rooms_home_room"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    home_uuid: Mapped[UUID] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"))
    room_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str | None] = mapped_column(String(200))

    home: Mapped[Home] = relationship(back_populates="rooms")


class RoomRelationship(Base):
    """Room adjacency, used by the Context Engine for movement inference."""

    __tablename__ = "room_relationships"
    __table_args__ = (
        UniqueConstraint("from_room_uuid", "to_room_uuid", "relationship_type",
                         name="uq_room_relationship"),
        CheckConstraint("from_room_uuid <> to_room_uuid", name="ck_room_relationship_not_self"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    from_room_uuid: Mapped[UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    to_room_uuid: Mapped[UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    relationship_type: Mapped[str] = mapped_column(String(32), default="ADJACENT")


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (UniqueConstraint("home_uuid", "device_id", name="uq_devices_home_device"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    home_uuid: Mapped[UUID] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"))
    device_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    manufacturer: Mapped[str | None] = mapped_column(String(200))
    model: Mapped[str | None] = mapped_column(String(200))
    room_uuid: Mapped[UUID | None] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"))
    available: Mapped[bool | None] = mapped_column(Boolean)
    """NULL means unknown — deliberately distinct from FALSE (offline)."""
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    home: Mapped[Home] = relationship(back_populates="devices")
    entities: Mapped[list["DeviceEntity"]] = relationship(back_populates="device")


class DeviceEntity(Base):
    """A vendor-facing entity belonging to a device (HA entity, etc.)."""

    __tablename__ = "device_entities"
    __table_args__ = (
        UniqueConstraint("device_uuid", "entity_id", name="uq_device_entities_device_entity"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    device_uuid: Mapped[UUID] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    entity_id: Mapped[str] = mapped_column(String(256), index=True)
    integration: Mapped[str] = mapped_column(String(64), default="home_assistant")

    device: Mapped[Device] = relationship(back_populates="entities")


class DeviceCapability(Base):
    """Which canonical capabilities a device exposes."""

    __tablename__ = "device_capabilities"
    __table_args__ = (
        UniqueConstraint("device_uuid", "capability", name="uq_device_capabilities"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    device_uuid: Mapped[UUID] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    capability: Mapped[str] = mapped_column(String(64), index=True)
    safety_class: Mapped[str] = mapped_column(String(32))


class DeviceVendorMapping(Base):
    """How a canonical capability maps onto a vendor entity and service."""

    __tablename__ = "device_vendor_mappings"
    __table_args__ = (
        UniqueConstraint("device_uuid", "capability", "integration", name="uq_vendor_mapping"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    device_uuid: Mapped[UUID] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    capability: Mapped[str] = mapped_column(String(64))
    integration: Mapped[str] = mapped_column(String(64), default="home_assistant")
    entity_id: Mapped[str | None] = mapped_column(String(256))
    service_domain: Mapped[str | None] = mapped_column(String(64))
    service_name: Mapped[str | None] = mapped_column(String(64))


class DeviceCurrentState(Base):
    """Current value per device capability — separate from event history."""

    __tablename__ = "device_current_states"
    __table_args__ = (
        UniqueConstraint("device_uuid", "capability", name="uq_current_state"),
        CheckConstraint("quality >= 0 AND quality <= 1", name="ck_current_state_quality"),
        CheckConstraint(
            "status IN ('UNKNOWN', 'KNOWN', 'STALE')", name="ck_current_state_status"
        ),
        Index("ix_current_states_capability", "capability"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    home_uuid: Mapped[UUID] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"))
    device_uuid: Mapped[UUID] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    capability: Mapped[str] = mapped_column(String(64))
    value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    """Stored as JSONB so booleans, numbers and enums share one column."""
    unit: Mapped[str | None] = mapped_column(String(16))
    quality: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_event_id: Mapped[UUID | None] = mapped_column()


class DeviceEvent(Base):
    """Append-only normalized event history (spec §13.1).

    The unique constraint on ``event_id`` is the persistence-level idempotency
    guard: a redelivered event cannot be stored — or applied — twice.
    """

    __tablename__ = "device_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_device_events_event_id"),
        CheckConstraint("quality >= 0 AND quality <= 1", name="ck_device_events_quality"),
        Index("ix_device_events_home_occurred", "home_id", "occurred_at"),
        Index("ix_device_events_device_capability", "device_id", "capability"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[str] = mapped_column(String(16))
    home_id: Mapped[str] = mapped_column(String(64), index=True)
    device_id: Mapped[str | None] = mapped_column(String(128))
    entity_id: Mapped[str | None] = mapped_column(String(256))
    room_id: Mapped[str | None] = mapped_column(String(64))
    capability: Mapped[str | None] = mapped_column(String(64))
    value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    unit: Mapped[str | None] = mapped_column(String(16))
    quality: Mapped[float] = mapped_column(Float, default=1.0)
    privacy_class: Mapped[str] = mapped_column(String(32), default="HOUSEHOLD_PRIVATE")
    correlation_id: Mapped[UUID | None] = mapped_column()
    causation_id: Mapped[UUID | None] = mapped_column()
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class AuditEvent(Base):
    """Immutable audit trail (spec §25.5): actor, reason and source recorded."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_home_occurred", "home_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    home_id: Mapped[str | None] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    category: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(128))
    actor: Mapped[str] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(64))
    reason_code: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    correlation_id: Mapped[UUID | None] = mapped_column()


class SystemHealthEvent(Base):
    __tablename__ = "system_health_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    hub_id: Mapped[str] = mapped_column(String(64), index=True)
    service: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class TwinCheckpoint(Base):
    """Where the twin's durable consumer has reached, for rebuild and resume."""

    __tablename__ = "twin_checkpoints"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    home_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    stream_sequence: Mapped[int] = mapped_column(Integer, default=0)
    events_applied: Mapped[int] = mapped_column(Integer, default=0)
    fingerprint: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ── Phase 8: the remaining spec §13 tables ──
#
# These carry the decisions and actions a household can be asked to trust, so
# they are append-only in the same way `device_events` is: the migration adds
# the same mutation-refusing trigger. A record of what the platform decided is
# only worth having if it cannot be quietly rewritten (safety invariant 12).


class ContextRecordRow(Base):
    __tablename__ = "contexts"
    __table_args__ = (
        Index("ix_contexts_home_type", "home_id", "context_type"),
        Index("ix_contexts_home_started", "home_id", "started_at"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_contexts_confidence"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    context_id: Mapped[UUID] = mapped_column(index=True)
    home_id: Mapped[str] = mapped_column(String(64), index=True)
    context_type: Mapped[str] = mapped_column(String(64))
    scope: Mapped[str] = mapped_column(String(128))
    confidence: Mapped[float] = mapped_column(Float)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    producer: Mapped[str] = mapped_column(String(128))
    reason_codes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    context_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ContextEvidenceRow(Base):
    __tablename__ = "context_evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    context_id: Mapped[UUID] = mapped_column(index=True)
    capability: Mapped[str] = mapped_column(String(64))
    device_id: Mapped[str | None] = mapped_column(String(128))
    room_id: Mapped[str | None] = mapped_column(String(64))
    value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)


class RecommendationRow(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint("recommendation_id", name="uq_recommendations_id"),
        Index("ix_recommendations_home_created", "home_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    recommendation_id: Mapped[UUID] = mapped_column(index=True)
    home_id: Mapped[str] = mapped_column(String(64), index=True)
    recommendation_type: Mapped[str] = mapped_column(String(64))
    device_id: Mapped[str] = mapped_column(String(128))
    capability: Mapped[str] = mapped_column(String(64))
    proposed_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    confidence: Mapped[float] = mapped_column(Float)
    reason_codes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    model_name: Mapped[str] = mapped_column(String(128))
    model_version: Mapped[str] = mapped_column(String(32))
    required_policy: Mapped[str] = mapped_column(String(64))
    requires_user_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    shadow: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PolicyDecisionRow(Base):
    """Append-only. Every decision, including every denial (spec §14.6)."""

    __tablename__ = "policy_decisions"
    __table_args__ = (
        UniqueConstraint("decision_id", name="uq_policy_decisions_id"),
        Index("ix_policy_decisions_home_evaluated", "home_id", "evaluated_at"),
        CheckConstraint(
            "decision IN ('ALLOW','DENY','REQUIRE_USER_APPROVAL','PREPARE_ONLY',"
            "'ESCALATE_TO_FIXED_SAFETY_RULE')",
            name="ck_policy_decision_outcome",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    decision_id: Mapped[UUID] = mapped_column(index=True)
    recommendation_id: Mapped[UUID | None] = mapped_column()
    home_id: Mapped[str] = mapped_column(String(64), index=True)
    decision: Mapped[str] = mapped_column(String(40))
    safety_class: Mapped[str] = mapped_column(String(32))
    policy_version: Mapped[str] = mapped_column(String(16))
    input_hash: Mapped[str] = mapped_column(String(64))
    reason_codes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ActionRequestRow(Base):
    __tablename__ = "action_requests"
    __table_args__ = (
        # The persistence-level idempotency guard: the same intent cannot be
        # recorded twice, so a redelivered request cannot become two actions.
        UniqueConstraint("idempotency_key", name="uq_action_requests_idempotency"),
        Index("ix_action_requests_home_created", "home_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    action_id: Mapped[UUID] = mapped_column(index=True)
    idempotency_key: Mapped[str] = mapped_column(String(256))
    decision_id: Mapped[UUID] = mapped_column(index=True)
    home_id: Mapped[str] = mapped_column(String(64), index=True)
    correlation_id: Mapped[UUID] = mapped_column()
    device_id: Mapped[str] = mapped_column(String(128))
    capability: Mapped[str] = mapped_column(String(64))
    value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    previous_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    safety_class: Mapped[str] = mapped_column(String(32))
    origin: Mapped[str] = mapped_column(String(32), default="adaptive")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ActionAttemptRow(Base):
    __tablename__ = "action_attempts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    action_id: Mapped[UUID] = mapped_column(index=True)
    attempt: Mapped[int] = mapped_column(Integer)
    dispatched: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_kind: Mapped[str | None] = mapped_column(String(16))
    reason: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ActionResultRow(Base):
    __tablename__ = "action_results"
    __table_args__ = (
        UniqueConstraint("action_id", name="uq_action_results_action"),
        Index("ix_action_results_home_completed", "home_id", "completed_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    action_id: Mapped[UUID] = mapped_column(index=True)
    idempotency_key: Mapped[str] = mapped_column(String(256))
    decision_id: Mapped[UUID] = mapped_column()
    home_id: Mapped[str] = mapped_column(String(64), index=True)
    correlation_id: Mapped[UUID] = mapped_column()
    status: Mapped[str] = mapped_column(String(24))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    observed_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    compensated: Mapped[bool] = mapped_column(Boolean, default=False)
    reason_codes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ManualOverrideRow(Base):
    __tablename__ = "manual_overrides"
    __table_args__ = (Index("ix_manual_overrides_home_at", "home_id", "occurred_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    home_id: Mapped[str] = mapped_column(String(64), index=True)
    device_id: Mapped[str] = mapped_column(String(128))
    capability: Mapped[str] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cancelled_action_id: Mapped[UUID | None] = mapped_column()


class UserFeedbackRow(Base):
    __tablename__ = "user_feedback"
    __table_args__ = (
        UniqueConstraint("feedback_id", name="uq_user_feedback_id"),
        Index("ix_user_feedback_home_recorded", "home_id", "recorded_at"),
        CheckConstraint(
            "kind IN ('ACCEPT','REJECT','NOT_NOW','MODIFY','UNDO','NEVER_REPEAT')",
            name="ck_user_feedback_kind",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    feedback_id: Mapped[UUID] = mapped_column(index=True)
    home_id: Mapped[str] = mapped_column(String(64), index=True)
    recommendation_id: Mapped[UUID] = mapped_column(index=True)
    action_id: Mapped[UUID | None] = mapped_column()
    kind: Mapped[str] = mapped_column(String(24))
    source: Mapped[str] = mapped_column(String(24), default="USER")
    actor: Mapped[str] = mapped_column(String(128))
    modified_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RiskCaseRow(Base):
    __tablename__ = "risk_cases"
    __table_args__ = (
        UniqueConstraint("case_id", name="uq_risk_cases_id"),
        Index("ix_risk_cases_home_state", "home_id", "state"),
        CheckConstraint(
            "state IN ('NORMAL','WATCH','PRE_ALERT','CONFIRMED','ACTION_IN_PROGRESS',"
            "'RECOVERY','CLOSED')",
            name="ck_risk_case_state",
        ),
        # A confirmed case must name the deterministic rule that confirmed it —
        # the same requirement the contract enforces, restated in the database
        # so a bad write cannot create an unattributed confirmation.
        CheckConstraint(
            "state NOT IN ('CONFIRMED','ACTION_IN_PROGRESS') OR confirmed_by IS NOT NULL",
            name="ck_risk_case_confirmed_by",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(index=True)
    home_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Float)
    room_id: Mapped[str | None] = mapped_column(String(64))
    producer: Mapped[str] = mapped_column(String(128))
    confirmed_by: Mapped[str | None] = mapped_column(String(128))
    reason_codes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RiskEvidenceRow(Base):
    __tablename__ = "risk_evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(index=True)
    origin: Mapped[str] = mapped_column(String(32))
    capability: Mapped[str] = mapped_column(String(64))
    device_id: Mapped[str | None] = mapped_column(String(128))
    room_id: Mapped[str | None] = mapped_column(String(64))
    value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
