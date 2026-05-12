"""Role-based access control definitions and middleware."""
from __future__ import annotations

from enum import Enum

from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class RBACMiddleware(BaseHTTPMiddleware):
    """Enforces route-level role requirements declared via require()."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # TODO: enforce RBAC rules
        return await call_next(request)


def require(role: Role):
    """FastAPI dependency that enforces a minimum role level."""

    async def _check(request: Request) -> None:
        # TODO: compare request.state.user.role against role
        pass

    return _check
