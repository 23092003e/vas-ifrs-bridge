"""Per-tenant token and request rate limiting middleware."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class UsageLimiterMiddleware(BaseHTTPMiddleware):
    """Enforces per-tenant monthly token budgets and per-minute request limits."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # TODO: check Redis counters, raise 429 if exceeded
        return await call_next(request)
