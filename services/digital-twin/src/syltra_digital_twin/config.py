"""Digital Twin configuration — secrets via environment only (spec §25.3)."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TwinSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    nats_url: str = "nats://localhost:4222"
    nats_user: str = "syltra"
    nats_password: SecretStr = SecretStr("")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "syltra"
    postgres_user: str = "syltra"
    postgres_password: SecretStr = SecretStr("")

    syltra_home_id: str = "home_dev_001"
    syltra_hub_id: str = "hub_dev_001"
    syltra_log_level: str = "INFO"

    digital_twin_port: int = 8082
    consumer_durable_name: str = "digital-twin"

    @property
    def database_url(self) -> str:
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
