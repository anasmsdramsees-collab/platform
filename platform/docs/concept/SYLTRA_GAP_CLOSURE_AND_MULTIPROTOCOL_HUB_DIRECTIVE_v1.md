# SYLTRA Gap Closure and Multi-Protocol Hub Directive v1

Status: Approved implementation directive

Date: 2026-08-20

Applies to: SYLTRA Adaptive Platform, SYLTRA Hub, SYLTRA Home console, Edge Agent, protocol services, pilot deployment, and repository gap tracking.

## 1. Purpose

This directive closes the product decisions recorded in `SYLTRA_GAPS(1).md`, defines the missing engineering work, and makes multi-protocol device connectivity a release requirement for SYLTRA Hub.

The hub must support these protocol families through local-first integrations:

- Z-Wave
- Zigbee
- Matter over Wi-Fi, Ethernet, and Thread
- Wi-Fi and Ethernet devices with supported local APIs
- Bluetooth Low Energy
- Thread as an IPv6 mesh transport used by Matter or HomeKit-compatible integrations

"Support" does not mean every product carrying a radio logo will expose every vendor-specific feature. SYLTRA must maintain a tested compatibility registry and must not claim full compatibility for an untested device model.

## 2. Binding product decisions

### 2.1 Confirmed gas hazard actuator

Decision: a confirmed gas hazard may prepare a shutoff command, but the MVP must not execute a gas-valve action without explicit owner confirmation.

Required flow:

1. A certified gas detector creates a deterministic confirmed hazard.
2. The Safety Governor identifies the mapped valve and verifies reachability.
3. The system notifies occupants and presents the exact proposed valve action.
4. An Owner or authorized Safety Operator confirms the action using a two-step confirmation.
5. The Action Orchestrator executes the command, verifies the reported valve state, and records the result.
6. A failed or unverified shutoff escalates immediately and never appears as successful.

Automatic shutoff is excluded from the MVP. It requires a later certified installation profile, compatible actuator, risk review, regulatory review, explicit owner opt-in, and a tested fallback procedure.

### 2.2 Installations, users, and roles

Decision: include them in the MVP.

Minimum roles:

- Owner
- Household Admin
- Resident
- Installer
- Guest
- Auditor or Support
- Safety Operator, assignable only by an Owner

Required controls:

- least privilege;
- separate comfort, security, commissioning, and safety permissions;
- confirmation and reason for permission changes;
- audit records for role and permission changes;
- time-limited installer and guest access;
- recoverable commissioning stages;
- session revocation;
- no role receives unrestricted safety action permission by default.

### 2.3 Cloud connector

Decision: build the minimum connector required by the specification, disabled by default.

It must provide:

- an explicit export allowlist;
- field-level redaction;
- bounded offline queueing;
- per-destination consent;
- status and queue-depth metrics;
- a hard local control boundary so cloud failure never blocks local control;
- no household telemetry export before owner consent.

### 2.4 Brand fonts and assets

Decision:

- use IBM Plex Sans Arabic for Arabic;
- use Inter for English and Latin technical text;
- vendor the fonts locally and retain their OFL 1.1 notices;
- load no remote fonts or CDN assets;
- use approved production SVG assets only;
- do not trace or auto-generate final SVG logos from raster images without visual approval.

Both selected font families publish under the SIL Open Font License 1.1. Keep their license texts in `THIRD_PARTY_NOTICES.md` and the packaged font directory.

### 2.5 Automation builder and scheduled triggers

Decision: both are in MVP scope.

The automation builder must create only typed, validated automation graphs. It must not produce unrestricted free-text commands.

The local Scheduler owns time-based triggers. It must use the household IANA timezone, store execution time in UTC, handle timezone changes and daylight-saving transitions, and prevent duplicate execution after restart or clock correction.

Critical capabilities remain unavailable to ordinary automations.

### 2.6 Energy history

Decision: implement a real time-series energy endpoint.

Requirements:

- store measured power and energy only;
- never infer missing energy values as measured data;
- return coverage and missing intervals;
- provide hourly, daily, weekly, and monthly aggregation;
- support per-device, room, circuit, and home views where measurements exist;
- allow tariff configuration with effective dates;
- label calculated cost separately from measured energy;
- include retention and downsampling policies.

## 3. SYLTRA Hub multi-protocol architecture

### 3.1 Architectural rule

SYLTRA Adaptive must never contain protocol-specific business logic. All protocol implementations sit below a Device Gateway boundary and publish normalized capabilities, state, availability, diagnostics, and actions.

Required flow:

```text
Physical device
  -> protocol controller or vendor-local integration
  -> Home Assistant entity/device registry
  -> SYLTRA Edge Agent
  -> capability normalizer
  -> event bus and Digital Twin
  -> context, adaptive, risk, policy, and action services
```

The reverse action path must pass through Policy and Safety before the Edge Agent calls the protocol controller.

### 3.2 Required hub radios and network interfaces

The production hardware design must include:

1. Ethernet, preferred for hub backhaul.
2. Dual-band Wi-Fi with stable 2.4 GHz support for IoT commissioning.
3. Bluetooth Low Energy adapter supported by BlueZ.
4. A dedicated Zigbee 3.0 coordinator radio.
5. A separate dedicated Thread radio configured as an OpenThread Border Router.
6. A dedicated Z-Wave 800-series adapter for the Saudi/EU region.

For Saudi Arabia, the Z-Wave design target is the EU region profile using 868.4 MHz and 869.85 MHz. Final hardware selection still requires Saudi spectrum and product-compliance confirmation before production.

Do not run Zigbee and Thread simultaneously on one 802.15.4 radio in the production hub. Home Assistant documents single-radio multiprotocol firmware as experimental and not recommended. Separate radios reduce contention and simplify backup, recovery, and fault isolation.

Place 2.4 GHz radios and USB adapters to reduce RF and USB 3 interference. The enclosure and board layout must receive RF coexistence testing.

### 3.3 Protocol service topology

Run each controller behind a replaceable service boundary:

| Protocol | Controller or integration boundary | Required local dependency |
|---|---|---|
| Zigbee | Home Assistant ZHA as the default validated backend | Dedicated coordinator and network backup |
| Z-Wave | Z-Wave JS Server plus Home Assistant Z-Wave integration | Region-correct 800-series adapter and S2 keys |
| Matter | Home Assistant Matter integration through a pinned Matter Server boundary | IPv6, mDNS, persistent fabric storage, BLE commissioning path |
| Thread | OpenThread Border Router plus Home Assistant Thread diagnostics | Dedicated Thread radio and IPv6 routing |
| Bluetooth | Home Assistant Bluetooth integration | BlueZ, D-Bus access, local adapter, optional proxies |
| Wi-Fi and Ethernet | Matter, HomeKit, MQTT, HTTP, CoAP, and supported local vendor integrations | mDNS, SSDP, DHCP-reservation support, local credentials |

The Matter Server implementation is in transition in 2026. The older Python server entered maintenance/archive status while the matter.js server is the migration target. SYLTRA must hide this behind a stable adapter, pin a tested version, preserve Matter fabric data, and require hardware-in-the-loop regression before migration.

For the first pilot, use the Home Assistant OS Matter and Thread route because it is the supported and best-tested path. A self-managed container image may become the product path only after SYLTRA owns and passes the required IPv6, mDNS, Thread, commissioning, recovery, and OTA test matrix.

### 3.4 Device Gateway contract

Every protocol adapter must implement equivalent operations:

```text
discover()
commission(request)
remove(device_id)
list_devices()
read_state(device_id)
subscribe_events(cursor)
execute(typed_action)
health()
diagnostics(device_id)
backup_network()
restore_network(backup_id)
```

Every normalized device record must include:

- stable SYLTRA device ID;
- source integration and source device ID;
- manufacturer, model, hardware revision, and firmware version where exposed;
- protocol and controller instance;
- room and installation assignment;
- normalized capabilities;
- raw capabilities retained only for diagnostics;
- availability and last-seen time;
- power source and battery state where exposed;
- security level and commissioning method;
- local or cloud dependency classification;
- compatibility status;
- last successful command and last verified state.

### 3.5 Capability normalization

Use one canonical capability registry. Examples:

```text
switch.power
light.power
light.brightness
light.color_temperature
climate.mode
climate.target_temperature
cover.position
lock.state
sensor.temperature
sensor.humidity
sensor.illuminance
sensor.motion
sensor.occupancy
sensor.gas_alarm
sensor.smoke_alarm
sensor.water_leak
meter.power_w
meter.energy_kwh
valve.state
```

No dashboard, model, policy, or automation may query a capability name that is absent from the live canonical registry.

Adapters must map vendor-specific values into canonical units and enums. Unmapped properties must increment a labeled metric and remain visible in diagnostics. They must not be silently discarded.

### 3.6 Compatibility registry

Create a versioned Device Compatibility Registry with these states:

- CERTIFIED: the model passed commissioning, state, action, restart, offline, backup, restore, and update tests.
- SUPPORTED: core functions passed, with documented limitations.
- PARTIAL: read-only or incomplete capabilities.
- CLOUD_DEPENDENT: local control is unavailable for one or more required functions.
- BLOCKED: unsafe, unstable, unsupported region, or known incompatible.
- UNTESTED: discovered but not validated.

The console must show the status before commissioning completes. Marketing must use "supports major devices across six protocol families" rather than "supports every device" unless the model appears as CERTIFIED.

## 4. Closure of unverified boundaries

### 4.1 Real Home Assistant contract test

Build a hardware-in-the-loop test profile that starts a real Home Assistant instance and connects the production Edge Agent to it.

The test must use raw payloads from the real Home Assistant WebSocket API, not a project-written mock.

Required fixtures:

- authentication handshake;
- entity, device, area, and integration registries;
- state_changed events;
- entity creation, rename, disable, remove, and unavailable transitions;
- service calls and result or error responses;
- reconnect and subscription recovery;
- malformed or missing optional fields;
- protocol devices from every supported family.

Store sanitized payload fixtures and replay them in CI. Run the real boundary suite on release hardware before every pilot release.

Closure evidence:

- one 24-hour observe-only run;
- no Edge Agent crash;
- no lost event sequence after reconnect;
- zero silently discarded device fields;
- reviewed unmapped capabilities;
- a signed compatibility report for each tested device.

### 4.2 Real-home pilot

Run at least one pilot home using `DispatchMode.OBSERVE_ONLY` for seven days before enabling recommendations.

Minimum inventory:

- two Zigbee device models;
- two Z-Wave device models;
- one Matter-over-Wi-Fi device;
- one Matter-over-Thread device;
- two Wi-Fi local-integration models;
- two Bluetooth models;
- one gas detector, one leak detector, and one mapped shutoff actuator in non-executing prepare-only mode;
- one AC controller and one lighting circuit.

Review every refused command and every unmapped capability before progressing from observe mode.

### 4.3 Scale and history soak

Add a reproducible soak profile with:

- 100 simulated devices;
- at least 50 normalized events per second in bursts;
- one year of synthetic history loaded through supported ingestion paths;
- duplicate, delayed, out-of-order, stale, and unavailable events;
- restart and replay during load;
- database growth and retention execution.

Measure and fail the release when these targets are exceeded on documented reference hardware:

- normalized event publish p95: 250 ms;
- current-state update p95: 500 ms;
- policy evaluation p95: 200 ms;
- local MVP model inference p95: 250 ms;
- API query p95 for seven-day energy history: 750 ms;
- deterministic Digital Twin rebuild with no state mismatch;
- no unbounded memory, stream, or disk growth.

Publish machine-readable and human-readable soak reports.

### 4.4 Deployed offline test

Add an end-to-end deployed-stack test:

1. Start the pilot stack.
2. Commission local devices from each supported protocol.
3. Disconnect the WAN while retaining the LAN.
4. Exercise read, command, automation, safety notification, and local-console paths.
5. Restart the hub with WAN still unavailable.
6. Verify local control returns without external DNS or cloud access.

Cloud-dependent vendor integrations and mobile push must be labeled separately and must not be used as proof of local operation.

## 5. Engineering gap closures

### 5.1 Signed update and rollback

Implement an atomic A/B release mechanism for the hub.

Required sequence:

1. Download or side-load a signed release manifest and immutable image set.
2. Verify signature, checksums, hardware target, schema compatibility, and minimum rollback version.
3. Back up configuration, protocol network credentials, Matter fabric data, databases, and security keys using encrypted storage.
4. Install into the inactive slot.
5. Run preflight and migration checks.
6. Boot or switch to the candidate slot.
7. Run health, protocol, database, and local-control probes.
8. Commit the slot only after the health window passes.
9. Roll back automatically on failed boot, failed migration, failed protocol probes, or missing local control.

Database migrations must declare forward and rollback compatibility. A non-reversible migration must block unattended update until a restorable backup is verified.

Acceptance tests must cover power loss during every update stage.

### 5.2 Console live stream

Replace 15-second primary polling with `/v1/stream`.

Requirements:

- authenticated WebSocket connection;
- monotonic event sequence number;
- event type and entity or aggregate identifier;
- heartbeat;
- reconnect with bounded exponential backoff and jitter;
- resume from the last acknowledged sequence where retained;
- snapshot resynchronization when the cursor is too old;
- deduplication;
- visibility and offline state in the UI;
- polling only as a degraded fallback;
- no duplicate notifications or action timeline entries after reconnect.

### 5.3 Structural divergence

