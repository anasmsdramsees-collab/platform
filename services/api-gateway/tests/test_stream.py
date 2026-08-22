"""The live change feed (`/v1/stream`).

A stream is easy to get wrong in a way that looks right: it delivers while you
are watching it, and drops the one message that mattered while you were not.
So most of this file is about the seams — reconnection, a cursor too old to
answer, a client that fell behind, and the boundary between homes.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from syltra_api_gateway.platform import Platform
from syltra_api_gateway.stream import BUFFER_SIZE, StreamHub

# The home the shared fixtures seed. Spelled out rather than imported from
# conftest: importlib import mode gives that module no importable name.
SEEDED_HOME = "home_001"

HOME = "home_stream"
OTHER = "home_other"
NOW = datetime(2026, 8, 20, 21, 0, tzinfo=UTC)


# ── sequences answer "did I miss anything?" ──


@pytest.mark.asyncio
async def test_sequences_are_monotonic_per_home() -> None:
    hub = StreamHub()
    assert hub.publish(HOME, "A", now=NOW).seq == 1
    assert hub.publish(HOME, "B", now=NOW).seq == 2
    # A second home counts separately: one busy household must not advance
    # another's cursor and make it re-read for nothing.
    assert hub.publish(OTHER, "A", now=NOW).seq == 1


@pytest.mark.asyncio
async def test_a_client_that_missed_nothing_is_told_so() -> None:
    hub = StreamHub()
    hub.publish(HOME, "A", now=NOW)
    missed, resync = hub.missed(HOME, cursor=1)
    assert missed == []
    assert resync is False


@pytest.mark.asyncio
async def test_a_client_that_missed_some_is_given_them() -> None:
    hub = StreamHub()
    for reason in ("A", "B", "C"):
        hub.publish(HOME, reason, now=NOW)
    missed, resync = hub.missed(HOME, cursor=1)
    assert [change.seq for change in missed] == [2, 3]
    assert resync is False


@pytest.mark.asyncio
async def test_a_cursor_older_than_the_buffer_asks_for_a_resync() -> None:
    """The case that matters: a gap the server cannot describe.

    Returning the events it still has would leave the client believing it had
    caught up. Saying "resync" makes it re-read, which is always correct and
    occasionally redundant — the right way round.
    """
    hub = StreamHub()
    for index in range(BUFFER_SIZE + 10):
        hub.publish(HOME, f"E{index}", now=NOW)

    missed, resync = hub.missed(HOME, cursor=1)
    assert resync is True
    assert missed == []


@pytest.mark.asyncio
async def test_a_fresh_client_is_not_told_to_resync() -> None:
    """Cursor zero on a home with history is a first connection, not a gap."""
    hub = StreamHub()
    hub.publish(HOME, "A", now=NOW)
    missed, resync = hub.missed(HOME, cursor=0)
    assert resync is False
    assert [change.seq for change in missed] == [1]


# ── a slow client must not stall a safety path ──


@pytest.mark.asyncio
async def test_publishing_never_blocks_on_a_full_subscriber() -> None:
    """`publish` is called from the risk driver's pass.

    A console that stopped reading must not be able to delay the loop that
    watches the gas detectors, so the queue drops rather than waits.
    """
    hub = StreamHub()
    queue = hub.subscribe(HOME)

    for index in range(500):
        await asyncio.wait_for(asyncio.to_thread(hub.publish, HOME, f"E{index}"), timeout=1.0)

    assert queue.qsize() <= 64
    # The newest survives, which is the one that matters: it alone tells the
    # client to re-read, and re-reading catches up on everything dropped.
    newest = hub.latest_sequence(HOME)
    drained = []
    while not queue.empty():
        drained.append(queue.get_nowait().seq)
    assert newest in drained


@pytest.mark.asyncio
async def test_unsubscribing_stops_delivery() -> None:
    hub = StreamHub()
    queue = hub.subscribe(HOME)
    hub.unsubscribe(HOME, queue)
    hub.publish(HOME, "A", now=NOW)
    assert queue.empty()
    assert hub.subscriber_count == 0


# ── the endpoint ──


def test_the_socket_refuses_an_unauthenticated_peer(client: TestClient) -> None:
    with pytest.raises(Exception):  # noqa: B017 - starlette raises on a rejected handshake
        with client.websocket_connect("/v1/stream?token=nonsense&home_id=" + HOME):
            pass


def test_the_socket_refuses_a_home_the_token_cannot_see(
    client: TestClient, auth: Callable[..., dict[str, str]]
) -> None:
    token = auth()["Authorization"].split()[1]
    with pytest.raises(Exception):  # noqa: B017
        with client.websocket_connect(f"/v1/stream?token={token}&home_id=home_not_yours"):
            pass


def test_a_connected_client_learns_the_current_sequence(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    token = auth()["Authorization"].split()[1]
    platform.stream.publish(SEEDED_HOME, "SEEDED_HOME")
    with client.websocket_connect(f"/v1/stream?token={token}&home_id={SEEDED_HOME}") as socket:
        hello = socket.receive_json()
        assert hello["type"] == "connected"
        assert hello["seq"] == platform.stream.latest_sequence(SEEDED_HOME)
        assert "heartbeat_seconds" in hello


def test_a_change_reaches_a_connected_client(
    client: TestClient, auth: Callable[..., dict[str, str]], platform: Platform
) -> None:
    token = auth()["Authorization"].split()[1]
    with client.websocket_connect(f"/v1/stream?token={token}&home_id={SEEDED_HOME}") as socket:
        socket.receive_json()
        platform.stream.publish(SEEDED_HOME, "RISK_CASE_CONFIRMED")
        message = socket.receive_json()
        assert message["type"] == "changed"
        assert "RISK_CASE_CONFIRMED" in message["reasons"]
