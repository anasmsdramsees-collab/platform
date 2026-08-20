"""Edge Agent entrypoint: logging, NATS, streams, health server, service loop."""

import asyncio
import contextlib
import logging
import signal

import nats
import uvicorn

from syltra_edge_agent.config import EdgeAgentSettings
from syltra_edge_agent.ha_client import HomeAssistantWebSocketClient
from syltra_edge_agent.health import create_health_app
from syltra_edge_agent.service import EdgeAgentService
from syltra_eventing import EventPublisher, ensure_streams
from syltra_observability import configure_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = EdgeAgentSettings()
    configure_logging(
        service="edge-agent",
        instance_id=settings.syltra_hub_id,
        level=settings.syltra_log_level,
        secrets=[
            settings.home_assistant_token.get_secret_value(),
            settings.nats_password.get_secret_value(),
        ],
    )

    nc = await nats.connect(
        settings.nats_url,
        user=settings.nats_user or None,
        password=settings.nats_password.get_secret_value() or None,
        max_reconnect_attempts=-1,
    )
    js = nc.jetstream()
    await ensure_streams(js)
    logger.info("connected to NATS; streams ensured")

    client = HomeAssistantWebSocketClient(settings.websocket_url, settings.home_assistant_token)
    publisher = EventPublisher(js, service="edge-agent")
    service = EdgeAgentService(settings, client, publisher)

    def _ready() -> bool:
        return service.connected and nc.is_connected

    server = uvicorn.Server(
        uvicorn.Config(
            create_health_app(_ready),
            host="0.0.0.0",  # noqa: S104  # nosec B104 - container-internal health port
            port=settings.edge_agent_health_port,
            log_level="warning",
        )
    )

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, service.stop)

    health_task = asyncio.create_task(server.serve())
    try:
        await service.run()
    finally:
        server.should_exit = True
        await health_task
        await nc.drain()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
