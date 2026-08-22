# System Overview

SYLTRA Adaptive Edge Platform — the shape of the system and its event model.

For an explanation of the whole platform written for a person rather than a
component, start with [`docs/PLATFORM_OVERVIEW.md`](../PLATFORM_OVERVIEW.md).
This document is the architectural detail behind it.

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

Every component below is built and tested. `IMPLEMENTATION_STATUS.md` carries the
phase-by-phase history and the acceptance evidence for each.

| Component | Where |
|---|---|
| Canonical contracts (envelope, capabilities, enums, gateway interface) | `libs/contracts` |
| Eventing (subjects, streams, validated publishing, dead-letter) | `libs/eventing` |
| Observability (JSON logs, secret redaction, correlation IDs, metrics) | `libs/observability`, `services/*/metrics.py` |
| Edge Agent (HA WebSocket, mapping, normalization, publishing, health) | `services/edge-agent` |
| `HomeAssistantDeviceGateway` adapter | `services/edge-agent/gateway.py` |
| Deterministic simulator + mock HA boundary (21 scenarios) | `simulator/` |
| Digital Twin (deterministic projection, fingerprints, freshness) | `services/digital-twin` |
| Context Engine (13 deterministic contexts) | `services/context-engine` |
| Adaptive Engine (3 models, ONNX, learning ladder, drift suspension) | `services/adaptive-engine` |
| Automation Engine (typed user rules, non-critical only) | `services/automation-engine` |
| Policy and Safety Service (16 rules, 5 outcomes) | `services/policy-safety` |
| Action Orchestrator (verification, retry, manual override, observe-only) | `services/action-orchestrator` |
| Risk Engine (advisory) and Safety Governor (deterministic confirmation) | `services/risk-engine` |
| Feedback Service | `services/feedback-service` |
| Local API Gateway, console, SILA | `services/api-gateway`, `apps/` |
| Encrypted backup, privacy export and deletion, watchdogs | `libs/operations` |

**Not built:** the Cloud Connector (`services/cloud-connector/` is a placeholder;
§14.11 specifies it and nothing depends on it), installations, user management,
and execution of a confirmed-hazard response — the last needs product-owner
approval under spec §0 rule 9.

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
- **Advisory AI.** No model output can reach an actuator. A recommendation must
  clear the Policy and Safety Service, and a person or a deterministic rule must
  authorise it, before anything is dispatched.
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

## Observing only

The Action Orchestrator can be configured so that **nothing reaches a device at
all** — `DispatchMode.OBSERVE_ONLY`. Everything else still runs, and each refusal
records the command that was not sent. This is the posture a first run in a real
home should use; see `docs/pilot/PILOT_CHECKLIST.md`.

## Where to go next

- [`docs/PLATFORM_OVERVIEW.md`](../PLATFORM_OVERVIEW.md) — the whole platform, explained
- [`EVENT_MODEL.md`](EVENT_MODEL.md) — how state becomes knowledge
- [`../safety/SAFETY_CASE.md`](../safety/SAFETY_CASE.md) — the safety argument, in evidence
