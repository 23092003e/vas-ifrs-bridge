"""Knowledge base management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/collections")
async def list_collections() -> dict:
    """List available knowledge base collections."""
    raise HTTPException(status_code=501, detail="Collection listing is not implemented")
