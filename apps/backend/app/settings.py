"""Application settings loaded from environment variables."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    supabase_url: str
    supabase_service_role_key: str
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    openai_api_key: str
    anthropic_api_key: str
    ollama_base_url: str = "http://localhost:11434"
    redis_url: str = "redis://localhost:6379/0"
    gcs_bucket_docs: str
    gcs_bucket_exports: str
    secret_key: str
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "http://localhost:3001"


settings = Settings()
