"""Create and approve source-linked double-entry journal drafts."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.errors import UnbalancedJEError
from app.db.models import AdjustmentEntry
from app.db.repos.gl import get_upload, journal_query
from app.deps import DB, Workspace
from app.gl.adjustments import AccountCode, JournalLine, journal_totals

router = APIRouter()


class AdjustmentDraft(BaseModel):
    id: UUID
    upload_id: UUID
    source_account: AccountCode
    note: str = Field(min_length=1, max_length=2000, pattern=r"\S")
    lines: list[JournalLine] = Field(min_length=2, max_length=100)


def adjustment_response(entry: AdjustmentEntry) -> dict:
    return {
        "id": entry.id,
        "upload_id": entry.gl_upload_id,
        "source_account": entry.account_code,
        "note": entry.note,
        "status": entry.status,
        "lines": entry.lines,
        "created_by": entry.created_by,
        "approved_by": entry.approved_by,
        "created_at": entry.created_at,
        "approved_at": entry.approved_at,
    }


@router.get("/")
async def list_adjustments(db: DB, tenant: Workspace, upload_id: UUID | None = None) -> list[dict]:
    if upload_id is not None:
        await get_upload(db, tenant.id, str(upload_id))
    entries = await db.scalars(journal_query(tenant.id, str(upload_id) if upload_id else None))
    return [adjustment_response(row) for row in entries]


@router.post("/")
async def create_adjustment(
    body: AdjustmentDraft, db: DB, tenant: Workspace, request: Request
) -> dict:
    upload = await get_upload(db, tenant.id, str(body.upload_id), lock=True)
    mappings = upload.mapping_snapshot or []
    mapped = next(
        (
            row
            for row in mappings
            if row["src_account_code"] == body.source_account and row["target_account_code"]
        ),
        None,
    )
    if mapped is None:
        raise HTTPException(422, "Select a mapped source account from this upload")
    try:
        debit, credit = journal_totals(body.lines)
    except UnbalancedJEError as exc:
        raise HTTPException(422, str(exc)) from exc
    if debit >= 10**16:
        raise HTTPException(422, "Journal total exceeds the supported amount")
    lines = [line.model_dump(mode="json") for line in body.lines]
    entry_id = str(body.id)
    await db.execute(
        insert(AdjustmentEntry)
        .values(
            id=entry_id,
            tenant_id=tenant.id,
            gl_upload_id=upload.id,
            account_code=body.source_account,
            note=body.note,
            debit=debit,
            credit=credit,
            status="draft",
            lines=lines,
            created_by=request.state.user_id,
        )
        .on_conflict_do_nothing(index_elements=["id"])
    )
    entry = await db.scalar(
        select(AdjustmentEntry).where(
            AdjustmentEntry.id == entry_id, AdjustmentEntry.tenant_id == tenant.id
        )
    )
    if entry is None or (entry.gl_upload_id, entry.account_code, entry.note, entry.lines) != (
        upload.id,
        body.source_account,
        body.note,
        lines,
    ):
        raise HTTPException(409, "Adjustment key has already been used")
    response = adjustment_response(entry)
    await db.commit()
    return response


async def _lock_adjustment(entry_id: UUID, db: DB, tenant: Workspace) -> AdjustmentEntry:
    entry = await db.scalar(
        select(AdjustmentEntry).where(
            AdjustmentEntry.id == str(entry_id), AdjustmentEntry.tenant_id == tenant.id
        )
    )
    if entry is None:
        raise HTTPException(404, "Adjustment not found")
    await get_upload(db, tenant.id, entry.gl_upload_id, lock=True)
    await db.refresh(entry)
    return entry


@router.post("/{entry_id}/approve")
async def approve_adjustment(entry_id: UUID, db: DB, tenant: Workspace, request: Request) -> dict:
    entry = await _lock_adjustment(entry_id, db, tenant)
    if entry.status not in {"draft", "approved"}:
        raise HTTPException(409, "Adjustment cannot be approved")
    try:
        debit, credit = journal_totals(
            [JournalLine.model_validate(row) for row in entry.lines or []]
        )
    except (UnbalancedJEError, ValidationError) as exc:
        raise HTTPException(409, "Stored journal lines are invalid") from exc
    if (debit, credit) != (entry.debit, entry.credit):
        raise HTTPException(409, "Stored journal totals do not match the lines")
    if entry.status == "draft":
        entry.status = "approved"
        entry.approved_by = request.state.user_id
        entry.approved_at = datetime.now(UTC)
    response = adjustment_response(entry)
    await db.commit()
    return response


@router.post("/{entry_id}/reject")
async def reject_adjustment(entry_id: UUID, db: DB, tenant: Workspace) -> dict:
    entry = await _lock_adjustment(entry_id, db, tenant)
    if entry.status not in {"draft", "rejected"}:
        raise HTTPException(409, "Only drafts can be rejected")
    entry.status = "rejected"
    response = adjustment_response(entry)
    await db.commit()
    return response
