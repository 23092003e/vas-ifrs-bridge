"""Account mapping rule endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_mappings() -> dict:
    """Return all VAS→IFRS mapping rules for the tenant."""
    # TODO: query mappings table
    return {"mappings": []}


@router.put("/{rule_id}")
async def update_mapping(rule_id: str, body: dict) -> dict:
    """Update a single mapping rule."""
    # TODO: persist updated rule
    return {"rule_id": rule_id}
