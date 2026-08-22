"""A fully assembled platform behind the API, built from synthetic data."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from syltra_action_orchestrator import ActionOrchestrator, OrchestratorConfig
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_api_gateway import Platform, create_app
from syltra_api_gateway.dependencies import RateLimiter
from syltra_context_engine.service import ContextService
from syltra_feedback_service import FeedbackService
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_risk_engine import RiskEngineService
from syltra_security import Role, TokenStore
from syltra_testing import comfort_history, make_envelope

HOME = "home_001"
OTHER_HOME = "home_002"
NOW = datetime.now(tz=UTC)


class NullPublisher:
    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


class NullGateway:
    def __init__(self) -> None:
        self.state: dict[tuple[str, str], Any] = {}

    async def execute_capability_command(self, command: Any) -> Any:
        from syltra_contracts import CommandResult

        self.state[(command.device_id, command.capability)] = command.value
        return CommandResult(accepted=True)

    async def read(self, device_id: str, capability: str) -> Any:
        return self.state.get((device_id, capability))


@pytest.fixture
def platform() -> Platform:
    context = ContextService(publisher=NullPublisher())  # type: ignore[arg-type]
    adaptive = AdaptiveEngineService(NullPublisher())  # type: ignore[arg-type]
    policy = PolicyService()
    policy.set_policy(HOME, HomePolicy())
    feedback = FeedbackService()
    risk = RiskEngineService()
    gateway = NullGateway()
    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision=policy.get,
        config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
    )

    # Seed two homes so isolation is testable rather than vacuous.
    for home_id, temperature in ((HOME, 27.4), (OTHER_HOME, 19.0)):
        for capability, value, unit in (
            ("environment.temperature", temperature, "C"),
            ("occupancy.motion", True, None),
        ):
            envelope = make_envelope(
                capability=capability,
                value=value,
                unit=unit,
                home_id=home_id,
                device_id=f"{home_id}_sensor",
                room_id="living_room",
                occurred_at=NOW,
            )
            context.twin.apply(envelope)
            adaptive.observe(envelope)

    for event in comfort_history(days=21):
        adaptive.observe(event.model_copy(update={"home_id": HOME}))
    adaptive.train_home(HOME)

    context.engine.evaluate(HOME, context.twin.home(HOME), NOW)  # type: ignore[arg-type]
    return Platform(
        twin=context.twin,
        context=context,
        adaptive=adaptive,
        policy=policy,
        orchestrator=orchestrator,
        feedback=feedback,
        risk=risk,
    )


@pytest.fixture
def tokens() -> TokenStore:
    return TokenStore()


@pytest.fixture
def client(platform: Platform, tokens: TokenStore) -> TestClient:
    return TestClient(create_app(platform, tokens=tokens, rate_limiter=RateLimiter()))


@pytest.fixture
def auth(tokens: TokenStore) -> Callable[..., dict[str, str]]:
    """Issue a bearer header for a role and set of homes."""

    def _auth(role: Role = Role.OWNER, homes: set[str] | None = None) -> dict[str, str]:
        token, _ = tokens.issue(
            f"user_{role.value.lower()}", role, homes or {HOME}, ttl=timedelta(hours=1)
        )
        return {"Authorization": f"Bearer {token}"}

    return _auth
