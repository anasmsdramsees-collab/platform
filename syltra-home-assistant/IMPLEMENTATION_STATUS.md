# SYLTRA Adaptive Edge Platform — Implementation Status

Tracks progress against `SYLTRA_Claude_Code_Master_Build_Spec.md` Section 22.
Updated after every completed task. A phase is marked complete only when every
acceptance criterion passes.

Legend: ✅ done · 🔄 in progress · ⬜ not started · ⚠️ blocked/stub

## Phase overview

| Phase | Objective | Status |
|---|---|---|
| 0 | Repository foundation | ✅ complete (2026-08-18) |
| 1 | Infrastructure and Home Assistant connection | ✅ complete (2026-08-18) |
| 2 | Contracts and Digital Twin | ✅ complete (2026-08-18) |
| 3 | Context Engine | ✅ complete (2026-08-18) |
| 4 | Adaptive Engine in shadow mode | ✅ complete (2026-08-18) |
| 5 | Recommendations, policy, and actions | ✅ complete (2026-08-19) |
| 6 | Risk and safety | ✅ complete (2026-08-19) |
| 7 | Local API, console, and SILA interface | ✅ complete (2026-08-19) |
| 8 | Pilot hardening | ✅ complete (2026-08-19) |

**Current quality gate:** 739 unit/contract + 94 integration + 13 end-to-end tests
passing · 275 safety tests · 93% branch coverage · ruff + mypy `--strict` clean
across 151 source files · bandit clean · 21/21 simulator scenarios pass.

**All eight phases are complete.** The MVP definition of done (spec §32) is
assessed at the end of this document.

## Phase 0 — Repository foundation ✅

Structure per spec §8, `uv` workspace on pinned Python 3.12.13, Docker Compose
skeleton, all spec §9 Makefile targets, path-filtered CI, and ADR-001 (Home
Assistant as replaceable runtime), ADR-002 (uv + Python 3.12), ADR-003 (platform
and website coexistence). All acceptance criteria passed: bootstrap on a clean
machine, lint and tests green, no secrets committed, documentation explains the
next phase.

## Phase 1 — Infrastructure and Home Assistant connection ✅

Home Assistant pinned to `2026.8.1` (ADR-004) and running unmodified; Mosquitto,
NATS JetStream and PostgreSQL on a private network with loopback-only ports; the
Edge Agent connecting over the supported WebSocket API; capability mappings for
10 Home Assistant domains; the `DeviceIntegrationGateway` interface with its
`HomeAssistantDeviceGateway` adapter; `libs/eventing` and `libs/observability`;
and a deterministic simulator with 17 virtual devices behind a mock Home
Assistant boundary.

All acceptance criteria passed, including: normalized events reaching JetStream
(verified against a live server), reconnect after a Home Assistant restart
(backoff 1.1 → 2.2 → 3.8 → 8.1s, capped, while staying live at 503 not-ready),
invalid events routed to the dead-letter stream with reason codes, and the Home
Assistant token appearing **0 times** in logs, metrics and published events.

## Phase 2 — Contracts and Digital Twin ✅

| Deliverable | Status | Notes |
|---|---|---|
| Versioned schemas | ✅ | JSON Schema generated from the Pydantic models into `contracts/jsonschema/v1.0/` (9 documents). `make contracts` regenerates; a contract test and a CI step fail the build on drift. |
| Complete capability definitions (spec §10.3) | ✅ | All 31 capabilities declare data type, unit, range/enum, access, safety class, freshness, reversibility and confirmation level. |
| Database migrations | ✅ | Alembic migration creating 14 tables of the spec §13 model, with UUID keys, value constraints, idempotency uniqueness, and append-only enforcement. |
| Digital Twin Service | ✅ | `services/digital-twin`: pure projection, persistence, durable JetStream consumer, `twin.state.updated` publication, read APIs, health and metrics, Dockerfile. |
| State freshness | ✅ | Per-capability freshness windows; `UNKNOWN` / `KNOWN` / `STALE` reported distinctly, with `usable_for_decisions` gating. |
| Event replay and rebuild | ✅ | `rebuild_from_history()` reconstructs the twin from stored events; deterministic ordering by `(occurred_at, event_id)`. |
| Home, room and device APIs | ✅ | Twin, rooms, devices, single device, single capability, and a stale-capability listing. |

### Phase 2 acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| Identical event sequence produces identical twin state | ✅ | SHA-256 state fingerprints compared across independent projections; a property-based test shuffles delivery order across 25 generated orderings and asserts convergence. |
| Duplicate and out-of-order tests pass | ✅ | Duplicates inert in the projection **and** rejected by the `UNIQUE(event_id)` constraint (proven through the real database); older events never overwrite newer state, with an explicit `correction` escape hatch. |
| Multi-home isolation passes | ✅ | Verified in the projection, in storage, and across every API path; a foreign device returns 404, never another household's data. Live check: 17 devices each for `home_dev_001` and `home_pipeline`, zero cross-contamination. |
| State rebuild after reset passes | ✅ | Reset-then-replay reproduces the fingerprint; a second service instance sharing the database restores identical state (spec §14.2 restart survival). |

### Additional verification performed

- **Live end-to-end run.** Simulator → Edge Agent → JetStream → containerized
  Digital Twin → read API: **49 events applied, 17 devices, 5 rooms**, with
  capability values reported `KNOWN`; **45 current-state rows** persisted
  separately from **49 append-only history rows**; 87 `twin.state.updated`
  events on `SYLTRA_DERIVED`.
- **Append-only enforced by the database.** `INSERT` succeeds while `UPDATE` and
  `DELETE` are rejected by trigger on `device_events` and `audit_events` —
  recorded history cannot be rewritten by any service or future bug
  (safety invariant 12).
- **Unknown ≠ false.** An unobserved capability reports `UNKNOWN` with a `None`
  value and `usable_for_decisions: false`, rather than a falsy default — the
  distinction safety invariant 4 depends on.
- **Stale ≠ usable.** A two-hour-old gas reading is still visible but reports
  `STALE` and refuses to support a decision.

### Defects found and fixed during Phase 2

| Defect | Impact | Fix |
|---|---|---|
| `exclude = ["src/"]` in mypy also matched `simulator/src/` | Simulator was silently untyped | Anchored to `^src/` |
| Replay ordered only by `occurred_at` | Events sharing an instant could replay in different orders, making "deterministic" rebuild non-deterministic | Tiebreak on `event_id` |
| `upsert_current_states` called `twin.home()` twice with an unguarded `None` | Latent `AttributeError` on an unknown home | Guard once and return early |
| Bandit flagged a seeded RNG in `libs/testing` | — | Documented `# nosec` with the determinism rationale (a crypto RNG would break fingerprint comparison) |
| Compose project name collided with an unrelated `syltra-platform` project on this machine | `make up`/`down` would have adopted and recreated another project's 5-day-old PostgreSQL | Renamed project to `syltra-adaptive-edge` (documented in the compose file) |
| NATS healthcheck probed `:8222/healthz` but the monitoring port was never enabled | Container reported permanently unhealthy; both services use `depends_on: condition: service_healthy`, so `make up` would have hung indefinitely waiting for a container that could never pass | Enabled `--http_port=8222` (container-internal, not published); NATS now reports healthy |

## Phase 3 — Context Engine ✅

| Deliverable | Status | Notes |
|---|---|---|
| Deterministic initial contexts | ✅ | All 13 spec §14.3 contexts as pure rule functions. No ML participates, so contexts stay explainable and survive model outage (safety invariant 7). |
| Evidence and confidence tracking | ✅ | Every context carries its observations with provenance and status; confidence degrades 0.25 per missing or stale required signal. |
| Context expiry | ✅ | `expires_in` derived from the shortest freshness window among contributing capabilities; a periodic sweep expires contexts whose sensors went silent. |
| Simulated scenarios | ✅ | `sleep_routine`, `cooking_activity`, `empty_home`, `energy_anomaly`, `water_leak_watch`, `gas_risk_watch`, `sensor_stale` added — 14 scenarios total. |
| Context contracts | ✅ | `ContextRecord` / `EvidenceItem` in `libs/contracts`, JSON Schemas exported, evidence-required enforced at the contract layer. |
| Service, API and container | ✅ | JetStream consumer, sweeper loop, `context.updated` publication, `/contexts/current` read API, health and metrics, Dockerfile, compose entry. |

### Phase 3 acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| Each context has evidence and expiry | ✅ | Enforced by the contract (a context with no evidence is rejected) and asserted across rules, engine, API and live scenarios. |
| Missing sensors reduce confidence | ✅ | `HOME_OCCUPIED` scores 0.95 with motion + presence, 0.70 with motion alone; asserted directly. |
| Stale evidence does not remain active | ✅ | Stale motion produces no occupancy context; a gas context created while fresh disappears once the reading passes its 120s window; a sweep clears everything an hour after events stop. |
| Scenario tests pass deterministically | ✅ | 20 integration tests drive contexts from real Edge Agent output; repeated evaluation of unchanged state yields identical results and publishes nothing. |

### Additional verification performed

- **Live containerized run.** Simulator → Edge Agent → JetStream → Context
  Engine container → API produced 3 active contexts with confidence, expiry and
  evidence counts: `HOME_OCCUPIED` (0.95, 2 evidence items),
  `ROOM_OCCUPIED:living_room` (0.90), `HIGH_ENERGY_USAGE` (0.90) — all expiring
  within their 300s evidence window.
- **Lifecycle metrics observed live**: `STARTED`, `UPDATED` and `ENDED`
  transitions counted per context type, making context churn visible.
- **Advisory-only enforcement.** `POSSIBLE_GAS_RISK` and
  `POSSIBLE_WATER_LEAK` carry `advisory_only` in the record and the API, so a
  consumer can distinguish a watch signal from a fact without reading rule
  internals (safety invariants 6 and 18).
- **Scope correctness.** The `COOKING` rule does not fire when motion is in the
  living room rather than the kitchen — verified explicitly, so the rule is
  genuinely scope-aware rather than keyword-triggered.

### Defects found and fixed during Phase 3

| Defect | Impact | Fix |
|---|---|---|
| Simulator clock anchored to a fixed past epoch | Every simulated reading looked stale to freshness checks, so contexts could never form from simulator output | Clock now starts at *now* by default, with an optional fixed `start_time` for frozen-clock tests; step ordering stays deterministic |
| `QUIET_HOURS` embedded the instantaneous clock in its evidence | Evidence differed on every evaluation, so the material-change check would republish the context continuously for the whole quiet-hours window | Evidence records the window, not the instant |
| `syltra_context_engine` package had no `__init__.py` | mypy resolved its modules twice under different names; the package was not importable as intended | Added the package `__init__.py` with its public surface |
| Two services each defined `tests/test_api.py` | pytest and mypy both failed on the duplicate module name | Renamed to `test_twin_api.py` / `test_context_api.py`; pytest also switched to `--import-mode=importlib` to prevent recurrence |


## Phase 4 — Adaptive Engine in shadow mode ✅

| Deliverable | Status | Notes |
|---|---|---|
| Feature pipeline | ✅ | Polars (ADR-006) with a versioned schema; deterministic row ordering; NumPy conversion pins column order at the scikit-learn boundary. |
| Routine baseline | ✅ | Weekday × 30-minute buckets, exponentially weighted by recency (`0.97^days`). |
| Temperature preference baseline | ✅ | Ridge regression on cyclical hour, weekend flag and indoor temperature; output clamped to the capability's declared 16–30 °C range. |
| Energy anomaly baseline | ✅ | Modified z-score from median and MAD — robust statistics first, as spec §14.4 orders. MAD floored so a flat history is uninformative rather than a false-positive generator. |
| Model registry | ✅ | Per-home versions with evaluation gates, promotion, rollback, suspension, and an audited lifecycle. |
| Model cards | ✅ | Every version carries one, with shared safety language: output is never an actuator command; life-safety decisions are out of scope. |
| ONNX export and inference | ✅ | Export verifies round-trip equivalence before writing and deletes the artifact if it disagrees with its estimator; inference validates shape, feature count and finiteness both ways. |
| Shadow recommendations | ✅ | Published to a separate `syltra.ai.home.{home}.shadow` subject, flagged `shadow: true`, never actionable. |

### Phase 4 acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| Models never dispatch actions | ✅ | Enforced by type: the engine's only output is `Recommendation`, which has no dispatch surface; reaching a device needs `PolicyDecision` then `ActionRequest`. Asserted structurally, and shadow output is proven to never reach the live subject. |
| Training is reproducible | ✅ | Identical parameters and metrics across independent runs for all three models, with deterministic feature extraction. |
| Feature schema is versioned | ✅ | `FEATURE_SCHEMA_VERSION` recorded on every registered version; frames validated against declared column names and types. |
| Inference output is validated | ✅ | Wrong feature count, non-finite input, non-finite output and wrong result shape all raise rather than propagate. |
| Model rollback works | ✅ | Promote → promote → rollback restores the predecessor and audits it; rollback without a predecessor or active version is refused. |
| Insufficient-data behavior is tested | ✅ | All three models refuse sparse and empty histories with reason codes, refuse a single busy day for lack of day diversity, and refuse when their own capability is absent. |

### Additional verification performed

- **Live containerized run.** The adaptive-engine container started in SHADOW,
  consumed 244 published training events, trained the routine and comfort
  baselines, and registered both as `TRAINED` (not serving).
