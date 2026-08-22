"""Risk case contracts and the fixed risk state machine (spec §14.5).

The distinction this module exists to enforce: **inference can raise awareness,
but only deterministic evidence can confirm an emergency.**

A risk case moves through seven states. The Risk Engine — which reasons over
combinations of signals and may be wrong — can reach `WATCH` and `PRE_ALERT`
and nothing further. `CONFIRMED` is reachable only through the Safety Governor,
acting on a certified alarm capability with a fresh reading. That boundary is
encoded in `AI_REACHABLE_STATES` and enforced by `assert_transition`, so no
service can widen its own authority by calling a different method.

Safety invariants 6 (emergency actions require deterministic approved
conditions) and 18 (critical rules use approved sensor alarm states and device
capabilities, not inferred text or LLM output) both reduce to this rule.
"""

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from syltra_contracts.enums import RiskCategory, RiskState


class RiskSeverity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceOrigin(StrEnum):
    """Where a piece of risk evidence came from — the load-bearing field.

    A `CERTIFIED_ALARM` reading is a device designed and approved to detect the
    hazard. `INFERENCE` is SYLTRA reasoning about combinations of ordinary
    sensors. Only the former may confirm.
    """

    CERTIFIED_ALARM = "CERTIFIED_ALARM"
    SENSOR_READING = "SENSOR_READING"
    INFERENCE = "INFERENCE"
    USER_REPORT = "USER_REPORT"
    SYSTEM_HEALTH = "SYSTEM_HEALTH"


CERTIFIED_ALARM_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {
        "safety.smoke_alarm",
        "safety.heat_alarm",
        "safety.gas_alarm",
        "safety.co_alarm",
        "safety.water_leak",
    }
)
"""The only capabilities whose reading may confirm a risk (spec §18.18)."""


AI_REACHABLE_STATES: Final[frozenset[RiskState]] = frozenset(
    {RiskState.NORMAL, RiskState.WATCH, RiskState.PRE_ALERT}
)
"""States inference alone may produce (spec §22 Phase 6 acceptance)."""


DETERMINISTIC_ONLY_STATES: Final[frozenset[RiskState]] = frozenset(
    {RiskState.CONFIRMED, RiskState.ACTION_IN_PROGRESS}
)
"""States reachable only through the Safety Governor's deterministic rules."""


_ALLOWED_TRANSITIONS: Final[dict[RiskState, frozenset[RiskState]]] = {
    RiskState.NORMAL: frozenset(
        {RiskState.WATCH, RiskState.PRE_ALERT, RiskState.CONFIRMED}
    ),
    # A certified alarm may fire with no prior warning, so NORMAL → CONFIRMED
    # is permitted — but only the Safety Governor can take it.
    RiskState.WATCH: frozenset(
        {RiskState.NORMAL, RiskState.PRE_ALERT, RiskState.CONFIRMED, RiskState.CLOSED}
    ),
    RiskState.PRE_ALERT: frozenset(
        {RiskState.WATCH, RiskState.CONFIRMED, RiskState.NORMAL, RiskState.CLOSED}
    ),
    RiskState.CONFIRMED: frozenset({RiskState.ACTION_IN_PROGRESS, RiskState.RECOVERY}),
    RiskState.ACTION_IN_PROGRESS: frozenset({RiskState.RECOVERY, RiskState.CONFIRMED}),
    # Recovery never returns straight to NORMAL: a case is closed deliberately,
    # so there is always a record that someone or something ended it.
    RiskState.RECOVERY: frozenset({RiskState.CLOSED, RiskState.CONFIRMED}),
    RiskState.CLOSED: frozenset(),
}


class RiskTransitionError(ValueError):
    """Raised when a state change is not permitted by the fixed machine."""


class UnauthorizedRiskTransition(RiskTransitionError):
    """Raised when inference attempts a deterministic-only transition."""


def can_transition(current: RiskState, target: RiskState) -> bool:
    if current is target:
        return True
    return target in _ALLOWED_TRANSITIONS[current]


