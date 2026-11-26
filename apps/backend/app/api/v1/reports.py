"""Snapshot and download an adjusted trial balance for a selected GL upload."""

import csv
from collections import defaultdict
from decimal import Decimal
from io import StringIO
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, StringConstraints
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import GLReport
from app.db.repos.gl import get_upload, journal_query
from app.deps import DB, Workspace

router = APIRouter()


class AdjustedTrialBalanceRequest(BaseModel):
    id: UUID
    upload_id: UUID
    report_type: Literal["adjusted_trial_balance"] = "adjusted_trial_balance"
    period: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


async def _get_report(db: DB, tenant: Workspace, report_id: str) -> GLReport | None:
    return await db.scalar(
        select(GLReport).where(GLReport.id == report_id, GLReport.tenant_id == tenant.id)
    )


def _response(report: GLReport) -> dict:
    return {
        "id": report.id,
        "upload_id": report.upload_id,
        "created_at": report.created_at,
        "created_by": report.created_by,
        "status": "done",
        **report.snapshot,
    }


@router.get("/")
async def list_reports(db: DB, tenant: Workspace, upload_id: UUID | None = None) -> list[dict]:
    query = select(GLReport).where(GLReport.tenant_id == tenant.id)
    if upload_id is not None:
        await get_upload(db, tenant.id, str(upload_id))
        query = query.where(GLReport.upload_id == str(upload_id))
    reports = await db.scalars(query.order_by(GLReport.created_at.desc(), GLReport.id).limit(50))
    return [
        {
            "id": row.id,
            "upload_id": row.upload_id,
            "period": row.snapshot["period"],
            "created_at": row.created_at,
        }
        for row in reports
    ]


@router.post("/generate")
async def generate_report(
    body: AdjustedTrialBalanceRequest, db: DB, tenant: Workspace, request: Request
) -> dict:
    upload = await get_upload(db, tenant.id, str(body.upload_id), lock=True)
    report_id = str(body.id)
    existing = await _get_report(db, tenant, report_id)
    if existing is not None:
        if existing.upload_id != upload.id or existing.snapshot["period"] != body.period:
            raise HTTPException(409, "Report key has already been used")
        return _response(existing)
    mappings = {
        mapping["src_account_code"]: mapping["target_account_code"]
        for mapping in upload.mapping_snapshot or []
    }
    if not upload.accounts or any(not mappings.get(row["account_code"]) for row in upload.accounts):
        raise HTTPException(409, "Map all trial balance accounts before reporting")
    journals = list(await db.scalars(journal_query(tenant.id, upload.id)))
    if any(row.status == "draft" for row in journals):
        raise HTTPException(409, "Approve pending journal drafts before reporting")

    source_balances: defaultdict[str, Decimal] = defaultdict(Decimal)
    adjustments: defaultdict[str, Decimal] = defaultdict(Decimal)
    for row in upload.accounts:
        source_balances[mappings[row["account_code"]]] += Decimal(row["balance"])
    approved = [row for row in journals if row.status == "approved"]
    for journal in approved:
        if not journal.lines:
            raise HTTPException(409, "An approved journal is missing its original allocations")
        for line in journal.lines:
            sign = 1 if line["type"] == "debit" else -1
            adjustments[line["account"]] += sign * Decimal(line["amount"])
    rows = [
        {
            "account": account,
            "mapped_balance": str(source_balances[account]),
            "adjustment": str(adjustments[account]),
            "adjusted_balance": str(source_balances[account] + adjustments[account]),
        }
        for account in sorted(source_balances.keys() | adjustments.keys())
    ]
    snapshot = {
        "period": body.period,
        "report_type": body.report_type,
        "rows": rows,
        "source_total": str(sum(source_balances.values(), Decimal(0))),
        "adjustment_total": str(sum(adjustments.values(), Decimal(0))),
        "approved_entry_ids": [row.id for row in approved],
    }
    await db.execute(
        insert(GLReport)
        .values(
            id=report_id,
            tenant_id=tenant.id,
            upload_id=upload.id,
            created_by=request.state.user_id,
            snapshot=snapshot,
        )
        .on_conflict_do_nothing(index_elements=["id"])
    )
    report = await _get_report(db, tenant, report_id)
    if report is None or report.upload_id != upload.id or report.snapshot["period"] != body.period:
        raise HTTPException(409, "Report key has already been used")
    response = _response(report)
    await db.commit()
    return response


def _csv_label(value: str) -> str:
    if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


@router.get("/{report_id}")
async def get_report(report_id: UUID, db: DB, tenant: Workspace) -> dict:
    report = await _get_report(db, tenant, str(report_id))
    if report is None:
        raise HTTPException(404, "Report not found")
    return _response(report)


@router.get("/{report_id}/download")
async def download_report(report_id: UUID, db: DB, tenant: Workspace) -> Response:
    report = await _get_report(db, tenant, str(report_id))
    if report is None:
        raise HTTPException(404, "Report not found")
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["period", "account", "mapped_balance", "adjustment", "adjusted_balance"])
    for row in report.snapshot["rows"]:
        writer.writerow(
            [
                _csv_label(report.snapshot["period"]),
                _csv_label(row["account"]),
                row["mapped_balance"],
                row["adjustment"],
                row["adjusted_balance"],
            ]
        )
    return Response(
        "\ufeff" + output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="adjusted-trial-balance-{report_id}.csv"'
        },
    )
