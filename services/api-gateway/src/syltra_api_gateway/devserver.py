"""Development server: the gateway plus a seeded platform and a demo token.

Used by `make demo` and the preview tooling to look at the console with real
data. It seeds synthetic household state (spec §26) and prints a token so the
console can authenticate. Never used in a pilot or production deployment.
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import uvicorn

from syltra_action_orchestrator import ActionOrchestrator, OrchestratorConfig
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_api_gateway.api import create_app
from syltra_api_gateway.dependencies import RateLimiter
from syltra_api_gateway.platform import Platform
from syltra_context_engine.service import ContextService
from syltra_contracts import CommandResult, LearningMode
from syltra_feedback_service import FeedbackService
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_risk_engine import RiskEngineService
from syltra_security import Role, TokenStore

logger = logging.getLogger(__name__)

HOME = os.environ.get("SYLTRA_HOME_ID", "home_dev_001")


class _DemoPublisher:
    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


class _DemoGateway:
    def __init__(self) -> None:
        self.state: dict[tuple[str, str], Any] = {}

    async def execute_capability_command(self, command: Any) -> CommandResult:
        self.state[(command.device_id, command.capability)] = command.value
        return CommandResult(accepted=True)

    async def read(self, device_id: str, capability: str) -> Any:
        return self.state.get((device_id, capability))


def build_platform() -> Platform:
    from syltra_automation_engine import AutomationEngine
    from syltra_contracts import (
        Automation,
        AutomationAction,
        AutomationCondition,
        AutomationTrigger,
        ConditionKind,
        TriggerKind,
    )
    from syltra_testing import comfort_history, make_envelope

    now = datetime.now(tz=UTC)
    context = ContextService(publisher=_DemoPublisher())  # type: ignore[arg-type]
    adaptive = AdaptiveEngineService(_DemoPublisher())  # type: ignore[arg-type]
    policy = PolicyService()
    policy.set_policy(HOME, HomePolicy())
    gateway = _DemoGateway()

    seeded = [
        ("motion_living", "living_room", "occupancy.motion", True, None),
        ("temp_living", "living_room", "environment.temperature", 27.4, "C"),
        ("humidity_living", "living_room", "environment.humidity", 41.0, "%"),
        ("light_living", "living_room", "light.power", False, None),
        ("ac_living", "living_room", "climate.target_temperature", 26.0, "C"),
        ("meter_home", "utility", "energy.power", 780.0, "W"),
        ("gas_kitchen", "kitchen", "safety.gas_alarm", False, None),
        ("leak_kitchen", "kitchen", "safety.water_leak", False, None),
        ("tracker_phone", "entrance", "occupancy.presence", True, None),
    ]
    for device_id, room, capability, value, unit in seeded:
        envelope = make_envelope(
            capability=capability, value=value, unit=unit, home_id=HOME,
            device_id=device_id, room_id=room, occurred_at=now,
        )
        context.twin.apply(envelope)
        adaptive.observe(envelope)

    for event in comfort_history(days=21):
        adaptive.observe(event.model_copy(update={"home_id": HOME}))
    adaptive.train_home(HOME)
    adaptive.set_mode(HOME, LearningMode.SHADOW, actor="devserver")
    adaptive.set_mode(HOME, LearningMode.RECOMMEND, actor="devserver")

    # These services run in-process here rather than as consumers, so their
    # readiness flags must be set explicitly or health reports a false
    # "degraded".
    context.mark_ready(True)
    adaptive.mark_ready(True)

    home_state = context.twin.home(HOME)
    if home_state is not None:
        context.engine.evaluate(HOME, home_state, now)

    # One automation, so the Automations screen shows something real rather
    # than only its empty state. Comfort-class, like every automation may be.
    automations = AutomationEngine()
    automations.upsert(
        Automation(
            home_id=HOME,
            name="Living room light on motion",
            owner="demo-owner",
            trigger=AutomationTrigger(
                kind=TriggerKind.STATE_EQUALS,
                capability="occupancy.motion",
                device_id="motion_living",
                value=True,
            ),
            conditions=(
                AutomationCondition(
                    kind=ConditionKind.CONTEXT_ACTIVE, context_type="HOME_OCCUPIED"
                ),
            ),
            actions=(
                AutomationAction(
                    capability="light.power", value=True, device_id="light_living"
                ),
            ),
        )
    )

    return Platform(
        automations=automations,
        twin=context.twin,
        context=context,
        adaptive=adaptive,
        policy=policy,
        orchestrator=ActionOrchestrator(
            gateway=gateway, read_state=gateway.read, get_decision=policy.get,
            config=OrchestratorConfig(environment="development", verify_delay_seconds=0.0),
        ),
        feedback=FeedbackService(),
        risk=RiskEngineService(),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    tokens = TokenStore()
    app = create_app(build_platform(), tokens=tokens, rate_limiter=RateLimiter())

    # One token per role. The console filters navigation by permission, so a
    # role-aware change is only really checked by signing in as each of them —
    # and hunting for a way to mint a non-owner token is exactly the friction
    # that stops people doing it.
    issued = {
        role: tokens.issue(f"demo-{role.value.lower()}", role, {HOME}, ttl=timedelta(hours=12))[0]
        for role in (Role.OWNER, Role.ADULT, Role.CHILD, Role.GUEST, Role.INSTALLER)
    }
    token = issued[Role.OWNER]

    port = int(os.environ.get("PORT", "8088"))
    print(f"\n  SYLTRA console:    http://127.0.0.1:{port}/console/?home={HOME}")
    # The catalogue is the design system on its own: static, no data, no token.
    print(f"  Component catalogue: http://127.0.0.1:{port}/console/catalogue/")
    print("\n  Development tokens, one per role:")
    for role, value in issued.items():
        print(f"    {role.value:<10} {value}")
    print("\n  Paste one in the browser console to sign in as that role:")
    print(f"    localStorage.setItem('syltra.token', '{token}')\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
