# SYLTRA safety case

Spec §18 states eighteen safety invariants and requires this document to map
each one to code, tests, logs, and operator controls. That mapping is below.

Two conventions used throughout:

- **Enforced by type** means a violation cannot be expressed in the codebase —
  the object required to do the forbidden thing does not exist, or refuses to be
  constructed. This is stronger than a check, because it cannot be forgotten.
- Every claim names a test. Run `make test-safety` to execute all of them
  (currently **275 tests**). **272 of them need no infrastructure at all** —
  no database, no message broker, no network, no ML runtime. The three that do
  exercise the dead-letter path and the encrypted-backup round trip against a
  real server, and skip cleanly when it is absent. Verified by running the suite
  with `POSTGRES_PASSWORD` and `NATS_PASSWORD` unset: **272 passed, 3 skipped**.

---

## 1. An AI recommendation is never an actuator command

**Code.** The Adaptive Engine's only output type is `Recommendation`
(`libs/contracts/recommendations.py`), which carries a target and a proposed
value but no dispatch mechanism. Reaching a device requires a `PolicyDecision`
and then an `ActionRequest`, produced by two other services.

**Enforced by type.** `ActionRequest.decision_id` is a required field, so an
action cannot be constructed without a policy decision in hand.

**Tests.** `test_a_recommendation_carries_no_execution_capability`,
`test_models_never_dispatch_actions`, `test_an_action_cannot_exist_without_a_decision_id`.

**Logs.** Every recommendation is published with its model name and version;
every action logs `ACTION_*` with its `decision_id`.

**Operator control.** Learning mode per home (`POST /learning-mode`); a home in
`OBSERVE` or `SHADOW` produces nothing actionable.

---

## 2. Every action passes through the Policy and Safety Service

**Code.** `ActionOrchestrator._preflight` re-fetches the decision and re-checks
`authorizes_execution_at(now)` immediately before dispatch — it does not trust
the caller's assertion that a decision existed.

**Tests.** `test_an_action_without_a_decision_on_record_never_dispatches`,
`test_only_an_allow_decision_reaches_a_device` (parametrized over all four
non-ALLOW outcomes), `test_a_decision_for_another_household_is_refused`,
`test_no_action_without_a_valid_policy_decision` (end to end), and — added in
Phase UI-3 — `test_approval_chain.py`, which drives the same guarantee over
HTTP rather than through the services directly.

That last file exists because of what its absence hid. Every test of this
invariant called the policy service in process, so nothing noticed that the
API never created a decision at all: `/recommendations` returned proposals and
`/approve` returned 404 for all of them. The invariant held — no action ran
without a decision — but only because no action could run. An invariant that
is satisfied by the feature being broken is not evidence that it works.

**Logs.** `POLICY_DECISION_CREATED` for every evaluation, including denials;
`ACTION_FAILED` with `NO_POLICY_DECISION` or `POLICY_DECISION_NOT_AUTHORIZING`.

**Operator control.** `HomePolicy` per home: consent, thresholds, quiet hours,
rate limits, and `unattended_automation`.

**Automations.** An automation is user-authored, which makes it trusted enough
to run without a fresh approval each time — not trusted enough to skip the gate
that checks quiet hours, manual override, rate limits and twin freshness. The
Automation Engine produces *proposals* and holds no gateway; a test asserts it
has no `execute`, `dispatch`, `send`, `gateway` or `orchestrator` attribute, and
that a proposal carries no field that could record a dispatch.

Spec §2.3 also limits automations to non-critical actions, and that is enforced
where the object is built rather than where it would run:
`AutomationAction` refuses at construction to name a capability that is
`LIFE_SAFETY_CRITICAL`, `SAFETY_RELATED` or `SECURITY_SENSITIVE`. An automation
that would close a valve or unlock a door cannot be stored, listed or exported,
so there is no later check to forget.
`test_an_automation_cannot_be_built_that_touches_a_critical_capability`.

