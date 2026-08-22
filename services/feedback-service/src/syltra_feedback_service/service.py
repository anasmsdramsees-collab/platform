"""Feedback Service (spec §14.8).

Records how a household responded to each recommendation, and turns that into
two things the rest of the platform can act on: a **confidence adjustment** per
recommendation type, and a **suppression list** for types the household has
refused outright.

The requirement that shapes the design is the loop-breaker. When SYLTRA sets a
thermostat, the thermostat reports its new value back through the event stream.
If that echo counted as the household expressing a preference, the platform
would treat its own guess as confirmation and reinforce it indefinitely. So
feedback carries a source, and only `USER` feedback moves preference.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from syltra_contracts import (
    FeedbackKind,
    FeedbackRecord,
    FeedbackSource,
    Recommendation,
)

from syltra_feedback_service import metrics

logger = logging.getLogger(__name__)

REJECTION_PENALTY = 0.15
"""Confidence lost per negative response."""

ACCEPTANCE_REWARD = 0.05
"""Confidence regained per acceptance — deliberately smaller than the penalty.

Trust should be slow to earn and quick to lose: a household that says no twice
has told us more than one that clicked yes twice.
"""

SUSPEND_BELOW = 0.4
"""Adjustment beneath which the producing model should be suspended (§19.4)."""

MIN_ADJUSTMENT = 0.0
MAX_ADJUSTMENT = 1.0

ECHO_WINDOW = timedelta(seconds=90)
"""How long after an action a matching state change is treated as its echo."""


@dataclass
class TypeStanding:
    """The household's running verdict on one recommendation type."""

    recommendation_type: str
    adjustment: float = 1.0
    accepted: int = 0
    rejected: int = 0
    undone: int = 0
    modified: int = 0
    deferred: int = 0
    suppressed: bool = False
    last_feedback_at: datetime | None = None
    preferred_values: list[Any] = field(default_factory=list)
    """Values the household chose instead, from MODIFY responses."""

    @property
    def total_responses(self) -> int:
        return self.accepted + self.rejected + self.undone + self.modified + self.deferred

    @property
    def acceptance_rate(self) -> float | None:
        if self.total_responses == 0:
            return None
        return round(self.accepted / self.total_responses, 3)

    @property
    def should_suspend(self) -> bool:
        """Spec §19.4: suspend on repeated rejection or undo."""
        return self.suppressed or self.adjustment < SUSPEND_BELOW


