# Event Model

How state becomes knowledge in SYLTRA. Contracts live in `libs/contracts`
(`syltra_contracts`); transport helpers in `libs/eventing` (`syltra_eventing`).

## Envelope

Every event on the bus uses the envelope defined in spec §11.1 and implemented as
`syltra_contracts.EventEnvelope`. It is immutable (frozen), validated at both the
publisher and consumer boundary, and preserves unknown optional fields so a relay
never destroys information it does not yet understand.

Enforced invariants:

| Rule | Where |
|---|---|
| Unknown `event_type` rejected | `EventEnvelope._known_event_type` |
| Incompatible major `schema_version` rejected | `EventEnvelope._compatible_schema_version` |
| Timestamps must be timezone-aware (UTC storage) | `EventEnvelope._timezone_aware` |
| `quality` constrained to 0.0–1.0 | field constraint |
| Unknown optional fields preserved | `extra="allow"` |
| Immutable after construction | `frozen=True` |

## Two streams, deliberately separate

Spec §11.3 requires raw and normalized event streams to stay separate:

- **Raw** (`syltra.raw.…`) — the device's own words: the Home Assistant state
  string plus attributes, with `capability = null`. Kept for diagnosis and replay.
- **Normalized** (`syltra.normalized.…`) — canonical capability readings that the
  intelligence layer consumes. A vendor entity name never appears here as a
  semantic dependency.

One Home Assistant `state_changed` event produces exactly one raw envelope and
zero or more normalized envelopes (a light yields both `light.power` and
`light.brightness`; an unmapped entity yields none). All of them share one
`correlation_id`, so a decision can be traced back to the exact observation.

## Subjects and streams (spec §12)

| Stream | Subjects | Retention | Why |
|---|---|---|---|
| `SYLTRA_RAW` | `syltra.raw.>` | 24h | High frequency, lowest value over time |
| `SYLTRA_NORMALIZED` | `syltra.normalized.>` | 7d | Twin/context/model input |
| `SYLTRA_DERIVED` | `syltra.twin.>`, `context`, `ai`, `risk`, `policy`, `action`, `feedback` | 30d | Explanation and audit |
| `SYLTRA_SYSTEM` | `syltra.system.>` | 3d | Hub and service health |
| `SYLTRA_DEADLETTER` | `syltra.deadletter.>` | 7d | Poison events with reason codes |

Retention is configurable per stream (`ensure_streams(max_age_overrides=…)`), which
is how per-privacy-class retention is tuned without code changes.

Identifiers embedded in subjects pass through `sanitize_token`, which maps
NATS-reserved characters (`.`, whitespace, `*`, `>`) to `_` and **rejects**
identifiers with no alphanumeric content — those would otherwise collapse onto one
placeholder token and route distinct devices onto the same subject.

## Delivery guarantees

- **Duplicates.** Two layers. In the Edge Agent, an identity of
  `(entity_id, occurred_at, state)` suppresses re-delivery before publishing. On
  the wire, `Nats-Msg-Id` carries the immutable `event_id`, so JetStream
  deduplicates inside a 120s window. Together these support safety invariant 10:
  duplicate events must not produce duplicate actions.
- **Out-of-order.** An event older than the newest seen for its entity is still
  published (history has value) but flagged: `metadata.out_of_order = true` and
  `quality` reduced to 0.5, so downstream consumers can discount it. It never
  overwrites newer state in the twin (Phase 2).
- **Invalid events.** Structurally invalid payloads never enter the normalized
  stream. They go to `syltra.deadletter.{service}` as a `DeadLetterRecord` with
  reason codes (`MISSING_ENTITY_ID`, `MISSING_STATE`, `INVALID_ENTITY_ID`,
  `NON_NUMERIC_SENSOR_VALUE`) and a bounded copy of the payload.
- **Unmapped entities.** Entities outside the canonical capability model are
  *rejected*, not guessed into a capability. They appear in the raw stream only.

## Freshness and quality

Every envelope carries `quality` (0.0–1.0) and `metadata.freshness_ms`
(receive time minus report time). These feed the staleness rules that later
phases depend on — spec safety invariants 3 and 4 require that a stale
recommendation cannot execute and a stale sensor value cannot confirm a risk.

## Privacy

Every event carries a `privacy_class`. Device events default to
`HOUSEHOLD_PRIVATE`, which stays local: no cloud path exists in the platform
today, and the Cloud Connector (Phase 8) is allowlist-driven and disabled by
default.