- **Lifecycle skip refused live.** `POST /learning-mode {"mode":"AUTHORIZED_AUTOMATION"}`
  from SHADOW returned **HTTP 409** with
  `"the adaptive lifecycle must advance one stage at a time (spec §19.2)"`.
- **Promotion is an explicit human act.** Models remained `TRAINED` until an
  operator promoted one; the audit trail recorded `MODEL_REGISTERED` ×2 (by
  `adaptive-engine`) and `MODEL_ACTIVATED` (by `operator`).
- **Evaluation gates enforced.** A version with MAE 99.0 was refused promotion
  (HTTP 409, `PROMOTION_REFUSED`) — "evaluated" means "evaluated *and passed*".

### Defects found and fixed during Phase 4

| Defect | Impact | Fix |
|---|---|---|
| Per-capability data shortfalls were a silent early return, not a refusal | **Found live**: `energy_anomaly` reported `trained=True` on a 244-event history containing no power readings at all, registering a model with no baseline that would have raised `KeyError` on its first `predict()`. The global data requirement counts every event in the home, so an ample frame can still hold nothing a particular model can learn from. | `InsufficientCapabilityData` raised from `_fit` routes through the same refusal path as sparse data; all three models re-check their own capability. Verified live: the same history now yields `REFUSED: INSUFFICIENT_POWER_SAMPLES`. Four regression tests added. |
| `syltra_adaptive_engine` package had no `__init__.py` | Package installed but not importable; the editable install had to be rebuilt after the file was added | Added the package `__init__.py` with its public surface (same class of defect as the context engine's in Phase 3 — worth watching for on every new service) |
| Polars schema dict typed as `dict[str, pl.DataType]` | mypy rejected it: Polars schemas mix dtype *instances* (`Datetime`) with dtype *classes* (`String`) | Introduced a `PolarsDataType` union alias |
| `make test` ran the integration suite too | Spec §9 scopes `make test` to unit and contract tests; running everything made it depend on a live stack and its credentials | Scoped to `libs services simulator`; `make test-safety` and `make test-integration` source `.env` |
| Integration test fixtures carried literal password fallbacks (`devonly-pg-pass`, `devonly-nats-pass`) | A default password in a checked-in file is still a password in the repository (spec §0 rule 8), and it would let a misconfigured run connect somewhere unintended instead of failing loudly | Credentials now come from the environment only; tests skip with a clear reason when unset, and `make test-integration` sources `.env`. Verified both paths: 77 pass with `.env`, 20 skip cleanly without it |


## Phase 5 — Recommendations, policy, and actions ✅

| Deliverable | Status | Notes |
|---|---|---|
| Recommendation lifecycle | ✅ | Recommendation → PolicyDecision → ActionRequest as three distinct types produced by three services; an `ActionRequest` cannot be constructed without a `decision_id`. |
| Feedback Service | ✅ | All six responses linked to their recommendation; asymmetric standing (trust slow to earn, quick to lose); automation-echo classification breaks the feedback loop. |
| Policy decisions | ✅ | 16 deterministic rules, ordered and short-circuiting, producing all five spec §14.6 outcomes with reason codes, evidence and a reproducible `input_hash`. |
| Action orchestration | ✅ | Idempotency, pre-dispatch re-checks, gateway dispatch, expected-state verification, bounded retry of transient failures only, compensating actions. |
| Manual override detection | ✅ | Denied at policy (recent manual control) and cancelled in flight at the orchestrator via `register_pending` / `cancel_conflicting`. |
| Comfort actions for AC, lights, curtains | ✅ | All three verified end to end against the simulator devices. |

### Phase 5 acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| No action without a valid policy decision | ✅ | Enforced by type (`decision_id` required) and re-checked at dispatch: a missing decision, any non-ALLOW outcome, an expired ALLOW, or a decision for another household all leave the device untouched. |
| Duplicate requests cause one action | ✅ | Idempotency key derived from the decision; a redelivered request returns the original result and issues exactly one device command. |
| Manual override cancels a conflict | ✅ | Verified at both layers and end to end — a person adjusting the AC a minute earlier stops the chain with `USER_CONTROL_TAKES_PRECEDENCE`. |
| Expired actions do not run | ✅ | Expired recommendations, decisions and action TTLs each block dispatch independently. |
| Result verification works | ✅ | An action succeeds only when the device reports the expected state; a dispatch that returns cleanly but does not change the device is a failure. |
| Failure and retry policy is tested | ✅ | Transient failures retried within `max_attempts`; a gateway refusal is never retried; failed reversible actions are compensated. |

### Additional verification performed

- **The full chain runs against real simulator devices** (spec §24.4): AC
  setpoint, lighting and curtain position each go recommendation → policy →
  action → device → verification, with the value read back from the mock Home
  Assistant rather than asserted from intent.
- **Approval flow proven end to end**: an untrusted home returns
  `REQUIRE_USER_APPROVAL`, the pending decision authorizes nothing, and only a
  *new* decision issued on approval permits execution.
- **`NEVER_REPEAT` closes the loop**: feedback suppression feeds the policy
  service, and the next proposal of that type is denied `SUPPRESSED_BY_USER`.
- **Life-safety escalation is categorical**: gas valve, breaker and siren
  proposals return `ESCALATE_TO_FIXED_SAFETY_RULE` at confidence 1.0, not merely
  at low confidence.
- **Correlation threads the chain**: recommendation id → decision → action
  result, with policy, orchestrator and feedback each leaving an audit entry.

### Defects found and fixed during Phase 5

| Defect | Impact | Fix |
|---|---|---|
| The orchestrator mixed an injected `now` with wall-clock reads | Preflight and the retry loop could disagree about the current time — a TTL check passing in one place and failing in another. Surfaced as eight failing tests whose actions expired mid-flight. | `execute()` pins one clock for the whole call; every time check inside uses it |
| Manual-override cancellation had no usable API | An action could only be cancelled once `execute` had already been called, so the test needed private-attribute hackery to construct a pending state — a sign the real cancellation window did not exist | Added `register_pending()` / `pending_keys()`; a caller registers intent before dispatch so `cancel_conflicting` can reach it in flight |


## Phase 6 — Risk and safety ✅

| Deliverable | Status | Notes |
|---|---|---|
| Risk-case model | ✅ | `RiskCase` with severity, confidence, evidence provenance and expiry; confirmed cases must name their rule and carry certified evidence. |
| Fixed risk state machine | ✅ | Seven states with a declared transition table; `AI_REACHABLE_STATES` and `DETERMINISTIC_ONLY_STATES` are disjoint. |
| Gas, water, energy, sensor-health, connectivity scenarios | ✅ | Eight inference rules across all nine spec §14.5 categories, plus five new simulator scenarios (21 total). |
| Safety Governor | ✅ | Five deterministic confirmation rules over certified alarm capabilities, with freshness, replay and clock-skew guards. |
| Safety-case documentation | ✅ | `SAFETY_CASE.md` maps all 18 invariants to code, tests, logs and operator controls, and records four known gaps honestly. `RISK_STATE_MACHINE.md` documents the machine. |
| Development blocks for critical actuators | ✅ | Enforced independently in the gateway and the orchestrator (Phase 5), with the governor's named-response bounds above them. |

### Phase 6 acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| AI only creates watch and pre-alert states | ✅ | Three independent mechanisms: the transition guard raises on any inference attempt at `CONFIRMED`; `RiskProposal` cannot be *constructed* with a confirmed state; and `RiskCase` validation rejects a confirmed case lacking certified evidence. |
| Confirmed actions require deterministic conditions | ✅ | Confirmation requires origin, capability, freshness, absolute age, clock sanity and value — all six, from a fixed five-rule table. |
| Safety tests pass without the Adaptive Engine | ✅ | A fresh-interpreter subprocess test asserts the governor's import closure contains none of `sklearn`, `onnxruntime`, `skl2onnx`, `polars` or `syltra_adaptive_engine`. 187 of 188 safety tests need no infrastructure whatsoever. |
| Replayed historical alarms cannot trigger live actions | ✅ | Absolute age is checked *separately from* the capability freshness window, so a generous window cannot become a replay loophole. A week-old alarm confirms nothing. |
| Loss of cloud has no local safety impact | ✅ | Confirmation and risk evaluation both run with `socket.socket` disabled entirely — any accidental network call raises rather than silently degrading. |
| All safety invariants map to tests | ✅ | All 18 mapped in `SAFETY_CASE.md`, each naming the code, the tests, the log lines and the operator control. |

### Additional verification performed

- **Verified independence rather than mocked it.** The degraded-mode tests build
  the safety path with nothing else present instead of stubbing dependencies —
  a mock would prove the code tolerates a stub; building without them proves the
  dependency does not exist.
- **Context adjusts confidence but never silences a hazard.** A gas alarm during
  cooking is raised at lower confidence, not suppressed; in an empty home it is
  raised at CRITICAL.
- **The protection-gap case.** Stale safety sensors open a `DEVICE_FAILURE` case
  at HIGH severity — the risk nobody looks for is a home that seems quiet
  because the sensors that would say otherwise stopped reporting.
- **Unknown occupancy is not empty.** The intrusion rule fires only on
  `occupied is False`, never on `None`.

### Defects found and fixed during Phase 6

| Defect | Impact | Fix |
|---|---|---|
| A single evaluation emitted both an advisory `OPENED` and a `CONFIRMED` change for the same hazard | Consumers would see a `PRE_ALERT` that never really held — a UI flash, and a misleading entry in any transition history | A confirmation in the same pass supersedes the advisory change; consumers see one transition, to the state that actually applies |
| `SAFETY_CASE.md` initially claimed 156 safety tests and "no infrastructure required" | Both were wrong: the count was 188, and one test does need NATS | Corrected to 188, with the precise claim (187 need nothing but Python) and the exact command to reproduce it |


## Phase 7 — Local API, console, and SILA interface ✅

| Deliverable | Status | Notes |
|---|---|---|
| Local API Gateway | ✅ | The spec §21 endpoint set, token authentication, home-scoped authorization, WebSocket streaming, OpenAPI, pagination and per-route rate limits. Composed from in-process read models, so no endpoint can leak a broker subject or a database shape. |
| Arabic RTL and English LTR console | ✅ | Self-contained HTML/CSS/JS (ADR-007) served by the gateway. CSS logical properties throughout, so Arabic is genuine mirroring rather than a stylesheet fork. |
| Live home state | ✅ | Twin, rooms, devices, contexts with evidence — verified live in both languages. |
| Recommendations and explanations | ✅ | Every response carries `reason_codes` for machines and translated `reasons` for people. |
| Risk view | ✅ | Advisory cases labelled as advisory in both languages; confirmed cases name the deterministic rule. |
| Approval and feedback flows | ✅ | Approve, reject, not-now, never-repeat — each routed through policy, with `NEVER_REPEAT` feeding the suppression list. |
| Structured SILA intent interface | ✅ | A closed vocabulary of nine typed intents; `extra="forbid"` so free text cannot be smuggled alongside a valid intent. |
| `syltra_edge` HA integration (spec §27) | ✅ | Diagnostic-only integration: config flow, health coordinator, redacted diagnostics, ar/en translations, one SYLTRA-specific service. |
| `libs/security` | ✅ | Roles, permissions split by consequence, home-scoped authorization, hashed short-lived tokens. |

### Phase 7 acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| Authorization isolates homes and roles | ✅ | A foreign home returns **404, not 403** — "forbidden" would confirm the home exists. Role separation verified per endpoint; `ACT_SAFETY` belongs to no role at all. |
| The UI works in Arabic RTL and English LTR | ✅ | Verified live in a browser: brand, tabs, cards and status borders all mirror; Arabic reason codes render with technical English terms correctly aligned inside them. |
| SILA cannot bypass policy | ✅ | Structural: SILA holds no gateway. A manual request becomes a `Recommendation`, goes to policy, and reports the decision — `executed` is always False on that path. |
| Reason codes are translated | ✅ | A contract test extracts reason codes from the source by AST and fails if any is untranslated; it caught two missing entries during the build. |
| Accessibility checks pass | ✅ | Skip link, tablist pattern with arrow-key navigation that respects reading direction, labelled controls, polite live region, visible focus, zoom permitted, colour never the only status signal. |

### Additional verification performed

- **Live browser verification in both languages.** The console was driven
  against a seeded platform: English LTR and Arabic RTL screenshots confirm true
  mirroring, and the contexts view shows translated reason codes
  ("تم رصد حركة") beside evidence rendered with technical English capability
  names — the mixed-script alignment spec §28 asks for.
- **No internal detail leaks.** A test sweeps every read endpoint for
  `nats://`, `postgresql`, subject names, `jetstream` and SQL fragments.
- **The console cannot render untrusted values as markup.** Everything from the
  API goes through `textContent`; `innerHTML`, `insertAdjacentHTML`,
  `document.write` and `eval` are absent from the code.
- **Shadow recommendations are not actionable in the UI** — their buttons are
  disabled, matching the policy layer's refusal.

### Defects found and fixed during Phase 7

| Defect | Impact | Fix |
|---|---|---|
| A module-level `assert` enforced "no role holds ACT_SAFETY" | **`python -O` strips assert statements**, so the guarantee would silently vanish in an optimised production image — a safety rule that disappears under a compiler flag is not a rule. Found by bandit. | Replaced with an import-time `raise`; a regression test runs a subprocess under `-O` and asserts the guarantee still holds |
| `create_app(tokens=...)` used `tokens or TokenStore()` | `TokenStore` defines `__len__`, so an **empty store is falsy** and the caller's store was silently discarded — every token it later issued was unknown to the app. Surfaced as blanket 401s. | `TokenStore() if tokens is None else tokens`, with the trap documented at the site |
| Two `conftest.py` files resolved to the same module name | mypy refused to check the repository at all | Made the `tests/` tree a package so each module has a unique dotted path |
| The HA integration's pure logic was only reachable by AST surgery in tests | Validation and redaction could not be tested without installing Home Assistant, which ADR-001 forbids as a dependency | Extracted `validation.py` with no Home Assistant imports; `config_flow` and `diagnostics` delegate to it |


## Phase 8 — Pilot hardening ✅

| Deliverable | Status | Notes |
|---|---|---|
| Deterministic pilot configuration | ✅ | Compose with restart policies; `SYLTRA_ENVIRONMENT` gates critical actuators. |
| Encrypted backup and restore | ✅ | AES-256-GCM with scrypt key derivation; no plaintext code path; manifest authenticated as AAD; `0600`. |
| Service watchdogs | ✅ | `libs/operations/watchdog.py` supervises every service; `edge-agent`, `risk-engine` and `policy-safety` are critical and alert on restart. Closes the last `SAFETY_CASE.md` gap. |
| Resource limits | ✅ | Per-service memory and CPU, with a guaranteed reservation for the Risk Engine — a safety component starved by a noisy neighbour is a safety failure. |
| Update and rollback design | ✅ (design) | `docs/architecture/DEPLOYMENT.md`; implementation is a tracked gap. |
| Observability | ✅ | Metrics on every service; `/health/live`, `/health/ready`, `/metrics` throughout. |
| Pilot runbook | ✅ | `RUNBOOK.md`, `BACKUP_RESTORE.md`, `INCIDENT_RESPONSE.md`, `PILOT_CHECKLIST.md`. |
| Privacy export and deletion | ✅ | `export_home()` and `delete_home()`; deletion **verifies** and reports incomplete if anything remains. |
| Fault-injection tests | ✅ | All eleven spec §24.7 faults, plus soak tests for unbounded growth. |
| Persistence (carried from Phase 7) | ✅ | The remaining spec §13 tables with append-only triggers on every decision and action record. |

### Phase 8 acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| Platform recovers after service and hub restart | ✅ | Every service rebuilds from the event stream; the twin is deterministic, so restart is not a risk. Watchdog restarts what stops answering. |
| Internet loss does not stop local control | ✅ | Confirmation and risk evaluation run with `socket.socket` disabled entirely. |
| Database backup and restore pass | ✅ | Round-trip test; tampered backups, swapped manifests and wrong passphrases all refused. |
| Model suspension and rollback pass | ✅ | Registry tests from Phase 4, still green. |
| Simulator runs without unbounded resource growth | ✅ | 2,000 events across 20 batches leave 4 devices; dedup window, adaptive history and risk cases all provably bounded. |
| Pilot checklist complete | ✅ | `docs/pilot/PILOT_CHECKLIST.md`, including limitations to state plainly to the household and a sign-off block. |

### Additional verification performed

- **Household data never reaches disk in the clear.** The backup test reads the
  raw bytes and asserts no household string appears.
- **The database refuses an unattributed confirmation.** A `CONFIRMED` risk case
  with no `confirmed_by` violates a check constraint — the safety invariant
  enforced in storage, not only in the contract.
- **Deletion verifies rather than assuming.** A stubborn table produces an
  incomplete report rather than a false success.
- **Diagnostic bundles carry pseudonyms, not identifiers**, salted per bundle so
  a mapping cannot be built across bundles.

### Defects found and fixed during Phase 8

| Defect | Impact | Fix |
|---|---|---|
| The new `AUDIT_STORE_UNAVAILABLE` reason code shipped untranslated | A household would have seen a raw identifier | Caught by the AST-based translation coverage test — the second time that test has paid for itself |


## Stubs and deferred items

Everything below is tracked, not forgotten. Nothing here is required by the MVP
definition of done (spec §32).

| Item | Where | Notes |
|---|---|---|
| Confirmation-authorized responses are named but not executed | `services/risk-engine` | Deliberate: no emergency actuator is operated automatically in the MVP. Wiring it requires product-owner approval (spec §0 rule 9) |
| Update and rollback implemented | `infrastructure/` | Designed in `DEPLOYMENT.md` |
| Cloud connector | `services/cloud-connector` | **Not implemented at all** — a stronger position than "disabled by default" |
| Occupancy-fusion, recommendation-acceptance and device-anomaly models | `services/adaptive-engine/models/` | Spec §14.4 models 2, 4 and 6; Phase 4 delivered the three the phase required |
| Mosquitto password file | `config/mosquitto/` | Generated when an MQTT device is first integrated |
| TimescaleDB | ADR-005 | Deferred; revisit when volumes or hardware justify it |

## Assumptions on record

- The existing Next.js website shares this repository; the platform coexists at
  the root without touching `src/` (ADR-003).
- Integration tests use a mock Home Assistant WebSocket boundary (spec §24.3
  permits this) plus a **real** NATS server and PostgreSQL database.
- All data in development and tests is synthetic (spec §26). No household data
  exists anywhere in this repository.
- Per spec §0 rule 19, **nothing has been committed**; all eight phases sit in
  the working tree awaiting explicit commit instruction.

## Environment notes

- A local `.env` was created for development (gitignored, placeholder values
  only). Real Home Assistant tokens must be generated per operator.
- An unrelated Docker Compose project named `syltra-platform` runs on this
  machine. The SYLTRA platform project is deliberately named
  `syltra-adaptive-edge` so the two can never adopt each other's containers.
- The development database holds synthetic data from test runs; `make reset-demo`
  clears demo streams and refuses to run outside a development environment.

## Post-MVP work completed

Two items from the stubs table were closed after the MVP was declared done,
because both were the kind of gap that is dangerous to leave sitting.

### Backup collection (was: stubbed)

`make backup` previously wrote a placeholder. An operator running it would have
received a file and could reasonably have believed they had a backup — the most
hazardous form of stub. The collector now reads all 20 household tables over a
real session.

| Property | Evidence |
|---|---|
| Every household table is scoped | `declared_tables()` is asserted equal to `HOUSEHOLD_TABLES`, so a table cannot be added without deciding how it is scoped |
| Every query runs against the real schema | An integration test executes all 20 against PostgreSQL — catching a renamed column or broken join that a dictionary-based test cannot see |
| One household's backup never contains another's | Asserted against a two-home fixture |
| Types survive the JSON round trip | UUIDs and timestamps checked explicitly |
| Nothing readable on disk | The raw bytes are searched for household strings |
| An empty home still backs up cleanly | A hub commissioned yesterday must not be an edge case |

Verified end to end through the CLI: **6 rows across 20 tables**, manifest
readable without the passphrase, no household strings in the file, `0600`.

### Drift detection (was: suspension existed, nothing triggered it)

All seven spec §19.4 conditions are now detected, and a drifted model suspends
itself. The design principle: **a model that has lost the household's trust
should stand itself down before anyone has to ask.**

Suspension is deliberately easier to trigger than to reverse — a suspended model
does not come back because feedback later improves, since whatever caused the
drift has not necessarily gone away. Returning requires a new version promoted
through the same gate.

### Defects found and fixed

| Defect | Impact | Fix |
|---|---|---|
| The backup integration test's skip guard caught `ModuleNotFoundError` and reported it as "PostgreSQL unavailable" | The missing sync driver made 8 tests **skip while looking green** — a skip for the wrong reason proves nothing | The driver is now a real dependency; the guard narrowed to connection failures only, so a broken environment fails loudly |
| f-string SQL in the collector | Bandit flagged it. The table name was allowlist-derived, but "it's validated" is the argument behind every injection | Added an identifier check immediately before interpolation as a second, independent defence, plus three tests attacking it directly |


## MVP definition of done (spec §32)

| # | Criterion | Status |
|---|---|---|
| 1 | A clean machine starts the development stack using documented commands | ✅ `make bootstrap` then `make up` |
| 2 | The simulator provides all required devices and scenarios | ✅ 17 virtual devices, 21 scenarios |
| 3 | Home Assistant state changes become normalized events | ✅ verified live against a real HA container |
| 4 | The Digital Twin rebuilds deterministically from events | ✅ SHA-256 fingerprint equality, property-tested |
| 5 | Contexts include confidence, evidence and expiry | ✅ enforced by the contract |
| 6 | Adaptive models run locally in controlled lifecycle modes | ✅ ONNX Runtime, the §19.2 ladder enforced one rung at a time |
| 7 | Recommendations are explainable and never execute directly | ✅ enforced by type |
| 8 | Policy and Safety gate every action | ✅ re-checked at dispatch, not trusted |
| 9 | The Action Orchestrator verifies outcomes and detects manual overrides | ✅ |
| 10 | Risk states distinguish AI pre-alert from deterministic confirmation | ✅ three independent mechanisms |
| 11 | Safety behavior works without the Adaptive Engine or cloud | ✅ proven in a fresh interpreter and with sockets disabled |
| 12 | Arabic RTL and English console flows work | ✅ verified live in a browser |
| 13 | Logs, metrics, health checks and audit records exist | ✅ — thirteen of §29's fourteen metrics instrumented and dashboarded; the fourteenth has no component to measure |
| 14 | Security, privacy, backup, recovery and pilot documentation exists | ✅ all 22 spec §31 documents |
| 15 | Unit, contract, integration, end-to-end, safety and fault tests pass | ✅ 739 + 94 + 13, 275 safety |
| 16 | No secrets or real household data in the repository | ✅ bandit clean; synthetic data only |
| 17 | Third-party licenses documented | ✅ `THIRD_PARTY_NOTICES.md` |
| 18 | No unresolved critical blocker | ✅ none open |

**The MVP is complete.** The remaining items in the stubs table are post-MVP
work, and the safety case records two open gaps honestly rather than claiming
closure.

## Phase UI-0 — Design foundations ✅

Governed by `SYLTRA_Platform_UI_UX_Guidelines.md`, not the platform build spec.
Scope was deliberately narrow: **build the foundations, redesign nothing.**

| Deliverable | Where |
|---|---|
| Audit of the existing console against the guidelines | `docs/ui/UI_AUDIT.md` — 35 conflicts, C1–C35, at four severities |
| ADR for a design system with no build step | `docs/adr/ADR-008-design-system-without-a-build-step.md` |
| Design tokens (single source of truth) | `apps/local-console/src/design-system/tokens/tokens.json` |
| The six §24 generated outputs | `tokens/tokens.css`, `tokens/motion.css`, `themes/dark-theme.css`, `themes/light-theme.css`, `typography/typography.css` — regenerated by `make tokens` |
| Arabic RTL foundation and accessibility baseline | `foundation.css` |
| Shared component primitives | `primitives.css` |
| Contrast verification library | `libs/design-tokens` — `make contrast` |
| Component catalogue (living style guide) | `/console/catalogue/` — `make console` |

### Phase UI-0 acceptance criteria

| Criterion | Status |
|---|---|
| No feature component contains a hardcoded brand colour | ✅ Zero hex literals in `foundation.css`, `primitives.css`, `console.css` and `catalogue.css`. The console was migrated onto the tokens, so this holds for the product and not only the catalogue. |
| Arabic and English direction switch works | ✅ Logical properties throughout, enforced by test; verified live — sidebar mirrors, identifiers and numbers stay LTR, chronological charts stay LTR, no horizontal overflow at 400px |
| Token contrast checks pass | ✅ 44 pairs per theme, both themes, computed from the WCAG 2.2 formulas. The catalogue recomputes them in the browser and agrees. |
| Themes work without layout changes | ✅ Enforced structurally: a test asserts both themes define exactly the same token names and that every theme value is a colour |

### Additional verification performed

- Served the catalogue and every design-system asset through the **real gateway
  app**, not a stand-in — including directory-index resolution and four
  directory-traversal attempts against the new `/design-system` mount.
- Rendered the whole catalogue in a browser at 1280px and 400px, in both themes,
  both directions and both densities, checking computed styles rather than
  appearance: 55 components, none invisible or zero-sized, no unresolved token,
  no page-level horizontal overflow.
- Confirmed the busy button keeps its idle width (72px both), so nothing
  reflows mid-action.

### Defects found and fixed during Phase UI-0

Building the catalogue was not a formality — rendering every component at every
size found three real defects that reading the stylesheets did not.

| Defect | Impact | Fix |
|---|---|---|
| Tables had no scroll container | A 621px device table inside a 400px viewport was **clipped** by its card. The far columns became unreachable, and nothing signalled they existed — worse than a scrollbar (WCAG 1.4.10) | `.table-scroll`, keyboard-reachable, plus a `--pinned-header` modifier that gives the wrapper a real scrollport so `position: sticky` still means something |
| The skip link was `position: absolute` | It resolves against the initial containing block, so after any scroll it was focusable but off-screen — the exact failure a skip link exists to prevent | `position: fixed` |
| The console distinguished advisory from confirmed by **colour alone** | The single most important distinction in the product, invisible to a colour-blind user and under forced colors | The console now uses the shared badge: advisory dashed, confirmed solid, shadow dotted — three cues that survive greyscale |
| `--grid-gap` and `--type-title-size` were referenced but never defined | Silent: the property falls back to its initial value and the component looks *nearly* right | Corrected, and a test now fails on any `var()` naming a token no generated stylesheet defines |

### What UI-0 deliberately did not do

- **No screen was redesigned.** The console keeps its nine-tab shell; the
  sidebar, workspace selector and role-filtered navigation are UI-1 (C24–C28).
- **No brand SVG was generated.** Guidelines §5.4 forbids producing the eight
  production SVGs from the PNGs without visual review and product-owner
  approval, so the console still renders a typed wordmark (C32–C35).
- **No font was vendored.** IBM Plex Sans Arabic and Inter are named first and
  degrade to system families. Vendoring WOFF2 needs a licensing and
  repository-size decision (C12).

## Phase UI-1 — Shell and primitives ✅

Scope: the application shell, the §4 navigation, workspace and property
selection, and completion of the §12 primitives. Screens moved into the shell;
their content is UI-2.

| Deliverable | Where |
|---|---|
| Shell primitives — 264/72px sidebar, 64px top bar, content region, nav items, breadcrumbs, page header, metric row | `apps/local-console/src/design-system/shell.css` |
| Identity endpoint the shell needs | `GET /v1/me` — role, permissions, home scope |
| Console rebuilt around the shell | `apps/local-console/static/index.html`, `console.js` |
| Shell specimens, expanded and collapsed | `/console/catalogue/#shell` |

### Phase UI-1 acceptance criteria

| Criterion | Status |
|---|---|
| Keyboard navigation passes | ✅ Up/Down move through the sidebar, Home/End jump to the ends, and the route does not change on focus — verified live: focus advanced correctly and the hash was unchanged after five key presses |
| Minimum target size passes | ✅ Zero of the 20 focusable elements fall below 24px; navigation items are 44px |
| Arabic and English visual regression passes | ✅ At 1440px the sidebar moves from x=0 to x=1176, the current-page marker flips from `inset 3px` to `inset -3px`, the collapse chevron mirrors, the brand mark does not, and neither direction overflows |
| 768px layout remains usable | ✅ The sidebar collapses to 72px, all 13 navigation items stay reachable with their accessible names intact, nothing in the content region is clipped, and the page does not scroll sideways |

### Navigation, and what sits behind each item

§4 fixes thirteen items and their order. Five have no backend yet and are
rendered **marked, not hidden** — a console that silently omits half its
information architecture looks finished when it is not (§20).

| §4 item | UI-1 content | Permission |
|---|---|---|
| Overview | System status, twin summary, active contexts | READ_HOME |
| Properties | *Not yet available* | READ_HOME |
| Rooms | `/v1/homes/{id}/rooms` | READ_HOME |
| Devices | `/v1/homes/{id}/devices` | READ_HOME |
| Automations | *Not yet available* | READ_HOME |
| SILA Intelligence | Recommendations and the learning ladder together (§17.9) | READ_HOME |
| Risk Centre | `/v1/homes/{id}/risks` | READ_HOME |
| Energy | *Not yet available* | READ_HOME |
| Installations | *Not yet available* | READ_HOME |
| Users and Roles | *Not yet available* | MANAGE_POLICY |
| Audit Trail | `/v1/audit` | READ_AUDIT |
| System Health | System status and the action timeline | READ_HOME |
| Settings | Privacy and consent, session scope | READ_HOME |

**Roles.** The guidelines describe six personas (organization owner, platform
administrator, operations user, installer, household administrator, viewer);
the platform issues six roles that do not match them (OWNER, ADULT, CHILD,
GUEST, INSTALLER, SERVICE). Rather than invent an organization-role model the
backend does not have, navigation filters on **permissions**, which are the
authority the backend actually grants. A role's permission set can change
without touching the console.

**Hiding is not authorization** (§3). The filter is presentation. Every
endpoint re-checks scope and permission on every request, and
`services/api-gateway/tests/test_identity.py` proves it: for each role lacking
`READ_AUDIT`, `/v1/me` omits the permission *and* `/v1/audit` returns 403 when
asked directly. A caller who edits the URL finds the same refusal as one who
never saw the item.

### Additional verification performed

- Drove the rebuilt console live at 1440px and 768px, in both themes and both
  directions, measuring computed geometry rather than appearance.
- Confirmed the metric row never exceeds four cards at any width from 900px to
  3200px, and degrades to three, two and one as it narrows (§9.3).
- Confirmed the `:focus-visible` and `.skip-link:focus` rules are present in
  the live CSSOM with the expected declarations. Focus *rendering* could not be
  observed: `:focus-visible` requires real user focus, and the automation pane
  runs backgrounded. §28 already keeps the keyboard walkthrough as a manual
  test, and it stays outstanding.

### Defects found and fixed during Phase UI-1

| Defect | Impact | Fix |
|---|---|---|
| `console.css` still carried the whole pre-shell layout | Its `main { max-width: 72rem }` fought the shell grid: the content region rendered **336px wide inside a 1176px track** | The shared rules moved into the design system (`.card-grid`, `.reasons`, `.evidence`, `.muted`) and `console.css` was deleted. The console now has no stylesheet of its own, which is what makes "no feature component contains a hardcoded brand colour" true by construction rather than by review |
| `.metric-row` used bare `auto-fit` | Six metric cards fitted in one row at 1440px, against §9.3's limit of four | The track minimum is now a quarter of the available inline size, capping the row at four however wide the screen gets |
| Pruning unused translation keys used a regex that missed indirect calls | Twenty keys reached through helpers such as `empty("no_devices")` were deleted as unused | Restored, and the usage scan now reads every string literal rather than only direct `t("…")` calls |

### What UI-1 deliberately did not do

- **Screen content is untouched.** Views moved into the shell and were retitled
  to the §4 names; the §13 domain components and the §17 screen layouts are
  UI-2 onward.
- **No brand SVG, no vendored font.** C12 and C32–C35 remain open on the
  product owner, unchanged from UI-0.

## Phase UI-2 — Core operational screens ✅

Scope: Overview, Properties, Property detail, Rooms, Room detail, Devices,
Device detail and System Health, built from the §13 domain components.

| Deliverable | Where |
|---|---|
| §13 domain components — property status header, room card, device row, context indicator, recommendation card, risk card, §20 notices, filters, detail list | `apps/local-console/src/design-system/domain.css` |
| Nine screens, all against real API payloads | `apps/local-console/static/console.js` |
| A permission for technician-only detail | `READ_DIAGNOSTICS` — OWNER and INSTALLER |
| Console/API contract test | `services/api-gateway/tests/test_console_contract.py` |
| Specimens for every domain component and every §20 state | `/console/catalogue/#domain`, `#states20` |

### Phase UI-2 acceptance criteria

| Criterion | Status |
|---|---|
| Real API contracts or deterministic fixtures | ✅ Every screen reads the live API, and a contract test asserts that each field name the console reads exists in the response |
| All data states implemented | ✅ Initial loading (skeleton), partial, empty first-use, empty *filtered*, offline, stale, permission-denied and service failure — each with its own words |
| Role-based views tested | ✅ Exercised live as all five roles; see the table below |
| Stale and offline states visible | ✅ Device state is derived from the platform's own per-capability freshness rule, so the kitchen gas detector shows STALE with its age while the living-room sensors show ONLINE in the same table |

### Role-based views, verified live

Signed in as each of the five roles the development server now issues:

| Role | Audit Trail | Users and Roles | Diagnostics panel | Capability shown as | Privacy export | Approve controls |
|---|---|---|---|---|---|---|
| OWNER | shown | shown | shown | `climate.target_temperature` | shown | shown |
| ADULT | hidden | hidden | hidden | "target temperature" | denied notice | shown |
| CHILD | hidden | hidden | hidden | "target temperature" | denied notice | none |
| GUEST | hidden | hidden | hidden | "target temperature" | denied notice | none |
| INSTALLER | hidden | hidden | **shown** | `climate.target_temperature` | denied notice | none |

That last row is the point of §17.7: an installer needs entity ids and a
household member does not, and neither of them is the same as an owner.

### Defects found and fixed during Phase UI-2

The first three were **shipped in UI-1 and reported as complete**. They passed
every test because the tests checked the console's source against itself; only
reading the real payloads found them.

| Defect | Impact | Fix |
|---|---|---|
| `status.healthy` does not exist | `undefined` is falsy, so the console reported the system **degraded while every component was ok** | Health is derived by counting `components`, which is the platform's own answer. A test asserts no `healthy` field has appeared, so the console switches rather than keeping a second definition |
| Contexts were read as `label`/`type` | The real field is `context_type`, so every context card rendered an empty heading | Read the real field; every context type is now translated |
| Recommendations were read as `title`/`explanation` | The real fields are `recommendation_type`, `target` and `proposed_value`; the proposal line was blank | Proposals are composed from the real fields into plain language |
| A column header rendered as the raw key `state` | Table headings reach `t()` through a helper, so the existing key test did not see them | The key test now also reads heading arrays and filter labels |
| The property header printed the identifier twice | It was used as both the name and the subtitle | The heading *is* the identifier; the subtitle now explains why, and only to a technician |
| Readings rendered as `27.4 C` | The API reports the bare SI symbol, correctly | A display-only unit map adds the degree sign, in the console where typography belongs, not in the contract |

**The lesson, recorded rather than hidden:** a test suite that only reads the
code under test cannot find a contract mismatch. `test_console_contract.py`
exists so this class of bug fails in CI rather than in a browser.

### What UI-2 deliberately did not do

- **Properties is real but thin.** §17.3 asks for city, energy summary and
  owner. The platform holds none of them, so those columns are absent and the
  screen says so, rather than showing empty cells that look like missing data.
- **No device controls.** §13.3 permits a "primary safe control" on a device
  row. There is no command endpoint, and inventing one to satisfy a UI phase
  would put an actuator in the product ahead of its safety review.
- **Automations, Energy, Installations, Users** remain marked as unavailable:
  four screens whose backends do not exist.

## Phase UI-3 — Intelligence and action screens ✅

Scope: SILA Intelligence, the recommendation flow end to end, contexts,
feedback, and the action timeline. The automation list and builder are excluded:
no backend produces automations.

| Deliverable | Where |
|---|---|
| §13.4 recommendation card with the policy decision on it | `recommendationCard`, `policyPanel` |
| §16 learning-mode banner stating what the mode permits | `learningModeBanner` |
| §17.9 SILA Intelligence — mode, recommendations, learned contexts, suspended models, technical view, learning controls | `renderIntelligence` |
| §13.7 action timeline with manual override marked | `timeline` |
| §17.10 Risk Centre ordering | `RISK_STATE_ORDER` |
| Approval chain repaired end to end | `services/api-gateway/tests/test_approval_chain.py` |

### Phase UI-3 acceptance criteria

| Criterion | Status |
|---|---|
| Inferred and confirmed states are distinguishable | ✅ Advisory dashed, confirmed solid, shadow dotted; the Risk Centre groups by state with confirmed first, so a watch can never sit above a hazard |
| Recommendation reason and confidence are visible | ✅ Every card carries the plain-language reasons, confidence as a qualified level *and* a number, and the model provenance — named for a technician, described in words for everyone else |
| SILA cannot bypass approval or policy UI | ✅ Every proposal carries the policy decision, its reason and its safety class. Approve and Reject render **only** where policy returned REQUIRE_USER_APPROVAL — never against a refusal, never for a shadow prediction |
| Manual override is visible | ✅ `MANUAL_OVERRIDE_DETECTED` and `ACTION_CANCELLED_BY_MANUAL_OVERRIDE` are marked in the timeline rather than listed as one more automated step |

### Two defects that made approval impossible

Both were in the platform, not the UI, and both were invisible because every
existing test drove the services directly instead of through the API.

| Defect | Impact | Fix |
|---|---|---|
| Nothing ever created a policy decision | `/recommendations` returned proposals; `/approve` looked for a pending decision and found none. **Every approval through the console returned 404** — the console's primary action could not work at all | Policy is evaluated on the recommendation read path, against the twin's current state. The decision, and its reason, now travel with the recommendation, so the console can show what policy decided instead of offering a button that fails |
| `build_recommendations` minted a fresh UUID per call | A recommendation's identity changed between two polls of the same console. Once policy evaluation joined the read path, that leaked one policy decision **per poll** — 240 an hour, forever | Identity is now derived from (home, type, target, validity window): the same standing proposal is the same recommendation however often it is rebuilt. `created_at` became the window start, so "expires 18:45" stays put instead of sliding forward on every read |

Shadow predictions are explicitly excluded from policy evaluation. Creating an
approvable decision for one would be exactly the bypass §19.2 exists to
prevent, and a test asserts the API refuses.

### Smaller defects found during Phase UI-3

| Defect | Impact | Fix |
|---|---|---|
| The approval confirmation was set before the refresh | `refresh()` clears the status line, so the message flashed and vanished — a person clicked Approve and was told nothing | Set after the refresh, and a test asserts the order |
| The timeline read newest-first | §13.7's stages have a sequence; "approved" above "policy decided" inverts cause and effect | Sorted chronologically within the window |
| The gateway test fixture never seeded the AC's own setpoint | Policy denied every proposal with `TARGET_STATE_NOT_FRESH`, so the approval path was never exercised in any gateway test | The fixture seeds it, and the denial case became a test in its own right — a recommendation policy has refused must not be approvable |

### What UI-3 deliberately did not do

- **No automation list or builder.** §26 lists them under UI-3; nothing in the
  platform produces or stores an automation, so there is nothing to list and
  no schema to build against.
- **No undo control.** §13.4 lists UNDO among the responses, and the feedback
  API accepts it — but undo belongs to an action that has run, and no action
  has run through the console yet. Offering it on a proposal would mean
  undoing something that never happened.

## Phase UI-4 — Risk and energy ✅

Scope: risk detail and timeline, critical-action verification, the Energy
dashboard, anomalies, and data-quality indicators. The Risk Centre itself
landed in UI-3.

| Deliverable | Where |
|---|---|
| §21 critical-action confirmation — the pattern, reviewed before it is needed | `domain.css`, `/console/catalogue/#critical` |
| Risk detail with evidence and timeline | `renderRiskDetail`, `#/risks/{case_id}` |
| Energy dashboard from real readings only | `renderEnergy` |
| Data completeness and freshness | `dataQuality`, `/console/catalogue/#dataquality` |

### Phase UI-4 acceptance criteria

| Criterion | Status |
|---|---|
| All risk states tested | ✅ Seven states, grouped in the §17.10 order, each with a distinct label and border treatment; the ordering test asserts confirmed can never sit below a watch |
| No critical action is one-click | ✅ The confirmation carries all ten §21 disclosures, Cancel precedes the destructive control in reading order, and the confirming control is styled as its own thing rather than a primary button — a generic "OK" is on the prohibited list |
| No colour-only risk communication | ✅ Advisory dashed, confirmed solid, shadow dotted; each dispatch step carries a `data-state` as well as a colour |
| Charts expose units, gaps, freshness and accessible summaries | ✅ There is no time series to chart. Every number carries its unit, the power total states how many meters it came from, and the coverage bar is `role="img"` with a label that restates its number |

### The Energy screen is bounded by what the platform measures

§17.11 asks for consumption over time, baseline comparison and cost, and in the
same breath says **"never fabricate cost, savings, carbon, or device-level
estimates."** The platform records power as it is read and keeps no
aggregation, so the screen shows current power, the per-device breakdown where
a device meters it, anomalies, and coverage — and then says plainly that trend,
comparison and cost are not available and are not estimated.

One meter in a nine-device home is 11% coverage. Stating that is the most
useful thing on the page, because it tells a reader how much of their home the
number represents.

### Defects found and fixed during Phase UI-4

The first two share a cause: matching a capability by its **name** instead of
by what the contract says it is.

| Defect | Impact | Fix |
|---|---|---|
| `light.power` was treated as a wattage | It is a **boolean on/off control**. Summing it counted `true` as a quantity and reported the home as twice as well metered as it is — "2 of 2 metered devices" when only one meters anything. An inflated coverage figure is worse than an omission: it makes an incomplete number look complete | A device meters power if it reports a reading whose **unit is watts**. Derived from the data, not from a word in the name |
| The lights-on count read `light.on` | Not a capability the platform defines, so the count was always zero and every room card claimed the lights were off. Nothing failed | Reads `light.power`; a test now asserts every capability the console names exists in the registry, and that no boolean is summed |
| A malformed risk id reported a service failure | `/risks/{id}` returns 422 for an id that is not a UUID. The console reported "risk cases could not be loaded", blaming the service for a mistyped URL | 404 and 422 both mean a bad link, and say so |

### What UI-4 deliberately did not do

- **The critical-action confirmation is not wired to anything.** The console
  commands no actuators, and §26 lists the component under this phase. Building
  and reviewing the pattern now is the point; attaching it to an action that
  does not exist would not be.
- **No chart.** §18's rules were applied to the numbers that exist rather than
  used to justify drawing a trend from a single reading.

## Phase UI-5 — Audit and settings ✅ (partial by necessity)

Scope: the audit trail to §17.14 and platform settings. **Installation projects
and user management were not built**: neither has a backend, and both are
described below rather than stubbed.

| Deliverable | Where |
|---|---|
| §17.14 audit trail — seven columns, two filters, append-only | `renderAudit` |
| Audit reason codes translated | `/v1/audit` now takes a locale |
| Audit entries keep what they acted on | the API no longer discards `detail` |
| Settings — appearance, density, privacy, session | `renderSettings` |
| §8.4 density modes made selectable | `applyDensity` |

### Phase UI-5 acceptance criteria

| Criterion | Status |
|---|---|
| Audit history is read-only | ✅ Structural: the audit view renders **no buttons at all** beyond its filters, issues no write of any kind, and says so on the screen. A test asserts no DELETE, PATCH or PUT can appear there |
| Arabic RTL workflow passes | ✅ Verified across the audit and settings screens; reason codes now translate, so the trail reads as sentences in both languages |
| Permission changes require confirmation and audit reason | ⬜ **Not applicable** — there is no user management to change a permission with. Recorded as unmet rather than claimed |
| Commissioning stages are recoverable | ⬜ **Not applicable** — there is no commissioning workflow |

The last two are marked unmet deliberately. A phase is not complete because the
criteria it cannot reach were quietly dropped.

### Defects found and fixed during Phase UI-5

| Defect | Impact | Fix |
|---|---|---|
| The audit endpoint never translated its reason codes | Every other endpoint did. The audit trail — the screen most likely to be read *after something has gone wrong* — was the one place a household saw `AUTOMATION_NOT_YET_TRUSTED` instead of a sentence | `/v1/audit` takes a locale and translates, like the rest |
| The API discarded the orchestrator's and risk engine's `detail` | The trail could say something was dispatched but not **to what** — a §17.14 field and the first thing an incident review needs | `detail` is merged into the entry |
| Density was a token with no control | §8.4 requires Comfortable and Compact. The tokens have carried both since UI-0 and nothing ever offered the choice; a density mode no one can select is a density mode the product does not have | A control in Settings, applied at boot |
| A technician saw a friendly capability name in the audit target | They see the identifier everywhere else, because it is what they type into a diagnostic | Gated on the same permission as every other identifier |

### Privacy export and deletion are present but disabled

The controls exist so the capability is discoverable, and are disabled with an
explanation that both run through the operator tools where they are confirmed
and recorded. A household's entire record is the most destructive thing this
console could touch, and §21 rules out one-click destructive actions.

## Phase UI-6 — Hardening ✅

An audit phase. The work was finding defects in what UI-0 through UI-5 built,
not adding to it.

| Deliverable | Result |
|---|---|
| Full accessibility pass | Nine automated checks driven over all 13 routes, in both languages: duplicate ids, unlabelled controls, nameless controls, heading hierarchy, landmarks, unhidden icons, target size, table headers, list structure |
| Component adoption audit | **Zero** classes the console uses that the design system does not define |
| Localization review | Every visible string reaches `t()`; every key is reachable; eight dead keys removed |
| Error recovery | Every primary screen can report a failure and can report having nothing to show — asserted per renderer |
| Documentation | `docs/ui/DESIGN_SYSTEM.md` |
| Visual regression | Structural rather than pixel: geometry and computed styles are measured, and every component has a catalogue specimen |

### Phase UI-6 acceptance criteria

| Criterion | Status |
|---|---|
| WCAG 2.2 AA audit has no unresolved critical issue | ✅ Two found and fixed; the sweep now returns clean on every route in both languages |
| Primary workflows pass keyboard and screen reader smoke tests | ⚠️ Keyboard verified (focus order, arrow navigation, no traps, all targets ≥24px). **Screen reader not verified** — §28 keeps it manual and it remains outstanding |
| No duplicated local component replaces a shared component without reason | ✅ Zero local classes; the console has no stylesheet of its own |
| No unresolved RTL layout defect | ✅ All 13 routes in Arabic: no overflow, no clipping, sidebar and markers mirror, identifiers and charts stay LTR |
| Loading, empty, error, offline, stale and permission states exist for every primary screen | ✅ Loading and permission are shared so they cannot drift; failure and empty are asserted per renderer |

### Defects found by the audit

| Defect | Impact | Fix |
|---|---|---|
| Links filling a table cell were 17–22px tall | WCAG 2.2 §2.5.8 exempts links *inline in a sentence*; a link that is a cell's whole content is a discrete target and needs 24px. Every device, room and property link in every table was below it | `min-block-size` with padding, so a wrapped name still grows |
| Four screens went from `h1` straight to `h3` | A screen-reader user navigating by heading found a gap where a section should be. Rooms, room detail, energy and settings | Each got the section heading it was missing; settings cards became second-level, since each card *is* a section |
| `renderProperties` swallowed every failure | A property whose data would not load was listed with zeroes. "0 devices, 0 risks" for a property nobody could reach reads as a quiet, healthy home | Unreadable properties are named, and a blank is shown where a number could not be read |
| The models table lost its empty state in the UI-3 rewrite | An empty table with a heading above it reads as broken | Restored — and the test that found it now guards every primary screen |
| Eight translation keys were dead | Left behind by screen rewrites. A string nothing reads is a string nobody maintains | Removed, and a test now fails on an unreachable key |

### What the tests cannot check, and is still outstanding

Recorded here rather than left implied:

- **A screen reader walkthrough.** Nobody has run one.
- **200% browser zoom** on every screen.
- **An Arabic reading pass by someone who reads Arabic.** The strings are
  translated and the layout mirrors correctly; nobody has read it for tone.
- **Windows high-contrast mode.** The rules are written and the CSSOM confirms
  they load; nobody has looked at it.
- **Focus-ring rendering.** `:focus-visible` needs real user focus, which a
  backgrounded automation pane does not grant. The rules are present and load
  correctly; whether they look right is a manual check.

## A flaky privacy test, found while closing the UI

Not a UI defect, but found by running the full suite repeatedly during the UI-6
gate and worth recording because of what it was guarding.

`test_household_data_never_reaches_disk_in_the_clear` scanned the whole backup
file for household strings, including `27.4` — a temperature. A backup's
manifest is **unencrypted by design** so `backup info` can report what a file is
without the passphrase, and its `created_at` is an ISO timestamp. Roughly one
run in six hundred, the seconds field reads `27.4…` and the scan matched the
timestamp.

**The encryption was never at fault**, and no household data ever reached disk
in the clear. But a privacy test with a false-alarm mode is worse than no test:
the failure looks exactly like a leak, and after the second false alarm people
start re-running it instead of reading it.

The test now scans the **ciphertext**, and the manifest is checked by asserting
its **exact key set** — which is stronger than any substring search, because
household data arriving in the manifest shows up as a new field whether or not
anyone thought to search for its contents. Two new tests came with it: the
manifest carries identifiers and row counts only, and two backups of the same
data are never byte-identical, which proves a fresh nonce.

## UI definition of done (guidelines §27)

The eighteen criteria that decide whether the platform UI is complete. Six are
not fully met, and each says why rather than being rounded up.

| # | Criterion | Status |
|---|---|---|
| 1 | Dark and light themes use shared tokens | ✅ One `tokens.json`; a test asserts both themes define exactly the same names and only colours |
| 2 | Arabic RTL and English LTR use the same components | ✅ One set of components; direction comes from `dir` alone |
| 3 | Navigation adapts by role and workspace | ✅ Filtered by permission, verified live as all five roles. One workspace exists, and the control is present for when there are more |
| 4 | Overview shows operational priorities, not decorative KPIs | ✅ Every tile is something a person acts on; §17.2's order |
| 5 | Device and hub health states are explicit | ✅ §14's states, derived from the platform's own freshness rule; unknown is shown, never blank |
| 6 | SILA recommendations show reason, confidence, expiry, and feedback | ✅ Plus the policy decision, which is what stops a proposal reading as a decision |
| 7 | Risk states distinguish possible, inferred, and confirmed | ✅ Dashed, dotted and solid; grouped so confirmed is never below a watch |
| 8 | Critical controls use confirmation and verification flows | ⚠️ **The pattern is built and reviewed; nothing uses it.** The console commands no actuators. This becomes ✅ the day the first one is wired through it |
| 9 | Energy charts show units, time, freshness, and data gaps | ⚠️ **There are no charts.** The platform keeps no time series, so there is nothing to plot. Units, freshness and coverage are shown; trend and cost are named as absent rather than estimated |
| 10 | Every primary screen has loading, empty, partial, offline, stale, permission and error states | ✅ Loading and permission shared so they cannot drift; failure and empty asserted per renderer |
| 11 | Shared components are documented | ✅ `docs/ui/DESIGN_SYSTEM.md` and the living catalogue |
| 12 | Accessibility automation and manual smoke tests pass | ⚠️ Automation passes. **200% zoom is now verified** (clean at 720px and 400px; only data tables exceed the viewport, each in a scrollable labelled wrapper), and so is the accessible-name tree (navigation announces "Overview", not "◧Overview"). What is left needs a person listening: a screen reader walkthrough, an Arabic reading pass, and high contrast. See `docs/ui/ACCESSIBILITY_VERIFICATION.md` |
| 13 | Visual regression covers dark, light, Arabic, English and 768px | ⚠️ **Structural, not pixel.** Geometry and computed styles are measured in all five combinations, which catches layout breakage; it does not catch a component rendering the wrong colour on the right geometry. That needs a baseline someone has approved |
| 14 | No Home Assistant customer-facing UI or terminology | ✅ A test sweeps every stylesheet and script |
| 15 | No unapproved logo redraw or brand icon | ✅ Typed wordmark; §5.4 forbids generating the SVGs from the PNGs without approval, so none was |
| 16 | No green as a brand colour | ✅ Enforced by a test over the brand palette |
| 17 | No safety-critical operation depends on AI text or a one-click control | ✅ Safety actions are commanded by the Safety Governor; the console offers no control that could reach one |
| 18 | The interface reflects real backend state and does not fabricate success | ✅ — and this is the criterion that cost the most. Three screens once read fields that did not exist, an inflated meter count claimed twice the coverage, and the approve button returned 404 for every recommendation. `test_console_contract.py` and the capability-name tests exist so that class of failure is caught by CI rather than by reading the screen carefully |

**Four of the six shortfalls need something outside this repository**: a person
to run the manual accessibility checks, a product decision on three missing
backends, brand assets, and an actuator to exist before its confirmation flow
can be wired. The fifth (charts) needs a time-series endpoint. The sixth
(pixel regression) needs a baseline someone has approved.

## Post-MVP — notify and prepare for confirmed hazards ✅ (half of a recorded gap)

The safety case recorded: *"the authorized responses named by confirmation
rules are not wired to the Action Orchestrator."* Spec §20.4 gives the AI role
as "notify and prepare the allowed response", and both of those are now built.
Execution is not, and cannot be reached from this path.

| Stage | Built? | Why |
|---|---|---|
| **Notify** | ✅ executes | `notification.send` is NON_CRITICAL and needs no confirmation. Telling a household their gas alarm is sounding operates nothing |
| **Prepare** | ✅ executes, touches nothing | Resolves the valve from the twin, prefers one in the affected room, records whether it can be reached, computes the command — and does not send it |
| **Execute** | ❌ absent by construction | Closing a valve, sounding a siren, unlocking egress. Needs your approval under spec §0 rule 9 |

A confirmed gas alarm now produces, and the console shows:

> **You have been told** — the household is told what was confirmed and where.
> **Prepared, not sent** — SYLTRA has identified `valve_main` and verified it
> can be reached. It would be set to `closed`. The command has not been sent
> and will not be sent by this console.
> *Nothing has been sent to any device.*

### Execution is impossible here, not merely unimplemented

Five independent guards, each with a test:

1. `ResponseStage` has two members and no third. There is no value meaning
   "execute", so no caller can construct one.
2. A `NOTIFY` step may only use `notification.send` — a valve command labelled
   NOTIFY raises rather than walking past checks that read the stage.
3. The planner imports no gateway, orchestrator or action module and calls
   nothing named `execute`, `dispatch`, `send` or `publish`. **Asserted on the
   parsed syntax tree**, because the module's own docstring explains that it
   never reaches a gateway and a substring search reports the explanation as
   the offence — the third time that trap appeared in this build.
4. No API route contains `valve`, `siren`, `breaker`, `isolate`, `dispatch` or
   `execute`.
5. The console renders the plan and no control: no button, no listener, no
   request. `dispatched` is reported, never toggled.

### An unreachable valve is reported, not hidden

A prepared isolation naming no reachable valve is a plan that fails at the
moment it matters. It is surfaced now rather than then.

**What this changes for you:** the decision — should a confirmed gas alarm
close a valve automatically? — is unchanged and still yours. What changed is
that everything needed to make it is now visible before it is taken: which
valve, whether it answers, and exactly what would be sent.

## Post-MVP — Automations ✅

The largest functional gap in the platform. Spec §2.3 asks for *"user-authorized,
non-critical actions through a policy and safety gate"*, and until now every
recommendation ended at "wait for a person" with nothing a household could
author itself.

| Deliverable | Where |
|---|---|
| Design decision | `docs/adr/ADR-009-deterministic-automations-without-an-interpreter.md` |
| Contracts | `libs/contracts/.../automations.py` |
| Engine | `services/automation-engine` |
| Permission | `MANAGE_AUTOMATIONS` — OWNER and ADULT only |
| API | list, get, create, enable/disable, dry-run |
| Console | the §17.8 screen, replacing the unavailable marker |

### Typed rules, not a scripting language

ADR-009 records the reasoning. The short version: a DSL is an interpreter
evaluating user text against live home state, in the one component that
commands devices — and "this automation may only touch non-critical
capabilities" is a question you can decide by looking at typed data and cannot
decide about arbitrary text. The cost is that some automations people want will
not be writable. That is the right way round for a system that turns on heaters
in rooms where people sleep.

### The guarantees, and how each is held

| Guarantee | How |
|---|---|
| Non-critical only (§2.3) | `AutomationAction` **refuses at construction** to name a `LIFE_SAFETY_CRITICAL`, `SAFETY_RELATED` or `SECURITY_SENSITIVE` capability. An automation that would unlock a door cannot be stored, listed or exported — there is no later check to forget |
| Not a way past policy (invariant 2) | The engine produces proposals and holds no gateway. A test asserts it has no `execute`, `dispatch`, `send`, `gateway` or `orchestrator` attribute, and that a proposal has no field that could record a dispatch |
| A person's hand wins (invariant 5, §0 rule 16) | An automation targeting something a person just set is skipped, with `MANUAL_OVERRIDE_ACTIVE` as the recorded reason. The window lapses, so one manual change does not permanently disable it |
| No feedback loops (§14.8) | Two mechanisms: an automation will not fire on its own echo, and cannot fire again inside its re-arm interval. The floor is 30 seconds and cannot be set away |
| Survives the AI being down (invariant 7) | A fresh interpreter asserts the import graph pulls in no model runtime |
| Time-bounded (§0) | Every proposal expires |
| Freshness | Conditions use the twin's own `is_usable_for_decisions`, the same predicate policy and the risk engine use — so an automation cannot act on a value the rest of the platform would refuse |

### Invariant 7 was half-tested for the whole build

`test_fixed_automation_is_unaffected_by_a_missing_adaptive_engine` carried that
name while exercising only the Safety Governor, because no automation existed.
The invariant was reported as satisfied on the strength of half of it. It now
runs an actual automation, and the safety case says so.

### Two defects found while building it

| Defect | Impact | Fix |
|---|---|---|
| The auto-refresh wiped a requested result | A person clicks "Test run" and up to fifteen seconds later their answer silently vanishes — the button looks broken. Same class as the approval confirmation that used to flash and disappear | The periodic refresh holds while an explicitly requested result is on screen, and releases on navigation |
| A new reason code shipped untranslated | Caught immediately by the AST-based translation test, as designed | Seven automation reason codes translated in both languages |

### What is not built

- **The visual builder.** §17.8 asks for a builder with version history and
  rollback. Automations are created through the API; the screen lists, tests
  and switches them, and says on the screen that the editor is missing rather
  than implying a button that is not there.
- **Scheduled triggers.** Triggers are state, threshold and context. "At 7pm"
  needs a clock source in the evaluation loop, which is a separate decision
  about who owns time in this platform.

## Before a real home — a hub that cannot act ✅

The pilot plan is a real home after the build. The single most important
question for that is whether the platform can be *guaranteed* not to act, and
the honest answer was no: the protections were three separate things someone had
to get right — the learning mode, the absence of automations, and the policy
gate. The environment block covered life-safety and safety-related capabilities
only, and **comfort actions were never blocked in any environment**. A light
switching itself on in a stranger's house on night one is exactly the wrong
first impression.

`OrchestratorConfig.dispatch = OBSERVE_ONLY` makes it one thing.

Everything else still runs — events arrive, the twin projects, contexts resolve,
models train, policy decides, automations evaluate — and nothing reaches a
device. Each refusal records the capability, device, value and safety class of
the command that was not sent. **That record is the deliverable of a pilot week**,
not a side effect: it answers "what would SYLTRA have done in this house?"

| Property | How it is held |
|---|---|
| Nothing is dispatched | The check is the first line of `_preflight`, the one function every dispatch passes through |
| Every class, not only the critical ones | Parametrized over all five safety classes |
| Before every other condition | Proven by handing it a request that would otherwise fail differently and asserting the observe refusal returns |
| The refusal is legible | Records what would have been sent, translated in both languages |
| Cannot switch itself on | Enabled is the default, and a test says so — a mode that could silently disable a working home would be its own hazard |
| Visible without reading a config file | System Health says *"This hub is watching, not acting"* before anything else on the page |

The pilot checklist now begins with the switch rather than three promises, and
gains a section for what must be true **before** dispatch is enabled: the week's
refused commands read rather than counted, nothing in them unwelcome, the
household agreeing, and someone present the first time it acts.

## The observability gap, and a correction

Asked whether the build was complete, I checked §32's eighteen criteria and
found Phase 8's *observability dashboard* deliverable undelivered —
`config/observability/` held a `.gitkeep`. I then said the instrumentation was
complete and only the dashboard was missing. **That was wrong**, and I had
inferred it from forty metrics existing without checking coverage.

**Six of §29's fourteen required metrics had no source at all**, concentrated in
the services that decide and act:

| §29 metric | Owner | Was |
|---|---|---|
| policy outcomes | policy-safety | no metrics module |
| action success and failure | action-orchestrator | no metrics module |
| manual override rate | action-orchestrator | no metrics module |
| active risk cases | risk-engine | no metrics module |
| database latency | digital-twin | not instrumented |
| cloud connector status | cloud-connector | **service does not exist** |

Five services had no metrics module whatsoever. A count is not coverage.

### Now

Thirteen of fourteen are instrumented, registered, and incremented by real
events. The fourteenth is unmet because the component it would measure is not
built — see below. New modules for policy-safety, action-orchestrator,
risk-engine and automation-engine; database latency added to the twin.

Three tests keep it that way, and each closes a different way this could rot:

- every §29 metric is **registered in the live Prometheus registry**, not merely
  defined — a metric that is defined but never registered passes a grep and
  fails a scrape;
- a policy decision and an observe-only refusal are **actually counted**, because
  registering a metric nobody increments is the same gap one step further on;
- every metric the **dashboard queries** exists, because a panel querying
  nothing shows "No data" forever, and during a pilot that is indistinguishable
  from a quiet home.

A fourth finds any metrics module missing from the list, so a whole service
cannot end up silently outside the check.

### The dashboard

`config/observability/`, behind a compose profile so `make up` stays small:

```bash
make observe    # → http://127.0.0.1:3001
```

Sixteen panels, ordered by the questions a pilot week asks. The first is **"Hub
can act on devices"** — during an observe-only week it reads *No*, and a test
asserts it stays first, because reading order is the only thing that guarantees
which fact someone sees first.

Then: confirmed hazards, advisory cases, devices not reporting, cloud
connected, events in. Then policy outcomes and refusals-by-reason, which in
observe-only mode are the entire story of what the platform would have done.

Prometheus keeps 30 days locally. Grafana refuses to start without
`GRAFANA_ADMIN_PASSWORD` — a dashboard of a household's behavioural history
does not ship with a default password — and has telemetry, update checks and
sign-up disabled. Nothing in the profile reaches outside the hub.

## A second finding: the Cloud Connector does not exist

§14.11 gives it MVP responsibilities — disabled by default, an export
allowlist, offline queueing, payload redaction. `services/cloud-connector/`
contains a `.gitkeep`.

It is not a *critical* blocker: the platform's promise is that local control
never depends on the cloud, and a connector that does not exist is trivially
disabled. But it is a specified MVP component that is absent, and the status
file said the MVP was complete. **Recorded here rather than papered over**, and
the metrics test names it as the one unmet requirement rather than inventing a
gauge that would report a healthy cloud link nothing could provide.

Whether to build it is your call. Nothing else depends on it.

## Next up

The MVP (master build spec, phases 0–8) and every UI phase the guidelines define
are complete. What remains needs a decision or a person, not more code.

### Needs a product-owner decision

1. **Decide whether a confirmed hazard may operate an actuator.** Notify and
   prepare are built and shipped; execution is not, and needs your approval
   under spec §0 rule 9. The plan already names the valve and confirms it
   answers, so the decision can be made on evidence rather than in the
   abstract. This is also what would make §27 criterion 8 (critical controls
   use confirmation and verification) reachable — the UI pattern is built and
   waiting for an action to attach to.
2. **Scope the two remaining backends**: Installations, and Users and Roles.
   Each has a navigation entry marked unavailable. Two UI-5 acceptance criteria
   stay unmet until user management exists. Automations now exist; what they
   still need from you is whether the visual builder is worth building, and
   whether scheduled ("at 7pm") triggers are in scope.
3. **Supply the brand assets** — the eight §5.4 production SVGs and a
   font-licensing decision. The console renders a typed wordmark because §5.4
   forbids generating the SVGs from the PNGs without approval.
4. **A time-series endpoint**, if the Energy screen should show consumption
   over time. It currently shows what is measured and names what is not.

### Needs a person, not a decision

5. **The pilot itself.** `docs/pilot/PILOT_CHECKLIST.md` and its sign-offs.
   Week one runs with `dispatch = OBSERVE_ONLY`, and the deliverable is the
   list of commands the hub did not send.
6. **The manual accessibility checks.** A screen reader walkthrough, an Arabic
   reading pass for tone, Windows high-contrast, and a judgement on focus-ring
   visibility. 200% zoom and the accessible-name tree are done and recorded in
   `docs/ui/ACCESSIBILITY_VERIFICATION.md`.

### Housekeeping

7. **Merge the branch.** The build lives on `claude/syltra-code-master-build-58095f`
   and is committed there. Merging into `main` is a decision, not a task.

## Testing the offline claim

Asked whether the platform runs without internet, I answered from inspection —
no service calls an external host, no CDN asset, no fetched model weights — and
then recorded in `docs/GAPS.md` §1.6 that nothing had ever *tested* it.

That was too strong. `tests/safety/test_degraded_modes.py` already ran the
governor and the risk engine with `socket.socket` replaced by a raiser, which is
a stronger claim than an outage and a narrower one: those two components open no
socket at all. The local control path is different — controlling a light
legitimately talks to Home Assistant, NATS and PostgreSQL, all on this machine —
so "no sockets" is the wrong assertion for it.

`tests/safety/test_offline_operation.py` makes the right one. Its guard models
an unplugged router rather than a disabled socket layer: loopback keeps working,
everything else fails with ENETUNREACH and a dead resolver, and every attempt to
leave the machine is recorded. The recommendation → policy → device →
verification chain is built and run inside it.

Each test asserts twice — the device really changed, and nothing reached for the
internet at all. Only the second distinguishes *working offline* from
*degrading gracefully*, and only the first of those is what §0 rule 4 asks for.

Three of the six tests test the guard rather than the platform: that it blocks
and records an outbound connection, that it blocks name resolution, and that it
leaves loopback alone. Without them a guard that silently stopped guarding would
make the other three pass while proving nothing — the §6 pattern in
`docs/GAPS.md`, which has caught this build more than once. I also mutated the
control path with a tolerated cloud call and confirmed both tests fail.

What remains open is the same claim about the deployed stack: these run in one
process against the mock Home Assistant, with no containers. §1.6 now says so.

## Closing the engineering gaps

Asked to finish anything outstanding, I worked `docs/GAPS.md` §4 and §5 — the
entries blocked on nobody. Three of the five closed.

**The OpenAPI document.** Spec §21 asks for a specification as an artifact.
FastAPI served one live at `/v1/openapi.json`, which is enough to read and not
enough to depend on: it exists only while the hub runs, and it changes the
moment a route does. `make contracts` now writes a versioned copy, generated
from an empty platform so no household value can leak into it, and a test fails
the build when a route changes without regeneration.

Two things that document cannot do are asserted rather than left implicit: the
set of routes outside a home scope is fixed with a recorded reason for each, so
a new unscoped endpoint fails the build; and `/v1/stream` is absent because
OpenAPI 3.1 has no way to describe a WebSocket. A reader would otherwise
conclude the endpoint does not exist.

**The worked examples.** Eighteen documents in `contracts/examples/v1.0/`, and
deliberately not eighteen unrelated blobs: they are one evening in one synthetic
home — a motion reading opens a context, a model proposes 23 °C, policy allows
it, the device confirms, the resident accepts — with ids shared across every
document that references them. A test follows `recommendation_id` from the
recommendation to the decision to the feedback record, because that is the thing
a schema alone cannot teach.

**A defect the existing suite caught immediately.** The first draft used reason
codes I had invented: `COMFORT_CLASS_AUTOMATABLE`, `WITHIN_COMFORT_BAND`,
`HUMIDITY_SUSTAINED_ABOVE_BASELINE`. All six read plausibly and none is emitted
by any service. `test_every_emitted_reason_code_is_translated` failed on them
within seconds — it scans `libs/*/src` too, so the examples entered the same
vocabulary check as the live API. They now use `ROOM_MOTION_DETECTED`,
`WITHIN_POLICY`, `ADVISORY_PENDING_CONFIRMATION` and `UNMAPPED_ENTITY`, each one
real and translated in both languages.

**Feedback Service metrics.** The last service with no instrumentation. §19.2
advances a household up the learning ladder on the strength of its feedback, so
that evidence was being weighed with nothing counting it. `SUPPRESSED_TYPES` is
the gauge worth watching: a household refusing a recommendation type outright is
the platform being told to stop, which is better seen on a dashboard than
discovered in a complaint.

**The empty directories.** §5 offered two options and I took the second-guessing
one deliberately: each now carries a README naming where its content actually
lives, rather than being deleted. An empty `models/exported/` makes a claim —
"models are exported, and this is where they land" — and both halves are wrong.
Deleting it removes the claim and also removes the only place a reader looking
for exported models would think to look. A test checks every path those READMEs
name still resolves, because a pointer nobody checks is a pointer that rots.

Two entries stay open, both medium and neither blocked on anything but time:
update-and-rollback is designed but not implemented, and the console still polls
every 15 seconds while `/v1/stream` sits unused.

Full suite: 1000 passed, 28 skipped (the skips need Docker).

## A full house, and weather with no weather service ✅

The wall panel worked and had almost nothing on it. Two faults, neither of them
in the panel's own code.

**The demo house had nine devices.** Enough to prove a tile renders, not enough
to see whether a wall of them reads. `devserver.py` now seeds twenty-two: five
lights, three switched sockets, two air conditioners, a curtain, the sensors that
were already there, and four outdoors. A panel with eight tiles on it turned out
to answer a question the one-tile version could not — whether somebody can find
the light they want without reading every label — which is the whole reason for
building it before a hub exists.

**A wall panel with no air conditioning.** The panel rendered booleans and
skipped everything else, on the reasoning that a temperature dial needs a screen
you are looking at. In a climate where the outdoor sensor reads 41°, that left
the one control a household actually reaches for on a laptop in another room.

The fix was not a list of dial-shaped capabilities in `panel.js`. The gateway now
describes each operable reading — `{"kind": "TOGGLE"}` or `{"kind": "STEP",
"minimum": 16, "maximum": 30, "step": 1, "unit": "C"}` — from the capability
registry, and the panel draws what it is described. The range and the step size
stay in one place; the panel still names no capability anywhere in it. A step is
a presentation decision (half a degree per press is eight presses to feel a
difference), so the gateway decides it once from the declared unit.

Enums return no control on purpose. Six climate modes behind one tile is how a
house ends up heating in August; that choice needs a screen with the options
visible at once, and the console has one.

### The weather band

`GET /v1/homes/{id}/weather`, composed from the household's own outdoor sensors
and from nothing else. Temperature, humidity, illuminance, air quality — each
one a reading with an age on it.

Most of the design is refusal:

- **No forecast.** Nothing in this building can measure tomorrow. A forecast
  needs a network and somebody else's service, and a panel showing one starts
  lying the moment the line is down — in the same typeface as the true numbers
  beside it. `"forecast": null` is in the payload as a statement, not an
  omission.
- **No invented reading.** A house with no outdoor thermometer gets no
  temperature, not an indoor one relabelled. Two outdoor sensors do not become
  an average, because an average is a temperature no sensor measured; the
  fresher one wins.
- **No condition that light cannot support.** The condition comes from measured
  illuminance — sun, cloud, twilight, night. Rain is not among them, and cannot
  be: a light sensor cannot tell a shower from a cloud, and no capability in the
  registry senses precipitation.
- **"Feels like" is withdrawn rather than aged.** The heat index needs both
  temperature and humidity; if either is stale the figure disappears. It is also
  absent below 27°, where the honest counterpart is wind chill and there is no
  wind capability to compute it from. The low-humidity adjustment matters here:
  without it the panel overstates a 41°/12% afternoon by several degrees.
- **Stale is shown with its age.** A blank where a humidity used to be reads as
  a broken panel; a plain number reads as current. Neither is true.

One line of small type under the reading says the numbers were measured at this
home. It is deliberately the smallest thing in the band and deliberately there —
a decade of phones has trained everybody to read a temperature block as
"somewhere near you, from the internet", and this one is neither.

**A bug found by looking at it.** The panel fetched `i18n.json` from cache. A
wall panel is powered on for years without anybody reloading it, so a hub update
that adds wording would leave the screen showing the previous dictionary — or,
for a new key, the key itself, which is exactly what the browser showed:
`weather_sun` in place of "مشمس". The fetch now revalidates.

The stepper is the one thing on the panel that does not mirror in Arabic. A
number line is not a reading direction: larger is right of smaller everywhere,
and mirroring would move the raise button to where the lower button was on the
same physical wall for a household that switches language.

Demo device names are now Arabic, because a device name is the household's own
words rather than a string the platform translates. A screen switched to English
still says مكيّف الصالة.

Verified live: pressing **+** on the living room air conditioner moved 23° to
24° through policy, orchestrator, gateway and twin; the kitchen light toggled.
Full suite: 1214 passed, 29 skipped. `make lint` clean over 210 source files.

### Two temperatures

"41 outside" is half a fact. The half a household acts on is the difference —
open a window, or is the cooling winning — so the band now carries an indoor
temperature beside the outdoor one, and the gap between them in words: **أبرد بـ
17°**.

The indoor figure is **one room's thermometer, named**. Not an average of the
house: averaging a shaded bedroom with a sunlit majlis produces a temperature no
sensor measured and no room feels like. The freshest reading wins, ties break on
the room name so the same house always shows the same room rather than whichever
device the twin returned first — a panel whose indoor reading hops between rooms
every five seconds is a panel nobody trusts. `indoor_rooms` says how many rooms
it is *not* speaking for.

The difference is withdrawn when either side is stale, because a difference
between a current reading and an hour-old one is arithmetic on two different
afternoons.

Room names get wording for the common ones and pass through untouched otherwise:
a room name is the household's own words, not a string the platform translates.

**A rendering bug fixed while looking at it.** A bare `38°` inside an Arabic
sentence renders as `°38` — the degree sign is direction-neutral and takes the
direction of the text around it. Every figure on the panel is now wrapped in a
directional isolate (U+2066 / U+2069). This affects any right-to-left screen
showing a number with a unit, which is most of them.

Verified live: بالخارج 41° مشمس · يُحَسّ كأنه 38° / بالداخل · الصالة 24° · أبرد
بـ 17°. Full suite: 1218 passed, 29 skipped; `make lint` clean.

**Checked while I was in there:** with no client attached, a freshly started hub
dispatches zero actions in eighty seconds and every device holds its seeded
value. Nothing in the platform commands an actuator on its own.

## The panel keeps its own copy of itself ✅

The platform has never needed the internet. What it needed was the hub — and the
panel is *served by* the hub, so a hub that was restarting (an update, a power
cut, a router that boots slower) left a browser error page on somebody's wall
where a control surface used to be. For a device whose whole job is to be there,
that is the worst failure it has.

`apps/wall-panel/static/sw.js` keeps the shell — page, styles, script, wording,
fonts — on the panel itself.

### The one rule

**Nothing under `/v1/` is ever cached, and never served from cache.** A cached
light switch on a wall is worse than a blank one, because somebody trusts it:
they press "off", the tile goes dark, and the light is still on in a room they
have already left. The panel may keep its own face offline, never its own idea
of the house. The gateway now sends `Cache-Control: no-store` on every API
response — including refusals, so a remembered 401 cannot lock a panel out after
its token was issued — which also stops a proxy or an extension from holding a
household's state anywhere the household did not put it.

### Three things the same bug was hiding

Building this surfaced three faults, each one the panel quietly lying:

1. **The tiles were left standing when the hub went away.** `refresh()` set an
   error line and returned, so the last state it saw stayed on the wall looking
   current — the exact thing every comment in that file warns against. The
   controls are now cleared.
2. **"All well" kept saying all was well.** A claim about the house, made by a
   panel that could not see the house. It goes blank.
3. **The panel stopped saying where it is.** The place came from the same pass
   that failed, though it lives in the panel's own storage. It is written at
   boot now: a screen that cannot say which hallway it is in looks broken in a
   way "cannot reach the hub" does not.

### Staying current without reloading under a hand

Shell files are answered from cache and revalidated behind the request, so a
panel on a wall for two years is not two years out of date. A changed ETag is
reported to the page, which reloads only at a quiet moment — never while a
hazard is on screen, never within a minute of a press, never mid-command.

### Where it does not run, and what covers that

Service workers need a secure context. A panel on the hub itself
(`http://localhost:8088/panel/`) gets all of this; a tablet on the LAN over
plain HTTP gets none of it, silently, because that is a browser rule. For those,
the gateway sends `max-age=300, stale-while-revalidate=2592000`, which lets the
browser's own cache cover a short restart less well. The real fix is a
certificate for the hub, and that is a decision about what an installer does in
somebody's house rather than code — written up as GAPS §2.7 with a
recommendation.

A development hub sends `no-store` for its own front end instead. A developer
who reloads and sees the previous version spends the next ten minutes debugging
the browser rather than the panel, which is exactly what happened the first time
these headers went in.

### A test for the thing that has no browser

`sw.js` is the only front-end file with real logic, and the suite has no browser
to run it in. `apps/wall-panel/tests/sw_harness.mjs` builds the smallest
environment a service worker needs — a `self`, a `caches`, a `fetch`, a
`Response` — and dispatches the browser's own events at it: install precaches
the shell and survives a missing font rather than failing wholesale, `/v1/` is
never intercepted, a cached file is served with the network down, an unseen page
falls back to the panel instead of the browser's error page, and a changed ETag
tells the page. It skips where `node` is absent, since the toolchain is Python.

### And a test file nobody was running

`testpaths` listed `libs`, `services`, `simulator`, `tests` — not `apps`. Every
front-end test, for the console and the panel both, was passing when run by hand
and skipped by every `make test`. **243 tests** were outside the suite. They all
pass; adding `apps` to `testpaths` cost nothing and would have caught any of
them the moment it broke. A test nobody runs is documentation with a false badge
on it — the same failure pattern as §6, one layer up.

**Verified in a real browser**, not only in the harness: with the hub stopped,
the panel reloaded from its own cache and drew itself — clock, place, and
"تعذّر الوصول إلى الهَب" — with no tiles and no claim about the house. Twenty
files cached, none of them under `/v1/`.

Full suite: 1465 passed, 29 skipped. `make lint` clean.

## The old platform's layout, ported ✅

You pointed at `smart-admin-eta.vercel.app` — the earlier SYLTRA Admin — and
asked for its layout. I could not sign in (I do not enter credentials or create
accounts), so the geometry came from the app's own stylesheet, which states it
exactly:

```
.sidebar { width: 232px; background: graphite; border-inline-end: hairline;
           position: sticky; top: 0; height: 100vh }
.content { flex: 1; padding: 1.75rem 2.25rem 4rem }
.card    { border: hairline; border-radius: 16px; background: graphite;
           padding: 1.25rem }
--r-sm: 2px  --r-md: 6px  --r-lg: 16px
.nav-item.active { background: rgba(ion, .14); color: ion }
```

Ported through `tokens.json` rather than by hand-editing CSS, so the console,
the catalogue and the wall panel all moved together and the generated files stay
generated (ADR-008):

- **Radii sharpened** to 2 / 6 / 16 / 20. This is the change you feel: controls
  at 6px instead of 10px read as an instrument rather than a phone.
- **Sidebar 232px** (was 264).
- **Content padding 28 / 36** (was 24 / 32).
- **The current nav item is now a wash of the accent** rather than a lighter
  grey. Grey said "hovered"; a tint says "here", which is what a sidebar of
  thirteen items has to answer from the corner of an eye.
- **Column headings set as small caps with air between them** — in Latin only,
  and not by preference: Arabic is a joined script, letter-spacing pulls the
  joins apart and renders a word as a row of disconnected shapes, and there is
  no case to raise. The Arabic heading keeps the same size, weight and colour
  without the treatment. The old platform never had to answer this, because it
  set its Arabic in a fallback font it never chose.

**Three things I did not copy, each for a reason:**

1. **The accent.** The old platform's is `#4c8dff`, a blue. Ours is Electric
   Cyan `#2BC4D9`, which the brand guidelines name as the identity colour and
   which the whole token set is built from. Changing it is a brand decision, not
   a layout one — say the word and it is one token.
2. **The top bar.** The old layout has none: sidebar and content, nothing else.
   Ours carries the property scope, the signed-in role and the language and
   theme controls. Dropping it would lose the household switcher and the role
   indicator, which the old single-account product never needed.
3. **The type.** Unbounded and Manrope, loaded from Google's servers. Both are
   Latin-only, so the old platform's Arabic — most of its interface — rendered
   in whatever the device happened to have. Ours is IBM Plex Sans Arabic and
   Inter, self-hosted, because a hub that fetches fonts from the internet is a
   hub that renders wrongly the day the line is down.

Full suite: 1465 passed, 29 skipped. `make lint` and `make contrast` clean.

## Scenes and goals — and the step that was never there ✅

Looking at the earlier SYLTRA product (`smart-admin-eta.vercel.app`) turned up
two ideas this platform did not have: **scenes**, the one-press shortcuts a
household actually uses, and **goals**, "you decide what must remain true".
Building them turned up a third thing, which was worse than either being
missing.

### An automation had never turned on a light

`ActionOrchestrator.execute` had exactly one caller in the platform: a person
pressing a control. The automation engine evaluated on a timer, produced
proposals, and stopped. A household could write a rule, watch a dry run say it
would fire, enable it, and wait forever.

That is the **fifth** time in this build that a correct, tested component had no
caller (§6 of GAPS). It was found the same way as the other four — by running
the thing rather than by writing another test.

`AutomationDispatcher` closes it, shaped like `IsolationDispatcher` so the two
objects that turn a decision into a command look alike and differ only in what
they may touch.

An automation is neither a recommendation nor a press, so the policy service has
a third gate rather than a reused one:

- **Kept:** a confirmed hazard stops it; a person who just touched the device
  overrides it (§0 rule 5); the rate limit holds, on the same counter as
  everything else, because a runaway rule is exactly what it is for.
- **Dropped:** confidence (a rule is not a guess), quiet hours (a household that
  wrote "porch light at 3am" asked for it), and the §19.2 learning ladder — it
  governs how far SYLTRA may act on what *it* inferred, and gating a
  hand-written rule on it would mean a new hub could not turn on a light until
  it had watched the household for a fortnight.

Using `evaluate` instead would also have meant inventing a `Recommendation` with
a fake model reference, which the audit trail would later show as a model's
decision to somebody trying to find out what turned on a light.

### Scenes

A scene is a named set of things to set at once, and it never fires on its own —
somebody presses it, every time. That difference is the whole security model.

An automation is confined to comfort (§2.3). A scene, having a person behind it,
may also **lock** a door. It may not **unlock** one: `SECURING_VALUES` is a
direction lock in the spirit of the risk engine's `FAIL_SAFE_VALUES`, and the
asymmetry is deliberate — refusing to unlock costs somebody a key, permitting it
costs one mistaken press, or one guest with a panel in a hallway. Valves,
breakers, sirens and cameras are out entirely.

A step names a device, a room, or the house, and expands against the twin when
pressed, so "all the lights off" keeps meaning that after somebody buys a lamp.

**Authorization is all-or-nothing; execution is not.** A "leaving" scene that
turns off the switches and cannot lock the door must not run half way — somebody
walks away believing the house is shut. Once authorized, one unplugged lamp must
not stop the rest, and the household is told exactly which steps were not
confirmed. The answer is `fully_carried_out`, never "ok".

### Goals

A goal is a sentence about a state rather than an event: *the living room is
never above 24*. It is checked on a clock, and it has an answer — including the
one every other product in this category rounds off.

**Unknown is not a shade of satisfied.** A goal whose sensor has gone quiet is
unmeasured, and an unmeasured goal never acts: correcting a room nobody can see
is guessing with somebody's air conditioning. A green tick for a room whose
thermometer died an hour ago is the exact failure this platform exists to
refuse, and it is a distinct state on the screen with its own wording.

Two more decisions worth naming:

- Where several devices report a room, **the worst reading decides** — never the
  mean. A mean is a temperature no room has, and it reports a goal satisfied
  while one corner is still thirty degrees.
- A goal the hub declines to correct because somebody is holding that device by
  hand reads as **HELD**, not as broken. Showing it as a failure would teach a
  household to ignore the colour, which is how a screen stops meaning anything.
  The loop and the screen call the same function, so they can never give two
  different answers about the same room.

The check may read anything. The correction reuses `AutomationAction`, so a
thing that acts unattended and repeatedly can never reach a lock.

### Where they are

Scenes are on the wall panel as tiles above the switches — that is the order
somebody standing in a hallway thinks in — and on the console with a per-device
answer after each press. Goals are on the console, read-only, because the
reading *is* the feature.

Both are new console navigation items, which §4 does not list. That divergence
is recorded in GAPS §5 rather than left in a test file.

Verified live throughout: the majlis light came on three seconds after the
kitchen light did; one press of *sleep* turned off five lights, closed a curtain
and set a bedroom to 21; and a goal caught 24.1 against a target of 24 and
dropped the living room air conditioning to 22.

Full suite: 1544 passed, 29 skipped. `make lint` clean over 223 source files.

## Layer 12 — the platform stops repeating a plan that is not working ✅

Clearing out `syltra concept/` turned up the product's founding document, and
one page of it described something this build got wrong. It is now
`docs/concept/SYLTRA_Adaptive_Concept.md`, §08:

> The air conditioning is on. The room reaches 27° and stops. The goal is not
> met. **The system does not repeat the same command.** It examines the
> difference, finds the window open, the curtains open and 43° outside, and
> changes the plan.

Goals had shipped the day before without that. A violated goal issued its
corrective actions, waited out its rearm, and issued exactly the same actions
again — forever, into a room with a window open. Every part was individually
right: the goal was right that the room was warm, the correction was right that
the air conditioning should be colder, the policy gate was right to allow it.
The loop as a whole was a machine for repeating a plan that was not working, and
calling it adaptive.

### What it decides

One question: **is the correction getting anywhere?** Answered by comparing the
reading now against the reading when the correction was issued, not by asking
again whether the goal is violated — which is equally true of a plan that is
working and a plan that is not.

- Moving toward the target by more than sensor noise → the plan is working.
  Leave it. Slow is not stalled, and re-issuing a command into a room that is
  already cooling is noise in an audit trail.
- Not moving, twice → **STALLED**. Stop re-issuing, and say so. Two attempts
  rather than one, because the first correction may have gone into a room
  somebody had just opened a door to, and one attempt is not evidence.

### What it refuses to decide

It does not invent a new plan. There is no Adaptive Planning Engine here
(concept Layer 08), and improvising one — closing a window on a household's
behalf because a room is warm — is exactly what §0 keeps away from a model.

What a stalled goal produces is a sentence a person can act on: *the living room
is still 24.1°, the air conditioning has been asked twice, and there is a window
open, a curtain open and 41° outside.*

### Obstacles are observed, never guessed

Everything in the obstacle list is read from the twin — a contact reporting
open, a cover reporting open, an outdoor thermometer — and each one carries the
device that reported it. "A window is open" is advice; "the living room window
is open" is something somebody can go and shut. Nothing infers an open window
from a temperature curve: a household told that, which then finds every window
shut, stops believing the next thing the panel says.

Two guards worth naming: a curtain at 10% is not what is keeping a room at 29°,
so a cover counts as open only past 40%; and 25° outside does not explain a room
that will not reach 24, so the weather is named only when it is more than eight
degrees past the target.

**Verified live**, not only in tests: the demo house holds a goal it cannot
reach. At t+40s it had been corrected twice; at t+60s it read *الخطة لا تنفع ·
جُرّب مرتين وما تغيّر شيء* with three obstacles — `window_living`,
`curtain_living`, `outdoor_temp` — and issued nothing further.

Full suite: 1556 passed, 29 skipped. `make lint` clean over 225 source files.

### What else came out of that folder

`docs/concept/` now holds six rescued documents with a README saying which are
live and which are superseded — including the earlier cloud-routing build prompt,
kept because it is where the decision that mattered most was made, and reversing
it later should mean reading it first. `SYLTRA_Claude_Code_Master_Build_Spec.md`
was also moved in: the document governing this whole build had been sitting
outside it, tracked by nothing.

## A hub that runs on a machine ✅

Asked for a simplified hub on a self-assembled mini-PC, before manufacturing.
The gap that turned up first is the one worth recording.

**There was no way to run this platform against a real house.** `devserver.py`
runs it against a synthetic household so a person can look at the console. Four
services have production entrypoints, each expecting NATS and Postgres beside
them. Between those two: nothing. The API gateway — which serves the console,
the wall panel, scenes, goals and every manual control — **had no `main` at
all**. Everything built over the past week could be demonstrated and could not
be installed.

### The shape

`syltra_api_gateway/hub.py` is one process holding the whole intelligence layer,
talking to a Home Assistant on the same box.

The seam that makes it possible was already there: `EdgeAgentService` takes its
publisher as an argument. In the distributed deployment that publisher writes to
NATS and the twin reads from it; here it hands each normalized envelope straight
to the twin and the adaptive engine. **One code path, not a second one for small
deployments** — the same service, connected differently.

Dropped for a single house: NATS, Postgres, Prometheus scraping. Kept: the
policy chain on every command, the safety governor on its own timer, and the
orchestrator's refusal to touch life-safety actuators outside production. A
prototype may lose yesterday's history. It may not lose the gate.

### Three refusals worth naming

- **No token, no start.** A hub that came up unable to reach Home Assistant
  would serve a console showing an empty house — which reads as *you have no
  devices* rather than *I am not connected*. It exits with the instruction
  instead.
- **No synthetic seed, asserted in a test.** A real hub showing a demo light
  beside a real one is worse than one showing nothing.
- **No broker imports, asserted on the parsed AST.** A comment saying "no NATS
  here" is not a guarantee; an import list is.

### One number found by running it

`verify_delay_seconds=1.5`. A real device takes a moment to report the state it
was just put into, and the orchestrator treats unverified as failed — at the
demo's `0.0` every light on a real panel would look broken.

### The machine, and what it is not

`docs/HUB_ON_A_MINI_PC.md` carries the hardware (8 GB, an SSD and not an SD
card, wired Ethernet, one Zigbee stick to start — and the USB-3 interference
that costs people days), the install path, and a section stating what the
prototype is not: tokens do not survive a restart, history does not survive a
restart, life-safety actuators stay blocked, it is plain HTTP on a LAN, and
nothing reaches the internet.

`infrastructure/scripts/install-hub.sh` installs Docker, `uv`, a `syltra` user
and the systemd unit — then **stops** and asks the operator to create the Home
Assistant token by hand. A script that creates a credential is a script that has
put one somewhere.

Verified on this machine: with a deliberately wrong token, the console, the
panel and the health endpoint all answered 200 while the Edge Agent reported
`Home Assistant rejected the token; retrying in 60s`. The API comes up even when
the house cannot be reached, which is the behaviour a person debugging an
installation needs.

Full suite: 1565 passed, 29 skipped. `make lint` clean over 227 source files.
