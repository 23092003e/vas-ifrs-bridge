"""IFRS adjustment journal entry endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/")
async def list_adjustments() -> dict:
    """Return all adjustment entries for the tenant."""
    raise HTTPException(status_code=501, detail="Adjustment storage is not implemented")


@router.post("/{entry_id}/approve")
async def approve_adjustment(entry_id: str) -> dict:
    """Mark an adjustment entry as approved."""
    raise HTTPException(status_code=501, detail="Adjustment approval is not implemented")
