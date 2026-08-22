# Context Engine

The twin says *what is true*. The Context Engine says *what is happening* —
someone is home, the kitchen is in use, the house is quiet. Everything above it
(Adaptive, Risk, Policy) reads contexts rather than re-deriving them, so its
honesty about uncertainty is what keeps later decisions safe.

## Deterministic rules, before any model

Spec §14.3 requires deterministic rules *ahead of* ML inference, and this
service contains no machine learning at all. Every rule is a pure function of
twin state plus the evaluation time. Two consequences matter:

- Contexts stay **explainable** — each one names the rule that produced it
  (`rule:home_occupied@1.0.0`) and the observations behind it.
- Contexts stay **available** when model services are down (safety invariant 7).

Phase 4 may add probabilistic refinement on top, but never underneath: a model
can raise confidence in a context the rules already support, not invent one.

## The three things every context must carry

| Field | Why it is mandatory |
|---|---|
| **Evidence** | An inference with no traceable basis cannot be explained to a user or audited later. The contract rejects a context with an empty evidence list outright. |
| **Confidence** | Distinguishes "two independent sensors agree" from "one sensor, and the other is stale". |
| **Expiry** | A context must never outlive the data justifying it. |

Confidence is not decoration. Each rule starts from a base value and **loses**
0.25 for every required signal that is missing or stale. `HOME_OCCUPIED` from
motion *and* a presence tracker scores 0.95; from motion alone, 0.70. A consumer
can act on the difference.

Expiry is derived from the evidence, never chosen freely:
`expires_in = min(freshness window of the contributing capabilities)`. Because
`occupancy.motion` goes stale after 300 seconds, an occupancy context expires
within 300 seconds of its last supporting reading. Transient contexts
(`ARRIVING`, `LEAVING`) are shorter still — five minutes — because they describe
a moment, not a standing condition.

## The rules

| Context | Fires when | Notes |
|---|---|---|
| `HOME_OCCUPIED` | Fresh motion, or a presence tracker at home | Confidence rises when both agree |
| `HOME_EMPTY` | Every usable occupancy signal says absent | Requires ≥1 usable signal — no data means *unknown*, not *empty* |
| `ROOM_OCCUPIED` | Fresh motion in a room | One per room; overlapping by design |
| `ARRIVING` | Presence turned home + entry contact opened | 5-minute window |
| `LEAVING` | Presence away + entry contact opened | 5-minute window |
| `QUIET_HOURS` | Clock inside the household window | Evidence is the window, not the instant |
| `SLEEPING` | Quiet hours + occupant home + no motion + lights off + dark | Deliberately conservative |
| `COOKING` | Kitchen occupancy + power or humidity signature | Room-scoped |
| `HIGH_ENERGY_USAGE` | Whole-home power above threshold | |
| `POSSIBLE_WATER_LEAK` | Certified leak detector wet | **Advisory only** |
| `POSSIBLE_GAS_RISK` | Certified gas alarm active | **Advisory only** |
| `CHILD_PRESENT` | A household-designated child tracker at home | Never biometric or camera-derived (spec §3) |
| `DEVICE_CONNECTIVITY_DEGRADED` | Devices offline or readings stale | Confidence scales with the affected fraction |

### Advisory-only contexts

`POSSIBLE_GAS_RISK` and `POSSIBLE_WATER_LEAK` carry `advisory_only: true` in
both the record metadata and the API response. They may raise awareness and let
the Risk Engine enter `WATCH` or `PRE_ALERT` — they can never confirm an
emergency or trigger an action. Confirmed response follows deterministic rules
against certified alarm capabilities (safety invariants 6 and 18). A consumer
can tell a watch signal from a fact without knowing any rule internals.

Because these rules read the twin, safety invariant 4 falls out naturally: a gas
reading past its 120-second freshness window is not `KNOWN`, so no risk context
can be raised from it.

## Lifecycle

Contexts are keyed by `(type, scope)` — `home` or `room:{room_id}` — and
overlap freely. A kitchen can simultaneously be `HOME_OCCUPIED`,
`ROOM_OCCUPIED:kitchen` and `COOKING:kitchen`.

| Transition | Meaning |
|---|---|
| `STARTED` | The context did not exist (or had expired) and now holds |
| `UPDATED` | Still holds, and something material changed |
| `ENDED` | Its rule stopped firing — evidence withdrawn |
| `EXPIRED` | Nothing refreshed it before `expires_at` |

A continuing context keeps its `context_id` and `started_at` across updates, so
a consumer can follow "this occupancy episode" rather than seeing a new
inference every few seconds.

**Publication is on material change only** (spec §14.3): a confidence move of at
least 0.1, a change in reason codes, or a change in the evidence set. Re-
confirming the same context with the same evidence publishes nothing. Without
this, a home with an active motion sensor would emit a context event every few
seconds forever.

Two mechanisms end a context, and both are needed. `ENDED` comes from
evaluation — the rule no longer fires, so the inference is withdrawn
immediately rather than lingering until expiry. `EXPIRED` comes from a periodic
sweep, which is what handles sensors that simply go *silent*: an event-driven
engine alone would leave contexts standing forever after the last event.

## Interfaces

Consumes `syltra.normalized.>`, maintains its own twin projection, publishes
`context.updated` on `syltra.context.home.{home_id}.updated`.

```text
GET /v1/homes/{home_id}/contexts/current
GET /health/live, /health/ready, /metrics
```

The API returns every active context with its full evidence chain, confidence,
`seconds_until_expiry`, producing rule, reason codes, and the `advisory_only`
flag.

Metrics: `syltra_context_active`, `syltra_context_mean_confidence`, and
`syltra_context_changes_total{context_type,kind}` — the last of which makes
context churn visible, an early signal of a flapping sensor.
