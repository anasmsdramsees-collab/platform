# ADR-009: Automations are typed rules, not a scripting language

- Status: accepted
- Date: 2026-08-20
- Context: spec §2.3 (safe automation), §0 rules 12 and 16, safety invariants 2,
  5 and 7; UI guidelines §17.8

## Context

The platform has an intelligence layer that proposes and a policy layer that
decides, but nothing a household can author itself. Every recommendation ends
at "wait for a person". Spec §2.3 asks for the missing piece: *"execute only
user-authorized, non-critical actions through a policy and safety gate, then
verify the resulting device state."*

Safety invariant 7 adds a constraint that shapes the whole design: **loss of
the Adaptive Engine does not stop fixed automations.** An automation is not an
AI output. It must keep working when every model is suspended.

## Decision

Automations are **typed data**, evaluated by a pure function. There is no
expression language, no script, no user-supplied code.

An automation is a trigger, zero or more conditions, and one or more actions.
Each is a small closed union — a capability crossing a threshold, a context
being active, a value being set. Adding a new kind of condition means adding a
variant to the type and a branch to the evaluator, both of which are reviewed.

### Why not an expression language

A DSL is the obvious answer and the wrong one here:

- **It is an interpreter.** Whatever the syntax, something evaluates
  user-supplied text against live home state. That is a class of vulnerability
  this platform does not otherwise have, in the one component that commands
  devices.
- **It cannot be checked before it runs.** "This automation may only touch
  non-critical capabilities" is a property you can decide by looking at typed
  data. On an expression it is a halting problem in miniature, and the honest
  answer becomes "we check at dispatch", which is later than a household
  deserves.
- **It defeats the summary.** §17.8 asks for a readable summary before save and
  conflict validation. Both are straightforward over a closed structure and
  approximate over free text.

The cost is real: a household cannot express something the types do not
support, and some automations people want will not be writable. That is the
trade, and it is the right way round for a system that turns on heaters in
rooms where people sleep.

### Non-critical only, enforced at construction

§2.3 says non-critical. An `AutomationAction` refuses at construction to target
a capability whose safety class is `LIFE_SAFETY_CRITICAL` or
`SECURITY_SENSITIVE`. Not checked at dispatch — refused at the point the object
is made, so an automation that would unlock a door cannot be stored, listed,
exported, or reasoned about as if it might one day run.

This is the same pattern as `RiskProposal` refusing to hold `CONFIRMED` and
`ResponseStage` having no `EXECUTE`: make the dangerous state unconstructable
rather than unreachable.

### Independent of the Adaptive Engine

The engine imports nothing from `syltra_adaptive_engine`, no model runtime and
no dataframe library, and a test runs a fresh interpreter to prove it. Invariant
7's "fixed automations" half previously had nothing to test on — the test named
for it exercised only the Safety Governor.

### Still behind the policy gate

An automation produces a *proposal*, exactly as the Adaptive Engine does, and
that proposal goes through the Policy and Safety Service. An automation is
user-authored, which makes it trusted enough to run without a fresh approval
each time — not trusted enough to skip the gate that checks quiet hours,
manual override, rate limits and twin freshness.

Concretely: the engine never holds a gateway, and cannot dispatch.

### Feedback loops

§14.8 requires that automation-generated state changes do not feed back. Two
mechanisms, because one is not enough:

- an automation records the actions it caused, and will not re-trigger on a
  state change matching one of them within the action's own verification
  window;
- every automation carries a minimum re-arm interval, and cannot fire again
  for the same trigger inside it.

The first stops the direct loop (an automation turning on a light, seeing the
light turn on, and turning it on again). The second bounds any loop the first
misses, including one that runs through a second automation.

## Consequences

- A household cannot write arbitrary logic. Accepted; see above.
- New trigger and condition kinds need a code change and a release. Accepted:
  the alternative is a component that changes behaviour without review.
- The visual builder §17.8 describes is **not** built by this decision. The
  types are what a builder would produce; the builder itself, its version
  history and its rollback are separate work.
