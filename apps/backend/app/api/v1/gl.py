"""Tenant-scoped trial balance upload and mapping snapshots."""

from __future__ import annotations

import hashlib
from decimal import Decimal, DecimalException
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
from uuid import UUID, uuid4
from zipfile import BadZipFile, ZipFile

import anyio
from fastapi import APIRouter, Header, HTTPException, Request, UploadFile
from openpyxl.utils.exceptions import InvalidFileException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import GLUpload
from app.db.repos.gl import get_upload, journal_query, tenant_mapping_rules
from app.deps import DB, Workspace
from app.gl.mapping_engine import map_accounts
from app.tools.parse_gl_file import parse_gl_file

router = APIRouter()
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_ACCOUNTS = 25_000


def upload_response(upload: GLUpload) -> dict:
    return {
        "id": upload.id,
        "filename": upload.filename,
        "status": upload.status,
        "row_count": upload.row_count,
        "mapped_count": upload.mapped_count,
        "accounts": upload.accounts,
        "mappings": upload.mapping_snapshot,
        "created_at": upload.created_at,
    }


@router.get("/")
async def list_uploads(db: DB, tenant: Workspace) -> list[dict]:
    uploads = await db.scalars(
        select(GLUpload)
        .where(GLUpload.tenant_id == tenant.id)
        .order_by(GLUpload.created_at.desc(), GLUpload.id)
        .limit(50)
    )
    return [
        {"id": row.id, "filename": row.filename, "status": row.status, "created_at": row.created_at}
        for row in uploads
    ]


@router.post("/upload")
async def upload_gl(
    file: UploadFile,
    db: DB,
    tenant: Workspace,
    request: Request,
    idempotency_key: Annotated[UUID | None, Header()] = None,
) -> dict:
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise HTTPException(415, "Expected a CSV or XLSX trial balance")
    if len(filename) > 500:
        raise HTTPException(422, "Filename is too long")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Trial balance exceeds 10 MiB")
    content_hash = hashlib.sha256(data).hexdigest()
    upload_id = str(idempotency_key or uuid4())
    existing = await db.scalar(
        select(GLUpload).where(GLUpload.tenant_id == tenant.id, GLUpload.id == upload_id)
    )
    if existing is not None:
        if existing.content_sha256 != content_hash or existing.filename != filename:
            raise HTTPException(409, "Upload key has already been used")
        return upload_response(existing)

    try:
        if suffix == ".xlsx":
            with ZipFile(BytesIO(data)) as workbook:
                entries = workbook.infolist()
                if (
                    len(entries) > 1000
                    or sum(item.file_size for item in entries) > 50 * 1024 * 1024
                ):
                    raise HTTPException(413, "Expanded workbook exceeds its supported size")
        with TemporaryDirectory() as directory:
            path = anyio.Path(directory) / f"upload{suffix}"
            await path.write_bytes(data)
            accounts = await parse_gl_file(str(path))
    except (
        ValueError,
        DecimalException,
        BadZipFile,
        InvalidFileException,
        SyntaxError,
        KeyError,
    ) as exc:
        raise HTTPException(422, "Invalid trial balance file") from exc
    if not accounts or len(accounts) > MAX_ACCOUNTS:
        raise HTTPException(422, "Trial balance must contain 1 to 25,000 account rows")
    if any(len(row["account_code"]) > 50 for row in accounts):
        raise HTTPException(422, "Account codes must be at most 50 characters")
    if len({row["account_code"] for row in accounts}) != len(accounts):
        raise HTTPException(422, "Trial balance contains duplicate account codes")
    if any(
        abs(value) >= 10**16 or value != value.quantize(Decimal("0.01"))
        for row in accounts
        for value in row.values()
        if isinstance(value, Decimal)
    ):
        raise HTTPException(422, "Amounts must fit 16 integer digits and two decimal places")
    rules = await tenant_mapping_rules(db, tenant.id)
    mappings = await map_accounts(accounts, tenant_rules=rules, use_llm=False)
    await db.execute(
        insert(GLUpload)
        .values(
            id=upload_id,
            tenant_id=tenant.id,
            user_id=request.state.user_id,
            filename=filename,
            gcs_path="",
            status="mapped",
            row_count=len(accounts),
            mapped_count=sum(bool(item["target_account_code"]) for item in mappings),
            content_sha256=content_hash,
            accounts=[{key: str(value) for key, value in row.items()} for row in accounts],
            mapping_snapshot=mappings,
        )
        .on_conflict_do_nothing(index_elements=["id"])
    )
    upload = await db.scalar(
        select(GLUpload).where(GLUpload.tenant_id == tenant.id, GLUpload.id == upload_id)
    )
    if upload is None or (upload.content_sha256 != content_hash or upload.filename != filename):
        raise HTTPException(409, "Upload key has already been used")
    response = upload_response(upload)
    await db.commit()
    return response


@router.get("/{upload_id}/status")
async def get_upload_status(upload_id: UUID, db: DB, tenant: Workspace) -> dict:
    return upload_response(await get_upload(db, tenant.id, str(upload_id)))


@router.post("/{upload_id}/remap")
async def remap_upload(upload_id: UUID, db: DB, tenant: Workspace) -> dict:
    upload = await get_upload(db, tenant.id, str(upload_id), lock=True)
    if not upload.accounts or await db.scalar(journal_query(tenant.id, upload.id).limit(1)):
        raise HTTPException(409, "Only uploads without journal entries can be remapped")
    rules = await tenant_mapping_rules(db, tenant.id)
    upload.mapping_snapshot = await map_accounts(upload.accounts, tenant_rules=rules, use_llm=False)
    upload.mapped_count = sum(bool(item["target_account_code"]) for item in upload.mapping_snapshot)
    response = upload_response(upload)
    await db.commit()
    return response
