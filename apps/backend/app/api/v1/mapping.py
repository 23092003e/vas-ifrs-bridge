"""Account mapping rule endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/")
async def list_mappings() -> dict:
    """Return all VAS→IFRS mapping rules for the tenant."""
    raise HTTPException(status_code=501, detail="Mapping storage is not implemented")


@router.put("/{rule_id}")
async def update_mapping(rule_id: str, body: dict) -> dict:
    """Update a single mapping rule."""
    raise HTTPException(status_code=501, detail="Mapping updates are not implemented")
