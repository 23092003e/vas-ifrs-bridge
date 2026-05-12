"""Document management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile) -> dict:
    """Upload a document to the tenant knowledge base."""
    # TODO: store to GCS and trigger ingestion pipeline
    return {"document_id": None}


@router.get("/")
async def list_documents() -> dict:
    """List all documents in the tenant knowledge base."""
    # TODO: query documents table
    return {"documents": []}
