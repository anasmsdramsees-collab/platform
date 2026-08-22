"""Local control survives the loss of the internet (spec §0 rule 4, invariant 8).

`test_degraded_modes.py` already proves the *safety* path opens no socket at
all. That is a stronger claim than this file makes, and a narrower one: the
safety path is deliberately network-free, while the local control path is not.
Controlling a light legitimately talks to Home Assistant, NATS and PostgreSQL —
all of them on this machine.

So the claim here is the one a household actually cares about: when the line to
the outside world goes down, the things inside the house still work. The guard
below models exactly that — loopback keeps working, everything else fails the
way an unplugged router makes it fail, with ENETUNREACH and a dead resolver.

Two assertions per test, and the second is the one that matters:

1. the control path completes and the device really changed;
2. nothing *reached* for the internet at all.

A component that tries a cloud call and tolerates the timeout would pass (1)
and fail (2). That is the distinction between working offline and degrading
gracefully, and only the first is what spec §0 rule 4 asks for.

What this file does not cover: Home Assistant integrations that are themselves
cloud-based, and NOTIFY steps routed to mobile push. Both need the internet by
their own nature, and no test here can change that.
"""

import errno
import ipaddress
import socket
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, NoReturn
from uuid import uuid4

import pytest
from syltra_action_orchestrator import (
    ActionOrchestrator,
    OrchestratorConfig,
    build_action_request,
)
from syltra_contracts import (
    ActionStatus,
    CommandResult,
    ModelReference,
    PolicyOutcome,
    Recommendation,
    RecommendationTarget,
)
from syltra_policy_safety import HomePolicy, PolicyService
from syltra_simulator.mock_ha import MockHomeAssistant

pytestmark = pytest.mark.safety

HOME = "home_offline"
NOW = datetime(2026, 8, 20, 19, 30, tzinfo=UTC)

LIGHT = ("sim_light_living", "light.power", "light.living_room")
AC = ("sim_ac_living", "climate.target_temperature", "climate.living_room")


# ── the guard: an unplugged router, not a disabled socket layer ──


