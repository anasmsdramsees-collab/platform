"""Gateway safety tests — safety invariant 16 (spec §18).

Development and simulation environments must block real critical actuator
targets. The Safety Governor (Phase 6) is the authoritative gate; this is
defense in depth at the integration boundary.
"""

from typing import Any

import pytest
from syltra_contracts import CapabilityCommand
from syltra_contracts.capabilities import CRITICAL_ACTUATOR_CAPABILITIES
from syltra_edge_agent.gateway import HomeAssistantDeviceGateway

pytestmark = pytest.mark.safety


class _StubClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append((domain, service, service_data))
        return {}

    async def get_states(self) -> list[dict[str, Any]]:
        return []


class _StubService:
    registry_snapshot = None


def make_gateway(environment: str) -> tuple[HomeAssistantDeviceGateway, _StubClient]:
    client = _StubClient()
    gateway = HomeAssistantDeviceGateway(client, _StubService(), environment)  # type: ignore[arg-type]
    return gateway, client


@pytest.mark.parametrize("capability", sorted(CRITICAL_ACTUATOR_CAPABILITIES))
@pytest.mark.parametrize("environment", ["development", "simulation"])
async def test_critical_actuators_blocked_in_development(
    capability: str, environment: str
) -> None:
    gateway, client = make_gateway(environment)
    result = await gateway.execute_capability_command(
        CapabilityCommand(device_id="sim_lock_front", capability=capability, value="unlocked")
    )
    assert not result.accepted
    assert result.reason == "CRITICAL_ACTUATOR_BLOCKED_IN_DEVELOPMENT"
    # Crucially, nothing was dispatched toward the device.
    assert client.calls == []


async def test_block_precedes_target_resolution() -> None:
    # The block must not depend on whether a mapping exists — an unknown
    # target must never be the reason a critical command "fails".
    gateway, _ = make_gateway("development")
    result = await gateway.execute_capability_command(
        CapabilityCommand(device_id="does_not_exist", capability="valve.state", value="closed")
    )
    assert result.reason == "CRITICAL_ACTUATOR_BLOCKED_IN_DEVELOPMENT"


async def test_unsupported_capability_is_refused_not_guessed() -> None:
    gateway, client = make_gateway("development")
    result = await gateway.execute_capability_command(
        CapabilityCommand(device_id="d", capability="environment.temperature", value=20)
    )
    assert not result.accepted
    assert result.reason == "UNSUPPORTED_CAPABILITY_COMMAND"
    assert client.calls == []


async def test_comfort_command_without_known_target_is_refused() -> None:
    gateway, client = make_gateway("development")
    result = await gateway.execute_capability_command(
        CapabilityCommand(device_id="unknown_device", capability="light.power", value=True)
    )
    assert not result.accepted
    assert result.reason == "UNKNOWN_TARGET_MAPPING"
    assert client.calls == []
