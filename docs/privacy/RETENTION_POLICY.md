# Retention policy

Spec §26 requires retention to be documented for every event stream and table.
The principle behind the numbers: **raw data is kept briefly, decisions are kept
long.** A raw motion reading loses value within a day; the record of *why the
platform did something* is what a household or an investigator needs a year
later.

## Event streams (JetStream)

Configured in `libs/eventing/streams.py`, tunable per deployment.

| Stream | Subjects | Retention | Why |
|---|---|---|---|
| `SYLTRA_RAW` | `syltra.raw.>` | **24 hours** | High-frequency, high-volume, useful only for debugging the integration boundary |
| `SYLTRA_NORMALIZED` | `syltra.normalized.>` | 7 days | Twin rebuild and short-window model training |
| `SYLTRA_DERIVED` | twin, context, ai, risk, policy, action, feedback | 30 days | Replay and explanation |
| `SYLTRA_SYSTEM` | `syltra.system.>` | 3 days | Operations only |
| `SYLTRA_DEADLETTER` | `syltra.deadletter.>` | 7 days | Long enough to diagnose a bad integration |

Raw retention is deliberately the shortest of any stream, satisfying spec §12's
requirement that "raw high-frequency data must have shorter retention than
derived events".

## Tables

| Table | Retention | Deletion mechanism |
|---|---|---|
| `device_events` | 90 days | Scheduled purge by `occurred_at` |
| `device_current_states` | Until the device is removed | Cascade from `devices` |
| `devices`, `rooms`, `device_entities` | Until deleted by the household | `delete_home()` |
| `contexts`, `context_evidence` | 30 days | Scheduled purge |
| `recommendations` | 30 days | Scheduled purge |
| `policy_decisions` | **1 year** | `delete_home()` only |
| `action_requests`, `action_attempts`, `action_results` | **1 year** | `delete_home()` only |
| `user_feedback` | **1 year** | `delete_home()` only |
| `risk_cases`, `risk_evidence` | **2 years** | `delete_home()` only |
| `audit_events` | **2 years** | `delete_home()` only |
| `model_versions` | Until superseded + 90 days | Model lifecycle |
| `system_health_events` | 3 days | Scheduled purge |

## Why the long tails are append-only

`policy_decisions`, `action_requests`, `action_results`, `user_feedback` and
`audit_events` carry database triggers refusing `UPDATE` and `DELETE`. Retention
for these is enforced by whole-partition expiry or by household deletion, never
by editing rows — a record that can be quietly amended is not an audit record
(safety invariant 12).

`risk_cases` and `contexts` are **not** append-only, because a case legitimately
moves through its state machine and a context is refreshed as evidence changes.
Their transitions are recorded in `audit_events`, which is immutable.

## Retention by privacy class

Retention is configurable per stream so a deployment can tighten it for a class
without code changes (spec §12: "retention must be configurable per privacy
class"). `ensure_streams(js, max_age_overrides=...)` takes the overrides.

A deployment that wanted `HOUSEHOLD_PRIVATE` raw data gone within an hour would
pass `{"SYLTRA_RAW": timedelta(hours=1)}` — no rebuild required.

## What retention does not cover

Household deletion is immediate and total, and overrides every number above.
`delete_home()` removes every row across all 20 household tables and then
verifies the result; the report is incomplete if anything remains.
