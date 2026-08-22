"""Context Engine read API (spec §21: /contexts/current)."""

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from syltra_context_engine import metrics as _metrics  # noqa: F401  (registers metrics)
from syltra_context_engine.service import ContextService


def create_app(service: ContextService) -> FastAPI:
    app = FastAPI(title="SYLTRA Context Engine", version="1.0", docs_url=None, redoc_url=None)

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready")
    async def ready(response: Response) -> dict[str, str]:
        if service.ready:
            return {"status": "ready"}
        response.status_code = 503
        return {"status": "not_ready"}

    @app.get("/metrics")
    async def prometheus_metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/v1/homes/{home_id}/contexts/current")
    async def current_contexts(home_id: str) -> dict[str, Any]:
        now = datetime.now(tz=UTC)
        records = service.active(home_id, now)
        return {
            "home_id": home_id,
            "evaluated_at": now.isoformat(),
            "contexts": [
                {
                    "context_id": str(record.context_id),
                    "context_type": record.context_type.value,
                    "scope": record.scope,
                    "confidence": record.confidence,
                    "started_at": record.started_at.isoformat(),
                    "last_updated_at": record.last_updated_at.isoformat(),
                    "expires_at": record.expires_at.isoformat(),
                    "seconds_until_expiry": round(
                        (record.expires_at - now).total_seconds(), 1
                    ),
                    "producer": record.producer,
                    "reason_codes": record.reason_codes,
                    "advisory_only": record.is_advisory_only(),
                    "evidence": [
                        {
                            "device_id": item.device_id,
                            "room_id": item.room_id,
                            "capability": item.capability,
                            "value": item.value,
                            "status": item.status,
                            "observed_at": (
                                item.observed_at.isoformat() if item.observed_at else None
                            ),
                            "note": item.note,
                        }
                        for item in record.evidence
                    ],
                }
                for record in records
            ],
        }

    return app
