"""Adaptive Engine entrypoint: consumer, periodic training, API server."""

import asyncio
import contextlib
import logging
import signal
from datetime import UTC, datetime, timedelta

import nats
import uvicorn
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from syltra_adaptive_engine.api import create_app
from syltra_adaptive_engine.service import AdaptiveEngineService
from syltra_contracts import LearningMode
from syltra_eventing import EventPublisher, ensure_streams
from syltra_observability import configure_logging

logger = logging.getLogger(__name__)


class AdaptiveSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    nats_url: str = "nats://localhost:4222"
    nats_user: str = "syltra"
    nats_password: SecretStr = SecretStr("")

    syltra_home_id: str = "home_dev_001"
    syltra_hub_id: str = "hub_dev_001"
    syltra_log_level: str = "INFO"

    adaptive_engine_port: int = 8084
    consumer_durable_name: str = "adaptive-engine"
    training_interval_minutes: int = 60
    recommendation_interval_minutes: int = 5

    default_learning_mode: str = LearningMode.SHADOW.value
    """Phase 4 ships homes in SHADOW: predictions recorded, never shown."""


async def _training_loop(
    service: AdaptiveEngineService, settings: AdaptiveSettings, stopping: asyncio.Event
) -> None:
    interval = timedelta(minutes=settings.training_interval_minutes).total_seconds()
    while not stopping.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stopping.wait(), timeout=interval)
            return
        try:
            results = service.train_home(settings.syltra_home_id)
            trained = [name for name, result in results.items() if result.trained]
            logger.info("training cycle complete; trained %s", trained or "nothing")
        except Exception:
            logger.exception("training cycle failed")


async def _recommendation_loop(
    service: AdaptiveEngineService, settings: AdaptiveSettings, stopping: asyncio.Event
) -> None:
    interval = timedelta(minutes=settings.recommendation_interval_minutes).total_seconds()
    while not stopping.is_set():
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stopping.wait(), timeout=interval)
            return
        try:
            home_id = settings.syltra_home_id
            proposals = service.build_recommendations(home_id, datetime.now(tz=UTC))
            if proposals:
                published = await service.publish_recommendations(home_id, proposals)
                logger.info(
                    "%d recommendation(s) produced, %d published live (mode=%s)",
                    len(proposals),
                    published,
                    service.mode(home_id).value,
                )
        except Exception:
            logger.exception("recommendation cycle failed")


async def main() -> None:
    settings = AdaptiveSettings()
    configure_logging(
        service="adaptive-engine",
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

    service = AdaptiveEngineService(
        EventPublisher(js, service="adaptive-engine"), hub_id=settings.syltra_hub_id
    )
    # A home enters at OBSERVE and is advanced deliberately; SHADOW is one rung
    # up, so the configured default is applied through the same guarded path.
    if settings.default_learning_mode != LearningMode.OBSERVE.value:
        service.set_mode(
            settings.syltra_home_id,
            LearningMode(settings.default_learning_mode),
            actor="startup-configuration",
        )

    server = uvicorn.Server(
        uvicorn.Config(
            create_app(service),
            host="0.0.0.0",  # noqa: S104  # nosec B104 - container-internal port
            port=settings.adaptive_engine_port,
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
    logger.info(
        "adaptive engine consuming syltra.normalized.> in %s mode",
        service.mode(settings.syltra_home_id).value,
    )

    stopping = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stopping.set)

    trainer = asyncio.create_task(_training_loop(service, settings, stopping))
    recommender = asyncio.create_task(_recommendation_loop(service, settings, stopping))
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
        for task in (trainer, recommender):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        server.should_exit = True
        await api_task
        await subscription.unsubscribe()
        await nc.drain()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