class FeedbackService:
    def __init__(self) -> None:
        self._records: dict[str, list[FeedbackRecord]] = defaultdict(list)
        self._standing: dict[str, dict[str, TypeStanding]] = defaultdict(dict)
        self._recommendation_types: dict[UUID, str] = {}
        self._recent_actions: dict[str, datetime] = {}
        """``home:device:capability`` -> when SYLTRA last wrote it."""
        self.audit: list[dict[str, Any]] = []

    # ── registration ──

    def register_recommendation(self, recommendation: Recommendation) -> None:
        """Remember which type a recommendation belonged to.

        Feedback arrives referencing a recommendation id; without this the
        response could not be attributed to the right type or model.
        """
        self._recommendation_types[recommendation.recommendation_id] = (
            recommendation.recommendation_type
        )

    def note_automation_write(
        self, home_id: str, device_id: str, capability: str, at: datetime
    ) -> None:
        """Record that SYLTRA itself just changed this device."""
        self._recent_actions[f"{home_id}:{device_id}:{capability}"] = at

    def classify_state_change(
        self, home_id: str, device_id: str, capability: str, at: datetime
    ) -> FeedbackSource:
        """Decide whether an observed change is a person or SYLTRA's own echo.

        This is the loop-breaker (spec §14.8). A change arriving shortly after
        SYLTRA wrote the same capability is the device reporting our own
        command back, not a household preference.
        """
        written_at = self._recent_actions.get(f"{home_id}:{device_id}:{capability}")
        if written_at is not None and timedelta(0) <= at - written_at <= ECHO_WINDOW:
            return FeedbackSource.AUTOMATION_ECHO
        return FeedbackSource.USER

    # ── recording ──

    def record(
        self,
        home_id: str,
        recommendation_id: UUID,
        kind: FeedbackKind,
        source: FeedbackSource = FeedbackSource.USER,
        action_id: UUID | None = None,
        modified_value: Any = None,
        actor: str = "occupant",
        now: datetime | None = None,
        recommendation_type: str | None = None,
    ) -> FeedbackRecord:
        """Record one response and update the household's standing."""
        moment = now or datetime.now(tz=UTC)
        record = FeedbackRecord(
            feedback_id=uuid4(),
            home_id=home_id,
            recommendation_id=recommendation_id,
            action_id=action_id,
            kind=kind,
            source=source,
            recorded_at=moment,
            actor=actor,
            modified_value=modified_value,
        )
        self._records[home_id].append(record)

        rec_type = (
            recommendation_type
            or self._recommendation_types.get(recommendation_id)
            or "unknown"
        )
        self._apply(home_id, rec_type, record)
        metrics.RESPONSES.labels(kind=kind.value, source=source.value).inc()
        self._publish_standing(home_id, rec_type)
        self.audit.append(
            {
                "occurred_at": moment.isoformat(),
                "home_id": home_id,
                "action": "FEEDBACK_RECORDED",
                "actor": actor,
                "kind": kind.value,
                "source": source.value,
                "recommendation_id": str(recommendation_id),
                "recommendation_type": rec_type,
                "teaches_preference": record.teaches_preference,
            }
        )
        return record

    def _apply(self, home_id: str, rec_type: str, record: FeedbackRecord) -> None:
        standing = self._standing[home_id].setdefault(
            rec_type, TypeStanding(recommendation_type=rec_type)
        )
        standing.last_feedback_at = record.recorded_at

        if not record.teaches_preference:
            # Recorded for audit, but an automation echo must not move
            # preference — that is the feedback loop this service exists to
            # prevent (spec §14.8).
            logger.debug("feedback from %s ignored for preference", record.source.value)
            return

        if record.kind is FeedbackKind.ACCEPT:
            standing.accepted += 1
            standing.adjustment = min(standing.adjustment + ACCEPTANCE_REWARD, MAX_ADJUSTMENT)
        elif record.kind is FeedbackKind.REJECT:
            standing.rejected += 1
            standing.adjustment = max(standing.adjustment - REJECTION_PENALTY, MIN_ADJUSTMENT)
        elif record.kind is FeedbackKind.UNDO:
            standing.undone += 1
            # An undo is stronger evidence than a rejection: the household let
            # it happen, saw the result, and reversed it.
            standing.adjustment = max(
                standing.adjustment - REJECTION_PENALTY * 1.5, MIN_ADJUSTMENT
            )
        elif record.kind is FeedbackKind.NEVER_REPEAT:
            standing.suppressed = True
            standing.adjustment = MIN_ADJUSTMENT
        elif record.kind is FeedbackKind.MODIFY:
            standing.modified += 1
            # A modification is partial agreement: the idea was right, the
            # value was not. Small penalty, and the value is kept as evidence.
            standing.adjustment = max(
                standing.adjustment - REJECTION_PENALTY / 3, MIN_ADJUSTMENT
            )
            if record.modified_value is not None:
                standing.preferred_values.append(record.modified_value)
        elif record.kind is FeedbackKind.NOT_NOW:
            # Timing, not substance. Deliberately no confidence change.
            standing.deferred += 1

        standing.adjustment = round(standing.adjustment, 4)

    # ── queries ──

    def _publish_standing(self, home_id: str, recommendation_type: str) -> None:
        """Mirror this household's standing into the gauges (spec §29)."""
        metrics.SUPPRESSED_TYPES.labels(home_id=home_id).set(len(self.suppressed_types(home_id)))
        metrics.TYPES_NEEDING_SUSPENSION.labels(home_id=home_id).set(
            len(self.types_needing_suspension(home_id))
        )
        rate = self.standing(home_id, recommendation_type).acceptance_rate
        if rate is not None:
            metrics.ACCEPTANCE_RATE.labels(
                home_id=home_id, recommendation_type=recommendation_type
            ).set(rate)

    def standing(self, home_id: str, recommendation_type: str) -> TypeStanding:
        return self._standing[home_id].get(
            recommendation_type, TypeStanding(recommendation_type=recommendation_type)
        )

    def adjustment_for(self, home_id: str, recommendation_type: str) -> float:
        return self.standing(home_id, recommendation_type).adjustment

    def suppressed_types(self, home_id: str) -> frozenset[str]:
        """Types the household has refused outright — fed to the policy service."""
        return frozenset(
            rec_type
            for rec_type, standing in self._standing[home_id].items()
            if standing.suppressed
        )

    def types_needing_suspension(self, home_id: str) -> frozenset[str]:
        """Types whose standing has fallen far enough to withdraw (§19.4)."""
        return frozenset(
            rec_type
            for rec_type, standing in self._standing[home_id].items()
            if standing.should_suspend
        )

    def records(self, home_id: str, recommendation_id: UUID | None = None) -> list[FeedbackRecord]:
        found = self._records.get(home_id, [])
        if recommendation_id is not None:
            found = [r for r in found if r.recommendation_id == recommendation_id]
        return list(found)

    def preferred_values(self, home_id: str, recommendation_type: str) -> list[Any]:
        return list(self.standing(home_id, recommendation_type).preferred_values)
