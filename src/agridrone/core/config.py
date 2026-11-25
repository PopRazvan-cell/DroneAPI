"""Application configuration from ``AGRIDRONE_*`` environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings.

    Values are read from the environment with the ``AGRIDRONE_`` prefix and,
    when present, from a local ``.env`` file.
    """

    model_config = SettingsConfigDict(
        env_prefix="AGRIDRONE_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    env: Literal["dev", "prod"] = "dev"
    secret_key: SecretStr = SecretStr("dev-only-change-me")
    dev_token: SecretStr = SecretStr("dev-token")
    log_level: str = "INFO"
    public_url: str = "http://localhost:8000"

    data_dir: Path = Path("./data")
    storage_dir: Path = Path("./data/store")

    photogrammetry_mode: Literal["mock", "nodeodm"] = "mock"
    nodeodm_url: str = "http://localhost:3000"

    tus_url: str = "http://localhost:8080/files/"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:5173"])

    database_url: str = "postgresql+asyncpg://agridrone:agridrone@localhost:5432/agridrone"
    redis_url: str = "redis://localhost:6379/0"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: object) -> object:
        """Accept both a comma-separated string and a real list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

    def ensure_dirs(self) -> None:
        """Create the local data/storage directories if they do not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "_uploads").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
