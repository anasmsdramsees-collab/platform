# Policy and Actions

This is the phase where SYLTRA can move something in a real home. Everything
before it observes and infers; everything here commits. The architecture is
built around one idea: **the gap between deciding and doing is where mistakes
become physical**, so every check is repeated at the moment of dispatch rather
than trusted from earlier in the pipeline.

## Three objects, three services

```text
Recommendation  →  PolicyDecision  →  ActionRequest  →  device
 (Adaptive)         (Policy/Safety)    (Orchestrator)
```

They are separate types produced by separate services, and none can be
constructed from thin air:

- An `ActionRequest` **cannot exist without a `decision_id`** — the field is
  required, so there is no shortcut from a model output to a device command
  (safety invariant 2).
- A `PolicyDecision` records reason codes, the safety class, the policy version,
  and an `input_hash` over exactly the facts it was evaluated against. An
  auditor can recompute that hash from stored evidence and prove *which state*
  a decision was made against.
- Both carry expiries, so staleness is a property of the object rather than a
  check someone might forget (invariant 3).

## The policy rule chain

Sixteen deterministic rules, evaluated in a fixed order, short-circuiting on the
first non-`ALLOW` outcome. **Priority is positional**: a denial early in the
chain can never be softened by a more permissive rule later.

Nothing in the chain calls a model, reads the network, or consults an LLM. That
is what makes two spec claims true rather than aspirational: safety rules are
testable without ML services running (invariant 17), and they keep working when
the Adaptive Engine is down (invariant 7).

| Order | Rule | Outcome when it fires |
|---|---|---|
| 1 | Shadow recommendation | `DENY` |
| 2 | Recommendation expired | `DENY` |
| 3 | Historical replay suspected | `DENY` |
| 4 | Life-safety capability | `ESCALATE_TO_FIXED_SAFETY_RULE` |
| 5 | Active risk case | `DENY` |
| 6 | Consent not granted | `DENY` |
| 7 | Household said never again | `DENY` |
| 8 | Recent manual control | `DENY` |
| 9 | Target state not fresh | `DENY` |
| 10 | Confidence below threshold | `DENY` |
| 11 | Already at proposed value | `DENY` |
| 12 | Cooldown active | `DENY` |
| 13 | Rate limit exceeded | `DENY` |
| 14 | Quiet hours | `PREPARE_ONLY` |
| 15 | Capability requires approval | `REQUIRE_USER_APPROVAL` |
| 16 | Automation not yet trusted | `REQUIRE_USER_APPROVAL` |

A few choices worth explaining:

**Life-safety capabilities escalate rather than deny.** Gas valves, breakers and
sirens return `ESCALATE_TO_FIXED_SAFETY_RULE` — the intent is handed to the
deterministic rule that owns them, which is the only authority permitted to act
(invariants 6, 13, 18). No confidence, however high, changes this; the
escalation is categorical, not a threshold certainty can clear.

**Manual control denies outright rather than queuing.** A person who just
adjusted a device has expressed a more recent and more authoritative intent than
any model. Queuing the action would resume overriding them the moment the window
lapsed, which is exactly the behavior spec §0 rule 16 forbids.

**Quiet hours return `PREPARE_ONLY`, not `DENY`.** The intent stays valid and can
execute when quiet hours end. Silent capabilities (thermostat setpoints) are
exempt; lights and covers are not, because they would wake a household.

**Approval issues a new decision.** `approve()` does not mutate the pending
record — the original `REQUIRE_USER_APPROVAL` stays in the audit trail exactly as
evaluated, and the approval is a separate, attributable act.

Denials are audited as carefully as approvals. After an incident the question is
what the system *refused*, not only what it permitted.

## The dispatch sequence

The orchestrator re-checks everything at dispatch time:

1. **Refuse without a live `ALLOW`** — the decision is re-fetched and
   re-evaluated, not taken on faith from the caller.
2. **Refuse an expired action.**
3. **Deduplicate by idempotency key** — derived as
   `home:decision:capability:action_n`, so a redelivered request returns the
   original result instead of acting twice (invariant 10).
4. **Re-check current state** — if the device is already where we want it,
   nothing is dispatched.
5. **Dispatch through the `DeviceIntegrationGateway`**, never a vendor API.
6. **Verify the expected state transition.** An action succeeds because the
   device *reports* what we asked for, not because the call returned.
7. **Retry only transient failures.** A gateway refusal is the integration's
   considered answer; repeating it would re-send a command already declined.
8. **Compensate where valid** — restore the previous value when verification
   fails and the capability is reversible.

Two details that came out of building it:

- **One clock per call.** `execute(request, now=...)` pins the clock for the
  entire call. Mixing an injected instant with wall-clock reads let preflight
  and the retry loop disagree about the current time — a TTL check could pass in
  one place and fail in another.
- **Critical actuators stay blocked in development** regardless of what policy
  said (invariant 16), checked in the orchestrator as defense in depth on top of
  the gateway's own block.

## Feedback, and the loop it breaks

`ACCEPT`, `REJECT`, `NOT_NOW`, `MODIFY`, `UNDO`, `NEVER_REPEAT` — each linked to
the recommendation it answers.

Standing per recommendation type moves asymmetrically. **Trust is slow to earn
and quick to lose**: a rejection costs 0.15, an acceptance returns 0.05, and an
undo costs more than a rejection because the household let it happen, saw the
result, and reversed it. `NOT_NOW` changes nothing — it is about timing, not
substance. `MODIFY` is partial agreement: small penalty, and the value the
household actually wanted is kept as evidence.

The subtle requirement is spec §14.8's last line: *prevent feedback loops caused
by automation-generated state changes*. When SYLTRA sets a thermostat, the
thermostat reports the new value back through the event stream. If that echo
counted as the household expressing a preference, the platform would treat its
own guess as confirmation and reinforce it indefinitely. So every state change
is classified — a change arriving within 90 seconds of our own write to the same
capability is an `AUTOMATION_ECHO`, recorded for audit but never allowed to move
preference.

`NEVER_REPEAT` feeds back into the policy service's suppression list, so the
household's refusal actually stops future proposals rather than merely being
recorded.

## What is still missing

Persistence. Decisions, actions and feedback live in memory and are rebuilt from
the event stream; the `policy_decisions`, `action_requests`, `action_results` and
`user_feedback` tables arrive with the API Gateway in Phase 7, which is the first
consumer that needs history rather than current state.
