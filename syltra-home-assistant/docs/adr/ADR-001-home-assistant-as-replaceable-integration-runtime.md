# ADR-001: Home Assistant as a replaceable device-integration runtime

- Status: Accepted (mandated by master spec §4.9)
- Date: 2026-08-18
- Deciders: SYLTRA product owner (via master build specification)

## Context

SYLTRA needs broad device connectivity (Matter, Zigbee, Thread, Wi-Fi, Bluetooth,
vendor integrations) on day one, without coupling its proprietary intelligence layer to
any single integration technology, and without forking an open-source project it does
not control.

## Decision

Use **Home Assistant Core as an embedded, replaceable device-integration runtime**
inside the SYLTRA Hub environment — never as the SYLTRA product core.

- Home Assistant runs unmodified in its own container. No fork, no source edits, no
  frontend re-skinning; its UI is a development/installer diagnostic tool only.
- Integration happens exclusively through supported APIs (WebSocket primarily, REST
  where WebSocket is unsuitable) plus a separate custom integration
  (`home-assistant/custom_components/syltra_edge/`).
- SYLTRA owns a `DeviceIntegrationGateway` interface with operations `list_devices`,
  `list_entities`, `get_state`, `subscribe_state_changes`,
  `execute_capability_command`, `get_device_health`, `get_registry_snapshot`.
  `HomeAssistantDeviceGateway` is one adapter behind it.
- Core services (Digital Twin, Context Engine, Adaptive Engine, Risk Engine, Policy
  Service, Safety Governor, Action Orchestrator, SILA, UI) depend only on the SYLTRA
  interface and canonical capability contracts — never on Home Assistant entity
  objects or internal Python modules.

## Boundary

```text
Devices and protocols → Home Assistant Core → (supported APIs)
  → SYLTRA Device Integration Gateway / Edge Agent → (normalized SYLTRA contracts)
  → Digital Twin, Context, AI, Risk, Policy, Actions, SILA and UI
```

Home Assistant is responsible for device discovery, protocol-facing entity
representation, registries, standard service calls, and local state-change events.
SYLTRA is responsible for everything above the normalized contract line.

## Consequences

- Replacing Home Assistant (e.g., with native Matter/Zigbee gateway adapters) must not
  require rewriting any core service — only a new gateway adapter.
- Apache-2.0 obligations for Home Assistant Core are honored in
  `THIRD_PARTY_NOTICES.md`; HA trademarks are never presented as SYLTRA property.
- The Edge Agent must translate vendor entities into normalized capabilities (spec
  §10); no vendor entity name may leak past the gateway.
- An HA version pin plus compatibility matrix is recorded when the container is first
  exercised (Phase 1).
