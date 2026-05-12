"""Structlog configuration for JSON structured logging."""
from __future__ import annotations

import structlog


def configure_logging() -> None:
    """Configure structlog with JSON renderer for production."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]
    )


logger = structlog.get_logger()
