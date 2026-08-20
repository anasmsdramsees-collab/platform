# ADR-002: uv-managed workspace on Python 3.12

- Status: Accepted
- Date: 2026-08-18
- Deciders: Implementation engineering (Phase 0)

## Context

The spec (§7.1) fixes Python for MVP services and requires exact version pinning in
lockfiles with latest stable releases (§0 rule 18), but leaves the package/workspace
manager and interpreter version open. The monorepo needs one lockfile across many
packages (`libs/*`, `services/*`), reproducible installs in CI and on the hub, and no
dependence on whatever Python the host machine ships (the dev machine has 3.9).

## Decision

- **`uv`** manages the toolchain: single `uv.lock` with exact pins for the whole
  workspace, `[tool.uv.workspace]` members added as their first real code lands,
  interpreter installed and pinned by `uv python install 3.12` + `.python-version`.
- **Python 3.12** is the platform interpreter. It is the newest line with mature,
  stable support across the full required ML/runtime chain (NumPy, scikit-learn, ONNX,
  ONNX Runtime, SQLAlchemy, FastAPI) and long support runway. 3.13 is not excluded
  later; moving is a one-line pin change plus a lockfile regeneration and CI pass.
- The workspace root is virtual (no root package). Shared tool config (ruff, mypy
  strict, pytest, coverage) lives in the root `pyproject.toml`.

## Consequences

- `make bootstrap` works on a clean machine with only `uv`, Make, and Docker present.
- CI uses `uv sync --locked`, so builds fail loudly if the lockfile drifts.
- The Home Assistant *container* keeps its own interpreter; only the custom component
  (`syltra_edge`, Phase 7) must track HA's supported Python, which is isolated from
  this decision.
- Alternatives considered: Poetry (workspace support weaker, slower, second lock
  format), pip + pip-tools (no workspace concept), system Python (3.9 — too old,
  unpinnable). Rejected accordingly.
