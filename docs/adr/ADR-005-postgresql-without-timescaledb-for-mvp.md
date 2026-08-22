# ADR-005: PostgreSQL 16 without TimescaleDB for the MVP

- Status: Accepted
- Date: 2026-08-18
- Deciders: Implementation engineering (Phase 2)

## Context

Spec §7.4 specifies "PostgreSQL for relational data" and "TimescaleDB for
time-series events **if compatible with the selected target**" — the extension is
explicitly conditional, not mandatory.

Two considerations decided it:

1. **Target compatibility is unproven.** The production target is a SYLTRA Hub
   (spec §6.2) whose final SBC, architecture, and base image are not yet fixed.
   Committing the schema to an extension that may be unavailable — or awkward to
   build — on that hardware would be a premature constraint.
2. **The MVP's volumes do not need it.** Spec §24.8 targets ≥100 simulated
   devices and ≥50 events/second in short bursts. Plain PostgreSQL with the
   indexes already defined on `device_events(home_id, occurred_at)` and
   `(device_id, capability)` handles that comfortably.

## Decision

Use **plain PostgreSQL 16** for the MVP. Do not depend on TimescaleDB anywhere in
the schema, queries, or migrations.

Keep the door open deliberately:

- `device_events` is a conventional append-only table with time-ordered indexes.
  Converting it to a hypertable later is an additive migration, not a redesign.
- No query uses Timescale-specific syntax, so adopting it changes performance
  characteristics only, never results.
- Retention today is enforced at the event-bus layer (JetStream `max_age` per
  stream, spec §12) and by explicit deletion routines, not by extension features.

## Revisit when

Any of these becomes true:

- measured `device_events` growth threatens query latency targets (spec §24.8);
- the chosen SYLTRA Hub image ships or easily builds the extension;
- continuous aggregates would meaningfully simplify the Adaptive Engine's
  feature pipeline (Phase 4).

At that point, add a hypertable migration plus a compression/retention policy and
update this ADR rather than replacing it.

## Consequences

- The development stack uses `postgres:16-alpine`, which is smaller and faster to
  pull than the Timescale image (a practical benefit for `make bootstrap` on a
  clean machine).
- Time-based retention for household data remains an explicit, auditable routine
  rather than an implicit extension behavior — which suits the privacy
  requirements in spec §26, where retention must be documented per stream and
  table.
