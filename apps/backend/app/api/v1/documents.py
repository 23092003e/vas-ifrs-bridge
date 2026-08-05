"""Document management endpoints."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from uuid import uuid4

import anyio
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile

from app.db.models import Document
from app.deps import DB
from app.ingestion.jobs import ingest_document

logger = logging.getLogger(__name__)
router = APIRouter()
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024
UPLOAD_CHUNK_SIZE_BYTES = 1024 * 1024
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".txt", ".md", ".csv"}


def _validate_filename(filename: str | None) -> str:
    if (
        not filename
        or filename in {".", ".."}
        or Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
    ):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return filename


@router.post("/upload")
async def upload_document(
    file: UploadFile,
    request: Request,
    db: DB,
    background_tasks: BackgroundTasks,
) -> dict:
    """Upload a document to the tenant knowledge base and trigger ingestion."""
    tenant = getattr(request.state, "tenant", None)
    if not tenant:
        raise HTTPException(status_code=403, detail="Tenant context required")

    filename = _validate_filename(file.filename)
    if Path(filename).suffix.lower() not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Unsupported document type")

    # Create storage directory if not exists
    storage_dir = f"storage/tenants/{tenant.id}"
    os.makedirs(storage_dir, exist_ok=True)

    # Save file locally
    local_path = os.path.join(storage_dir, f"{uuid4().hex}-{filename}")
    size_bytes = 0
    try:
        async with await anyio.open_file(local_path, "wb") as buffer:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE_BYTES):
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(status_code=413, detail="Uploaded file is too large")
                await buffer.write(chunk)
    except HTTPException:
        if os.path.exists(local_path):
            os.remove(local_path)
        raise
    except Exception as exc:
        logger.error("Failed to save uploaded file locally: %s", exc)
        if os.path.exists(local_path):
            os.remove(local_path)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file") from exc

    # Insert document record in DB
    doc = Document(
        tenant_id=tenant.id,
        filename=filename,
        gcs_path=local_path,  # Store local path in place of GCS
        mime_type=file.content_type,
        size_bytes=size_bytes,
        status="pending",
    )
    try:
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
    except Exception as exc:
        logger.exception("Failed to create document record")
        await db.rollback()
        if os.path.exists(local_path):
            os.remove(local_path)
        raise HTTPException(status_code=503, detail="Document storage unavailable") from exc

    # Run ingestion asynchronously in the background
    background_tasks.add_task(
        ingest_document,
        document_id=doc.id,
        local_path=local_path,
        tenant_id=tenant.id,
    )

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
    }


@router.get("/")
async def list_documents(request: Request, db: DB) -> dict:
    """List all documents in the tenant knowledge base."""
    tenant = getattr(request.state, "tenant", None)
    if not tenant:
        return {"documents": []}

    from sqlalchemy import select
    stmt = select(Document).where(Document.tenant_id == tenant.id).order_by(Document.created_at.desc())
    res = await db.execute(stmt)
    documents = res.scalars().all()

    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "size_bytes": d.size_bytes,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at.isoformat(),
            }
            for d in documents
        ]
    }
