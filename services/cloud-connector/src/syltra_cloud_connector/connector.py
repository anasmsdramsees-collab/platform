"""The only way household data may leave the hub (spec §14.11, §26).

For most of this build `services/cloud-connector/` held a `.gitkeep`, and the
argument for leaving it that way was decent: the platform promises that local
control never depends on the cloud, and a connector that does not exist is
trivially disabled.

The argument is wrong in one direction. A component that does not exist is not
a component that refuses — it is a component somebody adds in a hurry later,
under a deadline, without the refusals. So this exists in order to say no.

## Four gates, in order, and every one of them defaults to closed

1. **Disabled.** `CloudConnector` starts disabled for every household and only
   `enable()` changes that. Spec §0 rule 4 makes this the resting state: local
   control must never depend on the cloud, and the cheapest proof is a
   connector that is off.

2. **Consent, per destination.** A household consenting to send diagnostics to
   its installer has not consented to send anything to a manufacturer.
   Consent is recorded against a named destination and a named purpose, and
   `withdraw()` takes effect on the next record rather than at some later sync.

3. **An allowlist, per destination.** Only fields named in advance leave.
   Allowlisting is the direction that fails safe: a denylist forgets the field
   somebody added last week, and an allowlist merely omits it.

4. **Redaction, field by field.** What survives the allowlist is still
   rewritten — a device id becomes a stable pseudonym, a room name goes, a
   precise timestamp is rounded to the hour. Redaction is applied after the
   allowlist rather than instead of it, because the two answer different
   questions: *may this field go at all*, and *what may it say*.

## The boundary that is not a promise

Delivery is bounded and cannot block. `record()` enqueues and returns; a full
queue drops its oldest and counts the drop. Nothing in this module is awaited
by a control path, and nothing in it can make one wait — a hub whose uplink is
down is a hub with a full queue, not a hub with a slow light switch.

The queue is bounded rather than durable on purpose: a fortnight of unsent
telemetry recovered after an outage is a fortnight of household behaviour
travelling somewhere long after anybody remembered agreeing to it.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import blake2s
from typing import Any

from syltra_cloud_connector import metrics

logger = logging.getLogger(__name__)

#: Records held per destination while an uplink is down. Small on purpose.
DEFAULT_QUEUE_LIMIT = 500


class ExportRefused(PermissionError):
    """The connector declined to export something, and says which gate stopped it."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail
        metrics.REFUSALS.labels(reason_code=reason_code).inc()


@dataclass(frozen=True)
class Destination:
    """Somewhere a household has agreed data may go, and exactly what may go."""

    name: str
    purpose: str
    allowed_fields: frozenset[str]
    #: Fields that may go but must be rewritten first.
    pseudonymise: frozenset[str] = frozenset()
    round_timestamps_to_hour: bool = True

    def __post_init__(self) -> None:
        if not self.allowed_fields:
            msg = f"destination {self.name!r} allows no fields; it would export nothing"
            raise ValueError(msg)
        unknown = self.pseudonymise - self.allowed_fields
        if unknown:
            # A field pseudonymised but not allowed is a rule about something
            # that never leaves — usually a sign somebody expected it to.
            msg = f"{sorted(unknown)} are pseudonymised but not allowed for {self.name!r}"
            raise ValueError(msg)


@dataclass
class Consent:
    """One household's agreement, and when it was given or withdrawn."""

    destination: str
    purpose: str
    granted_at: datetime
    granted_by: str
    withdrawn_at: datetime | None = None

    def is_active_at(self, now: datetime) -> bool:
        return self.withdrawn_at is None or now < self.withdrawn_at


