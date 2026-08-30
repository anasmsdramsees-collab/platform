"""Configuration. Secrets arrive from the environment and never from the code."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    # The SYLTRA hub. SELLA reaches the house through the platform API rather
    # than through Home Assistant, so every command passes the policy chain and
    # the safety governor before it reaches a device.
    syltra_base_url: str = "http://localhost:8088"
    syltra_token: str = ""
    syltra_home_id: str = "home_dev_001"

    llm_provider: str = "mock"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    database_url: str = "postgresql://sella:sella@localhost:5432/sella"
    redis_url: str = "redis://localhost:6379/0"

    # Everything off by default. A provider without a key runs as a mock, and a
    # high risk tool stays defined but unreachable until the approval system in
    # phase six exists.
    mock_providers: bool = True
    enable_high_risk_tools: bool = False
    store_raw_audio: bool = False

    max_tool_calls_per_turn: int = Field(default=8, ge=1, le=32)
    tool_timeout_seconds: float = Field(default=10.0, gt=0)

    @property
    def secrets(self) -> list[str]:
        """Values the logger must never print."""
        return [v for v in (self.syltra_token, self.anthropic_api_key) if v]


@lru_cache
def get_settings() -> Settings:
    return Settings()