**Shadow predictions.** Policy is never evaluated for a shadow prediction, so
no approvable decision exists for one and the API refuses approval with 404.
A shadow prediction is recorded and compared; it is not a proposal, and giving
one an approvable decision would be the §19.2 bypass outright.
`test_a_shadow_recommendation_is_never_given_an_approvable_decision`.

---

## 3. A stale recommendation cannot execute

**Code.** `Recommendation.expires_at` is required and validated to follow
`created_at`; `rule_expired_recommendations_never_execute` denies at policy;
`ActionRequest.is_expired_at` blocks at dispatch. Three independent layers.

**Tests.** `test_expired_recommendation_is_never_actionable`,
`test_expired_recommendations_are_denied`, `test_an_expired_action_never_dispatches`,
`test_an_expired_recommendation_never_reaches_a_device`.

**Logs.** `RECOMMENDATION_EXPIRED`, `ACTION_EXPIRED`.

---

## 4. A stale sensor value cannot confirm a risk

**Code.** The Digital Twin reports `UNKNOWN` / `KNOWN` / `STALE` per capability
against per-capability freshness windows (`capability_definitions.py`).
`CapabilityState.is_usable_for_decisions` returns False for anything but
`KNOWN`. `RiskEvidenceItem.can_confirm` requires `is_fresh`. The Safety
Governor rejects non-`KNOWN` readings before considering them.

**Tests.** `test_stale_value_is_never_usable_for_decisions`,
`test_stale_gas_reading_cannot_raise_a_risk_context`,
`test_a_stale_alarm_reading_cannot_confirm`,
`test_a_confirmed_case_cannot_rest_on_a_stale_alarm`,
`test_acting_on_non_fresh_state_is_denied`.

**Logs.** `CONFIRMATION_REJECTED` with `READING_STALE` / `READING_UNKNOWN`.

**Operator control.** Freshness windows are declared per capability and
reviewable in one file.

---

## 5. Manual user control cancels conflicting pending adaptive actions

**Code.** Two layers. `rule_manual_override_conflict` denies at policy when a
person operated the same device and capability within the override window
(default 30 min). `ActionOrchestrator.cancel_conflicting` cancels actions
already registered as pending.

**Tests.** `test_recent_manual_control_blocks_a_conflicting_action`,
`test_manual_control_on_another_device_does_not_block`,
`test_manual_override_cancels_a_pending_action`,
`test_manual_override_stops_the_chain` (end to end).

**Logs.** `USER_CONTROL_TAKES_PRECEDENCE` in the decision;
`ACTION_CANCELLED_BY_MANUAL_OVERRIDE` in the orchestrator audit.

**Operator control.** `HomePolicy.manual_override_window`.

**Design note.** The action is *denied*, not queued. Queuing would resume
overriding the person the moment the window lapsed.

---

**Automations.** An automation that would move something a person has just
moved does not get to. The engine takes the time each device and capability was
last set by hand and skips any automation whose action targets one inside the
override window, recording `MANUAL_OVERRIDE_ACTIVE` as the reason rather than
silently doing nothing. The window lapses, so one manual change does not
permanently disable an automation the household still wants.
`test_a_manual_change_stops_the_automation_that_would_undo_it`,
`test_the_manual_override_lapses_so_automation_resumes`.

## 6. Emergency actions require deterministic approved conditions

**Code.** `SafetyGovernor` is the only component that can produce a
`Confirmation`, and it does so from a fixed table of rules over certified alarm
capabilities. `assert_risk_transition` refuses `CONFIRMED` unless the caller
passes `deterministic=True`. `rule_life_safety_escalates_to_fixed_rules` returns
`ESCALATE_TO_FIXED_SAFETY_RULE` for any adaptive proposal touching a
life-safety capability.

