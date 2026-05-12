"""Tenant context resolution from JWT claims or subdomain."""
from __future__ import annotations

from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TenantCtx(BaseModel):
    """Immutable tenant context attached to each request."""

    id: str
    name: str
    plan: str
    qdrant_collection: str


class TenantResolverMiddleware(BaseHTTPMiddleware):
    """Resolves tenant from JWT claim and attaches TenantCtx to request.state.tenant."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # TODO: resolve tenant and populate request.state.tenant
        return await call_next(request)
