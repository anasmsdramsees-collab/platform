# Data flow

Where household data travels, and where it stops. The short version: **it does
not leave the hub.** This document exists to make that checkable rather than
merely stated.

## The flow

```text
Devices
  │  (protocol traffic, on the home network)
  ▼
Home Assistant Core ─────────── stays on the hub
  │  WebSocket, localhost
  ▼
SYLTRA Edge Agent ───────────── privacy_class stamped here
  │  NATS JetStream, container network
  ▼
Digital Twin ── Context Engine ── Adaptive Engine ── Risk Engine
  │                                                    │
  └──────────────► Policy & Safety ◄───────────────────┘
                        │
                        ▼
                Action Orchestrator ──► Home Assistant ──► Devices
                        │
                        ▼
                  Local API Gateway
                        │  (authenticated, home network only)
                        ▼
              Console / SILA  ── the household
```

Every arrow above is inside the hub or on the home network. There is no arrow
leaving it.

## The boundary, concretely

| Boundary | What crosses | Enforcement |
|---|---|---|
| Devices → Home Assistant | Protocol traffic | Home network only |
| Home Assistant → Edge Agent | State changes | localhost WebSocket, token-authenticated |
| Edge Agent → services | Normalized events | Container network, never published externally |
| Services → API Gateway | Read models | In-process; the gateway holds no broker or DB client for callers |
| API Gateway → household | Views | Authenticated, home-scoped, on the home network |
| Hub → internet | **Nothing** | No cloud connector is implemented |

## Cloud: not built, not wired

Spec §14.11 describes a cloud connector that is disabled by default with an
explicit export allowlist. In this MVP it is **not implemented at all**, which
is a stronger position than "disabled": there is no code path, no credential,
and no configuration that could enable it by accident.

When it is built, spec §14.11 requires:

- disabled by default;
- an explicit allowlist, not a denylist;
- only approved configuration and aggregate metrics;
- household-private payloads redacted unless explicitly enabled;
- never proxying local action execution.

The safety tests already assert the current position: `test_confirmation_does_not_touch_the_network`
and `test_risk_evaluation_does_not_touch_the_network` disable `socket.socket`
entirely and confirm a hazard anyway.

## Diagnostic bundles

The one artifact designed to leave the hub. It carries:

- service health, versions, error types, timings;
- pseudonymized identifiers;
- **no** secrets, **no** household-private values, **no** raw events.

Built by `syltra_operations.privacy.diagnostic_bundle`, and asserted by
`test_diagnostics_carry_no_secrets_or_identifiers`.

## Backups

A backup contains everything — it is the most sensitive artifact the platform
produces. It is therefore always AES-256-GCM encrypted with a scrypt-derived
key and written `0600`.

The file has two parts, and they carry different guarantees:

- **The body is encrypted.** `test_household_data_never_reaches_disk_in_the_clear`
  scans the ciphertext for household strings, and
  `test_two_backups_of_the_same_data_are_not_byte_identical` proves a fresh
  nonce is used — without one, an observer comparing two backups could tell
  whether anything had changed between them.
- **The manifest is readable by design**, so `backup info` can report what a
  file is without the passphrase. Its shape is fixed, and
  `test_the_readable_manifest_carries_no_household_data` asserts its **exact
  key set** rather than searching it for known strings. That is the stronger
  check: household data arriving in the manifest would show up as a new field,
  whether or not anyone thought to search for its contents.

The manifest check used to be a substring scan over the whole file, and it
raised a false alarm roughly one run in six hundred: `created_at` is an ISO
timestamp, and whenever its seconds field read `27.4…` a search for the
household temperature `27.4` matched the timestamp. The encryption was never at
fault. It is recorded here because a privacy test that cries wolf is worse than
no test — people learn to re-run it.
