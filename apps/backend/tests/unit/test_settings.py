from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.settings import Settings


def test_production_rejects_placeholder_configuration() -> None:
    """Removing production validation must allow insecure defaults to boot."""
    with pytest.raises(ValidationError):
        Settings(app_env="production", _env_file=None)


def test_production_rejects_development_auth_bypass() -> None:
    """Allowing auth bypass in production would grant every request admin access."""
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            database_url="postgresql+asyncpg://user:pass@db:5432/vasifrs",
            supabase_url="https://project.supabase.co",
            supabase_service_role_key="configured-service-role-key",
            qdrant_url="https://qdrant.example.com",
            secret_key="configured-production-secret-key-32-chars",
            dev_auth_bypass=True,
            _env_file=None,
        )
