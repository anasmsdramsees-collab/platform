"""Dead-letter record contract (spec §11.3): invalid events carry reason codes."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeadLetterRecord(BaseModel):
    """An event that could not be processed, preserved for diagnosis."""

    model_config = ConfigDict(extra="allow", frozen=True)

    deadletter_id: UUID
    service: str
    occurred_at: datetime
    reason_codes: list[str] = Field(min_length=1)
    error: str
    original_subject: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def _timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            msg = "timestamps must be timezone-aware (UTC storage, spec §7.4)"
            raise ValueError(msg)
        return v
