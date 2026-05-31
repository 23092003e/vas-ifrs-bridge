"""Tenant context resolution from JWT claims."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


logger = logging.getLogger(__name__)

BYPASS_PATHS = {"/healthz", "/readyz", "/metrics", "/openapi.json", "/docs", "/redoc"}


class TenantCtx(BaseModel):
    """Immutable tenant context attached to each request."""

    id: str
    name: str
    plan: str
    qdrant_collection: str
    storage_prefix: str


class TenantResolverMiddleware(BaseHTTPMiddleware):
    """Resolves tenant from JWT claim; validates against X-Tenant-Id header."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.url.path in BYPASS_PATHS:
            return await call_next(request)

        user: dict = getattr(request.state, "user", {})
        jwt_tenant_id: str = (
            user.get("app_metadata", {}).get("tenant_id")
            or user.get("user_metadata", {}).get("tenant_id")
            or ""
        )

        header_tenant_id = request.headers.get("X-Tenant-Id", "")
        if header_tenant_id and header_tenant_id != jwt_tenant_id:
            logger.warning("Tenant mismatch: header=%s jwt=%s", header_tenant_id, jwt_tenant_id)
            return JSONResponse({"detail": "Tenant mismatch"}, status_code=403)

        tenant_id = jwt_tenant_id or header_tenant_id
        if not tenant_id:
            # Public endpoints (shared KB) allowed without tenant
            request.state.tenant = None
            return await call_next(request)

        # Ensure tenant exists in database
        try:
            from app.db.models import Tenant
            from sqlalchemy import select
            
            db = getattr(request.state, "db", None)
            if db:
                result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
                db_tenant = result.scalar_one_or_none()
                if not db_tenant:
                    workspace_name = (
                        user.get("user_metadata", {}).get("workspace")
                        or user.get("app_metadata", {}).get("tenant_name")
                        or "Default Workspace"
                    )
                    plan_name = user.get("app_metadata", {}).get("plan", "free")
                    db_tenant = Tenant(id=tenant_id, name=workspace_name, plan=plan_name)
                    db.add(db_tenant)
                    await db.commit()
        except Exception as exc:
            logger.warning("Failed to auto-register tenant: %s", exc)

        request.state.tenant = TenantCtx(
            id=tenant_id,
            name=user.get("app_metadata", {}).get("tenant_name", "") or user.get("user_metadata", {}).get("workspace", "Default Workspace"),
            plan=user.get("app_metadata", {}).get("plan", "free"),
            qdrant_collection=f"tenant_{tenant_id}",
            storage_prefix=f"tenants/{tenant_id}",
        )
        return await call_next(request)

