"""Application settings loaded from environment variables."""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    database_url: str = "postgresql+asyncpg://vasifrs:vasifrs@localhost:5432/vasifrs"
    supabase_url: str = "https://placeholder.supabase.co"
    supabase_service_role_key: str = "placeholder"
    supabase_jwt_secret: str = ""  # legacy HS256 projects only
    supabase_jwt_audience: str = "authenticated"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    gemini_api_key: str = "placeholder"
    openai_api_key: str = "sk-placeholder"  # optional, not required for Phase 1
    anthropic_api_key: str = "sk-ant-placeholder"  # optional, not required for Phase 1
    ollama_base_url: str = "http://localhost:11434"
    tei_url: str = "http://localhost:8080"
    compare_mode: Literal["generated", "evidence"] = "generated"
    redis_url: str = "redis://localhost:6379/0"
    gcs_bucket_docs: str = "vifb-docs-dev"
    gcs_bucket_exports: str = "vifb-exports-dev"
    secret_key: str = "dev-secret-key-change-in-production-32c"
    dev_auth_bypass: bool = False  # NEVER true in production
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_host: str = "http://localhost:3001"

    @model_validator(mode="after")
    def validate_production_security(self) -> Settings:
        if self.app_env != "production":
            return self
        if self.dev_auth_bypass:
            raise ValueError("DEV_AUTH_BYPASS must be false in production")

        insecure_fields = []
        if self.database_url == "postgresql+asyncpg://vasifrs:vasifrs@localhost:5432/vasifrs":
            insecure_fields.append("DATABASE_URL")
        if self.supabase_url == "https://placeholder.supabase.co":
            insecure_fields.append("SUPABASE_URL")
        if self.supabase_service_role_key == "placeholder":
            insecure_fields.append("SUPABASE_SERVICE_ROLE_KEY")
        if self.qdrant_url == "http://localhost:6333":
            insecure_fields.append("QDRANT_URL")
        if self.secret_key == "dev-secret-key-change-in-production-32c":
            insecure_fields.append("SECRET_KEY")
        if insecure_fields:
            raise ValueError(
                "Production configuration contains insecure defaults: "
                + ", ".join(insecure_fields)
            )
        return self


settings = Settings()
