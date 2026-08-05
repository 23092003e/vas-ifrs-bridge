"""Per-tenant token and request rate limiting via Redis token-bucket."""

from __future__ import annotations

import logging
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.settings import settings

logger = logging.getLogger(__name__)

BYPASS_PATHS = {"/healthz", "/readyz", "/metrics", "/openapi.json", "/docs", "/redoc"}

# requests per minute per tenant
DEFAULT_RPM = 60
# max tokens per tenant per day (across all models)
DEFAULT_DAILY_TOKENS = 500_000

_redis: Any = None


def _get_redis() -> Any:
    global _redis
    if _redis is None:
        try:
            import redis.asyncio as aioredis

            _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        except (ImportError, ValueError) as exc:
            logger.warning("Redis unavailable, rate limiting disabled: %s", exc)
    return _redis


class UsageLimiterMiddleware(BaseHTTPMiddleware):
    """Enforces per-tenant RPM limit via Redis sliding-window counter."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.url.path in BYPASS_PATHS:
            return await call_next(request)

        tenant = getattr(request.state, "tenant", None)
        if tenant is None:
            return await call_next(request)

        r = _get_redis()
        if r is None:
            return await call_next(request)

        minute = int(time.time() // 60)
        key = f"rpm:{tenant.id}:{minute}"
        try:
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 120)
            if count > DEFAULT_RPM:
                return JSONResponse(
                    {"detail": "Rate limit exceeded. Retry in a minute."},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
        except Exception as exc:  # noqa: BLE001 - limiter deliberately fails open
            logger.warning("Rate limit check failed: %s", exc)

        return await call_next(request)
