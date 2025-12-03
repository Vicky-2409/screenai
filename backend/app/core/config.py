"""Application settings loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # General
    project_name: str = "AI Resume Screener"
    environment: str = "development"
    debug: bool = True

    # Security / JWT
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    postgres_user: str = "ats"
    postgres_password: str = "ats_password"
    postgres_db: str = "ats"
    postgres_host: str = "db"
    postgres_port: int = 5432
    database_url: str | None = None

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # AI provider
    ai_provider: str = "auto"  # auto | openai | local
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    embedding_dim: int = 384
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Files
    upload_dir: str = "/data/uploads"
    max_upload_size_mb: int = 20

    # Rate limiting
    rate_limit_per_minute: int = 120

    @field_validator("database_url", mode="before")
    @classmethod
    def _empty_to_none(cls, v: str | None) -> str | None:
        return v or None

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

    @property
    def resolved_ai_provider(self) -> str:
        """Resolve 'auto' to a concrete provider based on key availability."""
        if self.ai_provider == "auto":
            return "openai" if self.openai_api_key else "local"
        return self.ai_provider

    @property
    def active_embedding_dim(self) -> int:
        """Embedding dimension for the active provider."""
        if self.resolved_ai_provider == "openai":
            # text-embedding-3-small default dimension
            return 1536 if self.openai_embedding_model == "text-embedding-3-small" else self.embedding_dim
        return 384  # all-MiniLM-L6-v2


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
