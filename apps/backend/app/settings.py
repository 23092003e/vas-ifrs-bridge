"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://vasifrs:vasifrs@localhost:5432/vasifrs"
    supabase_url: str = "https://placeholder.supabase.co"
    supabase_service_role_key: str = "placeholder"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    gemini_api_key: str = "placeholder"
    openai_api_key: str = "sk-placeholder"  # optional, not required for Phase 1
    anthropic_api_key: str = "sk-ant-placeholder"  # optional, not required for Phase 1
    ollama_base_url: str = "http://localhost:11434"
    tei_url: str = "http://localhost:8080"
    redis_url: str = "redis://localhost:6379/0"
    gcs_bucket_docs: str = "vifb-docs-dev"
    gcs_bucket_exports: str = "vifb-exports-dev"
    secret_key: str = "dev-secret-key-change-in-production-32c"
    dev_auth_bypass: bool = False  # NEVER true in production
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "http://localhost:3001"


settings = Settings()
