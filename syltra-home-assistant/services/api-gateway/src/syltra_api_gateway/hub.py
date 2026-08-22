"""The hub: one process, one house, real devices.

`devserver.py` runs the platform against a synthetic household so a person can
look at the console. Four services have production entrypoints of their own,
each expecting NATS and Postgres beside them. Between those two there was
nothing — **no way to run this platform against a real Home Assistant on a real
machine.** The API gateway, which serves the console, the wall panel, scenes,
goals and every manual control, had no `main` at all.

This is that missing entrypoint, and it is deliberately the *simple* shape: one
Python process holding the whole intelligence layer, talking to a Home Assistant
next to it on the same box. It is what a mini-PC on a bench needs before there
is anything to manufacture.

## What it drops, and why that is honest rather than lazy

The distributed deployment exists for a reason — NATS gives durable replay
across service restarts, Postgres gives history that outlives a reboot. A single
house on a single box needs neither to prove itself:

- **No NATS.** The Edge Agent already takes its publisher as an argument, so the
  same service that publishes to a broker in the full deployment writes straight
  into the twin here. One seam, no second code path.
- **No Postgres.** The twin is in memory. A restart loses history and re-reads
  the house from Home Assistant within seconds; it does not lose the household's
  automations, scenes or goals, because those are re-read from disk.
- **No Prometheus.** The metrics endpoint is still served. Nothing has to scrape
  it for the hub to run.

What it does **not** drop is the part that matters: every command still goes
through the policy chain, the safety governor still runs on its own timer, and
the orchestrator still refuses life-safety actuators outside production.

## Accounts, plainly

`TokenStore` is in memory, so this prototype issues one owner token at start-up
and prints it once. **Restarting the hub invalidates it.** That is a real
limitation of a bench prototype and is stated here rather than discovered: the
operator account model is what makes tokens outlive a restart, and it is not
built yet.
"""

import asyncio
import contextlib
import logging
import os
import signal
from datetime import timedelta
from typing import Any

import uvicorn
from syltra_action_orchestrator import ActionOrchestrator, OrchestratorConfig
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_automation_engine import (
    AutomationDispatcher,
    AutomationEngine,
    GoalRegistry,
    SceneActivator,
    SceneRegistry,
)
from syltra_automation_engine.driver import AutomationDriver
from syltra_context_engine.service import ContextService
from syltra_edge_agent.config import EdgeAgentSettings
from syltra_edge_agent.gateway import HomeAssistantDeviceGateway
from syltra_edge_agent.ha_client import HomeAssistantWebSocketClient
from syltra_edge_agent.service import EdgeAgentService
from syltra_feedback_service import FeedbackService
from syltra_observability import configure_logging
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_risk_engine import IsolationDispatcher, RiskEngineService
from syltra_risk_engine.driver import RiskDriver
from syltra_security import Role, TokenStore

from syltra_api_gateway.api import create_app
from syltra_api_gateway.dependencies import RateLimiter
from syltra_api_gateway.energy import EnergyHistory
from syltra_api_gateway.platform import Platform

logger = logging.getLogger(__name__)

#: How long the owner token issued at start-up lasts. A year, because the
#: prototype has no way to renew one and a hub that logs its owner out on a
#: Tuesday afternoon is a hub nobody keeps running.
OWNER_TOKEN_TTL = timedelta(days=365)


class _DirectPublisher:
    """The Edge Agent's publisher, with the broker taken out.

    In the full deployment this hands each normalized envelope to NATS, and the
    Digital Twin and Context Engine read it from there. On one box those three
    are in the same process, so the envelope goes straight to them — the same
    objects, the same order, one hop instead of three.

    A dead letter is logged rather than queued. There is no consumer to replay
    it to, and a silent drop would make a mapping bug look like a quiet house.
    """

    def __init__(self, context: ContextService, adaptive: AdaptiveEngineService) -> None:
        self._context = context
        self._adaptive = adaptive
        self.applied = 0

    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        self._context.twin.apply(envelope)
        self._adaptive.observe(envelope)
        self.applied += 1

    async def publish_deadletter(self, **kwargs: Any) -> None:
        logger.warning("event could not be normalized: %s", kwargs)


def _publish_change(platform: Platform) -> Any:
    def publish(home_id: str, reasons: tuple[str, ...]) -> None:
        platform.stream.publish(home_id, *reasons)

    return publish


