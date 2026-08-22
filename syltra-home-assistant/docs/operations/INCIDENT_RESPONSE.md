# Incident response

## Severity

| Level | Meaning | Response |
|---|---|---|
| **S1** | The home is unmonitored, or a confirmed hazard is unacknowledged | Immediate |
| **S2** | Safety monitoring degraded — stale detectors, offline hub | Same day |
| **S3** | Automation misbehaving; safety intact | Next working day |
| **S4** | Cosmetic or advisory | Backlog |

The distinction that matters: **a home that believes it is protected and is
not** is S1, even if nothing has gone wrong yet.

## First five minutes

1. **Is safety monitoring running?**
   `curl localhost:8080/v1/system/status | jq .components`
2. **Is there an open confirmed risk case?**
   `curl "localhost:8080/v1/homes/$HOME/risks"` — look for `advisory: false`.
3. **Has the platform been acting?**
   `curl "localhost:8080/v1/homes/$HOME/actions"`
4. **Preserve the audit trail.** Take a backup *before* restarting anything.
   `audit_events` is append-only and survives a restart, but a backup is
   cheaper than regret.

## Specific incidents

### A confirmed hazard the household did not act on

The Safety Governor confirmed from a certified alarm. Contact the household
directly — do not assume a notification was seen. The case names the rule that
confirmed it and the response it authorized.

The platform will not have operated a gas valve or breaker: those require a
deterministic approved rule, and the MVP authorizes a response name without
executing it.

### The platform did something the household did not want

The chain is fully traceable. Given an action id:

```bash
curl "localhost:8080/v1/homes/$HOME/actions/$ACTION" | jq
curl "localhost:8080/v1/audit?home_id=$HOME" | jq
```

Every action names its decision; every decision names its reason codes and
carries an `input_hash` you can recompute from the recorded evidence to prove
what state it was evaluated against.

Immediate mitigation, in increasing severity:

1. `NEVER_REPEAT` feedback on the recommendation type.
2. Suspend the model: `POST /v1/homes/{home}/models/{name}/suspend`.
3. Move the home down the learning ladder to `OBSERVE`.
4. Withdraw the feature's consent entirely.

### A device did something the platform did not do

Check whether an action exists at all. If the audit trail has no action for that
device at that time, SYLTRA did not command it — look at Home Assistant's own
automations, a vendor cloud, or a physical control.

### Suspected compromise

1. Revoke every token for the subject: `TokenStore.revoke_subject()`.
2. Rotate the Home Assistant long-lived token.
3. Rotate NATS and PostgreSQL credentials; restart services.
4. Review `audit_events` for actions with an unexpected actor.
5. Take a backup **before** remediating, for the record.

Tokens are stored as hashes, so a stolen database does not yield usable
credentials.

### The audit store is unreachable

Adaptive execution stops automatically — `AUDIT_STORE_UNAVAILABLE` — because an
action that cannot be recorded must not run (safety invariant 9). Deterministic
safety responses continue: refusing to act on a confirmed hazard because a log
is down would be the more dangerous failure.

Restore the database; adaptive execution resumes on the next successful write.

## Diagnostics for support

```bash
make diagnostics
```

Produces a bundle with pseudonymized identifiers and no secrets or
household-private values. Safe to send. The pseudonym salt stays on the hub, so
the mapping cannot be reconstructed elsewhere.

## After an incident

- Write down what the platform *decided* and why, using the audit trail. The
  reason codes are stable identifiers; quote them.
- If a safety invariant was involved, check `docs/safety/SAFETY_CASE.md` for the
  test that covers it and confirm it still passes. If the invariant held and the
  outcome was still wrong, the invariant is incomplete — that is a spec change,
  not a code patch.
- Add a simulator scenario reproducing the incident before fixing it.
