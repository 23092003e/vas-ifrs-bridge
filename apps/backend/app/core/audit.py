"""Audit logging middleware and helper function."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuditMiddleware(BaseHTTPMiddleware):
    """Records every mutating request to the audit_logs table."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        # TODO: persist audit record after response
        return response


async def log_audit(
    tenant_id: str,
    user_id: str,
    action: str,
    resource: str,
    payload: dict | None = None,
) -> None:
    """Persist a structured audit record to the audit_logs table."""
    # TODO: insert into audit_logs via async session
