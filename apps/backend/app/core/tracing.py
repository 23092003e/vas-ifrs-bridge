"""OpenTelemetry tracing middleware and span helpers."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TracingMiddleware(BaseHTTPMiddleware):
    """Injects OTEL trace context and records span per request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # TODO: start span, propagate context, record attributes
        return await call_next(request)