Keep placeholder directories only when each contains a README pointing to the authoritative implementation. A contract test must fail when a pointer becomes stale or when code appears in both locations.

Do not create a second implementation to satisfy the old directory layout.

## 6. Human verification gates

These items require signed evidence and must not be marked complete by automated tests alone:

- screen-reader walkthrough in Arabic and English;
- Arabic product-language review;
- Windows high-contrast review;
- keyboard focus-ring review;
- visual approval of light, dark, Arabic, English, desktop, tablet, and mobile screenshot baselines;
- review of refused commands from the real-home pilot.

Store reviewer, date, build commit, device or browser, findings, and sign-off in the repository.

## 7. Security requirements for multi-protocol commissioning

- Store Z-Wave S2 keys, Zigbee network keys, Thread credentials, Matter fabric keys, Wi-Fi credentials, and vendor-local tokens in encrypted storage.
- Redact all keys and setup codes from logs and diagnostics.
- Require physical proximity or owner authorization for commissioning.
- Use Matter attestation information and show an explicit warning for unverified devices.
- Prefer Z-Wave S2 and SmartStart where supported.
- Back up protocol networks separately from general application settings.
- Rate-limit commissioning and device removal.
- Audit inclusion, exclusion, factory reset, fabric sharing, and credential rotation.
- Never expose protocol controller ports outside the trusted local network.

## 8. Release test matrix

Every release candidate for SYLTRA Hub must pass:

| Area | Required evidence |
|---|---|
| Zigbee | commission, read, write, unavailable, coordinator backup and restore |
| Z-Wave | S2 inclusion, read, write, unavailable, key backup and adapter migration |
| Matter over Wi-Fi | commission, multi-admin share, read, write, restart, OTA where supported |
| Matter over Thread | commission, border-router restart, IPv6 recovery, read, write |
| Wi-Fi local | discovery, authentication, local-only operation, vendor error handling |
| Bluetooth | advertisement, connection, adapter recovery, proxy failover where used |
| Edge normalization | raw real payload to canonical capability contract |
| Safety | policy gate, owner confirmation, verification, failure escalation |
| Offline | local control before and after hub restart without WAN |
| Update | signed install, health gate, rollback, power-loss recovery |
| UI | stream reconnect, stale cursor resync, RTL, keyboard, screen reader, visual baseline |
| Scale | 100 devices, burst load, one-year history, deterministic rebuild |

## 9. Definition of closed

A gap is closed only when all four conditions exist:

1. production-path implementation, not a stub;
2. a test that crosses the real external boundary where applicable;
3. a stored evidence artifact with build or commit identity;
4. updated `IMPLEMENTATION_STATUS.md` and `SYLTRA_GAPS.md` entries.

Product decisions in Section 2 are closed by this directive. Engineering and real-world verification entries remain open until their evidence exists. Do not rewrite an implementation gap as "closed" because its design is documented.

## 10. Required implementation order

1. Add the Device Gateway contract and compatibility registry.
2. Establish dedicated Zigbee, Thread, Z-Wave, Bluetooth, Matter, and IP service boundaries.
3. Run the real Home Assistant contract profile.
4. Implement users, roles, installations, commissioning recovery, and audit.
5. Implement console streaming.
6. Implement energy time series and the local scheduler.
7. Implement the minimum disabled-by-default cloud connector.
8. Implement signed A/B update and rollback.
9. Run the scale and history soak.
10. Run manual accessibility and visual-baseline approval.
11. Run the observe-only real-home pilot.
12. Update the gap report only from the evidence produced above.

## 11. Authoritative technical references

- Home Assistant Z-Wave integration: https://www.home-assistant.io/integrations/zwave_js/
- Home Assistant ZHA integration: https://www.home-assistant.io/integrations/zha/
- Home Assistant Matter integration: https://www.home-assistant.io/integrations/matter/
- Home Assistant Thread integration: https://www.home-assistant.io/integrations/thread/
- Home Assistant Bluetooth integration: https://www.home-assistant.io/integrations/bluetooth/
- Home Assistant ZBT-1 multiprotocol status: https://www.home-assistant.io/connectzbt1
- Open Home Foundation Matter Server: https://github.com/matter-js/python-matter-server
- Matter.js Server Docker guidance: https://github.com/matter-js/matterjs-server/blob/main/docs/docker.md
- Silicon Labs Z-Wave global regions: https://www.silabs.com/wireless/z-wave/global-regions
- IBM Plex font licensing: https://github.com/IBM/plex
- Inter font licensing: https://github.com/rsms/inter

