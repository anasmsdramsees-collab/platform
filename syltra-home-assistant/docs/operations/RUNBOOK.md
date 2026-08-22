# Operations runbook

For whoever is on the other end when a hub misbehaves. Ordered by what you
should check first, not by what is most interesting.

## First: is the home safe?

Before diagnosing anything, establish whether safety monitoring is running.

```bash
curl -s localhost:8081/health/ready   # edge agent — is data arriving?
curl -s localhost:8080/v1/system/status | jq .components
```

If `risk_engine` or `policy_safety` is not `ok`, the home may be unmonitored.
That is the priority, ahead of any comfort feature.

**Safety monitoring does not depend on the Adaptive Engine, the database, or the
network.** If those are down and the Risk Engine is up, hazard detection is
still working — this is asserted by the safety suite, not assumed.

## Health checks

Every service exposes the same three endpoints:

```text
/health/live    the process is running
/health/ready   it is doing its job
/metrics        Prometheus format
```

`live` without `ready` means the service started but cannot reach a dependency —
usually NATS or PostgreSQL.

## Common situations

### No events arriving

```bash
make logs            # tail structured logs
curl localhost:8081/metrics | grep syltra_edge_events
```

1. Is Home Assistant up? `docker compose ps homeassistant`
2. Is the token valid? A rejected token logs
   `Home Assistant rejected the access token` and the Edge Agent stays alive at
   `503`, retrying — it does not crash, so the log is where to look.
3. Is NATS reachable? `syltra_edge_connected` is `0` when not.

### Events arriving, nothing happening

Check the learning mode:

```bash
curl -s localhost:8080/v1/homes/$HOME/models | jq .learning_mode
```

A home in `OBSERVE` or `SHADOW` is *supposed* to do nothing visible. This is the
most common "bug report" that is not a bug.

### Recommendations appear but never execute

Read the decision reasons — the platform always explains itself:

```bash
curl -s "localhost:8080/v1/audit?home_id=$HOME" | jq '.items[] | select(.source=="policy")'
```

Frequent legitimate causes: `AUTOMATION_NOT_YET_TRUSTED` (the home has not been
advanced up the learning ladder), `RECENT_MANUAL_OVERRIDE` (someone touched the
device), `TARGET_STATE_NOT_FRESH` (a sensor stopped reporting).

### A safety sensor stopped reporting

This raises a `DEVICE_FAILURE` risk case with `PROTECTION_GAP`, at HIGH
severity. It is not a nuisance alert: a home that looks quiet because its
detectors went silent is the failure this case exists to surface. Replace or
reconnect the device.

### The dead-letter stream is filling

```bash
curl localhost:8081/metrics | grep syltra_edge_events_invalid
```

Usually a device reporting a non-numeric value for a numeric capability. The
dead-letter record names the reason code and the entity.

## Restarting

```bash
docker compose restart <service>
```

Safe at any time. Every service rebuilds its state from the event stream, and
the twin is deterministic — an identical event sequence produces identical
state, which is why a restart is not a risk.

Restart **safety services last** if you are restarting several.

## Backup and restore

See `BACKUP_RESTORE.md`. Take a backup before any upgrade or migration.

## Escalation

| Situation | Action |
|---|---|
| Safety service `FAILED` in the watchdog | Immediate. The home is unmonitored. |
| Confirmed risk case open and unacknowledged | Immediate — contact the household. |
| Repeated `AUDIT_STORE_UNAVAILABLE` | Adaptive execution has stopped by design; restore the database. |
| Model suspended by drift | Not urgent. The platform has stood itself down correctly. |

## What not to do

- **Do not** modify Home Assistant Core to work around an integration problem
  (spec §0 rule 11). Fix it in the Edge Agent or the `syltra_edge` integration.
- **Do not** disable the policy gate to "just make it work". Every action goes
  through it; that is the design, not an obstacle.
- **Do not** edit `audit_events`, `policy_decisions` or `action_results`. The
  database will refuse, and the attempt is itself worth investigating.
