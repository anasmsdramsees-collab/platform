"""Digital Twin entrypoint: database, JetStream consumer, API server."""

import asyncio
import contextlib
import logging
import signal

import nats
import uvicorn
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from syltra_digital_twin.api import create_app
from syltra_digital_twin.config import TwinSettings
from syltra_digital_twin.service import DigitalTwinService
from syltra_eventing import EventPublisher, ensure_streams
from syltra_observability import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = TwinSettings()
    configure_logging(
        service="digital-twin",
        instance_id=settings.syltra_hub_id,
        level=settings.syltra_log_level,
        secrets=[
            settings.postgres_password.get_secret_value(),
            settings.nats_password.get_secret_value(),
        ],
    )

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    nc = await nats.connect(
        settings.nats_url,
        user=settings.nats_user or None,
        password=settings.nats_password.get_secret_value() or None,
        max_reconnect_attempts=-1,
    )
    js = nc.jetstream()
    await ensure_streams(js)
    publisher = EventPublisher(js, service="digital-twin")

    service = DigitalTwinService(session_factory, publisher, hub_id=settings.syltra_hub_id)
    await service.restore(settings.syltra_home_id)

    server = uvicorn.Server(
        uvicorn.Config(
            create_app(service),
            host="0.0.0.0",  # noqa: S104  # nosec B104 - container-internal port
            port=settings.digital_twin_port,
            log_level="warning",
        )
    )
    api_task = asyncio.create_task(server.serve())

    subscription = await js.subscribe(
        "syltra.normalized.>",
        durable=settings.consumer_durable_name,
        manual_ack=True,
        config=ConsumerConfig(
            durable_name=settings.consumer_durable_name,
            deliver_policy=DeliverPolicy.ALL,
            ack_policy=AckPolicy.EXPLICIT,
            max_deliver=5,
        ),
    )
    service.mark_ready(True)
    logger.info("digital twin consuming syltra.normalized.>")

    stopping = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stopping.set)

    try:
        while not stopping.is_set():
            try:
                message = await subscription.next_msg(timeout=1)
            except TimeoutError:
                continue
            except Exception:
                logger.exception("consumer error; continuing")
                continue
            await service.handle_message(message)
    finally:
        service.mark_ready(False)
        server.should_exit = True
        await api_task
        await subscription.unsubscribe()
        await nc.drain()
        await engine.dispose()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
