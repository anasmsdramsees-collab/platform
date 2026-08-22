# Hardware Integration Contract (Stage 19)

Any future SYLTRA hardware (Hub, Switch, Sense, Relay, Air, Panel — section 50) must satisfy this contract before it can join the platform. This is what "Hardware Readiness" (section 51) means concretely, expressed against the schema and APIs already built in Stages 1-17.

Manufacturing must not start before a device implements this contract and passes the Virtual Device E2E flow with a software stand-in (section 50).

## 1. Device Identity

- A globally unique, immutable hardware identity (e.g. a signed serial number / secure element ID), established at manufacturing time.
- Maps to `devices.device_key` once claimed by a hub — never to a Home Assistant `entity_id` (section 14's device abstraction boundary applies to real hardware too, not just HA-backed virtual devices).

## 2. Capabilities

- On first connect, the device must declare its capability set using the existing model (`device_capabilities`: `capability`, `unit`, `metadata`). See `backend/api/src/devices/dto/upsert-device.dto.ts` for the exact shape the cloud already accepts.
- Capability names must come from the shared vocabulary already in use (`power`, `temperature`, `mode`, `fan_speed`, `brightness`, `value`, `state`, ...) — extend `backend/edge-agent/src/capability-mapper.ts` (or the hub-native equivalent) rather than inventing per-device ad hoc names.

## 3. State

- Reports state using the existing `device_states` shape: `{ device_external_ref, capability, value, unit?, quality }`, matching `IncomingStatePayload` in `backend/api/src/state/state.service.ts`.
- `quality` must be one of `valid | stale | unknown` — a device that cannot vouch for a reading must say so rather than report a stale value as `valid`.

## 4. Commands

- Accepts commands shaped like `DeviceCommand` (`capability`, `action`, `value`, `correlation_id`) over the same MQTT command topic the Edge Agent already subscribes to (`syltra/{tenant}/hubs/{hub}/commands`).
- Must publish a result event (`CommandExecuted` or `CommandFailed`, carrying the same `correlation_id`) on the events topic — this is how `CommandsService.handleEventMessage` closes the loop and updates `device_commands.status`.
- Command execution must be idempotent per `correlation_id`: a retried command must not double-apply.

## 5. Events

- Uses the existing `DeviceEventType` vocabulary (`DeviceConnected`, `DeviceDisconnected`, `StateChanged`, `CommandExecuted`, `CommandFailed`, ...) — see `backend/api/src/database/entities/device-event.entity.ts`. Do not introduce a parallel event taxonomy.

## 6. Firmware Version

- Reports a semantic firmware version string on connect and after every update, recorded via `firmware_versions` (`hub_id` or `device_id`, `version`, `released_at`).
- OTA updates must support rollback (section 53) — a device that cannot roll back a failed update is not ready for fleet deployment, even if it's ready for a single pilot install.

## 7. Health

- Reports the health fields already modeled for hubs (`online`, `last_seen`, `cpu`, `memory`, `storage`, `ha_status`, `edge_status`, `mqtt_status`, `cloud_status`) or devices (`online`, `last_seen`, `availability`, `battery`, `signal`, `error`) per section 44 — on the hub's health MQTT topic (`syltra/{tenant}/hubs/{hub}/health`) at a regular interval (30s is the current Edge Agent default, see `backend/edge-agent/src/config.ts`).

## 8. Security Identity

- Authenticates using a device-scoped credential, never a shared/global secret. For hubs today this is the pairing-token JWT issued at registration (`HubsService.register`, `type: 'hub'` claim) — real hardware should graduate this to a hardware-backed secure element identity issued during manufacturing, with the pairing token becoming a one-time provisioning step rather than the long-lived credential.
- Only a `secret_ref` (pointer into a secret manager) is ever persisted server-side (`device_credentials.secret_ref`) — never a plaintext key.

## What's explicitly out of scope for Stage 1

PCB specifications, enclosure design, and certification are not addressed here (section 52: "final PCB specs are not fixed before the software stack is tested"). This contract only defines the software/protocol surface a physical device must speak.
