@AGENTS.md

# SYLTRA Adaptive Edge Platform — working rules

This repository hosts two codebases side by side:

1. **The SYLTRA SMART website** — Next.js app under `src/` (see `AGENTS.md` above; read
   `node_modules/next/dist/docs/` before touching website code).
2. **The SYLTRA Adaptive Edge Platform** — Python monorepo under `services/`, `libs/`,
   `apps/`, `simulator/`, `contracts/`, `home-assistant/`, `infrastructure/`, `tests/`,
   governed by `SYLTRA_Claude_Code_Master_Build_Spec.md` (in the main project root).
   Read that spec before platform work.

## Platform summary

SYLTRA is a local-first adaptive smart-home platform. Home Assistant Core is an
**embedded, replaceable device-integration runtime** — never the product core (ADR-001).
The SYLTRA intelligence layer (Digital Twin, Context Engine, Adaptive Engine, Risk
Engine, Policy/Safety, Action Orchestrator, SILA) talks to it only through the
`DeviceIntegrationGateway` interface and normalized capability contracts.

Data flow: `Devices → Home Assistant → Edge Agent → NATS JetStream → Twin/Context/AI/Risk
→ Policy → Safety Governor → Action Orchestrator → Home Assistant`.

## Non-negotiable rules (from the master spec, Section 0)

- Never place secrets, tokens, passwords, certificates, or private keys in the repository.
- Never let an ML model or LLM directly execute emergency actions; AI output is advisory
  until it passes the Policy and Safety Service.
- Never modify Home Assistant Core source; integrate through supported APIs and the
  separate `home-assistant/custom_components/syltra_edge/` integration.
- No cloud dependency for local control. Loss of internet must not stop local control.
- Manual user control always overrides adaptive automation.
- Critical safety behavior is deterministic, independently testable, and works while AI
  services are offline.
- Every action is idempotent, traceable, time-bounded, and reversible where supported.
- New framework, database, broker, or language ⇒ write an ADR in `docs/adr/` first.
- Pin exact dependency versions in lockfiles (`uv.lock`).
- Do not commit or push unless explicitly instructed.
- Do not claim a phase complete unless every acceptance criterion passes; update
  `IMPLEMENTATION_STATUS.md` after every completed task.
- Development and simulation must block real critical actuator targets (locks, gas
  valves, breakers, sirens, emergency exits).
- Use synthetic data only in development and tests — no real household data.

## Toolchain

- Python 3.12 managed by `uv` (ADR-002); workspace members are `libs/*` and `services/*`.
- Quality gates: `ruff` (format + lint), `mypy --strict` on platform code, `pytest`
  (+ `pytest-asyncio`, `hypothesis`), `bandit` for security linting.
- Run everything through the `Makefile` (`make lint`, `make test`, `make security`, …);
  each target is documented in `README.md`.
- Dev stack runs via `docker-compose.yml` (Home Assistant, Mosquitto, NATS JetStream,
  PostgreSQL/TimescaleDB, SYLTRA services).

## Phase discipline

Implement phases in the order of spec Section 22 (0 foundation → 1 infra/HA → 2
contracts/twin → 3 context → 4 adaptive shadow → 5 recommendations/policy/actions → 6
risk/safety → 7 API/console/SILA → 8 pilot hardening). Before each phase restate
objective, files, acceptance tests, and safety implications; after each phase run
format/lint/type/tests, fix failures, and update `IMPLEMENTATION_STATUS.md`.
