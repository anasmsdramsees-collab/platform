"""Wires the mock Home Assistant boundary to a real Edge Agent instance.

Used by ``make simulate`` and by the integration tests, so both exercise the
identical code path: mock HA → Edge Agent → publisher.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, cast

from pydantic import SecretStr

from syltra_contracts import EventEnvelope
from syltra_eventing import EventPublisher
from syltra_edge_agent.config import EdgeAgentSettings
from syltra_edge_agent.ha_client import HomeAssistantWebSocketClient
from syltra_edge_agent.service import EdgeAgentService
from syltra_simulator.mock_ha import MockHomeAssistant
from syltra_simulator.scenarios import Scenario, apply_step


@dataclass
class CapturedEvents:
    """In-memory publisher stand-in for tests and dry runs."""

    raw: list[tuple[str, EventEnvelope]] = field(default_factory=list)
    normalized: list[tuple[str, EventEnvelope]] = field(default_factory=list)
    deadletter: list[dict[str, Any]] = field(default_factory=list)

    async def publish_envelope(self, subject: str, envelope: EventEnvelope) -> None:
        if subject.startswith("syltra.raw."):
            self.raw.append((subject, envelope))
        else:
            self.normalized.append((subject, envelope))

    async def publish_deadletter(
        self,
        reason_codes: list[str],
        error: str,
        original_subject: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.deadletter.append(
            {
                "reason_codes": reason_codes,
                "error": error,
                "original_subject": original_subject,
                "payload": payload or {},
            }
        )

    def capability_events(self, capability: str) -> list[EventEnvelope]:
        return [e for _, e in self.normalized if e.capability == capability]


def build_settings(ha: MockHomeAssistant, **overrides: Any) -> EdgeAgentSettings:
    return EdgeAgentSettings(
        home_assistant_url=ha.url,
        home_assistant_token=SecretStr(ha.token),
        syltra_home_id=overrides.pop("home_id", "home_sim_001"),
        syltra_hub_id=overrides.pop("hub_id", "hub_sim_001"),
        syltra_environment="simulation",
        reconnect_initial_seconds=overrides.pop("reconnect_initial_seconds", 0.05),
        reconnect_max_seconds=overrides.pop("reconnect_max_seconds", 0.5),
        **overrides,
    )


class SimulationRun:
    """Starts a mock HA + Edge Agent pair and drives scenarios against them.

    ``publisher`` accepts anything satisfying the publisher protocol the Edge
    Agent uses (``EventPublisher`` in production, ``CapturedEvents`` in tests).
    """

    def __init__(self, publisher: EventPublisher | CapturedEvents | None = None) -> None:
        self.ha = MockHomeAssistant()
        self.events = CapturedEvents()
        self._publisher: EventPublisher = cast(
            EventPublisher, publisher if publisher is not None else self.events
        )
        self._service: EdgeAgentService | None = None
        self._task: asyncio.Task[None] | None = None

    @property
    def service(self) -> EdgeAgentService:
        if self._service is None:
            msg = "simulation not started"
            raise RuntimeError(msg)
        return self._service

    async def start(self, **settings_overrides: Any) -> None:
        await self.ha.start()
        settings = build_settings(self.ha, **settings_overrides)
        client = HomeAssistantWebSocketClient(settings.websocket_url, settings.home_assistant_token)
        self._service = EdgeAgentService(settings, client, self._publisher)
        self._task = asyncio.create_task(self._service.run())
        await self.wait_until_connected()

    async def wait_until_connected(self, timeout: float = 10.0) -> None:
        await _wait_for(lambda: self._service is not None and self._service.connected, timeout)
        # Bootstrap seeds current states; wait for it to finish publishing.
        await _wait_for(lambda: self.service.registry_snapshot is not None, timeout)
        await asyncio.sleep(0.1)

    async def run_scenario(self, scenario: Scenario, settle: float = 0.25) -> CapturedEvents:
        for step in scenario.steps:
            await apply_step(self.ha, step)
            await asyncio.sleep(0.02)
        await asyncio.sleep(settle)
        return self.events

    def mark(self) -> tuple[int, int, int]:
        """Snapshot counters so a scenario's own output can be isolated."""
        return len(self.events.raw), len(self.events.normalized), len(self.events.deadletter)

    async def stop(self) -> None:
        if self._service is not None:
            self._service.stop()
        if self._task is not None:
            self._task.cancel()
            try:  # noqa: SIM105 - suppress needs the import; keep explicit
                await self._task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
        await self.ha.stop()


async def _wait_for(
    predicate: Callable[[], bool], timeout: float, interval: float = 0.02
) -> None:
    elapsed = 0.0
    while elapsed < timeout:
        if predicate():
            return
        await asyncio.sleep(interval)
        elapsed += interval
    msg = f"condition not met within {timeout}s"
    raise TimeoutError(msg)


async def wait_for(predicate: Callable[[], bool], timeout: float = 10.0) -> None:
    await _wait_for(predicate, timeout)


async def wait_for_async(
    predicate: Callable[[], Awaitable[bool]], timeout: float = 10.0
) -> None:
    elapsed = 0.0
    while elapsed < timeout:
        if await predicate():
            return
        await asyncio.sleep(0.05)
        elapsed += 0.05
    msg = f"condition not met within {timeout}s"
    raise TimeoutError(msg)