async def run_hub() -> None:
    settings = EdgeAgentSettings()
    configure_logging(
        service="hub",
        instance_id=settings.syltra_hub_id,
        level=settings.syltra_log_level,
        secrets=[settings.home_assistant_token.get_secret_value()],
    )

    if not settings.home_assistant_token.get_secret_value():
        # Refused rather than started: a hub that comes up with no way to reach
        # Home Assistant serves a console showing an empty house, which reads
        # as "you have no devices" rather than "I am not connected".
        msg = (
            "HOME_ASSISTANT_TOKEN is not set. Create a long-lived access token in "
            "Home Assistant (Profile → Security) and put it in the hub's environment."
        )
        raise SystemExit(msg)

    home_id = settings.syltra_home_id

    context = ContextService(publisher=_NullPublisher())  # type: ignore[arg-type]
    adaptive = AdaptiveEngineService(_NullPublisher())  # type: ignore[arg-type]
    policy = PolicyService()
    policy.set_policy(home_id, HomePolicy())

    client = HomeAssistantWebSocketClient(settings.websocket_url, settings.home_assistant_token)
    publisher = _DirectPublisher(context, adaptive)
    edge = EdgeAgentService(settings, client, publisher)  # type: ignore[arg-type]
    gateway = HomeAssistantDeviceGateway(client, edge, settings.syltra_environment)

    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=_state_reader(context),
        get_decision=policy.get,
        config=OrchestratorConfig(
            environment=settings.syltra_environment,
            # A real device takes a moment to report the state it was just put
            # into. Verifying instantly would call every command unverified.
            verify_delay_seconds=1.5,
        ),
    )
    risk = RiskEngineService(
        isolation=IsolationDispatcher(policy=policy, orchestrator=orchestrator)
    )

    platform = Platform(
        twin=context.twin,
        context=context,
        adaptive=adaptive,
        policy=policy,
        orchestrator=orchestrator,
        feedback=FeedbackService(),
        risk=risk,
        automations=AutomationEngine(),
        scenes=SceneRegistry(),
        scene_activator=SceneActivator(policy, orchestrator, context.twin),
        goals=GoalRegistry(),
        energy=EnergyHistory(),
    )
    platform.risk_driver = RiskDriver(context.twin, risk, on_change=_publish_change(platform))
    platform.automation_driver = AutomationDriver(
        context.twin,
        platform.automations,
        contexts=context,
        on_change=_publish_change(platform),
        dispatcher=AutomationDispatcher(policy, orchestrator),
        goals=platform.goals,
        manual_override=policy.manual_override_active,
    )
    platform.automation_driver.scheduler.set_timezone(
        home_id, os.environ.get("SYLTRA_TIMEZONE", "Asia/Riyadh")
    )

    tokens = TokenStore()
    owner_token, _ = tokens.issue(
        "owner", Role.OWNER, {home_id}, ttl=OWNER_TOKEN_TTL, display_name="Owner"
    )

    app = create_app(platform, tokens=tokens, rate_limiter=RateLimiter())

    @app.on_event("startup")
    async def _start() -> None:
        await platform.risk_driver.start()
        await platform.automation_driver.start()

    @app.on_event("shutdown")
    async def _stop() -> None:
        await platform.automation_driver.stop()
        await platform.risk_driver.stop()

    port = int(os.environ.get("SYLTRA_HUB_PORT", "8088"))
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="0.0.0.0",  # noqa: S104  # nosec B104 - a hub is reached from the house
            port=port,
            log_level=settings.syltra_log_level.lower(),
        )
    )

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, edge.stop)

    _announce(home_id, port, owner_token)

    api_task = asyncio.create_task(server.serve())
    try:
        # The Edge Agent's own loop: connect, bootstrap the registry, stream
        # state changes, reconnect with backoff. It is the thing that makes the
        # house appear in the twin.
        await edge.run()
    finally:
        server.should_exit = True
        await api_task


def _announce(home_id: str, port: int, owner_token: str) -> None:
    """Print what a person needs to use the hub, once.

    In the log rather than a file: on a prototype the operator is the person who
    started the process, and a token written to disk outlives the session that
    was allowed to see it.
    """
    logger.info("SYLTRA hub is up for %s", home_id)
    logger.info("  console:    http://<this-machine>:%d/console/", port)
    logger.info("  wall panel: http://<this-machine>:%d/panel/", port)
    logger.info("  owner token (this run only): %s", owner_token)
    logger.info(
        "  paste it in the browser console: "
        "localStorage.setItem('syltra.token', '%s')",
        owner_token,
    )


def _state_reader(context: ContextService) -> Any:
    """What the orchestrator reads back to verify a command took effect."""

    async def read(device_id: str, capability: str) -> Any:
        home = context.twin.home(os.environ.get("SYLTRA_HOME_ID", "home_dev_001"))
        if home is None:
            return None
        device = home.devices.get(device_id)
        if device is None:
            return None
        return device.capability(capability).value

    return read


class _NullPublisher:
    """The context and adaptive services publish their own outputs. On one box
    nothing subscribes to them, and they are read from the API instead."""

    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


def run() -> None:
    asyncio.run(run_hub())


if __name__ == "__main__":
    run()
