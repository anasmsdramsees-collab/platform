#!/usr/bin/env bash
# Reset DEMO data only (make reset-demo).
#
# Safety rule (spec §9): this must never touch user or household data. It
# purges the SYLTRA JetStream streams in a development environment only, and
# refuses to run when SYLTRA_ENVIRONMENT is anything but development/simulation.
set -euo pipefail
cd "$(dirname "$0")/../.."

environment="${SYLTRA_ENVIRONMENT:-development}"
if [ -f .env ]; then
  environment="$(grep -E '^SYLTRA_ENVIRONMENT=' .env | tail -1 | cut -d= -f2- || true)"
  environment="${environment:-development}"
fi

case "$environment" in
  development|simulation) ;;
  *)
    echo "✘ refusing to reset demo data: SYLTRA_ENVIRONMENT=$environment is not a development environment"
    exit 1
    ;;
esac

echo "environment=$environment — purging SYLTRA demo streams"
uv run python - <<'PY'
import asyncio

import nats

from syltra_eventing.streams import purge_streams


async def main() -> None:
    nc = await nats.connect("nats://localhost:4222")
    try:
        purged = await purge_streams(nc.jetstream())
        print("✔ purged streams: " + (", ".join(purged) if purged else "(none present)"))
    finally:
        await nc.drain()


asyncio.run(main())
PY
echo "reset-demo OK (demo streams only; no user data touched)"
