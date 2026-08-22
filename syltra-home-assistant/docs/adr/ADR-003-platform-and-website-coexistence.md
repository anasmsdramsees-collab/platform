# ADR-003: Platform monorepo coexists with the existing website in one repository

- Status: Accepted
- Date: 2026-08-18
- Deciders: Implementation engineering (Phase 0)

## Context

The master spec (§8) defines a platform monorepo layout for this repository, and also
says: "If the repository already has a compatible structure, adapt it rather than
destructively replacing it." The repository already contained the SYLTRA SMART
marketing website — a Next.js app rooted in `src/` with `package.json`, a GitHub Pages
deploy workflow, and non-code business assets (`brand/`, `identity/`, `investment/`,
`posters/`, …).

## Decision

Add the platform monorepo **alongside** the website at the repository root. The two
trees are disjoint:

- Platform: `services/`, `libs/`, `apps/`, `simulator/`, `contracts/`,
  `home-assistant/`, `infrastructure/`, `models/`, `tests/`, `config/`, `docs/`,
  `pyproject.toml`, `uv.lock`, `Makefile`, `docker-compose.yml`.
- Website: `src/`, `public/`, `package.json`, `eslint.config.mjs`, `next.config.ts`,
  `.github/workflows/deploy-pages.yml` — all untouched.
- Shared root files (`README.md`, `CLAUDE.md`, `.gitignore`, `.env.example`,
  `SECURITY.md`) were extended, preserving their website content.

Isolation guarantees:

- Python tooling excludes the website (`ruff`/`mypy` exclude `src/`, `node_modules/`);
  the website's ESLint/TS toolchain never sees platform code.
- CI is split per codebase with path filters: `platform-ci.yml` runs only on platform
  paths; `deploy-pages.yml` remains the website pipeline.
- `apps/` (spec §8: local-console, sila-interface) does not collide with the website,
  which lives entirely under `src/`.

## Consequences

- One repository, two independent toolchains; neither can break the other's CI.
- If the platform later needs its own repo, the platform tree extracts cleanly (no
  shared build files beyond the root docs).
- Contributors must read `CLAUDE.md`, which routes website work to `AGENTS.md`
  conventions and platform work to the master spec.
