"""IFRS adjustment journal entry endpoints."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Stateful in-memory store for demonstrations and unit tests
_MOCK_ADJUSTMENT_ENTRIES = [
    {
        "entry_id": "ADJ-001",
        "debit_account": "IFRS Right-of-Use Asset",
        "credit_account": "IFRS Lease Liability",
        "amount": 150000.0,
        "status": "draft",
        "rationale": "Operating lease capitalized under IFRS 16 rules.",
        "standard": "IFRS 16",
    },
    {
        "entry_id": "ADJ-002",
        "debit_account": "IFRS Allowance for Credit Losses",
        "credit_account": "IFRS Retained Earnings",
        "amount": 25000.0,
        "status": "draft",
        "rationale": "Expected Credit Loss (ECL) adjustment under IFRS 9 rules.",
        "standard": "IFRS 9",
    },
]


@router.get("/")
async def list_adjustments() -> dict[str, Any]:
    """Return all adjustment entries for the tenant."""
    return {"adjustments": _MOCK_ADJUSTMENT_ENTRIES}


@router.post("/{entry_id}/approve")
async def approve_adjustment(entry_id: str) -> dict[str, Any]:
    """Mark an adjustment entry as approved."""
    for entry in _MOCK_ADJUSTMENT_ENTRIES:
        if entry["entry_id"] == entry_id:
            entry["status"] = "approved"
            return {
                "entry_id": entry_id,
                "status": "approved",
                "audit_log": f"Entry {entry_id} approved by authorized auditor.",
            }

    raise HTTPException(status_code=404, detail=f"Adjustment entry {entry_id} not found.")
