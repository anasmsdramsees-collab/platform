"""Validated JetStream publishing with dead-letter routing (spec §11.3)."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from nats.js import JetStreamContext

from syltra_contracts import EventEnvelope
from syltra_contracts.deadletter import DeadLetterRecord
from syltra_eventing.subjects import deadletter_subject


class EventPublisher:
    """Publishes contract-validated envelopes; anything invalid goes to the
    service's dead-letter subject with reason codes."""

    def __init__(self, js: JetStreamContext, service: str) -> None:
        self._js = js
        self._service = service

    async def publish_envelope(self, subject: str, envelope: EventEnvelope) -> None:
        """Publish a validated envelope. ``Nats-Msg-Id`` carries the immutable
        event id so JetStream deduplicates redelivery inside its window."""
        payload = envelope.model_dump_json().encode()
        await self._js.publish(
            subject,
            payload,
            headers={"Nats-Msg-Id": str(envelope.event_id)},
        )

    async def publish_deadletter(
        self,
        reason_codes: list[str],
        error: str,
        original_subject: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Send an invalid or poison event to this service's dead-letter stream."""
        record = DeadLetterRecord(
            deadletter_id=uuid4(),
            service=self._service,
            occurred_at=datetime.now(tz=UTC),
            reason_codes=reason_codes,
            error=error,
            original_subject=original_subject,
            payload=payload or {},
        )
        await self._js.publish(
            deadletter_subject(self._service),
            record.model_dump_json().encode(),
            headers={"Nats-Msg-Id": str(record.deadletter_id)},
        )


def decode_envelope(data: bytes) -> EventEnvelope:
    """Consumer-boundary validation (spec §11.3): parse and validate or raise."""
    return EventEnvelope.model_validate(json.loads(data))
