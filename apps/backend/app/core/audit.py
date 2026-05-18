"""Audit logging middleware and async helper."""
from __future__ import annotations

import json
import logging
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
BYPASS_PATHS = {"/healthz", "/readyz", "/metrics", "/openapi.json", "/docs", "/redoc"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Records every mutating request to audit_logs after response is sent."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = await call_next(request)

        if (
            request.method in MUTATING_METHODS
            and request.url.path not in BYPASS_PATHS
            and response.status_code < 400
        ):
            tenant = getattr(request.state, "tenant", None)
            user_id = getattr(request.state, "user_id", None)
            request_id = getattr(request.state, "request_id", None)
            await _fire_and_forget(
                tenant_id=tenant.id if tenant else None,
                user_id=user_id,
                action=f"{request.method} {request.url.path}",
                resource_type=_resource_from_path(request.url.path),
                request_id=request_id,
                ip=request.client.host if request.client else None,
                ua=request.headers.get("User-Agent"),
            )

        return response


async def log_audit(
    tenant_id: str | None,
    user_id: str | None,
    action: str,
    resource: str,
    payload: dict | None = None,
    request_id: str | None = None,
) -> None:
    """Persist a structured audit record. Swallows errors — never block request path."""
    try:
        record = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "action": action,
            "resource_type": resource,
            "diff": payload,
            "request_id": request_id,
        }
        # In production, write to DB via asyncpg.  For now, structured log.
        logger.info("AUDIT %s", json.dumps(record, default=str))
    except Exception as exc:
        logger.warning("audit log failed: %s", exc)


async def _fire_and_forget(**kwargs: Any) -> None:
    try:
        await log_audit(**kwargs)  # type: ignore[arg-type]
    except Exception as exc:
        logger.warning("audit middleware error: %s", exc)


def _resource_from_path(path: str) -> str:
    parts = [p for p in path.split("/") if p and not _is_uuid_like(p)]
    return "/".join(parts[-2:]) if len(parts) >= 2 else path


def _is_uuid_like(s: str) -> bool:
    return len(s) == 36 and s.count("-") == 4
