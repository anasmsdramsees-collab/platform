"""End-to-end: simulator → Edge Agent → JetStream → Digital Twin.

The whole ingest chain the platform actually ships, across a real NATS server
and a real PostgreSQL database — the twin is driven by the Edge Agent's own
output rather than hand-made events.
"""

import asyncio
import contextlib
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest_asyncio
from nats.aio.msg import Msg
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from syltra_digital_twin.core import StateStatus
from syltra_digital_twin.service import DigitalTwinService
from syltra_eventing import EventPublisher, ensure_streams
from syltra_simulator.harness import SimulationRun
from syltra_testing import make_envelope

HOME = "home_pipeline"

Pipeline = tuple[SimulationRun, DigitalTwinService, Any, Any]


async def _noop_ack() -> None:
    """Stand-in ack for synthesized broker messages."""
    return None


async def drain_into_twin(
    subscription: Any, service: DigitalTwinService, budget: int = 400
) -> int:
    """Consume everything currently pending, applying it to the twin."""
    processed = 0
    for _ in range(budget):
        try:
            message = await subscription.next_msg(timeout=0.5)
        except TimeoutError:
            break
        await service.handle_message(message)
        processed += 1
    return processed


@pytest_asyncio.fixture
async def pipeline(
    nats_connection: Any, db_sessions: async_sessionmaker[AsyncSession]
) -> AsyncIterator[tuple[SimulationRun, DigitalTwinService, Any, Any]]:
    """A live Edge Agent publishing into JetStream, plus a twin consuming it."""
    js = nats_connection.jetstream()
    await ensure_streams(js)
    for stream in ("SYLTRA_RAW", "SYLTRA_NORMALIZED", "SYLTRA_DERIVED", "SYLTRA_DEADLETTER"):
        with contextlib.suppress(Exception):
            await js.purge_stream(stream)

    run = SimulationRun(publisher=EventPublisher(js, service="edge-agent"))
    await run.start(home_id=HOME)

    service = DigitalTwinService(db_sessions, EventPublisher(js, service="digital-twin"))
    subscription = await js.subscribe(
        "syltra.normalized.>",
        durable="twin-test",
        manual_ack=True,
        config=ConsumerConfig(
            durable_name="twin-test",
            deliver_policy=DeliverPolicy.ALL,
            ack_policy=AckPolicy.EXPLICIT,
        ),
    )
    try:
        yield run, service, subscription, js
    finally:
        await run.stop()
        with contextlib.suppress(Exception):
            await subscription.unsubscribe()
        with contextlib.suppress(Exception):
            await js.delete_consumer("SYLTRA_NORMALIZED", "twin-test")


async def test_device_state_flows_from_home_assistant_into_the_twin(pipeline: Pipeline) -> None:
    run, service, subscription, _ = pipeline
    await run.ha.set_state("sensor.living_room_temperature", "29.5")
    await asyncio.sleep(0.4)
    assert await drain_into_twin(subscription, service) > 0

    device = service.twin.device(HOME, "sim_climate_sensor_living")
    assert device is not None
    temperature = device.capability("environment.temperature")
    assert temperature.value == 29.5
    assert temperature.observed
    assert temperature.status_at(datetime.now(tz=UTC)) is StateStatus.KNOWN
    assert device.room_id == "living_room"


async def test_twin_publishes_state_updated_events(pipeline: Pipeline) -> None:
    run, service, subscription, js = pipeline
    await run.ha.set_state("binary_sensor.living_room_motion", "on")
    await asyncio.sleep(0.4)
    await drain_into_twin(subscription, service)

    twin_sub = await js.subscribe("syltra.twin.>", durable="twin-updates-test", manual_ack=True)
    try:
        message = await twin_sub.next_msg(timeout=5)
        assert b'"twin.state.updated"' in message.data
        await message.ack()
    finally:
        with contextlib.suppress(Exception):
            await twin_sub.unsubscribe()
            await js.delete_consumer("SYLTRA_DERIVED", "twin-updates-test")


async def test_redelivered_event_does_not_apply_twice(pipeline: Pipeline) -> None:
    # Safety invariant 10, proven through the real persistence path: the second
    # apply must be rejected by the unique constraint on event_id.
    _, service, _, _ = pipeline
    envelope = make_envelope(home_id=HOME, device_id="dev_dupe", value=22.2)

    assert await service.apply_envelope(envelope) is True
    assert await service.apply_envelope(envelope) is False
    assert await service.apply_envelope(envelope) is False

    home = service.twin.home(HOME)
    assert home is not None
    assert home.events_applied == 1


