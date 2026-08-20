"""The aggregated read model behind the API (spec §14.9).

The gateway does not talk to NATS or PostgreSQL on behalf of a caller. It holds
references to the in-process services and composes their state into view models,
so no endpoint can leak a subject name, a stream sequence, a connection string
or a table shape (spec §14.9: avoid exposing internal NATS or database details).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from syltra_action_orchestrator import ActionOrchestrator
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_context_engine.service import ContextService
from syltra_digital_twin.core import TwinProjection
from syltra_feedback_service import FeedbackService
from syltra_policy_safety import PolicyService
from syltra_automation_engine import AutomationEngine
from syltra_risk_engine import RiskEngineService


@dataclass
class Platform:
    """Everything the gateway may read from.

    Assembled by the entrypoint and injected, so tests construct exactly the
    subset they need rather than standing up the whole stack.
    """

    twin: TwinProjection
    context: ContextService
    adaptive: AdaptiveEngineService
    policy: PolicyService
    orchestrator: ActionOrchestrator
    feedback: FeedbackService
    risk: RiskEngineService
    automations: AutomationEngine = field(default_factory=AutomationEngine)
    # The loop that feeds the risk engine. Optional so tests and the OpenAPI
    # export construct a platform without starting one, and reported as
    # degraded when absent rather than assumed fine.
    risk_driver: Any = None
    risk_driver_tolerance_seconds: float = 10.0
    hub_id: str = "hub_dev_001"
    started_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def _risk_engine_health(self) -> str:
        """"ok" only while something is asking the risk engine to look."""
        driver = self.risk_driver
        if driver is None:
            return "degraded"
        tolerance = self.risk_driver_tolerance_seconds
        return "ok" if driver.health.is_healthy(datetime.now(tz=UTC), tolerance) else "degraded"

    def known_homes(self) -> list[str]:
        return sorted(self.twin.home_ids)

    @property
    def dispatch_enabled(self) -> bool:
        """Whether this hub may command a device at all.

        Read from the orchestrator's own configuration rather than a separate
        setting, so the console cannot report "acting" while the component that
        would act is observing.
        """
        return self.orchestrator.dispatch_enabled

    def system_status(self, now: datetime | None = None) -> dict[str, Any]:
        moment = now or datetime.now(tz=UTC)
        return {
            "hub_id": self.hub_id,
            "checked_at": moment.isoformat(),
            "uptime_seconds": round((moment - self.started_at).total_seconds(), 1),
            "homes": len(self.known_homes()),
            # The most consequential fact about a hub, and the one a pilot
            # needs on screen rather than in a config file: can it act?
            "dispatch_enabled": self.dispatch_enabled,
            # Component health, not implementation detail: no broker URLs, no
            # stream names, no database DSNs.
            "components": {
                "digital_twin": "ok",
                "context_engine": "ok" if self.context.ready else "degraded",
                "adaptive_engine": "ok" if self.adaptive.ready else "degraded",
                "policy_safety": "ok",
                "action_orchestrator": "ok",
                # Hard-coding "ok" for the risk engine hid the worst fault the
                # hub can have: the loop that reads the detectors stopping
                # while everything else keeps rendering. It now reports what
                # the driver is actually doing, and "no driver at all" is a
                # fault rather than a silence.
                "risk_engine": self._risk_engine_health(),
                "feedback_service": "ok",
            },
        }