@dataclass
class CloudConnector:
    """Disabled, consent-gated, allowlisted, redacting, and bounded."""

    salt: str = "syltra-local"
    queue_limit: int = DEFAULT_QUEUE_LIMIT
    _enabled: set[str] = field(default_factory=set)
    _destinations: dict[str, Destination] = field(default_factory=dict)
    _consents: dict[tuple[str, str], Consent] = field(default_factory=dict)
    _queues: dict[tuple[str, str], deque[dict[str, Any]]] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)

    # ── gate 1: off ──

    def is_enabled(self, home_id: str) -> bool:
        return home_id in self._enabled

    def enable(self, home_id: str, actor: str, reason: str, now: datetime | None = None) -> None:
        if not reason.strip():
            msg = "enabling cloud export must say why"
            raise ExportRefused("REASON_REQUIRED", msg)
        self._enabled.add(home_id)
        metrics.ENABLED.labels(home_id=home_id).set(1)
        self._record(now, home_id, "CLOUD_EXPORT_ENABLED", actor, reason)

    def disable(self, home_id: str, actor: str, reason: str, now: datetime | None = None) -> None:
        """Stop exporting, and drop what was waiting.

        Keeping the queue would mean a household that turned the cloud off
        still has data leave the moment somebody turns it back on. Turning it
        off means off.
        """
        self._enabled.discard(home_id)
        metrics.ENABLED.labels(home_id=home_id).set(0)
        for (queued_home, destination), queue in list(self._queues.items()):
            if queued_home == home_id:
                queue.clear()
                metrics.QUEUE_DEPTH.labels(home_id=home_id, destination=destination).set(0)
        self._record(now, home_id, "CLOUD_EXPORT_DISABLED", actor, reason)

    # ── gate 2: consent, per destination ──

    def register_destination(self, destination: Destination) -> None:
        self._destinations[destination.name] = destination

    def grant_consent(
        self,
        home_id: str,
        destination: str,
        actor: str,
        now: datetime | None = None,
    ) -> Consent:
        moment = now or datetime.now(tz=UTC)
        known = self._destinations.get(destination)
        if known is None:
            msg = f"no destination named {destination!r}"
            raise ExportRefused("UNKNOWN_DESTINATION", msg)
        consent = Consent(
            destination=destination,
            purpose=known.purpose,
            granted_at=moment,
            granted_by=actor,
        )
        self._consents[(home_id, destination)] = consent
        self._record(moment, home_id, "CLOUD_CONSENT_GRANTED", actor, known.purpose)
        return consent

    def withdraw_consent(
        self, home_id: str, destination: str, actor: str, now: datetime | None = None
    ) -> None:
        moment = now or datetime.now(tz=UTC)
        consent = self._consents.get((home_id, destination))
        if consent is not None:
            consent.withdrawn_at = moment
        queue = self._queues.get((home_id, destination))
        if queue:
            # Withdrawal is not "stop after the backlog clears".
            queue.clear()
            metrics.QUEUE_DEPTH.labels(home_id=home_id, destination=destination).set(0)
        self._record(moment, home_id, "CLOUD_CONSENT_WITHDRAWN", actor, destination)

    def has_consent(self, home_id: str, destination: str, now: datetime | None = None) -> bool:
        consent = self._consents.get((home_id, destination))
        return consent is not None and consent.is_active_at(now or datetime.now(tz=UTC))

    # ── gates 3 and 4: what may go, and what it may say ──

    def record(
        self,
        home_id: str,
        destination: str,
        payload: dict[str, Any],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Queue one record for export, or refuse and say which gate stopped it."""
        moment = now or datetime.now(tz=UTC)
        if not self.is_enabled(home_id):
            msg = "the cloud connector is disabled for this household"
            raise ExportRefused("CLOUD_EXPORT_DISABLED", msg)
        known = self._destinations.get(destination)
        if known is None:
            msg = f"no destination named {destination!r}"
            raise ExportRefused("UNKNOWN_DESTINATION", msg)
        if not self.has_consent(home_id, destination, moment):
            msg = f"this household has not consented to export to {destination!r}"
            raise ExportRefused("NO_CONSENT", msg)

        exported = self._redact(known, payload, moment)
        queue = self._queues.setdefault((home_id, destination), deque(maxlen=self.queue_limit))
        if len(queue) == self.queue_limit:
            metrics.DROPPED.labels(home_id=home_id, destination=destination).inc()
        queue.append(exported)
        metrics.QUEUE_DEPTH.labels(home_id=home_id, destination=destination).set(len(queue))
        return exported

    def _redact(
        self, destination: Destination, payload: dict[str, Any], now: datetime
    ) -> dict[str, Any]:
        exported: dict[str, Any] = {}
        for key, value in payload.items():
            if key not in destination.allowed_fields:
                continue
            if key in destination.pseudonymise:
                exported[key] = self._pseudonym(value)
            elif destination.round_timestamps_to_hour and isinstance(value, datetime):
                # An exact timestamp is a movement record. The hour is enough
                # for the diagnostics anybody has a reason to ask for.
                exported[key] = value.replace(minute=0, second=0, microsecond=0).isoformat()
            elif isinstance(value, datetime):
                exported[key] = value.isoformat()
            else:
                exported[key] = value
        return exported

    def _pseudonym(self, value: Any) -> str:
        """Stable within this hub, meaningless outside it.

        Salted with a value that never leaves, so the same device is the same
        pseudonym in every record — which is what makes a diagnostic useful —
        and nothing downstream can turn one back into a device.
        """
        digest = blake2s(f"{self.salt}:{value}".encode(), digest_size=8)
        return f"anon_{digest.hexdigest()}"

    # ── delivery ──

    def pending(self, home_id: str, destination: str) -> int:
        return len(self._queues.get((home_id, destination), ()))

    def drain(self, home_id: str, destination: str) -> list[dict[str, Any]]:
        """Hand over what is waiting. Delivery itself lives outside this class."""
        queue = self._queues.get((home_id, destination))
        if not queue:
            return []
        records = list(queue)
        queue.clear()
        metrics.QUEUE_DEPTH.labels(home_id=home_id, destination=destination).set(0)
        metrics.DELIVERED.labels(home_id=home_id, destination=destination).inc(len(records))
        return records

    def _record(
        self, now: datetime | None, home_id: str, action: str, actor: str, detail: str
    ) -> None:
        entry = {
            "occurred_at": (now or datetime.now(tz=UTC)).isoformat(),
            "home_id": home_id,
            "action": action,
            "actor": actor,
            "detail": detail,
        }
        self.audit.append(entry)
        logger.info("%s for %s by %s (%s)", action, home_id, actor, detail)