**Tests.** `test_inference_can_never_reach_confirmed` (parametrized over every
advisory state), `test_life_safety_capabilities_escalate_to_fixed_rules`,
`test_no_confidence_however_high_unlocks_a_life_safety_capability`,
`test_a_fresh_certified_gas_alarm_confirms`.

**Logs.** `HAZARD_CONFIRMED` naming the rule and the authorized response.

---

## 7. Loss of the Adaptive Engine does not stop fixed automations or safety monitoring

This invariant has two halves, and until the automation engine existed only one
of them could be tested. The test named
`test_fixed_automation_is_unaffected_by_a_missing_adaptive_engine` exercised the
Safety Governor, because there were no fixed automations — so the invariant was
reported as satisfied on the strength of half of it. Both halves are now real.

**Code.** The Safety Governor imports nothing from the Adaptive Engine, no model
runtime, and no dataframe library. The policy rule chain is pure. The Automation
Engine (`services/automation-engine`) is likewise independent: automations are
typed data evaluated by a pure function, with no model anywhere in the path
(ADR-009).

**Tests.** `test_the_safety_path_imports_without_any_ml_package` and
`test_the_engine_imports_without_any_ml_package` each run a **fresh interpreter**
and assert that the import pulls in none of `sklearn`, `onnxruntime`,
`skl2onnx`, `polars` or `syltra_adaptive_engine` — so the guarantee cannot be
masked by another test's imports.
`test_confirmation_works_with_the_adaptive_engine_absent`,
`test_safety_monitoring_is_unaffected_by_a_missing_adaptive_engine`, and
`test_fixed_automation_is_unaffected_by_a_missing_adaptive_engine`, which now
runs an actual automation.

**Operator control.** A model can be suspended per home without affecting the
governor.

---

## 8. Loss of cloud connectivity does not stop local control

**Code.** No cloud connector exists yet, and the safety path holds no network
client of any kind.

**Tests.** `test_confirmation_does_not_touch_the_network` and
`test_risk_evaluation_does_not_touch_the_network` **disable `socket.socket`
entirely** and then confirm a hazard — any accidental DNS lookup, metrics push
or cloud check would raise rather than silently degrade.
`test_the_governor_holds_no_network_client`.

**Simulator.** The `internet_outage` scenario exercises local control while
offline.

---

## 9. Loss of the database must fail safely and prevent untraceable adaptive execution

**Code.** The Risk Engine and Safety Governor hold no database handle; their
inputs come from twin state, which is rebuilt from the event stream. Losing
storage costs history, not hazard detection.

**Tests.** `test_risk_state_is_reconstructable_without_a_database`,
`test_rebuild_after_reset_restores_the_same_state`.

**Closed in Phase 8.** `ActionOrchestrator` now refuses an adaptive action when
the durable audit sink is unreachable (`AUDIT_STORE_UNAVAILABLE`), while
deterministic safety responses continue — refusing to act on a confirmed hazard
because a log is down would be the more dangerous failure.

Additional tests: `test_an_adaptive_action_will_not_run_untraceably`,
`test_a_deterministic_safety_response_still_runs_without_the_audit_store`,
`test_the_in_memory_trail_survives_a_sink_failure`.

---

## 10. Duplicate events do not produce duplicate actions

**Code.** Four layers: JetStream `Nats-Msg-Id` dedup on the immutable event id;
`StateChangeNormalizer` duplicate detection; `TwinProjection.apply` ignoring a
repeated `event_id`; `UNIQUE(event_id)` on `device_events`; and
`derive_idempotency_key` making a redelivered action request return the original
result.

**Tests.** `test_duplicate_event_id_is_inert`,
`test_replaying_with_duplicates_yields_the_same_state`,
`test_a_duplicate_request_does_not_act_twice`,
`test_duplicate_requests_produce_one_device_command` (end to end).

**Logs.** `ACTION_DEDUPLICATED`.

---

## 11. Replayed historical events cannot trigger live actions

