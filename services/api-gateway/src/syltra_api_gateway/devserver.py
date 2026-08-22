"""Development server: the gateway plus a seeded platform and a demo token.

Used by `make demo` and the preview tooling to look at the console with real
data. It seeds synthetic household state (spec §26) and prints a token so the
console can authenticate. Never used in a pilot or production deployment.
"""

import json
import logging
import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from syltra_action_orchestrator import ActionOrchestrator, OrchestratorConfig
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_context_engine.service import ContextService
from syltra_contracts import CommandResult, LearningMode
from syltra_feedback_service import FeedbackService
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_risk_engine import IsolationDispatcher, RiskEngineService
from syltra_automation_engine import AutomationDispatcher
from syltra_automation_engine.driver import AutomationDriver
from syltra_risk_engine.driver import RiskDriver
from syltra_security import Role, TokenStore

from syltra_api_gateway.api import create_app
from syltra_api_gateway.dependencies import RateLimiter
from syltra_api_gateway.energy import EnergyHistory
from syltra_api_gateway.platform import Platform

logger = logging.getLogger(__name__)

HOME = os.environ.get("SYLTRA_HOME_ID", "home_dev_001")


class _DemoPublisher:
    async def publish_envelope(self, subject: str, envelope: Any) -> None:
        return None

    async def publish_deadletter(self, **kwargs: Any) -> None:
        return None


class _DemoGateway:
    """Stands in for Home Assistant, including the half people forget.

    A real device does not only accept a command — it then reports its new
    state, which travels back through the Edge Agent into the twin. Without
    that return path the demo accepted every press and showed nothing changing,
    which is how a working control looks broken: the light was on in the
    gateway and off on every screen reading the twin.
    """

    def __init__(self) -> None:
        self.state: dict[tuple[str, str], Any] = {}
        self.twin: Any = None

    async def execute_capability_command(self, command: Any) -> CommandResult:
        self.state[(command.device_id, command.capability)] = command.value
        self._report_back(command)
        return CommandResult(accepted=True)

    def _report_back(self, command: Any) -> None:
        """What Home Assistant would send after the device obeyed.

        The room comes from the twin rather than from the command, because a
        `CapabilityCommand` does not carry one — reading it off the command
        raised, the action was recorded as failed, and the state dict had
        already been written, so the *next* press found the light "already as
        requested". A demo that fails in a way that looks like success is worse
        than one that fails plainly.
        """
        if self.twin is None:
            return
        from syltra_testing import make_envelope

        home = self.twin.home(HOME)
        device = home.devices.get(command.device_id) if home is not None else None
        self.twin.apply(
            make_envelope(
                capability=command.capability,
                value=command.value,
                unit=None,
                home_id=HOME,
                device_id=command.device_id,
                room_id=device.room_id if device is not None else None,
                occurred_at=datetime.now(tz=UTC),
            )
        )

    async def read(self, device_id: str, capability: str) -> Any:
        return self.state.get((device_id, capability))


