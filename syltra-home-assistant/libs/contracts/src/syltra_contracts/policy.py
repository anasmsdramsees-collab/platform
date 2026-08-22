"""Policy decision contract (spec §16).

A `PolicyDecision` is the only thing that authorizes an action. It is
deliberately a separate object from both the `Recommendation` that prompted it
and the `ActionRequest` that carries it out, because safety invariant 2 —
*every action passes through the Policy and Safety Service* — is only
believable if there is no type that can skip the middle.

The decision records **why**: reason codes, the evidence considered, the policy
version that produced it, and a hash of the inputs. That hash is what makes a
decision auditable after the fact — you can prove which state a decision was
made against, not merely that one was made.
"""

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from syltra_contracts.enums import PolicyOutcome, SafetyClass

POLICY_VERSION = "1.0.0"


class PolicyDecision(BaseModel):
    """The authorization record for one proposed action (spec §16)."""

    model_config = ConfigDict(extra="allow", frozen=True)

    decision_id: UUID
    recommendation_id: UUID | None = None
    """None for a manual user action, which still requires a decision."""
    home_id: str
    decision: PolicyOutcome
    evaluated_at: datetime
    expires_at: datetime
    reason_codes: list[str] = Field(min_length=1)
    safety_class: SafetyClass
    policy_version: str = POLICY_VERSION
    input_hash: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    required_approval_from: str | None = None

    @field_validator("evaluated_at", "expires_at")
    @classmethod
    def _timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            msg = "policy timestamps must be timezone-aware (UTC storage)"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def _expiry_follows_evaluation(self) -> "PolicyDecision":
        if self.expires_at <= self.evaluated_at:
            msg = "a policy decision must expire after it is evaluated"
            raise ValueError(msg)
        return self

    def is_expired_at(self, now: datetime) -> bool:
        return now >= self.expires_at

    def authorizes_execution_at(self, now: datetime) -> bool:
        """True only for a live ALLOW.

        Every other outcome — including REQUIRE_USER_APPROVAL, which becomes
        executable only after a *new* decision is issued on approval — returns
        False. An expired ALLOW authorizes nothing (safety invariant 3).
        """
        return self.decision is PolicyOutcome.ALLOW and not self.is_expired_at(now)


def compute_input_hash(payload: dict[str, Any]) -> str:
    """Stable SHA-256 over the inputs a decision was made against.

    Sorted keys and a canonical separator make the hash reproducible across
    processes and machines, so an auditor can recompute it from stored evidence
    and confirm the decision was made against the state it claims.
    """
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()