**Code.** `rule_replayed_history_never_executes` denies any recommendation older
than an hour. The Safety Governor checks **absolute age** against
`MAX_EVENT_AGE` (5 minutes) *separately from* the capability's freshness window,
so a generous window cannot become a replay loophole.

**Tests.** `test_replayed_historical_recommendations_are_denied`,
`test_a_replayed_historical_alarm_cannot_confirm`,
`test_replay_rejection_is_independent_of_the_freshness_window`,
`test_a_replayed_alarm_from_last_week_confirms_nothing`.

**Logs.** `HISTORICAL_REPLAY_SUSPECTED`, `HISTORICAL_REPLAY_REJECTED`.

**Simulator.** `historical_event_replay`.

---

## 12. Every sensitive action has an immutable audit trail

**Code.** `device_events` and `audit_events` carry a database trigger raising
`restrict_violation` on `UPDATE` or `DELETE`. The policy, orchestrator, risk and
feedback services each maintain an audit list with actor, reason and detail.

**Tests.** `test_every_action_leaves_an_audit_record`,
`test_denials_are_audited_as_carefully_as_approvals`,
`test_every_case_change_is_audited`,
`test_the_chain_leaves_a_complete_audit_trail`.

**Verified live.** `INSERT` succeeds; `UPDATE` and `DELETE` are rejected by the
database — on `device_events`, `audit_events`, and (since Phase 8)
`policy_decisions`, `action_requests`, `action_attempts`, `action_results`,
`user_feedback`, `manual_overrides` and `recommendations`.

The database also refuses a `CONFIRMED` risk case with no `confirmed_by`, so an
unattributed confirmation cannot exist even if written directly.

---

## 13. Locks, gas valves, breakers and emergency exits use separate policy classes

**Code.** Every capability declares a `SafetyClass` and a `Confirmation` level.
Life-safety actuators require `DETERMINISTIC_SAFETY_RULE`; security-sensitive
ones require `USER_APPROVAL`. Neither can be `NONE`.

**Tests.** `test_no_critical_actuator_permits_unconfirmed_automation`,
`test_life_safety_actuators_require_deterministic_rules`,
`test_security_sensitive_capabilities_always_require_approval`.

---

## 14. A model cannot raise its own permission level

**Code.** The learning mode lives on the *home*, not the model. `can_transition`
permits single-step moves only, so `OBSERVE → AUTHORIZED_AUTOMATION` is
impossible. The API returns 409 on a skip.

**Tests.** `test_observe_cannot_jump_to_authorized_automation`,
`test_a_home_cannot_skip_from_observe_to_authorized_automation`,
`test_the_api_refuses_a_lifecycle_skip`,
`test_a_suspended_home_cannot_return_directly_to_automation`.

**Verified live.** The running container returned HTTP 409 with the spec
citation.

---

## 15. A model version cannot activate without evaluation and explicit promotion

**Code.** `ModelVersion` cannot be constructed without evaluation metrics.
`ModelRegistry.promote` is a separate act that refuses versions failing their
`EvaluationGate`. An `ACTIVE` version must record `promoted_at`.

**Tests.** `test_a_version_without_evaluation_cannot_exist`,
`test_a_version_failing_its_evaluation_gate_cannot_serve`,
`test_registered_versions_do_not_serve_until_promoted`.

**Logs.** `MODEL_REGISTERED`, `MODEL_ACTIVATED`, `MODEL_PROMOTION_REFUSED`.

**Operator control.** `POST /models/{name}/promote|rollback|suspend`.

---

## 16. Development and simulation block real critical actuator targets

**Code.** Two layers. `HomeAssistantDeviceGateway.execute_capability_command`
refuses critical capabilities when the environment is development or
simulation. `ActionOrchestrator._preflight` refuses again, independently.

**Tests.** `test_critical_actuators_are_blocked_in_development` (parametrized
over both environments).

**Logs.** `CRITICAL_ACTUATOR_BLOCKED_IN_DEVELOPMENT`.

**Operator control.** `SYLTRA_ENVIRONMENT`.

