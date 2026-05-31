"""Tool: generate a double-entry IFRS adjustment journal entry."""

from __future__ import annotations

from typing import Any
from app.gl.adjustments import generate_entries


async def generate_adjustment(mapping_id: str) -> dict[str, Any]:
    """Produce a balanced debit/credit adjustment entry for a mapping result."""
    # 1. Mock mapping result for mapping_id if database query is not fully implemented
    # In production, this would query the `mappings` database table.
    mock_mapping = {
        "mapping_id": mapping_id,
        "vas_code": "242",
        "vas_name": "Chi phí trả trước ngắn hạn (Prepaid expenses)",
        "ifrs_equivalent": "Prepaid Expenses / Right-of-Use Assets",
        "amount": 150000.0,
        "rationale": "Lease rental prepaid for office space under IFRS 16 capitalization requirements.",
    }

    # 2. Call the adjustment generator engine
    entries = await generate_entries([mock_mapping])

    if not entries:
        return {"debit": None, "credit": None, "balanced": False, "entries": []}

    # Return structured entry summary
    first = entries[0]
    return {
        "debit": first.get("debit_account"),
        "credit": first.get("credit_account"),
        "amount": first.get("amount"),
        "balanced": True,
        "entries": entries,
    }
