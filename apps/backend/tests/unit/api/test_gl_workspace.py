"""GL resources require a trusted tenant claim, even with a valid role."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core import auth
from app.main import app

ID = str(uuid4())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/v1/adjustments/", {}),
        ("POST", f"/v1/adjustments/{ID}/approve", {}),
        ("POST", "/v1/gl/upload", {"files": {"file": ("ledger.csv", "ignored")}}),
        ("GET", f"/v1/gl/{ID}/status", {}),
        ("GET", "/v1/mappings/", {}),
        ("PUT", "/v1/mappings/1111", {"json": {"ifrs_code": "CASH"}}),
        ("POST", "/v1/reports/generate", {"json": {"id": ID, "upload_id": ID, "period": "FY26"}}),
        ("GET", f"/v1/reports/{ID}/download", {}),
    ],
)
async def test_gl_routes_require_workspace(monkeypatch, method, path, body):
    async def token_without_tenant(_token):
        return {"sub": ID, "app_metadata": {"role": "accountant"}}

    monkeypatch.setattr(auth, "_DEV_BYPASS", False)
    monkeypatch.setattr(auth, "verify_jwt", token_without_tenant)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        result = await client.request(method, path, headers={"Authorization": "Bearer test"}, **body)

    assert result.status_code == 403
    assert result.json() == {"detail": "Tenant access required"}
