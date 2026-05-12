"""Tool: generate a double-entry IFRS adjustment journal entry."""
from __future__ import annotations


async def generate_adjustment(mapping_id: str) -> dict:
    """Produce a balanced debit/credit adjustment entry for a mapping result."""
    # TODO: call AdjustmentAgent and validate balance
    return {"debit": None, "credit": None, "balanced": False}