---

## 17. Safety rules must be testable without ML services running

**Code.** The governor and the policy chain are pure functions over twin state
and configuration.

**Tests.** The entire `services/risk-engine/tests/` and
`services/policy-safety/tests/` suites construct no model, and
`test_the_safety_path_imports_without_any_ml_package` proves the dependency
closure stays clean in a fresh interpreter.

---

## 18. Critical rules use approved sensor alarm states and device capabilities, not inferred text or LLM output

**Code.** `CERTIFIED_ALARM_CAPABILITIES` is a closed set of five.
`RiskEvidenceItem.can_confirm` requires both the origin *and* the capability to
qualify — claiming `CERTIFIED_ALARM` origin on `energy.power` confirms nothing.
`RiskCase` validation rejects a confirmed case whose evidence contains no
qualifying reading. `RiskProposal` cannot express a confirmed state at all.

**Tests.** `test_a_non_certified_capability_cannot_confirm`,
`test_a_non_certified_capability_never_confirms`,
`test_a_confirmed_case_must_carry_certified_evidence`,
`test_a_rule_cannot_even_construct_a_confirmed_proposal`.

**SILA.** The interface accepts structured intents only, never free text
converted to actuator calls (spec §14.10). No LLM output reaches any safety
path.

---

## Gaps closed in Phase 8

| Gap | How it was closed |
|---|---|
| Audit records were in memory only | The spec §13 tables now exist with append-only triggers; the orchestrator writes through a durable sink |
| Invariant 9 was not enforceable | An unreachable audit store now blocks adaptive execution while safety responses continue |
| No watchdog supervised the governor | `libs/operations/watchdog.py` supervises every service; `risk-engine` and `policy-safety` are marked critical and alert on restart |

## Remaining gaps

Recorded honestly rather than closed prematurely:

| Gap | Consequence | Resolves in |
|---|---|---|
| Confirmed hazards notify and isolate | **Closed for gas.** A confirmed gas hazard closes the valve automatically (owner decision, 2026-08-20), direction-locked so nothing can reopen one, verified by read-back, escalating when unverified. Water still prepares; egress and ventilation stay blocked. `dispatch_isolation` is tested and not yet wired into the running services | Wiring: the remaining step |
| Update and rollback is designed, not implemented | `docs/architecture/DEPLOYMENT.md` describes the intended sequence | Next iteration |

## Observing only: a hub that cannot act

The protections that stop SYLTRA acting were, until now, three separate things
someone had to get right: the learning mode, the absence of automations, and the
policy gate. Any one of them being wrong meant the platform could move something
in an occupied home. For a first pilot that is the wrong shape of guarantee.

`OrchestratorConfig.dispatch = OBSERVE_ONLY` makes it one thing.

**Code.** The check sits at the top of `_preflight`, the single function every
dispatch passes through, before the expiry check, before the decision lookup,
before anything. It ignores safety class entirely — including a confirmed safety
response, which is the case most likely to argue for an exception and the one
where an exception would be least defensible in a stranger's home.

**Tests.** `test_an_observing_hub_sends_nothing_to_a_device`,
`test_observe_only_holds_for_every_safety_class` (parametrized over all five),
`test_observe_only_is_checked_before_anything_else` — which proves ordering by
handing it a request that would otherwise fail for a different reason and
asserting the observe refusal is what returns —
`test_an_observing_hub_records_what_it_would_have_sent`, and
`test_dispatch_is_enabled_by_default`, because a mode that could switch itself
on silently would be its own hazard.

**Logs.** `ACTION_FAILED` with `DISPATCH_DISABLED_OBSERVE_ONLY`, and a detail
carrying the capability, device, value and safety class of the command that was
not sent. That record is the deliverable of a pilot week, not a side effect of
it.

**Operator control.** The console's System Health says *"This hub is watching,
not acting"* before anything else on the page, and lists whether the hub can act
as a plain fact. A pilot should not have to read a config file to know.