def assert_transition(
    current: RiskState, target: RiskState, *, deterministic: bool = False
) -> None:
    """Validate a state change, including who is allowed to make it.

    ``deterministic=True`` marks the caller as the Safety Governor acting on
    certified evidence. Anything else is inference, and inference cannot reach
    `CONFIRMED` or `ACTION_IN_PROGRESS` however confident it is.
    """
    if current is target:
        return
    if not can_transition(current, target):
        msg = f"risk state cannot move from {current.value} to {target.value}"
        raise RiskTransitionError(msg)
    if target in DETERMINISTIC_ONLY_STATES and not deterministic:
        msg = (
            f"{target.value} is reachable only through a deterministic safety rule "
            "against a certified alarm capability (spec §18 invariants 6 and 18); "
            "inference may raise WATCH or PRE_ALERT only"
        )
        raise UnauthorizedRiskTransition(msg)


class RiskEvidenceItem(BaseModel):
    """One observation supporting a risk case, with its provenance."""

    model_config = ConfigDict(extra="allow", frozen=True)

    origin: EvidenceOrigin
    capability: str
    value: Any = None
    device_id: str | None = None
    room_id: str | None = None
    observed_at: datetime | None = None
    status: str = "KNOWN"
    """Twin freshness status: KNOWN, STALE or UNKNOWN."""
    note: str | None = None

    @property
    def is_fresh(self) -> bool:
        return self.status == "KNOWN"

    @property
    def can_confirm(self) -> bool:
        """Whether this single item is sufficient to confirm a hazard.

        Three conditions, all required: it came from a certified alarm, that
        alarm is one of the approved capabilities, and the reading is fresh. A
        stale alarm reading cannot confirm (safety invariant 4).
        """
        return (
            self.origin is EvidenceOrigin.CERTIFIED_ALARM
            and self.capability in CERTIFIED_ALARM_CAPABILITIES
            and self.is_fresh
            and bool(self.value) is True
        )


class RiskCase(BaseModel):
    """An open or closed risk case (spec §14.5)."""

    model_config = ConfigDict(extra="allow", frozen=True)

    case_id: UUID
    home_id: str
    category: RiskCategory
    state: RiskState
    severity: RiskSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    opened_at: datetime
    last_updated_at: datetime
    expires_at: datetime | None = None
    """Watch and pre-alert states age out; confirmed cases do not."""
    evidence: list[RiskEvidenceItem] = Field(min_length=1)
    reason_codes: list[str] = Field(min_length=1)
    producer: str
    room_id: str | None = None
    confirmed_by: str | None = None
    """The deterministic rule that confirmed this case, if confirmed."""
    closed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("opened_at", "last_updated_at")
    @classmethod
    def _timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            msg = "risk timestamps must be timezone-aware (UTC storage)"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def _confirmed_cases_name_their_rule(self) -> "RiskCase":
        # A confirmation with no named rule cannot be audited or reproduced,
        # which is the whole point of requiring deterministic confirmation.
        if self.state in DETERMINISTIC_ONLY_STATES and not self.confirmed_by:
            msg = (
                f"a case in {self.state.value} must record the deterministic rule "
                "that confirmed it"
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _confirmed_cases_rest_on_certified_evidence(self) -> "RiskCase":
        if self.state in DETERMINISTIC_ONLY_STATES and not any(
            item.can_confirm for item in self.evidence
        ):
            msg = (
                f"a case in {self.state.value} must carry at least one fresh, "
                "certified alarm reading (spec §18 invariant 18)"
            )
            raise ValueError(msg)
        return self

    @property
    def is_open(self) -> bool:
        return self.state is not RiskState.CLOSED

    @property
    def is_advisory(self) -> bool:
        """True while the case rests on inference rather than confirmation."""
        return self.state in {RiskState.WATCH, RiskState.PRE_ALERT}

    @property
    def permits_emergency_response(self) -> bool:
        """Only a confirmed case may drive an emergency response."""
        return self.state in DETERMINISTIC_ONLY_STATES

    def is_active_at(self, now: datetime) -> bool:
        if self.expires_at is None:
            return self.is_open
        return self.is_open and now < self.expires_at


DEFAULT_WATCH_TTL = timedelta(minutes=30)
DEFAULT_PRE_ALERT_TTL = timedelta(minutes=15)
"""Advisory states expire; a confirmed case stays open until it is resolved."""