async def test_out_of_order_delivery_keeps_newest_value(pipeline: Pipeline) -> None:
    from datetime import timedelta

    from syltra_testing import BASE_TIME

    _, service, _, _ = pipeline
    newer = make_envelope(home_id=HOME, device_id="dev_order", value=28.0, occurred_at=BASE_TIME)
    older = make_envelope(
        home_id=HOME,
        device_id="dev_order",
        value=20.0,
        occurred_at=BASE_TIME - timedelta(minutes=15),
    )
    await service.apply_envelope(newer)
    await service.apply_envelope(older)

    device = service.twin.device(HOME, "dev_order")
    assert device is not None
    assert device.capability("environment.temperature").value == 28.0


async def test_unknown_capability_reports_unknown_not_false(pipeline: Pipeline) -> None:
    run, service, subscription, _ = pipeline
    await run.ha.set_state("sensor.living_room_temperature", "25.0")
    await asyncio.sleep(0.4)
    await drain_into_twin(subscription, service)

    device = service.twin.device(HOME, "sim_climate_sensor_living")
    assert device is not None
    gas = device.capability("safety.gas_alarm")
    assert gas.observed is False
    assert gas.value is None
    assert gas.status_at(datetime.now(tz=UTC)) is StateStatus.UNKNOWN


async def test_device_offline_is_reflected_in_availability(pipeline: Pipeline) -> None:
    run, service, subscription, _ = pipeline
    await run.ha.set_state("sensor.living_room_temperature", "unavailable")
    await asyncio.sleep(0.4)
    await drain_into_twin(subscription, service)

    device = service.twin.device(HOME, "sim_climate_sensor_living")
    assert device is not None
    assert device.available is False


async def test_twin_restores_after_restart(
    pipeline: Pipeline, db_sessions: async_sessionmaker[AsyncSession]
) -> None:
    run, service, subscription, js = pipeline
    for value in ("24.0", "24.5", "25.0"):
        await run.ha.set_state("sensor.living_room_temperature", value)
    await asyncio.sleep(0.5)
    await drain_into_twin(subscription, service)
    before = service.twin.snapshot(HOME, datetime.now(tz=UTC)).fingerprint()

    # A fresh instance sharing the database recovers the twin from stored
    # history alone — no event-bus replay required (spec §14.2: survives restart).
    restarted = DigitalTwinService(db_sessions, EventPublisher(js, service="digital-twin"))
    await restarted.restore(HOME)
    assert restarted.twin.snapshot(HOME, datetime.now(tz=UTC)).fingerprint() == before


async def test_full_scenario_reaches_the_twin(pipeline: Pipeline) -> None:
    from syltra_simulator.scenarios import SCENARIOS

    run, service, subscription, _ = pipeline
    await run.run_scenario(SCENARIOS["normal_day"])
    await asyncio.sleep(0.5)
    assert await drain_into_twin(subscription, service) > 0

    snapshot = service.twin.snapshot(HOME, datetime.now(tz=UTC))
    assert len(snapshot.devices) >= 4
    assert any(
        "environment.temperature" in device["capabilities"] for device in snapshot.devices.values()
    )


async def test_invalid_payload_at_twin_boundary_goes_to_dead_letter(pipeline: Pipeline) -> None:
    _, service, _, js = pipeline
    before = (await js.stream_info("SYLTRA_DEADLETTER")).state.messages

    # A message carrying malformed JSON, as a broker could deliver after a
    # producer bug — the twin must dead-letter it, not crash the consumer.
    message = cast(
        Msg,
        SimpleNamespace(
            subject="syltra.normalized.home.home_pipeline.device.broken",
            data=b"{not json",
            ack=_noop_ack,
        ),
    )
    await service.handle_message(message)

    after = (await js.stream_info("SYLTRA_DEADLETTER")).state.messages
    assert after == before + 1


async def test_homes_stay_isolated_through_the_pipeline(pipeline: Pipeline) -> None:
    _, service, _, _ = pipeline
    await service.apply_envelope(make_envelope(home_id="home_x", device_id="dev_x", value=19.0))
    await service.apply_envelope(make_envelope(home_id="home_y", device_id="dev_y", value=31.0))
    assert service.twin.device("home_x", "dev_y") is None
    assert service.twin.device("home_y", "dev_x") is None
