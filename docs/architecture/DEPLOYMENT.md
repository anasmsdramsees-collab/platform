# Deployment

## Development

One command:

```bash
make up
```

Brings up Home Assistant (pinned `2026.8.1`), Mosquitto, NATS with JetStream,
PostgreSQL 16, and the SYLTRA services. Everything is on a private container
network; only developer-facing ports are published, and only on loopback.

| Service | Port (loopback) | Purpose |
|---|---|---|
| Home Assistant | 8123 | **Diagnostic UI only** — never the customer experience |
| NATS | 4222 | Local client access |
| PostgreSQL | 5432 | Local client access |
| Mosquitto | 1883 | Local client access |
| Edge Agent | 8081 | Health and metrics |
| Digital Twin | 8082 | Health, metrics, read APIs |
| Context Engine | 8083 | Health, metrics, contexts |
| Adaptive Engine | 8084 | Health, metrics, models |
| API Gateway | 8080 | **The only service intended for household access** |

Nothing binds `0.0.0.0` on the host. The container-internal binds are inside the
private network.

## Production target: the SYLTRA Hub

| Requirement | Why |
|---|---|
| Linux, containerized services | Matches development; one artifact per service |
| Secure boot | The hub sits in someone's home |
| Hardware-backed device identity where available | Unique hub identity (spec §25.1) |
| Encrypted storage | Household behavioural history at rest |
| Ethernet + Wi-Fi | Ethernet preferred; Wi-Fi as fallback |
| Zigbee and Thread radios | Direct device integration |
| Local UPS or graceful shutdown | An unclean shutdown mid-action is the worst case |
| Signed updates | Supply chain (spec §25.4) |

Spec §6.2 is explicit that production hardware assumptions must not leak into
business logic, and they have not: no service reads a radio, a TPM, or a
battery. The hub is where the containers run, not something the code knows
about.

## Resource limits

Compose sets memory and CPU limits per service. The limits reflect what each
service actually does: the Adaptive Engine trains models and gets the largest
allowance; the Safety Governor's host, the Risk Engine, gets a modest but
**guaranteed** reservation, because a safety component starved of memory by a
noisy neighbour is a safety failure.

## Restart and supervision

Every service runs with `restart: unless-stopped`, and the watchdog
(`libs/operations/watchdog.py`) supervises health endpoints above that. Docker
restarts a *crashed* process; the watchdog catches a process that is running but
no longer answering — the failure mode that would otherwise be silent.

Critical services (`edge-agent`, `risk-engine`, `policy-safety`) raise an alert
on restart, because their absence means the home is unmonitored and the
household should be told rather than left to notice.

## Update and rollback

The intended shape, not yet implemented (tracked in `IMPLEMENTATION_STATUS.md`):

1. Signed image bundle, verified before anything is written.
2. Database migration applied inside a transaction where the change permits.
3. Services restarted one at a time, health-checked between each.
4. **Safety services last** — the platform should never be mid-update on its
   safety layer while its comfort layer is already running new code.
5. Automatic rollback if a health check fails after a bounded wait.
6. Model versions roll back independently of code (already implemented).

## Backup

```bash
make backup   # writes an AES-256-GCM encrypted archive
make restore  # verifies and restores
```

See `docs/operations/BACKUP_RESTORE.md`.

## What is deliberately absent

- **No cloud connector.** Not implemented, not configured, no credentials.
- **No inbound internet exposure.** Nothing in the compose file publishes a port
  beyond loopback, and the hub is not expected to be reachable from outside the
  home network.
- **No Home Assistant modification.** It runs as an unmodified upstream image
  (ADR-001, spec §0 rule 11).
