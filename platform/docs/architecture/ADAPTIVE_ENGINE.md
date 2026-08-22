# Adaptive Engine

This is where machine learning enters SYLTRA, and therefore where the platform's
central safety claim has to hold: **a model can propose, never act.**

## Why a model cannot reach a device

Not by policy or convention — by type. The engine's only output is a
`Recommendation`, which carries a target and a proposed value but no dispatch
mechanism of any kind. Reaching an actuator requires three separate objects:

```text
Recommendation  →  PolicyDecision  →  ActionRequest  →  device
   (Phase 4)         (Phase 5)          (Phase 5)
```

Each is produced by a different service. There is no method on `Recommendation`
that executes anything, and no method on the engine that calls a device. A test
asserts this structurally rather than trusting the reading (safety invariant 1).

Three more properties are enforced in code rather than documented as intentions:

| Invariant | How it is enforced |
|---|---|
| A model cannot raise its own permission level (14) | The learning mode lives on the *home*, and `can_transition` only permits single-step moves. `OBSERVE → AUTHORIZED_AUTOMATION` raises. |
| A version cannot activate without evaluation and explicit promotion (15) | `ModelVersion` cannot be constructed without evaluation metrics; `promote()` is a separate recorded act that refuses versions failing their gate. |
| A model cannot propose an unsafe value | `Recommendation` validates `proposed_value` against the capability's declared domain, so a 45 °C setpoint fails at construction. |

## The learning ladder (spec §19.2)

```text
DISABLED → OBSERVE → SHADOW → RECOMMEND → APPROVAL_REQUIRED → AUTHORIZED_AUTOMATION
                        ↓          ↓              ↓                    ↓
                    SUSPENDED ←────┴──────────────┴────────────────────┘
                        ↓
                     OBSERVE   (recovery re-enters low and earns its way back)
```

Every rung is one step. Phase 4 ships homes in **SHADOW**: models train, predict,
and record — but shadow recommendations are published to a *separate subject*
(`syltra.ai.home.{home}.shadow`), never the live recommendation subject the rest
of the platform consumes, and each is flagged `shadow: true` so
`is_actionable_at()` returns false regardless of expiry.

## The three baselines

Each declares the minimum data it needs, and **refusal is a normal outcome**
(spec §14.4). A refusal explains itself and registers nothing.

| Model | Method | Minimum data | Why this method |
|---|---|---|---|
| **Routine** | Weekday × 30-minute buckets, exponentially weighted by recency (`0.97^days`) | 30 samples, 7 days, 3 buckets | Households change; last week's pattern should outweigh last month's |
| **Temperature preference** | Ridge regression on cyclical hour, weekend flag, and indoor temperature | 20 samples, 5 days, 3 buckets | Small correlated household data makes unregularized fits swing wildly; a modest wrong answer is the right failure mode for something proposing temperatures |
| **Energy anomaly** | Modified z-score from median and MAD | 50 samples, 3 days, 6 buckets | Power history *contains* the spikes being detected, so mean and standard deviation are dragged upward by the anomalies themselves; median and MAD are not |

Two details worth knowing:

- The temperature model uses **cyclical hour encoding** (sin/cos), so 23:00 and
  01:00 are near neighbours rather than opposite extremes. Its output is always
  clamped to the capability's declared 16–30 °C range, so even a badly
  extrapolating fit cannot propose an unsafe setpoint.
- The energy model **floors MAD** at a small epsilon. A perfectly flat history
  has MAD 0, which would make every deviation infinitely anomalous; the floor
  turns that into "uninformative" instead of a false-positive generator.

### Sufficient data is checked twice

The global requirement counts every event in the home. That is not enough: a
frame can hold thousands of rows and still contain nothing a *particular* model
can learn from — plenty of light switches, no power readings. Each model
therefore re-checks its own capability and raises `InsufficientCapabilityData`,
which routes through the same refusal path. Without that second check a model
reports itself trained while holding no parameters, and crashes on first use.

## Feature pipeline

Polars (ADR-006), with a **versioned schema**: every model records the
`FEATURE_SCHEMA_VERSION` it trained against, and frames are validated against
the declared column names and types before use. Extraction is deterministic —
rows sorted by `(occurred_at, device_id, capability)` — because "reproducible
training" is otherwise unverifiable. Conversion to NumPy happens at the
scikit-learn boundary, where column order is pinned explicitly so a reordered
frame cannot silently feed features into the wrong positions.

## Artifacts and serving

ONNX is the portable artifact and ONNX Runtime the local engine (spec §7.5).
Export **verifies round-trip equivalence before writing**: if the exported
artifact disagrees with the estimator it came from by more than the tolerance,
the file is deleted and the export fails. An artifact that disagrees with the
model it claims to be is worse than no artifact, because it would pass every
downstream check while being wrong.

Inference validates both directions: wrong feature count, non-finite input, and
non-finite or wrong-shaped output all raise rather than propagate a
plausible-looking poison value into a recommendation.

## Registry, promotion and rollback

Per home (spec §14.4) — one household's model can never serve another.

- `register()` records a version as `TRAINED`. It does not serve.
- `promote()` refuses any version failing its **evaluation gate**: comfort needs
  MAE below 1.5 °C, routine needs at least one established slot, energy must
  flag at most 10% of its own training data. "Evaluated" means "evaluated *and
  passed*".
- `rollback()` restores the previous active version.
- `suspend()` withdraws a version on drift, degradation or a safety event
  (spec §19.4) without needing a replacement ready.

Every act is audited with actor and reason. Each version carries a **model card**
stating, in the same language for every model, that its output is never an
actuator command and that life-safety decisions are out of scope.

## Interfaces

Consumes `syltra.normalized.>`. Publishes to `syltra.ai.home.{home}.shadow` in
shadow mode, `syltra.ai.home.{home}.recommendation` from RECOMMEND upward.

```text
GET  /v1/homes/{home_id}/models
GET  /v1/homes/{home_id}/models/{name}/card
GET  /v1/homes/{home_id}/recommendations/shadow
GET  /v1/homes/{home_id}/audit
POST /v1/homes/{home_id}/train
POST /v1/homes/{home_id}/learning-mode        # 409 on a lifecycle skip
POST /v1/homes/{home_id}/models/{name}/promote   # 409 below the gate
POST /v1/homes/{home_id}/models/{name}/rollback
POST /v1/homes/{home_id}/models/{name}/suspend
```

The only mutations are lifecycle acts, and every one is an explicit human
decision the API records — never something a model performs for itself.
