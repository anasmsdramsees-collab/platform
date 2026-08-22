# SYLTRA

This repository contains two codebases:

| Codebase | Where | What it is |
|---|---|---|
| **SYLTRA Adaptive Edge Platform** | `platform/` (`services/`, `libs/`, `apps/`, `simulator/`, `contracts/`, `home-assistant/`, `infrastructure/`, `tests/`, `docs/` inside it) | Local-first adaptive smart-home intelligence platform (Python). Governed by `SYLTRA_Claude_Code_Master_Build_Spec.md`. |
| **SYLTRA SMART website** | `src/`, `public/` | The marketing website (Next.js). See [Website](#website) below. |

---

## SYLTRA Adaptive Edge Platform

SYLTRA turns a conventional smart home into an adaptive, local-first system: it keeps a
live digital twin of the home, understands occupancy and context, learns routines and
comfort preferences, detects early risk signals, and executes only user-authorized
actions through a deterministic policy and safety gate. Core operation continues without
internet access; raw household data stays local by default.

**Architecture in one line:** Devices → Home Assistant Core (embedded, replaceable
integration runtime) → SYLTRA Edge Agent → NATS JetStream → Digital Twin / Context
Engine / Adaptive Engine / Risk Engine → Policy & Safety → Action Orchestrator → back to
devices. See `platform/docs/adr/ADR-001-home-assistant-as-replaceable-integration-runtime.md`.

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (manages the pinned Python 3.12 toolchain — no
  system Python required)
- Docker with Docker Compose (for the development stack, Phase 1+)
- GNU Make

### Quick start

```bash
make bootstrap     # install Python toolchain and all workspace dependencies
make lint          # formatting, lint, and type checks
make test          # unit and contract tests
```

### Developer commands

All workflows run through the `Makefile`:

| Command | What it does |
|---|---|
| `make bootstrap` | Install development prerequisites: pinned Python via `uv`, all workspace packages, dev tools. |
| `make config-check` | Validate configuration and environment (env file presence, compose file syntax, no secrets in `.env.example`). |
| `make contracts` | Regenerate every contract artifact: JSON Schemas, the worked examples in `contracts/examples/`, and the OpenAPI document in `contracts/openapi/`. Tests fail the build if a checked-in copy drifts. |
| `make tokens` | Regenerate the design-system CSS from `tokens.json` (guidelines §24). A test fails if the checked-in CSS drifts. |
| `make contrast` | Report the WCAG contrast ratio of every token pair in both themes; exits non-zero if any pair fails. |
| `make observe` | Start Prometheus and Grafana behind the `observability` profile; the dashboard lands on `127.0.0.1:3001`. |
| `make console` | Run the local console and component catalogue on `127.0.0.1:8088`. Open `127.0.0.1:8088/dev-login` to sign in; the printed per-role tokens are there for checking what each role can see. |
| `make migrate` | Apply database migrations (Alembic) to the configured database. |
| `make migrate-status` | Show the current migration revision. |
| `make up` | Start the development platform (Docker Compose stack). |
| `make down` | Stop the development platform. |
| `make reset-demo` | Reset demo data only — never user data. |
| `make seed` | Load deterministic demo fixtures. |
| `make simulate` | Run the deterministic smart-home simulation (no infrastructure needed). |
| `make simulate-list` | List available simulator scenarios. |
| `make test` | Run unit and contract tests. |
| `make test-integration` | Run integration tests (requires Docker). |
| `make test-e2e` | Run end-to-end tests (requires the full stack). |
| `make test-safety` | Run all safety scenarios. |
| `make lint` | Run format check, lint, and type checks (`ruff`, `mypy`). |
| `make security` | Run security checks (`bandit`, dependency audit). |
| `make coverage` | Produce coverage reports (safety modules require full branch coverage). |
| `make demo` | Start the platform and the deterministic demo. |
| `make logs` | Tail structured service logs. |
| `make health` | Show service health. |

Targets whose subsystems arrive in a later phase (currently only `test-e2e`, which needs
the full recommendation→action chain from Phase 5) fail fast with a clear "arrives in
Phase N" message, so scripts and CI can depend on stable target names from day one.

Running the stack needs a `.env` (copy `.env.example` and fill in local values) and, for
the database, `make migrate` once the containers are up.

### Repository layout (platform)

```text
apps/                 Local console and SILA interface frontends
config/               Mosquitto, NATS, Home Assistant, observability configs
contracts/            JSON Schemas, OpenAPI specs, contract examples
docs/                 ADRs, architecture, safety, privacy, API, operations, pilot docs
home-assistant/       SYLTRA custom integration (custom_components/syltra_edge)
infrastructure/       Dockerfiles, migrations, operational scripts
libs/                 Shared Python packages (contracts, eventing, observability, security, testing)
models/               Model definitions, training, exported artifacts, evaluation
services/             Platform services (edge-agent, digital-twin, context-engine, automation-engine, ...)
simulator/            Virtual devices, deterministic scenarios, fixtures
tests/                Cross-service contract, integration, e2e, safety, performance tests
```

### Design system

The platform UI is governed by `SYLTRA_Platform_UI_UX_Guidelines.md`. The design
system lives in `apps/local-console/src/design-system/` and has no build step
(ADR-007, ADR-008): `tokens.json` is the single source of truth, and `make
tokens` regenerates the CSS that the gateway serves.

| Path | Contents |
| --- | --- |
| `tokens/tokens.json` | Single source of truth — colour, spacing, radius, elevation, type, motion, layout, density. |
| `tokens/tokens.css`, `tokens/motion.css` | Generated. Theme-independent scales. |
| `themes/dark-theme.css`, `themes/light-theme.css` | Generated. Colour only, so a theme switch never moves the layout. |
| `typography/typography.css` | Generated. Latin and Arabic ramps. |
| `foundation.css` | Bidirectional layout, text utilities and the accessibility baseline. |
| `primitives.css` | The shared components. |
| `shell.css` | The application shell — sidebar, top bar, content region, navigation (§9.2). |
| `domain.css` | The components that know what SYLTRA is about — property header, room card, device row, context and risk cards, and the §20 data states. |

The console has **no stylesheet of its own**: it is composed entirely from the
design system. That is what makes "no feature component contains a hardcoded
brand colour" true by construction rather than by review — there is no file
left for one to hide in.

The **component catalogue** is the living style guide. Run `make console` and
open `http://127.0.0.1:8088/console/catalogue/` — it needs no token, because it
shows the design system rather than a home. It renders every component in every
state and switches theme, direction and density without a reload — and
recomputes WCAG contrast from what the browser actually painted, independently
of the CI check in `libs/design-tokens`.

`make contrast` runs that check from the command line. Guidelines §28 keeps the
browser-only checks (screen reader, 200% zoom, RTL walkthrough) as manual tests.

For how to change a token, add a component, or add a screen — and which rules
are enforced by tests rather than convention — see
[docs/ui/DESIGN_SYSTEM.md](docs/ui/DESIGN_SYSTEM.md).

### Understanding the platform

Start with **[docs/PLATFORM_OVERVIEW.md](docs/PLATFORM_OVERVIEW.md)** — what
SYLTRA is, how a fact becomes an action, what each component does, and what is
deliberately not built. It assumes no knowledge of the codebase.

Then **[docs/GAPS.md](docs/GAPS.md)** — everything known to be missing,
unverified, or untrue, organised by who can close it. Read §1 first: it is the
only section describing things that might already be wrong rather than merely
absent.

### Status and roadmap

Progress, per-phase acceptance results, and known gaps are tracked in
[`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md). The build proceeds in phases
(spec Section 22): **Phase 0** repository foundation ✅ → **Phase 1** infrastructure
and Home Assistant connection ✅ → **Phase 2** contracts and Digital Twin ✅ →
**Phase 3** Context Engine ✅ → **Phase 4** Adaptive Engine in shadow mode (next) →
… → **Phase 8** pilot hardening.

### Security and privacy

- No secrets in the repository — `.env.example` holds placeholders only; real values go
  in `.env` / `.env.local`, which are gitignored. See [`SECURITY.md`](SECURITY.md).
- Raw household behavioral data stays local by default; cloud sync is disabled by
  default and allowlist-driven. Privacy documentation lives in `docs/privacy/`.
- Third-party licenses are tracked in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

## Website

The SYLTRA SMART website is a [Next.js](https://nextjs.org) app under `src/`.

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # production build
npm run lint       # eslint
```

The site is bilingual (Arabic RTL / English LTR) via the `[locale]` route segment. The
Sina site assistant calls the Anthropic API server-side; set `ANTHROPIC_API_KEY` in
`.env.local` (see `.env.example`). Deployment to GitHub Pages runs via
`.github/workflows/deploy-pages.yml`.
