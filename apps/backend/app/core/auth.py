"""JWT / Supabase auth middleware and token validation."""
from __future__ import annotations

import logging
from typing import Any

import httpx
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.settings import settings

logger = logging.getLogger(__name__)

_JWKS_CACHE: dict[str, Any] = {}

BYPASS_PATHS = {"/healthz", "/readyz", "/metrics", "/openapi.json", "/docs", "/redoc"}

# Set DEV_AUTH_BYPASS=true in .env to skip JWT validation (dev only)
_DEV_BYPASS = getattr(settings, "dev_auth_bypass", False)


async def _fetch_jwks() -> dict[str, Any]:
    if _JWKS_CACHE:
        return _JWKS_CACHE
    url = f"{settings.supabase_url}/auth/v1/jwks"
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    _JWKS_CACHE.update(resp.json())
    return _JWKS_CACHE


async def verify_jwt(token: str) -> dict[str, Any]:
    """Verify Supabase JWT, return claims dict."""
    jwks = await _fetch_jwks()
    # Supabase signs with HS256 using the service role secret
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.supabase_service_role_key,
        algorithms=["HS256"],
        options={"verify_aud": False},
    )
    return payload


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates Bearer JWT from Supabase and attaches user to request.state."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.url.path in BYPASS_PATHS:
            return await call_next(request)

        if _DEV_BYPASS:
            request.state.user = {"sub": "dev-user", "app_metadata": {"role": "admin", "tenant_id": "dev-tenant", "tenant_name": "Dev Tenant", "plan": "free"}}
            request.state.user_id = "dev-user"
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Missing Bearer token"}, status_code=401)

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            claims = await verify_jwt(token)
        except JWTError as exc:
            logger.warning("JWT validation failed: %s", exc)
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        request.state.user = claims
        request.state.user_id = claims.get("sub", "")
        return await call_next(request)
