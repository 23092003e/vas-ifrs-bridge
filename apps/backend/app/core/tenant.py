"""Tenant context resolution from JWT claims."""

from __future__ import annotations

import logging
import uuid
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
        app_metadata = user.get("app_metadata", {})
        jwt_tenant_id: str = app_metadata.get("tenant_id") or ""

        header_tenant_id = request.headers.get("X-Tenant-Id", "")
        if header_tenant_id and not jwt_tenant_id:
            logger.warning("Tenant header supplied without a trusted tenant claim")
            return JSONResponse({"detail": "Tenant mismatch"}, status_code=403)

        if not jwt_tenant_id:
            # Public endpoints (shared KB) allowed without tenant.
            request.state.tenant = None
            return await call_next(request)

        try:
            tenant_id = str(uuid.UUID(jwt_tenant_id))
        except (ValueError, TypeError, AttributeError):
            logger.warning("Invalid tenant ID in trusted claims")
            return JSONResponse({"detail": "Invalid tenant"}, status_code=403)

        if header_tenant_id:
            try:
                header_tenant_id = str(uuid.UUID(header_tenant_id))
            except (ValueError, TypeError, AttributeError):
                return JSONResponse({"detail": "Invalid tenant"}, status_code=403)

        if header_tenant_id and header_tenant_id != tenant_id:
            logger.warning("Tenant mismatch: header=%s jwt=%s", header_tenant_id, jwt_tenant_id)
            return JSONResponse({"detail": "Tenant mismatch"}, status_code=403)

        # Ensure tenant exists in database
        tenant_name = app_metadata.get("tenant_name") or "Default Workspace"
        tenant_plan = app_metadata.get("plan") or "free"
        try:
            from sqlalchemy import select

            from app.db.models import Tenant

            db = getattr(request.state, "db", None)
            if db:
                result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
                db_tenant = result.scalar_one_or_none()
                if not db_tenant:
                    db_tenant = Tenant(id=tenant_id, name=tenant_name, plan=tenant_plan)
                    db.add(db_tenant)
                    await db.commit()
                tenant_name = db_tenant.name
                tenant_plan = db_tenant.plan
        except Exception as exc:  # noqa: BLE001 - database boundary returns a safe 503
            logger.warning("Failed to auto-register tenant: %s", exc)
            if db := getattr(request.state, "db", None):
                try:
                    await db.rollback()
                except Exception as rollback_exc:  # noqa: BLE001 - preserve original DB failure
                    logger.error("Failed to roll back tenant transaction: %s", rollback_exc)
            return JSONResponse({"detail": "Tenant service unavailable"}, status_code=503)

        request.state.tenant = TenantCtx(
            id=tenant_id,
            name=tenant_name,
            plan=tenant_plan,
            qdrant_collection=f"tenant_{tenant_id}",
            storage_prefix=f"tenants/{tenant_id}",
        )
        return await call_next(request)
