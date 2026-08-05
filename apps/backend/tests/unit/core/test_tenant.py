from __future__ import annotations

import json
from typing import Any

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.tenant import TenantResolverMiddleware


async def _unused_app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    raise AssertionError("ASGI app should not be called directly in middleware unit tests")


def _request(path: str = "/v1/chat", *, headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": raw_headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }
    )


async def _tenant_response(request: Request) -> Response:
    tenant = getattr(request.state, "tenant", None)
    return JSONResponse({"tenant_id": tenant.id if tenant else None})


@pytest.mark.asyncio
async def test_header_cannot_grant_tenant_when_trusted_claim_is_missing() -> None:
    """Allowing the header as an authority would permit cross-tenant impersonation."""
    request = _request(headers={"X-Tenant-Id": "174c7f5b-2cb9-4746-b1a7-b0c5e42591d1"})
    request.state.user = {"sub": "user-1", "app_metadata": {}}
    middleware = TenantResolverMiddleware(_unused_app)

    response = await middleware.dispatch(request, _tenant_response)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_editable_metadata_cannot_select_tenant() -> None:
    """Reading tenant_id from user_metadata would let users choose another tenant."""
    request = _request()
    request.state.user = {
        "sub": "user-1",
        "app_metadata": {},
        "user_metadata": {"tenant_id": "174c7f5b-2cb9-4746-b1a7-b0c5e42591d1"},
    }
    middleware = TenantResolverMiddleware(_unused_app)

    response = await middleware.dispatch(request, _tenant_response)

    assert response.status_code == 200
    assert json.loads(response.body) == {"tenant_id": None}


@pytest.mark.asyncio
async def test_invalid_trusted_tenant_id_is_rejected_before_storage_use() -> None:
    """Removing UUID validation would permit unsafe collection and storage prefixes."""
    request = _request()
    request.state.user = {"sub": "user-1", "app_metadata": {"tenant_id": "../../other"}}
    middleware = TenantResolverMiddleware(_unused_app)

    response = await middleware.dispatch(request, _tenant_response)

    assert response.status_code == 403


class _FailingDb:
    def __init__(self) -> None:
        self.rolled_back = False

    async def execute(self, statement: Any) -> Any:
        raise RuntimeError("database unavailable")

    async def rollback(self) -> None:
        self.rolled_back = True


@pytest.mark.asyncio
async def test_tenant_lookup_failure_rolls_back_and_stops_request() -> None:
    """Swallowing DB errors leaves the shared request session unusable downstream."""
    request = _request()
    request.state.user = {
        "sub": "user-1",
        "app_metadata": {"tenant_id": "174c7f5b-2cb9-4746-b1a7-b0c5e42591d1"},
    }
    db = _FailingDb()
    request.state.db = db
    middleware = TenantResolverMiddleware(_unused_app)

    response = await middleware.dispatch(request, _tenant_response)

    assert response.status_code == 503
    assert db.rolled_back is True
