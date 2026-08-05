"""General ledger upload and processing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

router = APIRouter()


@router.post("/upload")
async def upload_gl(file: UploadFile) -> dict:
    """Accept a GL file (xlsx/csv) and enqueue for processing."""
    raise HTTPException(status_code=501, detail="GL upload is not implemented")


@router.get("/{upload_id}/status")
async def get_upload_status(upload_id: str) -> dict:
    """Return processing status for a GL upload."""
    raise HTTPException(status_code=501, detail="GL upload status is not implemented")
