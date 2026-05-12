"""Adjustment journal entry generator and balance validator."""
from __future__ import annotations

from app.core.errors import UnbalancedJE


def validate_balance(debit: float, credit: float) -> None:
    """Raise UnbalancedJE if debit != credit."""
    if round(debit, 2) != round(credit, 2):
        raise UnbalancedJE(f"Debit {debit} != Credit {credit}")


async def generate_entries(mapping_results: list[dict]) -> list[dict]:
    """Generate and validate double-entry adjustments from mapping results."""
    # TODO: compute adjustment entries and validate each pair
    return []
