from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app import main
from app.core import auth


class _Db:
    async def execute(self, statement: Any) -> None:
        return None


class _FailingDb:
    async def execute(self, statement: Any) -> None:
        raise RuntimeError("database unavailable")


@pytest.mark.asyncio
async def test_readiness_checks_database() -> None:
    assert hasattr(main, "readiness")

    assert await main.readiness(SimpleNamespace(state=SimpleNamespace(db=_Db()))) == {
        "status": "ready"
    }

    with pytest.raises(HTTPException) as exc_info:
        await main.readiness(SimpleNamespace(state=SimpleNamespace(db=_FailingDb())))

    assert exc_info.value.status_code == 503


def test_metrics_endpoint_exposes_prometheus_payload() -> None:
    assert hasattr(main, "metrics")

    response = main.metrics()

    assert response.media_type == "text/plain"
    assert b"vasifrs_requests_total" in response.body


@pytest.mark.asyncio
@pytest.mark.parametrize("allowed", [True, False])
async def test_cors_checks_preflight_before_auth(monkeypatch: pytest.MonkeyPatch, allowed: bool) -> None:
    monkeypatch.setattr(auth, "_DEV_BYPASS", False)
    origin = main.settings.cors_origins[0] if allowed else "https://unlisted.example"
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        response = await client.options("/v1/chat/stream", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type, x-tenant-id",
        })

    assert response.status_code == (200 if allowed else 400)
    assert response.headers.get("access-control-allow-origin") == (origin if allowed else None)
    if allowed:
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "authorization" in response.headers["access-control-allow-headers"]


@pytest.mark.asyncio
async def test_auth_error_has_cors_headers_for_allowed_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "_DEV_BYPASS", False)
    origin = main.settings.cors_origins[0]
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        response = await client.get("/v1/chat/conversations", headers={"Origin": origin})

    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == origin