def _publish_to(platform: Platform) -> Callable[[str, tuple[str, ...]], None]:
    """Adapt the hub's publisher to the driver's callback shape.

    A named function rather than a lambda because `publish` returns the change
    it recorded, and a lambda would quietly hand that return value back to a
    callback declared to return nothing.
    """

    def publish(home_id: str, reasons: tuple[str, ...]) -> None:
        platform.stream.publish(home_id, *reasons)

    return publish


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
    from syltra_testing import comfort_history, make_envelope, routine_history

    now = datetime.now(tz=UTC)
    context = ContextService(publisher=_DemoPublisher())  # type: ignore[arg-type]
    adaptive = AdaptiveEngineService(_DemoPublisher())  # type: ignore[arg-type]
    policy = PolicyService()
    policy.set_policy(HOME, HomePolicy())
    gateway = _DemoGateway()
    gateway.twin = context.twin
    energy = EnergyHistory()

    # Names, because a wall panel showing `light_living` is a panel that looks
    # unfinished to whoever lives there. The twin learns a name from a
    # `device.discovered` event, which is what Home Assistant supplies from its
    # own device registry.
    #
    # In Arabic, because a device name is the household's own words rather than
    # a string the platform translates — a screen switched to English still says
    # "مكيّف الصالة", exactly as it would in the house this demo stands for.
    named = {
        "motion_living": "حركة الصالة",
        "temp_living": "حرارة الصالة",
        "humidity_living": "رطوبة الصالة",
        "light_living": "إضاءة الصالة",
        "light_kitchen": "إضاءة المطبخ",
        "light_hall": "إضاءة الممر",
        "light_bedroom": "إضاءة غرفة النوم",
        "light_majlis": "إضاءة المجلس",
        "plug_tv": "التلفزيون",
        "plug_coffee": "آلة القهوة",
        "plug_heater": "سخان الماء",
        "ac_living": "مكيّف الصالة",
        "ac_bedroom": "مكيّف غرفة النوم",
        "curtain_living": "ستارة الصالة",
        "meter_home": "عدّاد المنزل",
        "gas_kitchen": "كاشف الغاز في المطبخ",
        "leak_kitchen": "كاشف تسرّب الماء",
        "tracker_phone": "الجوال",
        # Outdoors. A wall panel's weather comes from the household's own
        # sensors rather than from a forecast service: it works with the line
        # to the outside world down, which is the whole premise of the hub.
        "outdoor_temp": "حرارة الخارج",
        "outdoor_humidity": "رطوبة الخارج",
        "outdoor_light": "ضوء النهار",
        "outdoor_air": "جودة الهواء بالخارج",
    }
    for device_id, label in named.items():
        context.twin.apply(
            make_envelope(
                capability="device.online",
                value=label,
                unit=None,
                home_id=HOME,
                device_id=device_id,
                room_id=None,
                occurred_at=now,
                event_type="device.discovered",
            )
        )

    seeded = [
        # Things a household switches.
        ("light_living", "living_room", "light.power", True, None),
        ("light_kitchen", "kitchen", "light.power", False, None),
        ("light_hall", "hall", "light.power", True, None),
        ("light_bedroom", "bedroom", "light.power", False, None),
        ("light_majlis", "majlis", "light.power", False, None),
        ("plug_tv", "living_room", "switch.power", True, None),
        ("plug_coffee", "kitchen", "switch.power", False, None),
        ("plug_heater", "utility", "switch.power", True, None),
        ("ac_living", "living_room", "climate.target_temperature", 23.0, "C"),
        ("ac_bedroom", "bedroom", "climate.target_temperature", 22.0, "C"),
        ("curtain_living", "living_room", "cover.position", 60.0, "%"),
        # Things it reads.
        ("motion_living", "living_room", "occupancy.motion", True, None),
        ("temp_living", "living_room", "environment.temperature", 24.1, "C"),
        ("humidity_living", "living_room", "environment.humidity", 38.0, "%"),
        ("meter_home", "utility", "energy.power", 1420.0, "W"),
        ("gas_kitchen", "kitchen", "safety.gas_alarm", False, None),
        ("leak_kitchen", "kitchen", "safety.water_leak", False, None),
        ("tracker_phone", "entrance", "occupancy.presence", True, None),
        # Outdoors — a Riyadh afternoon in August, which is what the weather
        # tile is reading rather than a forecast from anywhere.
        ("outdoor_temp", "outside", "environment.temperature", 41.0, "C"),
        ("outdoor_humidity", "outside", "environment.humidity", 12.0, "%"),
        ("outdoor_light", "outside", "environment.illuminance", 94000.0, "lx"),
        ("outdoor_air", "outside", "environment.air_quality", 68.0, None),
    ]
    for device_id, room, capability, value, unit in seeded:
        envelope = make_envelope(
            capability=capability,
            value=value,
            unit=unit,
            home_id=HOME,
            device_id=device_id,
            room_id=room,
            occurred_at=now,
        )
        context.twin.apply(envelope)
        adaptive.observe(envelope)
        if capability == "energy.power":
            energy.record(HOME, float(value), now, device_id=device_id, room_id=room)

    for event in comfort_history(days=21):
        adaptive.observe(event.model_copy(update={"home_id": HOME}))
    # A routine as well as a preference, so the Automations screen has a real
    # proposal to show. Without it `routine_baseline` never fits and the
    # proposals endpoint answers with an empty list forever — which is exactly
    # the shape of "built and never seen working".
    for event in routine_history(days=28, hour=19, minute=0, home_id=HOME):
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
                AutomationAction(capability="light.power", value=True, device_id="light_living"),
            ),
        )
    )

    orchestrator = ActionOrchestrator(
        gateway=gateway,
        read_state=gateway.read,
        get_decision=policy.get,
        config=OrchestratorConfig(environment="development", verify_delay_seconds=0.0),
    )
    risk = RiskEngineService(
        isolation=IsolationDispatcher(policy=policy, orchestrator=orchestrator)
    )
    platform = Platform(
        automations=automations,
        twin=context.twin,
        context=context,
        adaptive=adaptive,
        policy=policy,
        orchestrator=orchestrator,
        feedback=FeedbackService(),
        energy=energy,
        # The isolation path is wired here, so a confirmed gas hazard closes the
        # valve rather than describing one. It stays harmless in development
        # because the orchestrator refuses every LIFE_SAFETY_CRITICAL actuator
        # outside production (safety invariant 16) — the wiring is live, the
        # valve is not, and the console shows the refusal rather than a
        # pretended success.
        risk=risk,
    )
    platform.automation_driver = AutomationDriver(
        context.twin,
        automations,
        contexts=context,
        on_change=_publish_to(platform),
        # Wired, so an automation in this demo actually turns on the light
        # rather than proposing to. It reaches comfort capabilities and nothing
        # else, and every command still goes through the policy gate.
        dispatcher=AutomationDispatcher(policy, orchestrator),
    )
    # The household's own clock. A person who writes "7pm" means 7pm here.
    platform.automation_driver.scheduler.set_timezone(
        HOME, os.environ.get("SYLTRA_TIMEZONE", "Asia/Riyadh")
    )
    platform.risk_driver = RiskDriver(
        context.twin,
        risk,
        contexts=context,
        on_change=_publish_to(platform),
    )
    return platform


