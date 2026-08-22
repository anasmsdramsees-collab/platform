# ADR-010 — Access is an invitation, never a consequence of selling

**Status:** Accepted
**Date:** 2026-08-21
**Decided by:** the product owner

## Context

SYLTRA will be sold to individuals, to distribution companies, to installers,
and to institutions. That answer arrived late in the build and it is the one
that could have broken the platform's central promise.

Every screen, every token and every test in this repository rests on **home
isolation**: a principal is bound to a set of homes and can address no other.
The promise made to a household is stronger than that — its behaviour stays in
its house.

A channel is the natural enemy of both. The obvious design gives a distributor a
fleet dashboard over the hubs it sold, and that dashboard cannot be local-first
and cannot avoid seeing when people are home. Almost every smart-home platform
has made this trade quietly.

## Decision

**A distributor has no access to anything.**

Selling a hub does not create a relationship with the house it went into. There
is no distributor role, no fleet view, no telemetry flowing outward by default,
and no setting that turns one on.

The only route in is an invitation:

- **`SUPPORT`** — SYLTRA's own technician, granted by the owner when they want
  help, expiring after four hours. It can read the home, read diagnostics and
  write automations, which is what remote programming needs. It cannot see a
  camera, cannot manage users, cannot read the audit trail.

- **`VIEW_CAMERA`** — its own permission, held by `OWNER` and `ADULT` only. The
  gateway removes capabilities the caller may not see from the device payload
  entirely rather than blanking them, because a key present with a null value
  still says *there is a camera here and you may not see it*.

- **`Organisation`** — a company holding units it does not live in. It becomes
  the `OWNER` of each unit, because that is what it is: the party who decides
  who may enter. It grants the tenant a membership and revokes it when the
  tenancy ends, through the directory that already existed.

- **`transfer_ownership`** — selling a unit is one call, not three.

## Why each rule is shaped the way it is

**Support expires without anybody closing it.** A support session is one
problem, not a relationship. Four hours is shorter than an installer's
afternoon on purpose.

**Support can program, and that is safe by construction rather than by trust.**
`AutomationAction` refuses any capability outside NON_CRITICAL and COMFORT, so a
support session cannot reach a lock, a valve or a breaker however it is used.
The safety comes from the contract, not from the role being well-behaved.

**Cameras are excluded by a permission, not by a capability name.** A name-based
exclusion is forgotten by whoever adds `camera.doorbell` next year. A permission
nobody holds excludes everything under the domain the day it appears.

**A company is an `OWNER`, not a new kind of owner.** A separate role would be
the same authority wearing a different name, and two names for one authority is
how one of them drifts.

**Selling is one call because three calls are three chances to do two of them.**
The order is not an implementation detail: the buyer is made owner *first*, so
the last-owner rule never sees a unit with nobody in charge and refuse the
revocation the sale depends on. Then everyone else is revoked. Then the history
is erased.

**The history is erased, and erasure is a required argument.** A buyer has no
business learning when the previous tenant slept, and this platform knows such
things because knowing them is its job. `erase_history` has no default, so a
future edit cannot quietly make it optional. It is injected rather than
imported: this module knows who may hold a unit and has no business knowing how
an event store deletes a past, and wiring that in would make a permissions
library a data-deletion library.

**The support account survives a sale.** A new owner inheriting a flat still
needs somebody to call.

**The tenant is told.** A company that can see the devices in the flat somebody
lives in is a condition of the tenancy rather than a discovery, and the Users
and Roles screen says so above the member list — where a person scrolling is
already asking who can see their home.

## Consequences

**What this costs.** A distributor cannot tell a customer why their hub is
offline without being invited in. That is a real support burden, and it is the
price of the promise. It can be reduced later by a household opting into
operational telemetry through the cloud connector — which already has the
allowlist, the redaction and the per-destination consent to do it honestly — but
that is opt-in and it is not this decision.

**What this preserves.** Home isolation stays true. Nothing sits above the hubs.
The offline guarantee is unaffected, because there was never anything to be
offline from.

**What is still open.** A company sees occupancy and motion in a rented flat,
and those say much of what a camera would. The owner accepted that: the company
owns the asset. If it later proves too much, the same operational/behavioural
split the cloud connector already implements is where the line would move.

## Alternatives rejected

**A fleet dashboard with household consent.** Considered, and made unnecessary
by the decision rather than rejected on its merits. Consent that arrives with a
product a household has already paid for is not freely given, and a dashboard
nobody built cannot be quietly widened.

**Excluding cameras by capability name.** Simpler today, wrong the first time
somebody adds a second camera capability.

**A `PROPERTY_COMPANY` role separate from `OWNER`.** Two names for one
authority. Rejected.
