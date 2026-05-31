"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router
from app.core.auth import AuthMiddleware
from app.core.tenant import TenantResolverMiddleware
from app.core.tracing import TracingMiddleware
from app.core.audit import AuditMiddleware
from app.core.usage_limiter import UsageLimiterMiddleware
from app.core.rbac import RBACMiddleware

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Any
from app.db.session import AsyncSessionLocal

app = FastAPI(title="VAS-IFRS Knowledge Engine", version="0.1.0")

class DbSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        async with AsyncSessionLocal() as session:
            request.state.db = session
            return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)
app.add_middleware(UsageLimiterMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(TenantResolverMiddleware)
app.add_middleware(DbSessionMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(TracingMiddleware)

app.include_router(router, prefix="/v1")


@app.get("/healthz")
async def health() -> dict:
    return {"status": "ok"}

