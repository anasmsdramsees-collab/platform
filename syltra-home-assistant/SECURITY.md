# Security Policy — SYLTRA Adaptive Edge Platform

## Reporting a vulnerability

Report suspected vulnerabilities privately to the SYLTRA maintainers
(anas.msd.ramsees@gmail.com). Do not open public issues for security reports. Include
reproduction steps, affected component, and impact. You will receive an acknowledgement
and a remediation plan; please allow coordinated disclosure before publishing.

## Threat posture

SYLTRA is a **local-first** platform that controls devices inside a home. The primary
assets are: household behavioral data, actuator control paths (especially locks, gas
valves, breakers, sirens), local credentials (Home Assistant token, broker credentials),
and the model/policy pipeline that decides actions.

## Standing controls (spec §25)

### Secrets

- No secrets, tokens, passwords, certificates, or private keys in the repository — ever.
- `.env.example` contains placeholders only; real values live in `.env` / `.env.local`,
  which are gitignored.
- Secrets are injected via environment or secret files; never baked into images, never
  written to logs or events. The Edge Agent must redact the Home Assistant token from
  all output.
- Rotation: revoke the old credential at its source (e.g., Home Assistant long-lived
  token page), issue a new one, update the local `.env`, restart affected services with
  `make down && make up`. Rotation events are audit-logged from Phase 5 onward.

### Identity and access

- Unique hub identity and per-service identity; least privilege throughout.
- Role-based user authorization at the API Gateway; separate permission classes for
  comfort, security-sensitive, and safety actions.
- Short-lived local access tokens where practical.

### Network

- Only the API Gateway (and the Home Assistant interface needed for development) are
  exposed; databases and message brokers stay on private container networks.
- MQTT and NATS require authentication; TLS wherever a connection crosses a trust
  boundary; no default public listeners.

### Software supply chain

- Dependencies pinned exactly in `uv.lock`; CI runs dependency vulnerability scanning
  and security linting (`bandit`).
- Container images are scanned before pilot use; an SBOM and `THIRD_PARTY_NOTICES.md`
  track third-party components. Signed releases are designed in for later pilot phases.

### Safety-relevant security rules

- No ML model or LLM output may directly execute emergency actions; every action passes
  the deterministic Policy and Safety Service.
- Development and simulation environments block real critical actuator targets.
- Replayed historical events cannot trigger live actions; action requests carry
  idempotency keys and TTLs.
- Every sensitive action, permission change, policy change, model activation/rollback,
  manual override, and data export/deletion is audit-logged (append-only).

## Scope note

The Next.js website in `src/` follows the same secrets rules (`ANTHROPIC_API_KEY` only
in `.env.local`); website-specific reports go through the same private channel.
