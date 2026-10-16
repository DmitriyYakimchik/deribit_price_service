from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Ticker = Literal["btc_usd", "eth_usd"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Deribit Price Service"
    app_env: str = "local"
    log_level: str = "INFO"

    postgres_scheme: str = "postgresql+asyncpg"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "crypto_prices"
    postgres_user: str = "crypto"
    postgres_password: str = "crypto"

    redis_scheme: str = "redis"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    rabbitmq_scheme: str = "amqp"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_default_user: str = "crypto"
    rabbitmq_default_pass: str = "crypto"

    deribit_base_url: str = "https://www.deribit.com/api/v2"
    deribit_timeout_seconds: float = Field(default=10.0, gt=0)
    price_collection_interval_seconds: int = Field(default=60, ge=10)
    collection_retry_attempts: int = Field(default=3, ge=0, le=10)
    collection_retry_delay_seconds: float = Field(default=2.0, ge=0)
    supported_tickers: tuple[Ticker, ...] = ("btc_usd", "eth_usd")

    @property
    def database_url(self) -> str:
        return (
            f"{self.postgres_scheme}://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"{self.redis_scheme}://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"{self.rabbitmq_scheme}://{self.rabbitmq_default_user}:{self.rabbitmq_default_pass}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}//"
        )

    @field_validator("deribit_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