def _host_is_local(host: object) -> bool:
    """True for addresses that never leave this machine."""
    if not isinstance(host, str) or host in ("", "localhost"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        # A name that is not localhost needs a resolver to answer, and the
        # resolver is on the far side of the connection that just went down.
        return False


def _address_is_local(address: object) -> bool:
    # AF_UNIX addresses are strings or bytes and never traverse a network.
    if not isinstance(address, tuple) or not address:
        return True
    return _host_is_local(address[0])


@contextmanager
def no_internet() -> Iterator[list[str]]:
    """Cut everything except loopback, recording each attempt to leave.

    Yields the list of attempts, so a test can assert on what was reached for
    rather than only on what survived.
    """
    attempts: list[str] = []
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_create_connection = socket.create_connection
    real_getaddrinfo = socket.getaddrinfo

    def _record(address: object) -> str:
        target = (
            f"{address[0]}:{address[1]}"
            if isinstance(address, tuple) and len(address) >= 2
            else str(address)
        )
        attempts.append(target)
        return target

    def _unreachable(address: object) -> NoReturn:
        _record(address)
        raise OSError(errno.ENETUNREACH, "Network is unreachable")

    def connect(self: socket.socket, address: Any) -> None:
        if not _address_is_local(address):
            _unreachable(address)
        real_connect(self, address)

    def connect_ex(self: socket.socket, address: Any) -> int:
        if not _address_is_local(address):
            _record(address)
            return errno.ENETUNREACH
        return real_connect_ex(self, address)

    def create_connection(address: Any, *args: Any, **kwargs: Any) -> socket.socket:
        if not _address_is_local(address):
            _unreachable(address)
        return real_create_connection(address, *args, **kwargs)

    def getaddrinfo(host: Any, port: Any, *args: Any, **kwargs: Any) -> Any:
        if not _host_is_local(host):
            _record((host, port))
            raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
        return real_getaddrinfo(host, port, *args, **kwargs)

    socket.socket.connect = connect  # type: ignore[assignment,method-assign]
    socket.socket.connect_ex = connect_ex  # type: ignore[assignment,method-assign]
    socket.create_connection = create_connection
    socket.getaddrinfo = getaddrinfo
    try:
        yield attempts
    finally:
        socket.socket.connect = real_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = real_connect_ex  # type: ignore[method-assign]
        socket.create_connection = real_create_connection
        socket.getaddrinfo = real_getaddrinfo


# ── the guard is tested before anything is tested with it ──
#
# Without these two, a guard that silently stopped guarding would make every
# test below pass while proving nothing.


def test_the_guard_blocks_and_records_a_reach_for_the_internet() -> None:
    with no_internet() as attempts, pytest.raises(OSError):
        socket.create_connection(("203.0.113.1", 80), timeout=0.1)
    assert attempts, "an outbound attempt was made but the guard did not see it"
    assert "203.0.113.1" in attempts[0]


def test_the_guard_blocks_name_resolution() -> None:
    with no_internet() as attempts, pytest.raises(socket.gaierror):
        socket.getaddrinfo("cloud.example.com", 443)
    assert attempts == ["cloud.example.com:443"]


def test_the_guard_leaves_loopback_alone() -> None:
    """An over-eager guard would fail the tests below for the wrong reason."""
    with no_internet() as attempts:
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        client = socket.create_connection(listener.getsockname(), timeout=1)
        served, _ = listener.accept()
        served.close()
        client.close()
        listener.close()
        assert socket.getaddrinfo("localhost", 0)
    assert attempts == []


# ── the control path, with the line down ──


class SimulatorGateway:
    """Drives the mock Home Assistant through capability commands."""

    def __init__(self, mock: MockHomeAssistant) -> None:
        self._mock = mock
        self._entities = {LIGHT[0]: LIGHT[2], AC[0]: AC[2]}
        self.commands: list[Any] = []

    async def execute_capability_command(self, command: Any) -> CommandResult:
        self.commands.append(command)
        entity = self._entities.get(command.device_id)
        if entity is None:
            return CommandResult(accepted=False, reason="UNKNOWN_TARGET_MAPPING")
        if command.capability == LIGHT[1]:
            await self._mock.set_state(entity, "on" if command.value else "off")
        elif command.capability == AC[1]:
            await self._mock.set_state(entity, "cool", {"temperature": float(command.value)})
        else:
            return CommandResult(accepted=False, reason="UNSUPPORTED_CAPABILITY_COMMAND")
        return CommandResult(accepted=True)

    async def read(self, device_id: str, capability: str) -> Any:
        entity = self._entities.get(device_id)
        state = None if entity is None else self._mock._states.get(entity)
        if state is None:
            return None
        if capability == LIGHT[1]:
            return state["state"] == "on"
        if capability == AC[1]:
            return state["attributes"].get("temperature")
        return None


def recommendation(device_id: str, capability: str, value: Any, kind: str) -> Recommendation:
    return Recommendation.model_validate(
        {
            "recommendation_id": uuid4(),
            "home_id": HOME,
            "recommendation_type": kind,
            "created_at": NOW,
            "expires_at": NOW + timedelta(minutes=15),
            "target": RecommendationTarget(device_id=device_id, capability=capability),
            "proposed_value": value,
            "confidence": 0.9,
            "reason_codes": ["REPEATED_USER_PATTERN"],
            "model": ModelReference(name="temperature_preference", version="1.0.0"),
            "required_policy": "COMFORT_AUTOMATION",
            "requires_user_approval": False,
        }
    )


@pytest.mark.parametrize(
    ("device_id", "capability", "value", "kind"),
    [
        (LIGHT[0], LIGHT[1], True, "lighting.routine"),
        (AC[0], AC[1], 23, "climate.precondition"),
    ],
)
async def test_local_control_completes_with_no_internet(
    device_id: str, capability: str, value: Any, kind: str
) -> None:
    """Recommendation → policy → device → verification, with the line down.

    The whole chain is built and run inside the guard, so a reach for the
    outside world during construction counts as much as one during dispatch.
    """
    with no_internet() as attempts:
        mock = MockHomeAssistant(start_time=NOW)
        await mock.start()
        gateway = SimulatorGateway(mock)
        policy = PolicyService()
        policy.set_policy(
            HOME,
            HomePolicy(unattended_automation=True, require_approval_below=0.0),
        )
        orchestrator = ActionOrchestrator(
            gateway=gateway,
            read_state=gateway.read,
            get_decision=policy.get,
            config=OrchestratorConfig(environment="production", verify_delay_seconds=0.0),
        )
        try:
            rec = recommendation(device_id, capability, value, kind)
            before = await gateway.read(device_id, capability)
            decision = policy.evaluate(rec, now=NOW, twin_value=before, twin_status="KNOWN")
            assert decision.decision is PolicyOutcome.ALLOW
            request = build_action_request(decision, rec, NOW, previous_value=before)
            result = await orchestrator.execute(request, now=NOW)
        finally:
            await mock.stop()

    assert result.status is ActionStatus.SUCCEEDED
    assert await gateway.read(device_id, capability) == value
    assert attempts == [], f"the control path reached for the internet: {attempts}"


async def test_a_denied_recommendation_stays_denied_with_no_internet() -> None:
    """Losing the internet must not loosen a decision, only keep it working."""
    with no_internet() as attempts:
        policy = PolicyService()
        policy.set_policy(
            HOME,
            HomePolicy(unattended_automation=True, require_approval_below=0.0),
        )
        rec = recommendation(LIGHT[0], LIGHT[1], True, "lighting.routine")
        weak = rec.model_copy(update={"confidence": 0.05})
        decision = policy.evaluate(weak, now=NOW, twin_value=False, twin_status="KNOWN")

    assert decision.decision is PolicyOutcome.DENY
    assert attempts == []
