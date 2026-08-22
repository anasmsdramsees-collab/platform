"""Edge Agent configuration — secrets arrive via environment only (spec §25.3)."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class EdgeAgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    home_assistant_url: str = "http://localhost:8123"
    home_assistant_token: SecretStr = SecretStr("")

    nats_url: str = "nats://localhost:4222"
    nats_user: str = "syltra"
    nats_password: SecretStr = SecretStr("")

    syltra_home_id: str = "home_dev_001"
    syltra_hub_id: str = "hub_dev_001"
    syltra_environment: str = "development"
    syltra_log_level: str = "INFO"

    edge_agent_health_port: int = 8081

    reconnect_initial_seconds: float = 1.0
    reconnect_max_seconds: float = 60.0

    @property
    def websocket_url(self) -> str:
        base = self.home_assistant_url.rstrip("/")
        if base.startswith("https://"):
            return "wss://" + base.removeprefix("https://") + "/api/websocket"
        return "ws://" + base.removeprefix("http://") + "/api/websocket"
