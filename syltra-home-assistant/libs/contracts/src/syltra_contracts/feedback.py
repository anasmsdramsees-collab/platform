"""Feedback contracts (spec §14.8).

Feedback is how a household teaches the platform, so it must record *which*
recommendation it refers to — otherwise "the user rejected something" is
untraceable and cannot adjust the right preference.

The subtle requirement in spec §14.8 is the last one: *prevent feedback loops
caused by automation-generated state changes*. When SYLTRA sets a thermostat and
the thermostat reports its new value back, that echo must not be mistaken for a
person expressing a preference — or the system would keep reinforcing its own
guesses. `FeedbackRecord.source` carries that distinction.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedbackKind(StrEnum):
    """The responses a household may give (spec §14.8)."""

    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    NOT_NOW = "NOT_NOW"
    MODIFY = "MODIFY"
    UNDO = "UNDO"
    NEVER_REPEAT = "NEVER_REPEAT"


NEGATIVE_FEEDBACK: frozenset[FeedbackKind] = frozenset(
    {FeedbackKind.REJECT, FeedbackKind.UNDO, FeedbackKind.NEVER_REPEAT}
)
"""Responses that should reduce confidence in the producing model (§14.8)."""

SUPPRESSING_FEEDBACK: frozenset[FeedbackKind] = frozenset({FeedbackKind.NEVER_REPEAT})
"""Responses that permanently stop this recommendation type for the home."""


class FeedbackSource(StrEnum):
    USER = "USER"
    """A person acted deliberately — the only kind that teaches preference."""
    AUTOMATION_ECHO = "AUTOMATION_ECHO"
    """A state change SYLTRA itself caused. Never treated as preference."""
    SYSTEM = "SYSTEM"
    """Expiry, timeout or similar; recorded but not preference-bearing."""


class FeedbackRecord(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    feedback_id: UUID
    home_id: str
    recommendation_id: UUID
    action_id: UUID | None = None
    kind: FeedbackKind
    source: FeedbackSource = FeedbackSource.USER
    recorded_at: datetime
    actor: str = "occupant"
    modified_value: Any = None
    """Set when ``kind`` is MODIFY — the value the household actually wanted."""
    note: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("recorded_at")
    @classmethod
    def _timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            msg = "feedback timestamps must be timezone-aware (UTC storage)"
            raise ValueError(msg)
        return v

    @property
    def is_negative(self) -> bool:
        return self.kind in NEGATIVE_FEEDBACK

    @property
    def teaches_preference(self) -> bool:
        """Only deliberate human feedback adjusts what the platform learns.

        This is the loop-breaker: an automation echo is recorded for audit but
        never feeds back into preference evidence.
        """
        return self.source is FeedbackSource.USER
