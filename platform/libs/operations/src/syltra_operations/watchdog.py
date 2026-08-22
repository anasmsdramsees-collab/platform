"""Service watchdog (spec §22 Phase 8).

Supervises each service's health endpoint and restarts what has stopped
responding. The Safety Governor is supervised like everything else — it was the
last open gap in `SAFETY_CASE.md`, because a crashed governor stops monitoring
*silently*, which is the worst way for a safety component to fail.

The escalation is deliberately slow to fire and quick to give up: a service is
restarted only after several consecutive failures (a single missed probe is
usually a busy moment, not a crash), and after a bounded number of restarts the
watchdog stops trying and raises an alert instead of thrashing.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

logger = logging.getLogger(__name__)


class ServiceState(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    """Failing probes, but not yet past the restart threshold."""
    RESTARTING = "RESTARTING"
    FAILED = "FAILED"
    """Restart budget exhausted — a human is needed."""


@dataclass(frozen=True)
class SupervisedService:
    name: str
    critical: bool = False
    """A critical service failing raises an alert immediately, not just a log.

    The Safety Governor and the Edge Agent are critical: without them the home
    is unmonitored, and a household should be told rather than left to notice.
    """
    failure_threshold: int = 3
    restart_budget: int = 5
    restart_window: timedelta = timedelta(hours=1)


@dataclass
class ServiceStatus:
    service: SupervisedService
    state: ServiceState = ServiceState.HEALTHY
    consecutive_failures: int = 0
    restarts: list[datetime] = field(default_factory=list)
    last_checked_at: datetime | None = None
    last_error: str | None = None

    def restarts_in_window(self, now: datetime) -> int:
        cutoff = now - self.service.restart_window
        return sum(1 for stamp in self.restarts if stamp >= cutoff)


HealthProbe = Callable[[str], bool]
RestartAction = Callable[[str], None]
AlertAction = Callable[[str, str], None]


class Watchdog:
    """Health supervision with bounded restart attempts."""

    def __init__(
        self,
        services: tuple[SupervisedService, ...],
        probe: HealthProbe,
        restart: RestartAction,
        alert: AlertAction | None = None,
    ) -> None:
        self._probe = probe
        self._restart = restart
        self._alert = alert
        self.statuses: dict[str, ServiceStatus] = {
            service.name: ServiceStatus(service=service) for service in services
        }

    def check_all(self, now: datetime | None = None) -> list[ServiceStatus]:
        moment = now or datetime.now(tz=UTC)
        return [self.check(name, moment) for name in sorted(self.statuses)]

    def check(self, name: str, now: datetime | None = None) -> ServiceStatus:
        moment = now or datetime.now(tz=UTC)
        status = self.statuses[name]
        status.last_checked_at = moment

        try:
            healthy = self._probe(name)
        except Exception as exc:  # noqa: BLE001 - any probe failure is a failure
            healthy = False
            status.last_error = type(exc).__name__

        if healthy:
            if status.state is not ServiceState.HEALTHY:
                logger.info("%s recovered", name)
            status.state = ServiceState.HEALTHY
            status.consecutive_failures = 0
            status.last_error = None
            return status

        status.consecutive_failures += 1
        if status.consecutive_failures < status.service.failure_threshold:
            # One missed probe is usually a busy moment, not a crash.
            status.state = ServiceState.DEGRADED
            return status

        if status.restarts_in_window(moment) >= status.service.restart_budget:
            # Thrashing helps nobody: stop, and make the failure visible.
            status.state = ServiceState.FAILED
            self._raise_alert(name, "restart budget exhausted; manual intervention required")
            return status

        status.state = ServiceState.RESTARTING
        status.restarts.append(moment)
        logger.warning(
            "%s failed %d consecutive health checks; restarting (%d in window)",
            name, status.consecutive_failures, status.restarts_in_window(moment),
        )
        if status.service.critical:
            self._raise_alert(name, "critical service restarted; the home may be unmonitored")
        try:
            self._restart(name)
        except Exception as exc:  # noqa: BLE001
            status.state = ServiceState.FAILED
            status.last_error = type(exc).__name__
            self._raise_alert(name, f"restart failed: {type(exc).__name__}")
        else:
            status.consecutive_failures = 0
        return status

    def unhealthy(self) -> list[str]:
        return sorted(
            name
            for name, status in self.statuses.items()
            if status.state is not ServiceState.HEALTHY
        )

    def _raise_alert(self, name: str, message: str) -> None:
        logger.error("WATCHDOG: %s — %s", name, message)
        if self._alert is not None:
            self._alert(name, message)


DEFAULT_SERVICES: tuple[SupervisedService, ...] = (
    # Critical: without these the home is unmonitored.
    SupervisedService("edge-agent", critical=True),
    SupervisedService("risk-engine", critical=True),
    SupervisedService("policy-safety", critical=True),
    # Important, but their loss degrades comfort rather than safety
    # (safety invariant 7).
    SupervisedService("digital-twin"),
    SupervisedService("context-engine"),
    SupervisedService("adaptive-engine"),
    SupervisedService("action-orchestrator"),
    SupervisedService("api-gateway"),
)
