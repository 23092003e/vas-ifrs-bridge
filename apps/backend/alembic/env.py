"""Alembic environment configuration."""
from __future__ import annotations

from alembic import context
from app.settings import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_online() -> None:
    """Run migrations in online mode using async engine."""
    pass  # TODO: implement with AsyncEngine


if context.is_offline_mode():
    pass
else:
    run_migrations_online()
