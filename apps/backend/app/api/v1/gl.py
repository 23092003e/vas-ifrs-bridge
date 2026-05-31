"""General ledger upload and processing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.post("/upload")
async def upload_gl(file: UploadFile) -> dict:
    """Accept a GL file (xlsx/csv) and enqueue for processing."""
    # TODO: validate, store to GCS, enqueue gl_tasks.process_gl
    return {"upload_id": None}


@router.get("/{upload_id}/status")
async def get_upload_status(upload_id: str) -> dict:
    """Return processing status for a GL upload."""
    # TODO: query gl_uploads table
    return {"status": "pending"}
