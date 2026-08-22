"""State-change normalization (spec §14.1): envelope construction, duplicate
suppression, out-of-order detection, quality and freshness calculation."""

from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from syltra_contracts import EventEnvelope, EventSource, EventSubject, PrivacyClass
from syltra_edge_agent.mapping import (
    UNAVAILABLE_STATES,
    CapabilityReading,
    MappingError,
    map_ha_state,
)

_DEDUP_CAPACITY = 4096


@dataclass
class NormalizationOutcome:
    raw_envelope: EventEnvelope | None = None
    envelopes: list[EventEnvelope] = field(default_factory=list)
    duplicate: bool = False
    out_of_order: bool = False
    unmapped: bool = False
    reason_codes: list[str] = field(default_factory=list)


class StateChangeNormalizer:
    """Turns Home Assistant ``state_changed`` payloads into validated SYLTRA
    envelopes. Stateful per connection: remembers recent event identities for
    duplicate detection and the newest ``last_updated`` per entity for
    out-of-order detection."""

    def __init__(
        self,
        home_id: str,
        hub_id: str,
        device_id_for: Callable[[str], str],
        room_id_for: Callable[[str], str | None],
        protocol: str = "home_assistant_websocket",
    ) -> None:
        self._home_id = home_id
        self._hub_id = hub_id
        self._device_id_for = device_id_for
        self._room_id_for = room_id_for
        self._protocol = protocol
        self._seen: OrderedDict[tuple[str, str, str], None] = OrderedDict()
        self._latest_per_entity: dict[str, datetime] = {}

    def _source(self) -> EventSource:
        return EventSource(
            service="edge-agent", instance_id=self._hub_id, protocol=self._protocol
        )

    def _remember(self, key: tuple[str, str, str]) -> bool:
        """Record an event identity; returns True if it was already seen."""
        if key in self._seen:
            self._seen.move_to_end(key)
            return True
        self._seen[key] = None
        if len(self._seen) > _DEDUP_CAPACITY:
            self._seen.popitem(last=False)
        return False

    def normalize(self, data: Mapping[str, Any]) -> NormalizationOutcome:
        """``data`` is the HA event payload: entity_id, old_state, new_state.

        Raises ``MappingError`` for structurally invalid payloads (caller
        routes those to the dead-letter stream).
        """
        entity_id = data.get("entity_id")
        new_state = data.get("new_state")
        if not isinstance(entity_id, str) or not entity_id:
            raise MappingError("MISSING_ENTITY_ID", "state_changed without entity_id")
        if not isinstance(new_state, dict):
            # Entity removed — represented as availability loss.
            new_state = {"entity_id": entity_id, "state": "unavailable", "attributes": {}}
        state = new_state.get("state")
        if not isinstance(state, str):
            raise MappingError("MISSING_STATE", f"{entity_id}: new_state has no state string")
        attributes_raw = new_state.get("attributes")
        attributes: dict[str, Any] = attributes_raw if isinstance(attributes_raw, dict) else {}

        received_at = datetime.now(tz=UTC)
        occurred_at = self._parse_timestamp(new_state.get("last_updated")) or received_at

        outcome = NormalizationOutcome()

        # Duplicate detection: identity = entity + report time + state value.
        dedup_key = (entity_id, occurred_at.isoformat(), state)
        if self._remember(dedup_key):
            outcome.duplicate = True
            outcome.reason_codes.append("DUPLICATE_EVENT")
            return outcome

        # Out-of-order detection: older than the newest seen for this entity.
        latest = self._latest_per_entity.get(entity_id)
        if latest is not None and occurred_at < latest:
            outcome.out_of_order = True
            outcome.reason_codes.append("OUT_OF_ORDER_EVENT")
        else:
            self._latest_per_entity[entity_id] = occurred_at

        correlation_id = uuid4()
        device_id = self._device_id_for(entity_id)
        subject = EventSubject(
            device_id=device_id,
            entity_id=entity_id,
            room_id=self._room_id_for(entity_id),
        )
        freshness_ms = max((received_at - occurred_at).total_seconds() * 1000.0, 0.0)
        base_metadata: dict[str, Any] = {"freshness_ms": round(freshness_ms, 3)}
        if ha_context := data.get("context"):
            if isinstance(ha_context, dict) and ha_context.get("id"):
                base_metadata["ha_context_id"] = str(ha_context["id"])
        if outcome.out_of_order:
            base_metadata["out_of_order"] = True

        outcome.raw_envelope = EventEnvelope(
            event_id=uuid4(),
            event_type="device.state.changed",
            schema_version="1.0",
            occurred_at=occurred_at,
            received_at=received_at,
            home_id=self._home_id,
            correlation_id=correlation_id,
            source=self._source(),
            subject=subject,
            capability=None,
            value=state,
            quality=1.0,
            privacy_class=PrivacyClass.HOUSEHOLD_PRIVATE,
            metadata={**base_metadata, "attributes": attributes},
        )

        readings = map_ha_state(entity_id, state, attributes)
        if not readings:
            outcome.unmapped = True
            outcome.reason_codes.append("UNMAPPED_ENTITY")
            return outcome

        quality = 1.0
        if outcome.out_of_order:
            quality = 0.5

        for reading in readings:
            outcome.envelopes.append(
                self._reading_envelope(
                    reading=reading,
                    state=state,
                    occurred_at=occurred_at,
                    received_at=received_at,
                    correlation_id=correlation_id,
                    subject=subject,
                    quality=quality,
                    metadata=base_metadata,
                )
            )
        return outcome

    def _reading_envelope(
        self,
        reading: CapabilityReading,
        state: str,
        occurred_at: datetime,
        received_at: datetime,
        correlation_id: Any,
        subject: EventSubject,
        quality: float,
        metadata: dict[str, Any],
    ) -> EventEnvelope:
        event_type = (
            "device.availability.changed"
            if reading.capability == "device.online" and state in UNAVAILABLE_STATES
            else "device.state.changed"
        )
        return EventEnvelope(
            event_id=uuid4(),
            event_type=event_type,
            schema_version="1.0",
            occurred_at=occurred_at,
            received_at=received_at,
            home_id=self._home_id,
            correlation_id=correlation_id,
            source=self._source(),
            subject=subject,
            capability=reading.capability,
            value=reading.value,
            unit=reading.unit,
            quality=quality,
            privacy_class=PrivacyClass.HOUSEHOLD_PRIVATE,
            metadata=dict(metadata),
        )

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
