# ADR-004: Home Assistant version pin and compatibility matrix

- Status: Accepted
- Date: 2026-08-18
- Deciders: Implementation engineering (Phase 1)
- Extends: ADR-001 (HA as replaceable integration runtime), ADR-002 (toolchain)

## Context

Spec §0 rule 18 requires latest stable dependencies compatible with the selected
Home Assistant version, exact lockfile pins, and a recorded compatibility matrix.
Phase 0 left the container on the moving `:stable` tag, which makes builds
non-reproducible and lets an upstream release silently change the integration
surface the Edge Agent depends on.

## Decision

Pin Home Assistant Core to **`ghcr.io/home-assistant/home-assistant:2026.8.1`**.

The Edge Agent depends only on this documented, long-stable WebSocket API surface:

| Command / message | Used for | Stability |
|---|---|---|
| `auth_required` / `auth` / `auth_ok` / `auth_invalid` | handshake | stable since 0.7x |
| `get_states` | bootstrap current state | stable |
| `config/device_registry/list` | device identity and area | stable |
| `config/entity_registry/list` | entity→device mapping | stable |
| `config/area_registry/list` | room names | stable |
| `subscribe_events` (`state_changed`) | live state stream | stable |
| `call_service` | actuator dispatch (gateway adapter) | stable |
| `ping` / `pong` | keepalive | stable |

## Compatibility matrix

| Component | Pinned version | Notes |
|---|---|---|
| Home Assistant Core | 2026.8.1 | Unmodified container (ADR-001) |
| NATS Server | 2.11-alpine | JetStream enabled |
| Eclipse Mosquitto | 2 | Auth required, no anonymous |
| TimescaleDB / PostgreSQL | latest-pg16 | Exact digest pinned in Phase 2 with migrations |
| Python | 3.12.13 | via `uv` (ADR-002) |
| aiohttp / nats-py / pydantic | exact pins in `uv.lock` | regenerate with `uv lock` |

## Consequences

- Upgrading Home Assistant is a deliberate change: bump the tag, run
  `make test-integration`, and update this matrix in the same commit.
- The mock Home Assistant boundary in `simulator/` reports `2026.8.1-sim` and
  implements exactly the surface listed above, so a drift between the mock and
  the real runtime shows up as a failing integration test rather than a
  production surprise.
- Because core services depend only on the SYLTRA gateway interface, an HA
  upgrade can only affect `services/edge-agent`, never the intelligence layer.