def _add_dev_sign_in(app: FastAPI, token: str, port: int) -> None:
    """A one-click sign-in that only this development server has.

    The console reads its token from `localStorage` and offers no sign-in form,
    which is right for a hub with a real identity provider in front of it and
    miserable for looking at the thing: it leaves pasting into DevTools as the
    only way in, and Chrome now refuses that paste until you type "allow
    pasting" first.

    This route stores the token and redirects. It is defined here rather than
    in `api.py` so it cannot reach a pilot: `create_app` never sees it. The
    token is not put in the URL — a URL is copied, bookmarked and logged, and
    this one is handed straight to the page instead.

    It sits at the root rather than under `/console/` because the console is a
    static mount, and a mount answers every path beneath it before a route
    added afterwards gets a look.
    """

    @app.get("/dev-login", response_class=HTMLResponse, include_in_schema=False)
    async def dev_login() -> HTMLResponse:
        page = (
            "<!doctype html><meta charset=utf-8><title>SYLTRA — development sign-in</title>"
            "<script>"
            f"localStorage.setItem('syltra.token', {json.dumps(token)});"
            f"location.replace('/console/?home={HOME}');"
            "</script>"
            "<p>Signing in…</p>"
        )
        return HTMLResponse(page)

    print(f"  One-click sign-in:   http://127.0.0.1:{port}/dev-login")


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
    _add_dev_sign_in(app, token, port)
    # The catalogue is the design system on its own: static, no data, no token.
    print(f"  Component catalogue: http://127.0.0.1:{port}/console/catalogue/")
    print("\n  Development tokens, one per role:")
    for role, value in issued.items():
        print(f"    {role.value:<10} {value}")
    print("\n  Paste one in the browser console to sign in as that role:")
    print(f"    localStorage.setItem('syltra.token', '{token}')\n")
    # The safety loop runs for as long as the app does. Started in a lifespan
    # rather than at import, so it belongs to the running server and stops with
    # it instead of outliving it as an orphaned task.
    driver = app.state.platform.risk_driver

    automations_driver = app.state.platform.automation_driver

    @app.on_event("startup")
    async def _start_drivers() -> None:  # pragma: no cover - server lifecycle
        await driver.start()
        await automations_driver.start()

    @app.on_event("shutdown")
    async def _stop_drivers() -> None:  # pragma: no cover - server lifecycle
        await automations_driver.stop()
        await driver.stop()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
