"""JWT / Supabase auth middleware and token validation."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates the Bearer JWT from Supabase and attaches the user to request.state."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # TODO: extract and verify JWT, populate request.state.user
        return await call_next(request)
