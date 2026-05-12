"""IFRS adjustment journal entry endpoints."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_adjustments() -> dict:
    """Return all adjustment entries for the tenant."""
    # TODO: query adjustment_entries table
    return {"adjustments": []}


@router.post("/{entry_id}/approve")
async def approve_adjustment(entry_id: str) -> dict:
    """Mark an adjustment entry as approved."""
    # TODO: update status and log audit
    return {"entry_id": entry_id, "status": "approved"}
