"""Digital Twin read APIs (spec §21 subset served by this service).

These are internal read models; the public surface is the Local API Gateway
(Phase 7), which adds authentication, authorization and rate limiting. Homes
are addressed explicitly in every path so no read can span households.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from syltra_digital_twin import metrics as _metrics  # noqa: F401  (registers metrics)
from syltra_digital_twin.core import StateStatus
from syltra_digital_twin.service import DigitalTwinService


def create_app(service: DigitalTwinService) -> FastAPI:
    app = FastAPI(
        title="SYLTRA Digital Twin",
        version="1.0",
        docs_url=None,
        redoc_url=None,
    )

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

    @app.get("/v1/homes/{home_id}/twin")
    async def get_twin(home_id: str) -> dict[str, Any]:
        snapshot = service.twin.snapshot(home_id, datetime.now(tz=UTC))
        return {
            "home_id": snapshot.home_id,
            "taken_at": snapshot.taken_at.isoformat(),
            "events_applied": snapshot.events_applied,
            "fingerprint": snapshot.fingerprint(),
            "devices": snapshot.devices,
            "rooms": snapshot.rooms,
        }

    @app.get("/v1/homes/{home_id}/rooms")
    async def get_rooms(home_id: str) -> dict[str, Any]:
        snapshot = service.twin.snapshot(home_id, datetime.now(tz=UTC))
        return {
            "home_id": home_id,
            "rooms": [
                {"room_id": room_id, "device_ids": device_ids}
                for room_id, device_ids in snapshot.rooms.items()
            ],
        }

    @app.get("/v1/homes/{home_id}/devices")
    async def get_devices(home_id: str) -> dict[str, Any]:
        snapshot = service.twin.snapshot(home_id, datetime.now(tz=UTC))
        return {"home_id": home_id, "devices": list(snapshot.devices.values())}

    @app.get("/v1/homes/{home_id}/devices/{device_id}")
    async def get_device(home_id: str, device_id: str) -> dict[str, Any]:
        snapshot = service.twin.snapshot(home_id, datetime.now(tz=UTC))
        device = snapshot.devices.get(device_id)
        if device is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "DEVICE_NOT_FOUND", "home_id": home_id,
                        "device_id": device_id},
            )
        return device

    @app.get("/v1/homes/{home_id}/devices/{device_id}/capabilities/{capability:path}")
    async def get_capability(home_id: str, device_id: str, capability: str) -> dict[str, Any]:
        device_state = service.twin.device(home_id, device_id)
        if device_state is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "DEVICE_NOT_FOUND", "home_id": home_id,
                        "device_id": device_id},
            )
        now = datetime.now(tz=UTC)
        state = device_state.capability(capability)
        # An unobserved capability is reported explicitly as UNKNOWN rather
        # than 404 or a falsy default — the caller must be able to tell
        # "never seen" from "seen and false".
        return {
            "home_id": home_id,
            "device_id": device_id,
            "capability": capability,
            "value": state.value,
            "unit": state.unit,
            "quality": state.quality,
            "status": state.status_at(now).value,
            "observed": state.observed,
            "age_seconds": state.age_seconds(now),
            "usable_for_decisions": state.is_usable_for_decisions(now),
        }

    @app.get("/v1/homes/{home_id}/stale")
    async def get_stale(home_id: str) -> dict[str, Any]:
        """Capabilities past their freshness window — an operator view that
        also feeds the sensor-degradation checks later phases rely on."""
        now = datetime.now(tz=UTC)
        home = service.twin.home(home_id)
        stale: list[dict[str, Any]] = []
        if home is not None:
            for device_id, device in home.devices.items():
                for capability, state in device.capabilities.items():
                    if state.status_at(now) is StateStatus.STALE:
                        stale.append(
                            {
                                "device_id": device_id,
                                "capability": capability,
                                "age_seconds": state.age_seconds(now),
                            }
                        )
        return {"home_id": home_id, "stale": stale}

    return app
