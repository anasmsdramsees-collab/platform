"""Health and metrics endpoints (spec §29): /health/live, /health/ready, /metrics."""

from collections.abc import Callable

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Imported for its registration side effect: /metrics must expose the Edge
# Agent's metrics regardless of which modules the caller happened to import.
from syltra_edge_agent import metrics as _metrics  # noqa: F401


def create_health_app(readiness: Callable[[], bool]) -> FastAPI:
    app = FastAPI(title="SYLTRA Edge Agent", docs_url=None, redoc_url=None)

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready")
    async def ready(response: Response) -> dict[str, str]:
        if readiness():
            return {"status": "ready"}
        response.status_code = 503
        return {"status": "not_ready"}

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
