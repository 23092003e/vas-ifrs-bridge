"""Exercise the complete GL flow against a migrated PostgreSQL database."""

import asyncio
import csv
import os
from decimal import Decimal
from io import BytesIO, StringIO
from time import time
from uuid import uuid4

import openpyxl
import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy import select

from app.core import auth
from app.db.models import AuditLog
from app.db.session import AsyncSessionLocal, engine
from app.main import app
from app.settings import settings

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("GL_INTEGRATION_TEST") != "1", reason="Requires a migrated test DB"
    ),
]

CSV = (
    "Mã TK,Tên tài khoản,Dư đầu kỳ Nợ,Dư đầu kỳ Có,Phát sinh Nợ,Phát sinh Có,"
    "Dư cuối kỳ Nợ,Dư cuối kỳ Có\n"
    "1111,Tiền mặt,60,0,40,0,100,0\n"
    "9999,Công nợ,0,60,0,40,0,100\n"
)


@pytest.mark.asyncio
async def test_gl_workflow(monkeypatch):
    local_secret = "integration-test-signing-key-only"
    monkeypatch.setattr(settings, "supabase_jwt_secret", local_secret)
    monkeypatch.setattr(auth, "_DEV_BYPASS", False)
    tenant, other_tenant, accountant, viewer, auditor = [str(uuid4()) for _ in range(5)]

    def headers(workspace, user, role="accountant"):
        return {
            "Authorization": "Bearer "
            + jwt.encode(
                {
                    "sub": user,
                    "iss": settings.supabase_url.rstrip("/") + "/auth/v1",
                    "aud": settings.supabase_jwt_audience,
                    "exp": int(time()) + 120,
                    "app_metadata": {"tenant_id": workspace, "role": role},
                },
                local_secret,
                algorithm="HS256",
            )
        }

    own = headers(tenant, accountant)
    read_only = headers(tenant, viewer, "viewer")
    export = headers(tenant, auditor, "auditor")
    other = headers(other_tenant, str(uuid4()))
    upload_id = str(uuid4())
    key = {**own, "Idempotency-Key": upload_id}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        async def upload(payload=CSV, request_headers=key):
            return await client.post(
                "/v1/gl/upload", files={"file": ("ledger.csv", payload)}, headers=request_headers
            )

        assert (await upload(request_headers=read_only)).status_code == 403
        assert (await upload("a,b\n1,2\n")).status_code == 422
        assert (
            await client.put("/v1/mappings/1111", json={"ifrs_code": "OTHER"}, headers=other)
        ).status_code == 200
        uploaded, replay = await asyncio.gather(upload(), upload())
        assert uploaded.status_code == replay.status_code == 200, (uploaded.text, replay.text)
        assert uploaded.json() == replay.json()
        assert uploaded.json()["id"] == upload_id
        workbook = openpyxl.Workbook()
        for row in csv.reader(StringIO(CSV)):
            workbook.active.append(row)
        spreadsheet = BytesIO()
        workbook.save(spreadsheet)
        workbook.close()
        xlsx = await client.post(
            "/v1/gl/upload", files={"file": ("ledger.xlsx", spreadsheet.getvalue())}, headers=own
        )
        assert xlsx.status_code == 200, xlsx.text
        assert xlsx.json()["accounts"] == uploaded.json()["accounts"]
        assert (await upload(CSV + "\n")).status_code == 409
        value = uploaded.json()
        assert value["mapped_count"] == 1
        assert value["accounts"][0]["opening_debit"] == "60"
        assert value["accounts"][0]["movement_debit"] == "40"
        assert value["accounts"][0]["balance"] == "100"
        assert value["mappings"][0]["target_account_code"] == "CASH_AND_CASH_EQUIVALENTS"
        assert (await client.get("/v1/gl/", headers=other)).json() == []
        assert (await client.get(f"/v1/gl/{upload_id}/status", headers=other)).status_code == 404
        report = {"id": str(uuid4()), "upload_id": upload_id, "period": "2026-11"}
        assert (
            await client.post("/v1/reports/generate", json=report, headers=own)
        ).status_code == 409

        assert (
            await client.put("/v1/mappings/9999", json={"ifrs_code": "TRADE_PAYABLES"}, headers=own)
        ).status_code == 200
        assert (await client.get("/v1/mappings/", headers=other)).json() == [
            {"vas_code": "1111", "ifrs_code": "OTHER"}
        ]
        remapped = await client.post(f"/v1/gl/{upload_id}/remap", headers=own)
        assert remapped.json()["mapped_count"] == 2

        draft = {
            "id": str(uuid4()),
            "upload_id": upload_id,
            "source_account": "1111",
            "note": "Fixture reclassification",
            "lines": [
                {"account": "CASH_AND_CASH_EQUIVALENTS", "type": "credit", "amount": "0.30"},
                {"account": "A", "type": "debit", "amount": "0.10"},
                {"account": "B", "type": "debit", "amount": "0.20"},
            ],
        }
        invalid = {**draft, "lines": draft["lines"][:2]}
        assert (await client.post("/v1/adjustments/", json=invalid, headers=own)).status_code == 422
        assert (await client.post("/v1/adjustments/", json=draft, headers=other)).status_code == 404
        entry = await client.post("/v1/adjustments/", json=draft, headers=own)
        assert entry.status_code == 200, entry.text
        assert entry.json()["lines"] == draft["lines"]
        assert (await client.post("/v1/adjustments/", json=draft, headers=own)).json()[
            "id"
        ] == draft["id"]
        assert (
            await client.post("/v1/adjustments/", json={**draft, "note": "changed"}, headers=own)
        ).status_code == 409
        assert (await client.post(f"/v1/gl/{upload_id}/remap", headers=own)).status_code == 409
        assert (
            await client.post("/v1/reports/generate", json=report, headers=own)
        ).status_code == 409
        approve_path = f"/v1/adjustments/{draft['id']}/approve"
        assert (await client.post(approve_path, headers=read_only)).status_code == 403
        assert (await client.post(approve_path, headers=other)).status_code == 404
        calls = await asyncio.gather(*(client.post(approve_path, headers=own) for _ in range(2)))
        assert all(response.status_code == 200 for response in calls)
        assert calls[0].json()["approved_at"] == calls[1].json()["approved_at"]
        assert calls[0].json()["approved_by"] == accountant

        rejected = {**draft, "id": str(uuid4()), "note": "Superseded adjustment"}
        assert (
            await client.post("/v1/adjustments/", json=rejected, headers=own)
        ).status_code == 200
        reject_path = f"/v1/adjustments/{rejected['id']}/reject"
        assert (await client.post(reject_path, headers=own)).json()["status"] == "rejected"
        assert (
            await client.post(f"/v1/adjustments/{rejected['id']}/approve", headers=own)
        ).status_code == 409

        generated = await client.post("/v1/reports/generate", json=report, headers=own)
        assert generated.status_code == 200, generated.text
        output = generated.json()
        assert output["approved_entry_ids"] == [draft["id"]]
        assert Decimal(output["source_total"]) == Decimal(output["adjustment_total"]) == 0
        assert {row["account"]: Decimal(row["adjusted_balance"]) for row in output["rows"]} == {
            "A": Decimal("0.10"),
            "B": Decimal("0.20"),
            "CASH_AND_CASH_EQUIVALENTS": Decimal("99.70"),
            "TRADE_PAYABLES": Decimal(-100),
        }
        assert (
            await client.post("/v1/reports/generate", json=report, headers=own)
        ).json() == output
        assert (
            await client.post(
                "/v1/reports/generate", json={**report, "period": "2026-12"}, headers=own
            )
        ).status_code == 409
        download = f"/v1/reports/{report['id']}/download"
        assert (await client.get(download, headers=other)).status_code == 404
        assert (await client.get(download, headers=read_only)).status_code == 403

    # Drop pooled connections and retrieve the stored snapshot in a fresh session.
    await engine.dispose()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        result = await client.get(download, headers=export)
        assert result.status_code == 200, result.text
        assert result.headers["content-disposition"].endswith('.csv"')
        rows = {
            row["account"]: row for row in csv.DictReader(StringIO(result.text.lstrip("\ufeff")))
        }
        assert rows["CASH_AND_CASH_EQUIVALENTS"]["adjusted_balance"] == "99.70"
    async with AsyncSessionLocal() as session:
        actions = list(
            await session.scalars(
                select(AuditLog.action).where(
                    AuditLog.tenant_id == tenant, AuditLog.user_id == accountant
                )
            )
        )
        assert f"POST {approve_path}" in actions
        assert "POST /v1/reports/generate" in actions
    await engine.dispose()
