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
    hub_id: str = "hub_dev_001"
    started_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def known_homes(self) -> list[str]:
        return sorted(self.twin.home_ids)

    def system_status(self, now: datetime | None = None) -> dict[str, Any]:
        moment = now or datetime.now(tz=UTC)
        return {
            "hub_id": self.hub_id,
            "checked_at": moment.isoformat(),
            "uptime_seconds": round((moment - self.started_at).total_seconds(), 1),
            "homes": len(self.known_homes()),
            # Component health, not implementation detail: no broker URLs, no
            # stream names, no database DSNs.
            "components": {
                "digital_twin": "ok",
                "context_engine": "ok" if self.context.ready else "degraded",
                "adaptive_engine": "ok" if self.adaptive.ready else "degraded",
                "policy_safety": "ok",
                "action_orchestrator": "ok",
                "risk_engine": "ok",
                "feedback_service": "ok",
            },
        }
