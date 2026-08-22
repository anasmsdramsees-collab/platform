"""Digital Twin service loop (spec §14.2).

Consumes normalized events from a durable JetStream consumer, appends them to
immutable history, applies them to the in-memory projection, persists the
current-state projection, and publishes ``twin.state.updated`` — but only when
observable state actually changed, so consumers are not woken by no-ops.
"""

import json
import logging
import time
from datetime import UTC, datetime
from uuid import uuid4

from nats.aio.msg import Msg
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from syltra_contracts import EventEnvelope, EventSource, EventSubject, PrivacyClass
from syltra_digital_twin import metrics
from syltra_digital_twin.core import StateStatus, TwinProjection
from syltra_digital_twin.repository import TwinRepository, rebuild_from_history
from syltra_eventing import EventPublisher
from syltra_eventing.subjects import twin_updated_subject

logger = logging.getLogger(__name__)


class DigitalTwinService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        publisher: EventPublisher,
        hub_id: str = "hub_dev_001",
    ) -> None:
        self._session_factory = session_factory
        self._publisher = publisher
        self._hub_id = hub_id
        self.twin = TwinProjection()
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def mark_ready(self, ready: bool = True) -> None:
        self._ready = ready
        metrics.CONSUMER_CONNECTED.set(1 if ready else 0)

    async def restore(self, home_id: str) -> int:
        """Rebuild in-memory state from stored history at startup.

        Restart must not lose the twin (spec §14.2: survives service restart).
        """
        async with self._session_factory() as session:
            repository = TwinRepository(session)
            await rebuild_from_history(repository, home_id, into=self.twin)
        home = self.twin.home(home_id)
        applied = home.events_applied if home else 0
        logger.info("restored twin for %s from %d stored events", home_id, applied)
        self._refresh_gauges(home_id)
        return applied

    async def handle_message(self, message: Msg) -> None:
        """Process one JetStream message end to end."""
        started = time.monotonic()
        metrics.EVENTS_CONSUMED.inc()
        try:
            envelope = EventEnvelope.model_validate(json.loads(message.data))
        except (ValueError, TypeError) as exc:
            metrics.EVENTS_INVALID.inc()
            logger.warning("invalid event at twin boundary → dead-letter")
            await self._publisher.publish_deadletter(
                reason_codes=["INVALID_EVENT_AT_CONSUMER"],
                error=str(exc),
                original_subject=message.subject,
            )
            await message.ack()
            return

        await self.apply_envelope(envelope)
        await message.ack()
        metrics.STATE_UPDATE_LATENCY.observe(time.monotonic() - started)

    async def apply_envelope(self, envelope: EventEnvelope) -> bool:
        """Append, project, persist, and publish. Returns True if state changed."""
        home_id = envelope.home_id
        async with self._session_factory() as session:
            repository = TwinRepository(session)
            stored = await repository.append_event(envelope)
            if not stored:
                # Already in history: a redelivery. The projection is
                # idempotent too, so nothing further is needed.
                metrics.EVENTS_DUPLICATE.inc()
                await session.commit()
                return False

            changed = self.twin.apply(envelope)
            if changed:
                await repository.upsert_current_states(home_id, self.twin)
                snapshot = self.twin.snapshot(home_id, datetime.now(tz=UTC))
                await repository.save_checkpoint(
                    home_id, snapshot.events_applied, snapshot.fingerprint()
                )
            await session.commit()

        if changed:
            metrics.EVENTS_APPLIED.inc()
            await self._publish_twin_updated(envelope)
            self._refresh_gauges(home_id)
        return changed

    async def _publish_twin_updated(self, cause: EventEnvelope) -> None:
        now = datetime.now(tz=UTC)
        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type="twin.state.updated",
            schema_version="1.0",
            occurred_at=cause.occurred_at,
            received_at=now,
            home_id=cause.home_id,
            correlation_id=cause.correlation_id,
            causation_id=cause.event_id,
            source=EventSource(
                service="digital-twin", instance_id=self._hub_id, protocol="internal"
            ),
            subject=EventSubject(
                device_id=cause.subject.device_id, room_id=cause.subject.room_id
            ),
            capability=cause.capability,
            value=cause.value,
            unit=cause.unit,
            quality=cause.quality,
            privacy_class=PrivacyClass.HOUSEHOLD_PRIVATE,
        )
        await self._publisher.publish_envelope(
            twin_updated_subject(cause.home_id), envelope
        )

    def _refresh_gauges(self, home_id: str) -> None:
        home = self.twin.home(home_id)
        if home is None:
            return
        now = datetime.now(tz=UTC)
        stale = unknown = 0
        for device in home.devices.values():
            for state in device.capabilities.values():
                status = state.status_at(now)
                if status is StateStatus.STALE:
                    stale += 1
                elif status is StateStatus.UNKNOWN:
                    unknown += 1
        metrics.TRACKED_DEVICES.labels(home_id=home_id).set(len(home.devices))
        metrics.STALE_CAPABILITIES.labels(home_id=home_id).set(stale)
        metrics.UNKNOWN_CAPABILITIES.labels(home_id=home_id).set(unknown)
