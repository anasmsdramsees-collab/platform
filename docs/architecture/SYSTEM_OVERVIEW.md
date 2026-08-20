# System Overview

SYLTRA Adaptive Edge Platform — what exists today and where it is going.

## The shape of the system

```text
Devices and protocols
        ↓
Home Assistant Core            (embedded, replaceable, UNMODIFIED — ADR-001/004)
        ↓ supported WebSocket API
SYLTRA Edge Agent              ← DeviceIntegrationGateway boundary
        ↓ normalized SYLTRA contracts
NATS JetStream
        ↓
Digital Twin · Context Engine · Adaptive Engine · Risk Engine
        ↓
Policy and Safety Service  →  Safety Governor
        ↓
Action Orchestrator  →  back through the gateway to devices
        ↓
Local API Gateway  →  SILA and the local console
```

The load-bearing idea: **Home Assistant is a device driver, not the product.**
Everything above the gateway boundary speaks only in canonical capabilities
(`environment.temperature`, `light.brightness`, …), never vendor entity names.
Replacing Home Assistant with native Matter/Zigbee adapters means writing one new
gateway adapter, not rewriting the intelligence layer.

## What is implemented

| Component | State | Where |
|---|---|---|
| Canonical contracts (envelope, capabilities, enums, gateway interface) | ✅ Phase 0–1 | `libs/contracts` |
| Eventing (subjects, streams, validated publishing, dead-letter) | ✅ Phase 1 | `libs/eventing` |
| Observability (JSON logs, secret redaction, correlation IDs) | ✅ Phase 1 | `libs/observability` |
| Edge Agent (HA WebSocket, mapping, normalization, publishing, health) | ✅ Phase 1 | `services/edge-agent` |
| `HomeAssistantDeviceGateway` adapter | ✅ Phase 1 | `services/edge-agent/gateway.py` |
| Deterministic simulator + mock HA boundary | ✅ Phase 1 | `simulator/` |
| Digital Twin, Context, Adaptive, Risk, Policy, Actions, API, SILA | ⬜ Phase 2–7 | `services/*` |

## Data flow today

1. A device changes state; Home Assistant emits `state_changed`.
2. The Edge Agent normalizes it: one **raw** envelope (device's own words) and
   zero or more **normalized** capability envelopes, sharing a `correlation_id`.
3. Duplicates are suppressed; out-of-order events are flagged and down-weighted;
   structurally invalid payloads go to the dead-letter stream with reason codes;
   entities outside the capability model are rejected rather than guessed.
4. Envelopes are published to JetStream with `Nats-Msg-Id = event_id`, so
   redelivery deduplicates at the broker too.

See `docs/architecture/EVENT_MODEL.md` for the contract detail.

## Operating principles in force

- **Local-first.** No cloud path exists in the platform. Losing the internet
  cannot affect local control because nothing local depends on it.
- **Vendor-abstracted.** Core services import `syltra_contracts`, never Home
  Assistant modules.
- **Fail visible, not silent.** Unmapped and invalid events are counted,
  logged with reason codes, and routed to the dead-letter stream.
- **Secrets never travel.** The Home Assistant token is held as `SecretStr`,
  injected by environment, and stripped from every log line by a redaction
  filter — verified by test and by inspecting a running container.
- **Advisory AI.** No model output can reach an actuator. Today no model exists;
  when one does (Phase 4), it produces recommendations that must clear the
  Policy and Safety Service (Phase 5–6) before any action.
- **Critical actuators blocked in development.** The gateway refuses lock, valve,
  breaker, siren, and garage commands in development and simulation environments
  (safety invariant 16), before target resolution.

## Resilience already demonstrated

- The Edge Agent survives Home Assistant restarts, reconnecting with bounded
  exponential backoff and jitter (verified: 1.1s → 2.2s → 3.8s → 8.1s, capped).
- With Home Assistant absent, the agent stays **live** but reports **not ready**
  (503) rather than crash-looping.
- After reconnect it re-bootstraps registries and re-seeds current state, so a
  consumer can rebuild from the normalized stream alone.

## Next

Phase 2 adds the Digital Twin: versioned JSON Schemas, database migrations,
deterministic state rebuild from the event stream, and home/room/device APIs.
