"""OpenAPI export (spec §21: the local API is specified, not just served).

FastAPI already serves a live document at `/v1/openapi.json`, which is enough
to read and not enough to *depend on*: it exists only while the hub is running,
and it changes the moment somebody edits a route. A pilot integrator, a mobile
client and a reviewer all need a copy that sits still and can be diffed.

So the same thing `make contracts` does for the JSON Schemas, `make openapi`
does here — write a versioned document into `contracts/openapi/` from the app
itself, and let a test fail the build when the checked-in copy drifts from the
routes.

The document is generated from an empty platform. Every schema, path and status
code comes from the route signatures; none of it comes from household data, so
the export needs no seeded state and contains none.
"""

import json
from pathlib import Path
from typing import Any

from syltra_action_orchestrator import ActionOrchestrator, OrchestratorConfig
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_api_gateway.api import API_VERSION, create_app
from syltra_api_gateway.dependencies import RateLimiter
from syltra_api_gateway.platform import Platform
from syltra_context_engine.service import ContextService
from syltra_contracts import CommandResult
from syltra_feedback_service import FeedbackService
from syltra_policy_safety import PolicyService
from syltra_risk_engine import RiskEngineService
from syltra_security import TokenStore


class _NullPublisher:
    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


class _NullGateway:
    async def execute_capability_command(self, command: Any) -> CommandResult:
        return CommandResult(accepted=False, reason="EXPORT_ONLY")

    async def read(self, device_id: str, capability: str) -> Any:
        return None


def _empty_platform() -> Platform:
    context = ContextService(publisher=_NullPublisher())  # type: ignore[arg-type]
    policy = PolicyService()
    gateway = _NullGateway()
    return Platform(
        twin=context.twin,
        context=context,
        adaptive=AdaptiveEngineService(_NullPublisher()),  # type: ignore[arg-type]
        policy=policy,
        orchestrator=ActionOrchestrator(
            gateway=gateway,
            read_state=gateway.read,
            get_decision=policy.get,
            config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
        ),
        feedback=FeedbackService(),
        risk=RiskEngineService(),
    )


def build_document() -> dict[str, Any]:
    """The OpenAPI document the running gateway would serve."""
    app = create_app(_empty_platform(), tokens=TokenStore(), rate_limiter=RateLimiter())
    document: dict[str, Any] = app.openapi()
    return document


def document_path(root: Path) -> Path:
    return root / "contracts" / "openapi" / f"v{API_VERSION}" / "syltra-local-api.openapi.json"


def write_document(root: Path) -> Path:
    path = document_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(build_document(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def main() -> None:  # pragma: no cover - thin CLI wrapper
    root = Path(__file__).resolve().parents[4]
    path = write_document(root)
    print(f"wrote {path.relative_to(root)}")


if __name__ == "__main__":  # pragma: no cover
    main()
