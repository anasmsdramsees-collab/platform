"""Context evaluation, lifecycle and change detection (spec §14.3).

The engine turns rule proposals into `ContextRecord`s and manages their
lifecycle:

- **Overlapping contexts are normal.** `HOME_OCCUPIED`, `ROOM_OCCUPIED:kitchen`
  and `COOKING:kitchen` can all be true at once; they are keyed by
  (type, scope), never collapsed.
- **Contexts expire.** A context whose evidence is no longer produced simply
  ages out at `expires_at`. Expiry is derived from the freshness of the
  evidence, so a context can never outlive the data behind it.
- **Publication is on material change only** (spec §14.3): appearing,
  disappearing, or a meaningful shift in confidence. Re-confirming the same
  context with the same confidence is not an event.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import uuid4

from syltra_contracts import ContextRecord, ContextType
from syltra_context_engine.rules import ContextProposal, RuleContext, evaluate_all
from syltra_digital_twin.core import HomeState

CONFIDENCE_CHANGE_THRESHOLD = 0.1
"""Confidence must move by at least this much to count as a material change."""


class ChangeKind(StrEnum):
    STARTED = "STARTED"
    UPDATED = "UPDATED"
    EXPIRED = "EXPIRED"
    ENDED = "ENDED"
    """Evidence stopped supporting the context before it expired."""


@dataclass(frozen=True)
class ContextChange:
    kind: ChangeKind
    record: ContextRecord

    @property
    def key(self) -> tuple[ContextType, str]:
        return (self.record.context_type, self.record.scope)


class ContextEngine:
    """Holds active contexts per home and evaluates rules against the twin."""

    def __init__(self, confidence_threshold: float = CONFIDENCE_CHANGE_THRESHOLD) -> None:
        self._active: dict[str, dict[tuple[ContextType, str], ContextRecord]] = {}
        self._threshold = confidence_threshold

    # ── queries ──

    def active_contexts(self, home_id: str, now: datetime) -> list[ContextRecord]:
        """Currently active, non-expired contexts, newest first."""
        contexts = self._active.get(home_id, {})
        return sorted(
            (c for c in contexts.values() if c.is_active_at(now)),
            key=lambda c: (c.context_type.value, c.scope),
        )

    def get(self, home_id: str, context_type: ContextType, scope: str) -> ContextRecord | None:
        record = self._active.get(home_id, {}).get((context_type, scope))
        return record

    # ── evaluation ──

    def evaluate(
        self,
        home_id: str,
        home: HomeState,
        now: datetime,
        **rule_options: object,
    ) -> list[ContextChange]:
        """Evaluate all rules and reconcile against currently active contexts.

        Returns only material changes, in a deterministic order.
        """
        rule_ctx = RuleContext(home=home, now=now, **rule_options)  # type: ignore[arg-type]
        proposals = evaluate_all(rule_ctx)
        return self._reconcile(home_id, proposals, now)

    def sweep_expired(self, home_id: str, now: datetime) -> list[ContextChange]:
        """Drop contexts whose expiry has passed, without re-evaluating rules.

        Called on a timer so contexts disappear when their sensors go silent —
        an event-driven engine alone would leave them active forever.
        """
        contexts = self._active.get(home_id, {})
        expired = [key for key, record in contexts.items() if not record.is_active_at(now)]
        changes: list[ContextChange] = []
        for key in sorted(expired, key=lambda k: (k[0].value, k[1])):
            record = contexts.pop(key)
            changes.append(ContextChange(kind=ChangeKind.EXPIRED, record=record))
        return changes

    # ── internals ──

    def _reconcile(
        self, home_id: str, proposals: list[ContextProposal], now: datetime
    ) -> list[ContextChange]:
        contexts = self._active.setdefault(home_id, {})
        changes: list[ContextChange] = []
        proposed_keys: set[tuple[ContextType, str]] = set()

        for proposal in proposals:
            key = (proposal.context_type, proposal.scope)
            proposed_keys.add(key)
            existing = contexts.get(key)

            if existing is None or not existing.is_active_at(now):
                record = self._build(home_id, proposal, now, started_at=now)
                contexts[key] = record
                changes.append(ContextChange(kind=ChangeKind.STARTED, record=record))
                continue

            record = self._build(
                home_id, proposal, now, started_at=existing.started_at,
                context_id_source=existing,
            )
            contexts[key] = record
            if self._is_material(existing, record):
                changes.append(ContextChange(kind=ChangeKind.UPDATED, record=record))

        # A context whose rule no longer fires has lost its evidence: end it
        # now rather than letting a stale inference linger until expiry.
        for key in sorted(set(contexts) - proposed_keys, key=lambda k: (k[0].value, k[1])):
            record = contexts.pop(key)
            if record.is_active_at(now):
                changes.append(ContextChange(kind=ChangeKind.ENDED, record=record))
            else:
                changes.append(ContextChange(kind=ChangeKind.EXPIRED, record=record))

        changes.sort(key=lambda c: (c.record.context_type.value, c.record.scope, c.kind.value))
        return changes

    def _build(
        self,
        home_id: str,
        proposal: ContextProposal,
        now: datetime,
        started_at: datetime,
        context_id_source: ContextRecord | None = None,
    ) -> ContextRecord:
        return ContextRecord(
            # A continuing context keeps its identity so consumers can follow it.
            context_id=context_id_source.context_id if context_id_source else uuid4(),
            home_id=home_id,
            context_type=proposal.context_type,
            scope=proposal.scope,
            started_at=started_at,
            last_updated_at=now,
            expires_at=now + proposal.expires_in,
            confidence=proposal.confidence,
            evidence=proposal.evidence,
            producer=proposal.producer,
            reason_codes=proposal.reason_codes,
            metadata=proposal.metadata,
        )

    def _is_material(self, previous: ContextRecord, current: ContextRecord) -> bool:
        """Only meaningful movement is worth publishing (spec §14.3)."""
        if abs(previous.confidence - current.confidence) >= self._threshold:
            return True
        if previous.reason_codes != current.reason_codes:
            return True
        return {(e.device_id, e.capability, str(e.value)) for e in previous.evidence} != {
            (e.device_id, e.capability, str(e.value)) for e in current.evidence
        }


def next_expiry(records: list[ContextRecord]) -> datetime | None:
    """Earliest expiry among records, for scheduling the next sweep."""
    if not records:
        return None
    return min(record.expires_at for record in records)


def time_until(moment: datetime | None, now: datetime, default: timedelta) -> timedelta:
    if moment is None:
        return default
    return max(moment - now, timedelta(seconds=0))
