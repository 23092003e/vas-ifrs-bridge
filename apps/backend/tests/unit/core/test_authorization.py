from __future__ import annotations

from typing import Any

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.rbac import RBACMiddleware


async def _unused_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    raise AssertionError("ASGI app should not be called directly in middleware unit tests")


def _request(
    path: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
) -> Request:
    raw_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": raw_headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }
    )


@pytest.mark.asyncio
async def test_rbac_rejects_admin_role_from_user_editable_metadata() -> None:
    """Removing the app_metadata-only check must expose this privilege escalation."""
    request = _request("/v1/admin")
    request.state.user = {"sub": "user-1", "user_metadata": {"role": "admin"}}
    middleware = RBACMiddleware(_unused_app)

    async def allowed(_: Request) -> Response:
        return JSONResponse({"ok": True})

    response = await middleware.dispatch(request, allowed)

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/v1/gl/upload"),
        ("POST", "/v1/adjustments/ADJ-001/approve"),
        ("PUT", "/v1/mappings/rule-1"),
        ("POST", "/v1/documents/upload"),
    ],
)
async def test_viewer_cannot_call_accounting_mutations(method: str, path: str) -> None:
    request = _request(path, method=method)
    request.state.user = {"sub": "user-1", "app_metadata": {"role": "viewer"}}
    middleware = RBACMiddleware(_unused_app)

    async def allowed(_: Request) -> Response:
        return JSONResponse({"ok": True})

    response = await middleware.dispatch(request, allowed)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_viewer_can_list_documents() -> None:
    request = _request("/v1/documents", method="GET")
    request.state.user = {"sub": "user-1", "app_metadata": {"role": "viewer"}}
    middleware = RBACMiddleware(_unused_app)

    async def allowed(_: Request) -> Response:
        return JSONResponse({"ok": True})

    response = await middleware.dispatch(request, allowed)

    assert response.status_code == 200