---

## Notify, isolate, and what still cannot happen

Spec §20.4 gives the AI role as "notify and prepare the allowed response", with
confirmed actions left to deterministic rules. On 2026-08-20 the product owner
made the decision that section leaves open: **a confirmed gas hazard closes the
valve.**

The reasoning, recorded because a future reader deserves it rather than the
conclusion alone: a certified detector reaching its alarm threshold is not an
opinion about whether there is gas. It is a measurement that there is. A design
that then asks a sleeping household for permission is a design that trades
minutes of exposure for a confirmation nobody is awake to give. Closing on a
false alarm costs a cold kitchen until somebody reopens the supply. Not closing
on a real one costs more.

**Notify** executes. `notification.send` is NON_CRITICAL and requires no
confirmation. It now tells the household the supply *has been* closed rather
than asking whether it should be — people need to know before they go looking
for a pilot light that will not relight.

**Isolate** executes, and only in one direction. This is where the safety of
the whole change lives:

- `FAIL_SAFE_VALUES` maps each isolable capability to its single safe value.
  `valve.state` maps to `"closed"` and to nothing else. `ResponseStep` rejects
  any ISOLATE step carrying a different value, so there is no argument through
  which a confirmed hazard, a miscarried rule or a future edit to a response
  definition can reopen a gas supply.
- The dispatcher re-checks the direction rather than trusting the planner,
  because a check that exists only upstream is a check the next caller skips.
- `PolicyService.authorize_safety_isolation` refuses any capability not
  governed by a `DETERMINISTIC_SAFETY_RULE`, any value that is not the fail-safe
  one, and any request that does not name the confirmation authorizing it. The
  decision it mints carries no `recommendation_id`, because there is no
  recommendation: the authority is the Safety Governor.
- Reopening is a person's job. Nothing in the platform sets a valve to `open`,
  and after a leak that is the point — restoring gas to a house whose fault the
  platform cannot see is the hazard, not the recovery.

**Verification is not optional.** An `IsolationOutcome` reports `succeeded`
only when the device confirmed the new state. A command that was accepted and
changed nothing — the failure mode a naive implementation misses, where nothing
errors and the gas keeps flowing — reports `ISOLATION_UNVERIFIED` and escalates.
A home with no reachable valve reports `NO_REACHABLE_ISOLATION_DEVICE` loudly,
because that is exactly the case where silence reads as safety.

**Execute, in general, is still absent:**

- `ResponseStage` has three members and none of them can drive an arbitrary
  capability to an arbitrary value.
- `siren.state` and `breaker.state` pass the deterministic-rule gate and still
  cannot be isolated: nobody has decided which way is safe for them, and
  silencing a siren during a fire is worse than either direction of a valve.
- Water still prepares rather than isolates. A leak damages property; gas kills
  people, and the decision that was made covered gas. Extending it quietly
  would be a decision nobody made.
- Unlocking egress and starting ventilation remain blocked. Neither is cutting
  a supply — one opens a door, one energizes a device.
- Development and simulation still block every critical actuator (invariant
  16). A development machine has no gas valve, and a simulation that closed one
  would be closing something real by accident.
- No AI is anywhere in the chain. The governor confirms from certified alarm
  capabilities only, and the isolation test constructs no recommendation, no
  model reference and no confidence score.

**Tests.** `tests/safety/test_gas_isolation.py` (16), covering the happy path,
both wrong-direction refusals, the forged-step recheck, the three failure modes,
and the development block. `services/risk-engine/tests/test_response.py` pins
the direction constraint at the type level.

**Not yet wired.** `dispatch_isolation` is tested end to end against the
orchestrator, and nothing in the running services calls it: `RiskEngineService`
plans and records outcomes but does not dispatch, and the API gateway reports
`carried_out: false` honestly because nothing has. Wiring it into the
composition root is the remaining step, and it is deliberately a separate,
visible act.

