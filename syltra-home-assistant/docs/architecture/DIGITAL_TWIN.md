# Digital Twin

The twin is the platform's answer to "what is true in this home right now?" Every
later service — Context, Adaptive, Risk, Policy — reads it rather than the raw
device stream, so its correctness is load-bearing for everything above it.

## Three states, not two

The single most important design decision here: a capability is never simply
"true or false".

| Status | Meaning | May drive a decision? |
|---|---|---|
| `UNKNOWN` | Never observed. `value` is `None`. | **No** |
| `KNOWN` | Observed, and within its freshness window. | Yes |
| `STALE` | Observed, but older than the capability allows. Value still visible. | **No** |

Collapsing `UNKNOWN` into `false` would let "we have no gas reading" be read as
"there is no gas alarm". Collapsing `STALE` into `KNOWN` would let a reading from
an hour ago confirm a live emergency. Safety invariant 4 depends on both
distinctions, so `is_usable_for_decisions()` returns true only for `KNOWN`.

Freshness is per capability, declared in `syltra_contracts.capability_definitions`
(spec §10.3): alarm sensors go stale in 120 seconds, comfort readings in 900,
battery levels in a day.

Device availability follows the same rule: `available` is `None` until observed —
unknown availability is not "offline".

## Determinism

The projection (`syltra_digital_twin.core.TwinProjection`) is a pure state
machine — events in, state out, no I/O. That is what makes the acceptance
criteria testable:

- **Identical sequence ⇒ identical state.** Verified by comparing SHA-256
  fingerprints of the resulting state.
- **Order-independent.** Events carry `occurred_at`; the newest observation per
  capability wins. A property-based test shuffles the stream and asserts
  convergence, which is what makes replay and redelivery safe.
- **Duplicates inert.** Applying the same `event_id` twice changes nothing
  (safety invariant 10).
- **Older loses.** An event predating the stored observation is ignored — unless
  it carries `metadata.correction`, the explicit escape hatch for a producer
  that needs to supersede bad data.

The fingerprint deliberately covers observable state (values, units, rooms,
membership) and excludes transport artifacts (event ids, receive timestamps), so
two hubs that saw the same home agree even though their plumbing differed.

## Storage

Two tables, two purposes (spec §13.1):

- **`device_events`** — append-only history. `UNIQUE(event_id)` makes storage
  idempotent: a redelivered event is skipped, not double-applied. A database
  trigger rejects `UPDATE` and `DELETE` outright, so recorded history cannot be
  rewritten by any service or future bug. `audit_events` carries the same trigger.
- **`device_current_states`** — one row per device capability, upserted. Current
  state never lives in the history table and history never lives in the current
  state.

Replay reads history ordered by `(occurred_at, event_id)`. The `event_id`
tiebreak matters: without it, two events sharing an instant could replay in
different orders on different runs and a "deterministic" rebuild would not be.

## Rebuild and restart

`DigitalTwinService.restore()` rebuilds the entire in-memory projection from
stored events at startup. A restarted service reaches the same fingerprint it
had before — verified in `tests/integration/test_twin_pipeline.py` by starting a
second service instance against the same database.

This means the twin is recoverable from history alone; it never depends on the
event bus retaining anything.

## Multi-home isolation

State is keyed by `home_id` at every level: projection, snapshot, storage query,
and API path. There is no read path that can return one home's device to another
home's request — asking for a foreign device returns 404, not another household's
data.

## Published events

The twin emits `twin.state.updated` on `syltra.twin.home.{home_id}.updated`, but
**only when observable state actually changed**. A device re-reporting the same
value is not an event; consumers are not woken by no-ops. Each published event
carries `causation_id` pointing at the device event that caused it, so a later
recommendation can be traced back to the observation behind it.

## Read APIs

Served by the twin for internal consumers; the authenticated public surface is
the Local API Gateway (Phase 7).

```text
GET /v1/homes/{home_id}/twin
GET /v1/homes/{home_id}/rooms
GET /v1/homes/{home_id}/devices
GET /v1/homes/{home_id}/devices/{device_id}
GET /v1/homes/{home_id}/devices/{device_id}/capabilities/{capability}
GET /v1/homes/{home_id}/stale
GET /health/live, /health/ready, /metrics
```

The capability endpoint reports `status`, `observed`, `age_seconds` and
`usable_for_decisions` explicitly, so a caller cannot accidentally treat unknown
or stale data as current. `/stale` lists everything past its freshness window —
an operator view that also feeds the sensor-degradation checks later phases use
to suspend adaptive behavior.
