#!/usr/bin/env bash
# Validate configuration and environment (make config-check).
set -euo pipefail
cd "$(dirname "$0")/../.."

fail=0

echo "── toolchain ──"
if command -v uv >/dev/null; then
  echo "✔ uv $(uv --version | cut -d' ' -f2)"
else
  echo "✘ uv not found — install from https://docs.astral.sh/uv/"; fail=1
fi
if command -v docker >/dev/null; then
  echo "✔ docker $(docker --version | sed 's/Docker version //;s/,.*//')"
else
  echo "✘ docker not found (needed from Phase 1 for the dev stack)"; fail=1
fi

echo "── lockfile ──"
if uv lock --check >/dev/null 2>&1; then
  echo "✔ uv.lock is up to date with pyproject.toml"
else
  echo "✘ uv.lock out of date — run 'uv lock'"; fail=1
fi

echo "── secret hygiene ──"
# .env files must never be tracked by git.
if tracked=$(git ls-files '.env' '.env.*' | grep -v '^\.env\.example$' || true); [ -n "$tracked" ]; then
  echo "✘ env file(s) tracked by git: $tracked"; fail=1
else
  echo "✔ no env files tracked by git (only .env.example)"
fi
# .env.example must contain placeholders only: empty values, obvious placeholders,
# or non-secret dev defaults. Anything long and high-entropy is suspicious.
if grep -E '^[A-Z_]+=[A-Za-z0-9+/_-]{24,}' .env.example | grep -vE '(changeme|example|placeholder|claude-)' ; then
  echo "✘ .env.example contains a value that looks like a real secret"; fail=1
else
  echo "✔ .env.example contains placeholders only"
fi

echo "── docker compose ──"
if command -v docker >/dev/null && docker info >/dev/null 2>&1; then
  # Structural validation; required env vars get harmless stand-ins so the
  # check does not depend on a local .env existing.
  if NATS_PASSWORD="${NATS_PASSWORD:-placeholder}" \
     POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-placeholder}" \
     HOME_ASSISTANT_TOKEN="${HOME_ASSISTANT_TOKEN:-placeholder}" \
     docker compose config -q; then
    echo "✔ docker-compose.yml is valid"
  else
    echo "✘ docker-compose.yml failed validation"; fail=1
  fi
else
  echo "– docker daemon not running; skipped compose validation"
fi

if [ "$fail" -ne 0 ]; then
  echo "config-check FAILED"; exit 1
fi
echo "config-check OK"
