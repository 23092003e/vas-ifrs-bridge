"""FastAPI application entry point."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.router import router
from app.core.audit import AuditMiddleware
from app.core.auth import AuthMiddleware
from app.core.rbac import RBACMiddleware
from app.core.tenant import TenantResolverMiddleware
from app.core.tracing import TracingMiddleware
from app.core.usage_limiter import UsageLimiterMiddleware
from app.db.session import AsyncSessionLocal
from app.observability.metrics import request_count
from app.settings import settings

logger = logging.getLogger(__name__)
app = FastAPI(title="VAS-IFRS Knowledge Engine", version="0.1.0")

class DbSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        async with AsyncSessionLocal() as session:
            request.state.db = session
            return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        request_count.labels(
            method=request.method,
            path=path,
            status=str(response.status_code),
        ).inc()
        return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware stack — Starlette uses LIFO: last added runs first on inbound.
# Desired inbound order: Metrics → Tracing → Auth → DbSession → Tenant → RBAC → UsageLimiter → Audit
# So we add in REVERSE order:
app.add_middleware(AuditMiddleware)            # 8th inbound (needs user/tenant set)
app.add_middleware(UsageLimiterMiddleware)     # 7th inbound
app.add_middleware(RBACMiddleware)             # 6th inbound
app.add_middleware(TenantResolverMiddleware)   # 5th inbound (needs db + user)
app.add_middleware(DbSessionMiddleware)        # 4th inbound
app.add_middleware(AuthMiddleware)             # 3rd inbound
app.add_middleware(TracingMiddleware)          # 2nd inbound (request_id)
app.add_middleware(MetricsMiddleware)          # 1st inbound, includes middleware responses

app.include_router(router, prefix="/v1")


@app.get("/healthz")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
async def readiness(request: Request) -> dict:
    """Report ready only when the request-scoped database connection works."""
    try:
        await request.state.db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Readiness database check failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type="text/plain")
