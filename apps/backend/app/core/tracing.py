"""OpenTelemetry tracing middleware and span helpers."""

from __future__ import annotations

import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider

    _provider = TracerProvider()
    trace.set_tracer_provider(_provider)
    _tracer = trace.get_tracer("vas-ifrs")
    _otel_available = True
except Exception:
    _otel_available = False
    _tracer = None  # type: ignore[assignment]


class TracingMiddleware(BaseHTTPMiddleware):
    """Injects request_id; records OTEL span per request when available."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()

        if _otel_available and _tracer:
            with _tracer.start_as_current_span(
                f"{request.method} {request.url.path}",
                attributes={
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "request_id": request_id,
                },
            ):
                response = await call_next(request)
        else:
            response = await call_next(request)

        latency_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Latency-Ms"] = str(latency_ms)
        return response
