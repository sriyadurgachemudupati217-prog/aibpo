"""Centralized application settings, loaded from environment variables."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    environment: Literal["development", "staging", "production"] = "development"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    password_reset_token_expire_minutes: int = 30
    frontend_base_url: str = "http://localhost:5173"

    # Database
    database_url: str

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # LLM (provider-agnostic — see app/nlp/llm_client.py)
    llm_provider: Literal["openai", "gemini"] = "openai"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None

    # Storage
    upload_storage_path: str = "/app/storage/uploads"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — env is only parsed once per process."""
    return Settings()
