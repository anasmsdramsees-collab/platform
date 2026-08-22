"""Context Engine service (spec §14.3).

Keeps its own twin projection fed from the normalized event stream, evaluates
the deterministic rules whenever state changes, and publishes `context.updated`
on material change. A periodic sweep expires contexts whose sensors have gone
silent — without it, an event-driven engine would leave inferences standing
forever after the last event.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from nats.aio.msg import Msg

from syltra_contracts import (
    ContextRecord,
    EventEnvelope,
    EventSource,
    EventSubject,
    PrivacyClass,
)
from syltra_context_engine import metrics
from syltra_context_engine.engine import ChangeKind, ContextChange, ContextEngine
from syltra_digital_twin.core import TwinProjection
from syltra_eventing import EventPublisher
from syltra_eventing.subjects import context_updated_subject

logger = logging.getLogger(__name__)

SWEEP_INTERVAL = timedelta(seconds=30)


class ContextService:
    def __init__(
        self,
        publisher: EventPublisher,
        hub_id: str = "hub_dev_001",
        engine: ContextEngine | None = None,
    ) -> None:
        self._publisher = publisher
        self._hub_id = hub_id
        self.engine = engine or ContextEngine()
        self.twin = TwinProjection()
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def mark_ready(self, ready: bool = True) -> None:
        self._ready = ready
        metrics.CONSUMER_CONNECTED.set(1 if ready else 0)

    async def handle_message(self, message: Msg) -> None:
        """Apply one normalized event, then re-evaluate contexts."""
        metrics.EVENTS_CONSUMED.inc()
        try:
            envelope = EventEnvelope.model_validate(json.loads(message.data))
        except (ValueError, TypeError) as exc:
            metrics.EVENTS_INVALID.inc()
            logger.warning("invalid event at context boundary → dead-letter")
            await self._publisher.publish_deadletter(
                reason_codes=["INVALID_EVENT_AT_CONSUMER"],
                error=str(exc),
                original_subject=message.subject,
            )
            await message.ack()
            return

        await self.apply_envelope(envelope)
        await message.ack()

    async def apply_envelope(self, envelope: EventEnvelope) -> list[ContextChange]:
        """Update the local twin and re-evaluate contexts for that home."""
        if not self.twin.apply(envelope):
            # No observable twin change means no new basis for inference.
            return []
        return await self.evaluate(envelope.home_id, datetime.now(tz=UTC))

    async def evaluate(self, home_id: str, now: datetime) -> list[ContextChange]:
        home = self.twin.home(home_id)
        if home is None:
            return []
        changes = self.engine.evaluate(home_id, home, now)
        await self._publish(changes)
        self._refresh_gauges(home_id, now)
        return changes

    async def sweep(self, home_id: str, now: datetime) -> list[ContextChange]:
        """Expire contexts whose evidence has aged out."""
        changes = self.engine.sweep_expired(home_id, now)
        if changes:
            await self._publish(changes)
            self._refresh_gauges(home_id, now)
        return changes

    async def run_sweeper(self, stopping: asyncio.Event, interval: timedelta = SWEEP_INTERVAL) -> None:
        """Periodic expiry loop, run alongside the consumer."""
        while not stopping.is_set():
            try:
                await asyncio.wait_for(stopping.wait(), timeout=interval.total_seconds())
                return
            except TimeoutError:
                pass
            now = datetime.now(tz=UTC)
            for home_id in list(self.twin.home_ids):
                try:
                    await self.sweep(home_id, now)
                except Exception:
                    logger.exception("context sweep failed for %s", home_id)

    async def _publish(self, changes: list[ContextChange]) -> None:
        for change in changes:
            metrics.CONTEXT_CHANGES.labels(
                context_type=change.record.context_type.value, kind=change.kind.value
            ).inc()
            await self._publish_change(change)

    async def _publish_change(self, change: ContextChange) -> None:
        record = change.record
        now = datetime.now(tz=UTC)
        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type="context.updated",
            schema_version="1.0",
            occurred_at=record.last_updated_at,
            received_at=now,
            home_id=record.home_id,
            correlation_id=record.context_id,
            source=EventSource(
                service="context-engine", instance_id=self._hub_id, protocol="internal"
            ),
            subject=EventSubject(room_id=record.scope_room_id),
            value=record.context_type.value,
            quality=record.confidence,
            privacy_class=PrivacyClass.HOUSEHOLD_PRIVATE,
            metadata={
                "change": change.kind.value,
                "context": json.loads(record.model_dump_json()),
            },
        )
        await self._publisher.publish_envelope(
            context_updated_subject(record.home_id), envelope
        )

    def _refresh_gauges(self, home_id: str, now: datetime) -> None:
        active = self.engine.active_contexts(home_id, now)
        metrics.ACTIVE_CONTEXTS.labels(home_id=home_id).set(len(active))
        if active:
            metrics.MEAN_CONFIDENCE.labels(home_id=home_id).set(
                round(sum(c.confidence for c in active) / len(active), 3)
            )
        else:
            metrics.MEAN_CONFIDENCE.labels(home_id=home_id).set(0.0)

    def active(self, home_id: str, now: datetime | None = None) -> list[ContextRecord]:
        return self.engine.active_contexts(home_id, now or datetime.now(tz=UTC))


__all__ = ["ChangeKind", "ContextService", "SWEEP_INTERVAL"]
