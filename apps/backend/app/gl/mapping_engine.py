"""Rule-based mapping engine with LLM fallback for unknown accounts."""
from __future__ import annotations


async def map_accounts(accounts: list[dict], tenant_id: str) -> list[dict]:
    """Apply rule-based mapping; fall back to LLM for unmatched codes."""
    # TODO: load rules, apply, collect unknowns, call LLM fallback
    return []
