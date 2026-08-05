"""Tool: generate a double-entry IFRS adjustment journal entry."""

from __future__ import annotations

from typing import Any


async def generate_adjustment(mapping_id: str) -> dict[str, Any]:
    """Produce a balanced debit/credit adjustment entry for a mapping result."""
    raise NotImplementedError("Mapping persistence is required before adjustment generation")
