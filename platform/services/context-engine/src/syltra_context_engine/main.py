"""Context Engine entrypoint: JetStream consumer, sweeper, API server."""

import asyncio
import contextlib
import logging
import signal

import nats
import uvicorn
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from syltra_context_engine.api import create_app
from syltra_context_engine.service import ContextService
from syltra_eventing import EventPublisher, ensure_streams
from syltra_observability import configure_logging

logger = logging.getLogger(__name__)


class ContextSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    nats_url: str = "nats://localhost:4222"
    nats_user: str = "syltra"
    nats_password: SecretStr = SecretStr("")

    syltra_home_id: str = "home_dev_001"
    syltra_hub_id: str = "hub_dev_001"
    syltra_log_level: str = "INFO"

    context_engine_port: int = 8083
    consumer_durable_name: str = "context-engine"


async def main() -> None:
    settings = ContextSettings()
    configure_logging(
        service="context-engine",
        instance_id=settings.syltra_hub_id,
        level=settings.syltra_log_level,
        secrets=[settings.nats_password.get_secret_value()],
    )

    nc = await nats.connect(
        settings.nats_url,
        user=settings.nats_user or None,
        password=settings.nats_password.get_secret_value() or None,
        max_reconnect_attempts=-1,
    )
    js = nc.jetstream()
    await ensure_streams(js)

    service = ContextService(
        EventPublisher(js, service="context-engine"), hub_id=settings.syltra_hub_id
    )

    server = uvicorn.Server(
        uvicorn.Config(
            create_app(service),
            host="0.0.0.0",  # noqa: S104  # nosec B104 - container-internal port
            port=settings.context_engine_port,
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
    logger.info("context engine consuming syltra.normalized.>")

    stopping = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stopping.set)

    sweeper = asyncio.create_task(service.run_sweeper(stopping))
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
        stopping.set()
        sweeper.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sweeper
        server.should_exit = True
        await api_task
        await subscription.unsubscribe()
        await nc.drain()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
