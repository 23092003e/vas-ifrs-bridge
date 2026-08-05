"""Adjustment journal entry generator and balance validator."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.errors import UnbalancedJEError

logger = logging.getLogger(__name__)


def validate_balance(debit: float, credit: float) -> None:
    """Raise UnbalancedJEError if debit != credit."""
    if round(debit, 2) != round(credit, 2):
        raise UnbalancedJEError(f"Debit {debit} != Credit {credit}")


async def generate_entries(mapping_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate and validate double-entry adjustments from mapping results."""
    from app.agents.adjustment_agent import AdjustmentAgent

    agent = AdjustmentAgent()
    tokens = []

    # 1. Run agent and gather all streamed tokens
    async for event in agent.arun(mapping_results=mapping_results):
        if event.startswith("data: "):
            try:
                payload = json.loads(event[6:].strip())
                if payload.get("type") == "token":
                    tokens.append(payload.get("delta", ""))
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("Failed to parse stream event: %s", e)
                continue

    full_text = "".join(tokens)

    # 2. Extract structured JSON block containing the entries
    # Look for ```json ... ``` blocks
    json_match = re.search(r"```json\s*(\[\s*\{.*\}\s*\])\s*```", full_text, re.DOTALL)
    if not json_match:
        # Fallback to general JSON list matching if Markdown code blocks are absent
        json_match = re.search(r"(\[\s*\{.*\}\s*\])", full_text, re.DOTALL)

    entries: list[dict[str, Any]] = []
    if json_match:
        try:
            entries = json.loads(json_match.group(1).strip())
        except json.JSONDecodeError as exc:
            raise ValueError("LLM returned an invalid adjustment JSON block") from exc
    else:
        raise ValueError("LLM response did not contain an adjustment JSON array")

    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValueError("LLM adjustment JSON must be a list of objects")

    # 3. Validate balance for each entry
    for entry in entries:
        # Accept amount-based balanced entries or explicit debit_amount/credit_amount
        raw_debit = entry.get("debit_amount")
        debit = float(raw_debit) if raw_debit is not None else float(entry.get("amount") or 0.0)

        raw_credit = entry.get("credit_amount")
        credit = float(raw_credit) if raw_credit is not None else float(entry.get("amount") or 0.0)

        try:
            validate_balance(debit, credit)
        except (ValueError, TypeError) as e:
            raise UnbalancedJEError(f"Invalid entry amounts: {debit} or {credit}. Error: {e}") from e

    return entries
