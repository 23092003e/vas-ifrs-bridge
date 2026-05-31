"""Knowledge base management endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/collections")
async def list_collections() -> dict:
    """List available knowledge base collections."""
    # TODO: query Qdrant for tenant collections
    return {"collections": []}
