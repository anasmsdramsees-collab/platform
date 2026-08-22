"""Adaptive Engine read and control API (spec §21 subset).

Read endpoints expose model state and shadow predictions so an operator can
judge whether a model is ready to advance. The only mutations are lifecycle
acts — set mode, promote, roll back, suspend — and every one is an explicit
human decision, never something a model can perform for itself
(safety invariants 14 and 15).
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from syltra_adaptive_engine import metrics as _metrics  # noqa: F401  (registers metrics)
from syltra_adaptive_engine.registry import PromotionRefused, RollbackUnavailable
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_contracts import LearningMode, LearningModeTransitionError


def create_app(service: AdaptiveEngineService) -> FastAPI:
    app = FastAPI(title="SYLTRA Adaptive Engine", version="1.0", docs_url=None, redoc_url=None)

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

    @app.get("/v1/homes/{home_id}/models")
    async def list_models(home_id: str) -> dict[str, Any]:
        return {
            "home_id": home_id,
            "learning_mode": service.mode(home_id).value,
            "history_events": service.history_size(home_id),
            "models": [
                {
                    "name": version.name,
                    "version": version.version,
                    "model_type": version.model_type.value,
                    "status": version.status.value,
                    "feature_schema_version": version.feature_schema_version,
                    "training_code_revision": version.training_code_revision,
                    "evaluation_metrics": version.evaluation_metrics,
                    "created_at": version.created_at.isoformat(),
                    "promoted_at": (
                        version.promoted_at.isoformat() if version.promoted_at else None
                    ),
                    "rollback_target": version.rollback_target,
                    "training_window": {
                        "start": version.training_window.start.isoformat(),
                        "end": version.training_window.end.isoformat(),
                        "sample_count": version.training_window.sample_count,
                        "distinct_days": version.training_window.distinct_days,
                    },
                }
                for version in service.registry.versions(home_id)
            ],
        }

    @app.get("/v1/homes/{home_id}/models/{name}/card")
    async def model_card(home_id: str, name: str) -> dict[str, Any]:
        versions = service.registry.versions(home_id, name)
        if not versions:
            raise HTTPException(
                status_code=404, detail={"error": "MODEL_NOT_FOUND", "name": name}
            )
        latest = versions[-1]
        return {
            "name": latest.name,
            "version": latest.version,
            "card": latest.card.model_dump(mode="json"),
        }

    @app.get("/v1/homes/{home_id}/recommendations/shadow")
    async def shadow_recommendations(home_id: str, limit: int = 50) -> dict[str, Any]:
        """Shadow predictions, for judging readiness before advancing a mode.

        These are explicitly labelled: they were never shown to the household
        and were never actionable.
        """
        entries = [r for r in service.shadow_log if r.home_id == home_id][-limit:]
        return {
            "home_id": home_id,
            "learning_mode": service.mode(home_id).value,
            "shadow": True,
            "recommendations": [r.model_dump(mode="json") for r in entries],
        }

    @app.post("/v1/homes/{home_id}/learning-mode")
    async def set_learning_mode(
        home_id: str, payload: dict[str, str] = Body(...)
    ) -> dict[str, Any]:
        requested = payload.get("mode", "")
        try:
            target = LearningMode(requested)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": "UNKNOWN_LEARNING_MODE", "mode": requested},
            ) from None
        try:
            applied = service.set_mode(home_id, target, actor=payload.get("actor", "operator"))
        except LearningModeTransitionError as exc:
            # A refused transition is a 409: the request is well-formed, the
            # lifecycle simply does not permit it.
            raise HTTPException(
                status_code=409,
                detail={"error": "TRANSITION_NOT_PERMITTED", "message": str(exc)},
            ) from exc
        return {"home_id": home_id, "learning_mode": applied.value}

    @app.post("/v1/homes/{home_id}/models/{name}/promote")
    async def promote(
        home_id: str, name: str, payload: dict[str, str] = Body(default={})
    ) -> dict[str, Any]:
        try:
            version = service.registry.promote(
                home_id, name, payload.get("version", ""), actor=payload.get("actor", "operator")
            )
        except PromotionRefused as exc:
            raise HTTPException(
                status_code=409,
                detail={"error": "PROMOTION_REFUSED", "message": str(exc)},
            ) from exc
        return {"name": version.name, "version": version.version, "status": version.status.value}

    @app.post("/v1/homes/{home_id}/models/{name}/rollback")
    async def rollback(
        home_id: str, name: str, payload: dict[str, str] = Body(default={})
    ) -> dict[str, Any]:
        try:
            version = service.registry.rollback(
                home_id,
                name,
                actor=payload.get("actor", "operator"),
                reason=payload.get("reason", "manual rollback"),
            )
        except RollbackUnavailable as exc:
            raise HTTPException(
                status_code=409,
                detail={"error": "ROLLBACK_UNAVAILABLE", "message": str(exc)},
            ) from exc
        return {"name": version.name, "version": version.version, "status": version.status.value}

    @app.post("/v1/homes/{home_id}/models/{name}/suspend")
    async def suspend(
        home_id: str, name: str, payload: dict[str, str] = Body(default={})
    ) -> dict[str, Any]:
        try:
            version = service.registry.suspend(
                home_id,
                name,
                reason=payload.get("reason", "operator suspension"),
                actor=payload.get("actor", "operator"),
            )
        except RollbackUnavailable as exc:
            raise HTTPException(
                status_code=409, detail={"error": "NO_ACTIVE_VERSION", "message": str(exc)}
            ) from exc
        return {"name": version.name, "version": version.version, "status": version.status.value}

    @app.post("/v1/homes/{home_id}/train")
    async def train(home_id: str) -> dict[str, Any]:
        results = service.train_home(home_id)
        return {
            "home_id": home_id,
            "trained_at": datetime.now(tz=UTC).isoformat(),
            "results": {
                name: {
                    "trained": result.trained,
                    "reason_codes": result.reason_codes,
                    "explanation": result.sufficiency.explain(),
                    "metrics": result.metrics,
                }
                for name, result in results.items()
            },
        }

    @app.get("/v1/homes/{home_id}/audit")
    async def audit(home_id: str) -> dict[str, Any]:
        return {
            "home_id": home_id,
            "events": [
                {
                    "occurred_at": event.occurred_at.isoformat(),
                    "action": event.action,
                    "model": event.model_reference,
                    "actor": event.actor,
                    "reason": event.reason,
                    "detail": event.detail,
                }
                for event in service.registry.audit
                if event.home_id == home_id
            ],
        }

    return app
