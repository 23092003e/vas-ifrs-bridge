"""FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI
from app.api.v1.router import router
from app.core.auth import AuthMiddleware
from app.core.tenant import TenantResolverMiddleware
from app.core.tracing import TracingMiddleware
from app.core.audit import AuditMiddleware
from app.core.usage_limiter import UsageLimiterMiddleware
from app.core.rbac import RBACMiddleware

app = FastAPI(title="VAS-IFRS Knowledge Engine", version="0.1.0")

app.add_middleware(AuditMiddleware)
app.add_middleware(UsageLimiterMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(TenantResolverMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(TracingMiddleware)

app.include_router(router, prefix="/v1")


@app.get("/healthz")
async def health() -> dict:
    return {"status": "ok"}
