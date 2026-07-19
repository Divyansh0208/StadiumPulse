"""Centralized app config. Single source of truth for env vars — replaces scattered
os.getenv() calls. Validates types/required fields at startup instead of failing
mysteriously mid-request.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # database
    database_url: str = "postgresql://stadium:stadium@localhost:5432/stadiumpulse"

    # NVIDIA NIM (sole GenAI vendor — free tier)
    nvidia_nim_api_key: str | None = None
    nvidia_nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    nim_chat_model: str = "meta/llama-3.1-8b-instruct"
    nim_timeout_seconds: int = 20
    nim_max_retries: int = 3

    # auth
    jwt_secret: str = "dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # CORS — comma-separated in env, e.g. "http://localhost:5173,http://localhost:5174"
    cors_allowed_origins: str = "http://localhost:5173,http://localhost:5174"

    # rate limiting
    rate_limit_per_minute: int = 30

    # misc
    venue_kb_path: str = "data/venue_kb.json"
    environment: str = "development"  # development | production

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — settings are read once, not re-parsed per request."""
    return Settings()
