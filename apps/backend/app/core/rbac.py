"""Role-based access control definitions and middleware."""
from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import Depends, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.rbac_table import ROUTE_ROLE_MAP

BYPASS_PATHS = {"/healthz", "/readyz", "/metrics", "/openapi.json", "/docs", "/redoc"}

ROLE_RANK = {
    "owner": 50,
    "admin": 40,
    "accountant": 30,
    "auditor": 20,
    "viewer": 10,
}


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class RBACMiddleware(BaseHTTPMiddleware):
    """Enforces route-level role requirements declared in rbac_table.py."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.url.path in BYPASS_PATHS:
            return await call_next(request)

        required = ROUTE_ROLE_MAP.get(request.url.path)
        if required is None:
            return await call_next(request)

        user: dict = getattr(request.state, "user", {})
        user_role = (
            user.get("app_metadata", {}).get("role")
            or user.get("user_metadata", {}).get("role")
            or "viewer"
        )
        if ROLE_RANK.get(user_role, 0) < ROLE_RANK.get(required, 0):
            from starlette.responses import JSONResponse
            return JSONResponse({"detail": "Insufficient role"}, status_code=403)

        return await call_next(request)


def require(role: Role):
    """FastAPI dependency that enforces a minimum role level."""

    async def _check(request: Request) -> None:
        user: dict = getattr(request.state, "user", {})
        user_role = (
            user.get("app_metadata", {}).get("role")
            or user.get("user_metadata", {}).get("role")
            or "viewer"
        )
        if ROLE_RANK.get(user_role, 0) < ROLE_RANK[role.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role.value}' or higher required",
            )

    return _check
