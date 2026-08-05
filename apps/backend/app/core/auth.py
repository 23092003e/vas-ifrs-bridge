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


async def _fetch_jwks(*, force_refresh: bool = False) -> dict[str, Any]:
    if _JWKS_CACHE and not force_refresh:
        return _JWKS_CACHE
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    headers = {"apikey": settings.supabase_service_role_key}
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
    _JWKS_CACHE.clear()
    _JWKS_CACHE.update(resp.json())
    return _JWKS_CACHE


def _decode_token(token: str, key: Any, algorithm: str) -> dict[str, Any]:
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1"
    claims = jwt.decode(
        token,
        key,
        algorithms=[algorithm],
        audience=settings.supabase_jwt_audience,
        issuer=issuer,
        options={
            "require_aud": True,
            "require_exp": True,
            "require_iss": True,
            "require_sub": True,
        },
    )
    if not claims.get("sub"):
        raise JWTError("Token subject is required")
    return claims


def _find_jwk(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    return next((key for key in jwks.get("keys", []) if key.get("kid") == kid), None)


async def verify_jwt(token: str) -> dict[str, Any]:
    """Verify Supabase JWT, return claims dict."""
    headers = jwt.get_unverified_header(token)
    algorithm = headers.get("alg", "")

    if algorithm == "HS256":
        if not settings.supabase_jwt_secret:
            raise JWTError("HS256 token received but SUPABASE_JWT_SECRET is not configured")
        return _decode_token(token, settings.supabase_jwt_secret, algorithm)

    if algorithm not in {"RS256", "ES256"}:
        raise JWTError("Unsupported JWT algorithm")

    kid = headers.get("kid")
    if not kid:
        raise JWTError("JWT key ID is required")

    jwks = await _fetch_jwks()
    key = _find_jwk(jwks, kid)
    if key is None:
        jwks = await _fetch_jwks(force_refresh=True)
        key = _find_jwk(jwks, kid)
    if key is None:
        raise JWTError("JWT signing key not found")
    if key.get("alg") and key["alg"] != algorithm:
        raise JWTError("JWT algorithm does not match signing key")

    return _decode_token(token, key, algorithm)



class AuthMiddleware(BaseHTTPMiddleware):
    """Validates Bearer JWT from Supabase and attaches user to request.state."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.url.path in BYPASS_PATHS:
            return await call_next(request)

        if _DEV_BYPASS:
            header_tenant = request.headers.get("X-Tenant-Id", "")
            import uuid
            try:
                uuid.UUID(header_tenant)
                tenant_id = header_tenant
            except ValueError:
                tenant_id = "d3b07384-d113-4ec5-a5ae-be8e3d67a6d8"

            request.state.user = {
                "sub": "dev-user",
                "app_metadata": {
                    "role": "admin",
                    "tenant_id": tenant_id,
                    "tenant_name": "Dev Tenant",
                    "plan": "free",
                },
            }
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
