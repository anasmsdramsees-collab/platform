# Data inventory

What SYLTRA holds about a household, why, and for how long. Spec §26 requires
this to exist and to be honest; the point of writing it down is that anything
not listed here should not be collected.

## Data classes

Every event carries a `privacy_class`, and the class determines where the data
may go.

| Class | Meaning | May leave the hub? |
|---|---|---|
| `PUBLIC` | Nothing household-specific | Yes |
| `SYSTEM_INTERNAL` | Service health, versions, metrics | Aggregate only, opt-in |
| `HOUSEHOLD_PRIVATE` | Device state, contexts, routines, actions | **No**, by default |
| `PERSONAL_SENSITIVE` | Anything tied to a named individual | **No** |
| `SAFETY_CRITICAL` | Alarm states and risk cases | **No** |

The default for device and behavioural data is `HOUSEHOLD_PRIVATE`, set at the
Edge Agent as events are normalized — so a new capability inherits the strict
class rather than a permissive one.

## What is held

| Data | Where | Class | Why it exists | Retention |
|---|---|---|---|---|
| Raw device events | `syltra.raw.*` (JetStream) | HOUSEHOLD_PRIVATE | Debugging the integration boundary | **24 hours** |
| Normalized capability events | `syltra.normalized.*`, `device_events` | HOUSEHOLD_PRIVATE | Twin rebuild, model training, audit | 7 days (stream) / configurable (table) |
| Current device state | `device_current_states` | HOUSEHOLD_PRIVATE | The digital twin | Until the device is removed |
| Device and room registry | `devices`, `rooms`, `device_entities` | HOUSEHOLD_PRIVATE | Naming and location | Until deleted |
| Contexts and evidence | `contexts`, `context_evidence` | HOUSEHOLD_PRIVATE | Explaining why something happened | 30 days |
| Recommendations | `recommendations` | HOUSEHOLD_PRIVATE | Explanation and feedback linkage | 30 days |
| Policy decisions | `policy_decisions` | HOUSEHOLD_PRIVATE | Audit: what was allowed and refused | 1 year, append-only |
| Actions and results | `action_requests`, `action_results` | HOUSEHOLD_PRIVATE | Audit: what the platform did | 1 year, append-only |
| Feedback | `user_feedback` | HOUSEHOLD_PRIVATE | Learning what the household wants | 1 year, append-only |
| Risk cases and evidence | `risk_cases`, `risk_evidence` | SAFETY_CRITICAL | Incident record | 2 years |
| Audit trail | `audit_events` | HOUSEHOLD_PRIVATE | Who did what | 2 years, append-only |
| Model versions and cards | `model_versions` | SYSTEM_INTERNAL | Reproducibility and rollback | Until superseded + 90 days |
| Service health | `system_health_events` | SYSTEM_INTERNAL | Operations | 3 days |
| Access tokens | in memory | PERSONAL_SENSITIVE | Authentication | 12 hours, **hash only** |

## What is deliberately *not* held

Spec §3 and §26 rule these out, and nothing in the codebase collects them:

- **No microphone recordings.** No audio path exists.
- **No raw video or camera frames.** The camera capability records
  *availability* and recording state, never imagery.
- **No biometric templates or facial recognition.**
- **No continuous location history.** Presence is a boolean per tracker, not a
  coordinate trail.
- **No individual identity beyond a household-assigned label.** `CHILD_PRESENT`
  comes from a device the household designated, never from recognition.

## Identifiers

`home_id`, `hub_id` and `device_id` are opaque local identifiers. They are
meaningful only on this hub. In diagnostic bundles they are replaced by salted
pseudonyms (`syltra_operations.privacy.pseudonymize`), so support can correlate
events within one bundle without being able to build a mapping across bundles.

## Household rights

| Right | How | Where |
|---|---|---|
| See everything held | `export_home()` returns every table | `libs/operations/privacy.py` |
| Delete everything | `delete_home()` deletes, then **verifies** | same |
| Withdraw consent per feature | `HomePolicy.consented_policies` | `services/policy-safety` |
| Stop a recommendation type permanently | `NEVER_REPEAT` feedback | `services/feedback-service` |

Deletion verifies rather than assuming: `DeletionReport.complete` is False if
anything remains, so a partial deletion is visible rather than silently reported
as success.
