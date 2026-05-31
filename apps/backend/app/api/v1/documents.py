"""Document management endpoints."""

from __future__ import annotations

import os
import shutil
import asyncio
import logging
from fastapi import APIRouter, UploadFile, Request, HTTPException

from app.deps import DB
from app.db.models import Document
from app.ingestion.jobs import ingest_document

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile,
    request: Request,
    db: DB,
) -> dict:
    """Upload a document to the tenant knowledge base and trigger ingestion."""
    tenant = getattr(request.state, "tenant", None)
    if not tenant:
        raise HTTPException(status_code=403, detail="Tenant context required")

    # Create storage directory if not exists
    storage_dir = f"storage/tenants/{tenant.id}"
    os.makedirs(storage_dir, exist_ok=True)

    # Save file locally
    local_path = os.path.join(storage_dir, file.filename)
    try:
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        logger.error("Failed to save uploaded file locally: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Insert document record in DB
    doc = Document(
        tenant_id=tenant.id,
        filename=file.filename,
        gcs_path=local_path,  # Store local path in place of GCS
        mime_type=file.content_type,
        size_bytes=os.path.getsize(local_path),
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Run ingestion asynchronously in the background
    asyncio.create_task(
        ingest_document(
            document_id=doc.id,
            local_path=local_path,
            collection=tenant.qdrant_collection,
        )
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
