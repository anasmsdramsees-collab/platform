"""SILA intent vocabulary (spec §14.10).

Spec §14.10 is unusually specific about what SILA is *not*: it receives
"structured intents, not unrestricted commands", and must "never convert an LLM
output directly into an actuator call". Both requirements reduce to one design
decision — **the boundary between SILA and the platform is a closed set of typed
intents, and free text never crosses it.**

Natural-language understanding may be added later behind `IntentParser`. Even
then, its only power is to *select* an intent from this vocabulary and fill its
typed fields. It cannot invent an intent, address a capability outside the
canonical model, or reach a device: an intent that would change something
produces a recommendation for the policy gate, exactly like a model's output.
"""

from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from syltra_contracts.capability_definitions import CAPABILITY_DEFINITIONS

SILA_VERSION = "1.0.0"


class IntentType(StrEnum):
    """The closed vocabulary. Nothing outside this set can be expressed."""

    # Read-only
    REPORT_HOME_STATUS = "REPORT_HOME_STATUS"
    REPORT_RISK_STATUS = "REPORT_RISK_STATUS"
    EXPLAIN_RECOMMENDATION = "EXPLAIN_RECOMMENDATION"
    EXPLAIN_DECISION = "EXPLAIN_DECISION"
    LIST_RECOMMENDATIONS = "LIST_RECOMMENDATIONS"
    # User responses to something the platform proposed
    APPROVE_RECOMMENDATION = "APPROVE_RECOMMENDATION"
    REJECT_RECOMMENDATION = "REJECT_RECOMMENDATION"
    SUBMIT_FEEDBACK = "SUBMIT_FEEDBACK"
    # A deliberate manual request, which still passes through policy
    REQUEST_CAPABILITY_CHANGE = "REQUEST_CAPABILITY_CHANGE"


READ_ONLY_INTENTS: frozenset[IntentType] = frozenset(
    {
        IntentType.REPORT_HOME_STATUS,
        IntentType.REPORT_RISK_STATUS,
        IntentType.EXPLAIN_RECOMMENDATION,
        IntentType.EXPLAIN_DECISION,
        IntentType.LIST_RECOMMENDATIONS,
    }
)

MUTATING_INTENTS: frozenset[IntentType] = frozenset(IntentType) - READ_ONLY_INTENTS


class SilaIntent(BaseModel):
    """A structured request. Deliberately carries no free-text command field."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    # `extra="forbid"` matters: a caller cannot smuggle an unrecognised field
    # (a raw command, a device path, an LLM completion) alongside a valid intent.

    intent: IntentType
    home_id: str
    locale: Literal["en", "ar"] = "en"
    recommendation_id: UUID | None = None
    decision_id: UUID | None = None
    device_id: str | None = None
    capability: str | None = None
    value: Any = None
    feedback_kind: str | None = None
    note: str | None = Field(default=None, max_length=500)
    """Free text is permitted *only* here, and only as a human-readable note
    attached to feedback. It is never parsed, matched, or acted upon."""

    @field_validator("capability")
    @classmethod
    def _known_capability(cls, v: str | None) -> str | None:
        if v is not None and v not in CAPABILITY_DEFINITIONS:
            msg = f"unknown capability {v!r}; SILA addresses the canonical model only"
            raise ValueError(msg)
        return v

    @property
    def is_read_only(self) -> bool:
        return self.intent in READ_ONLY_INTENTS

    @property
    def is_mutating(self) -> bool:
        return self.intent in MUTATING_INTENTS


class SilaResponse(BaseModel):
    """What SILA gives back: an answer, and what it did or did not do."""

    model_config = ConfigDict(extra="allow", frozen=True)

    intent: IntentType
    home_id: str
    locale: str
    direction: Literal["ltr", "rtl"]
    speech: str
    """A sentence suitable for display or synthesis, already localized."""
    data: dict[str, Any] = Field(default_factory=dict)
    reason_codes: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    executed: bool = False
    """True only when something actually changed. A request that produced a
    recommendation awaiting policy is *not* executed."""
    policy_decision: str | None = None

