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
            except Exception as e:
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
        except Exception as e:
            logger.error(
                "Failed to parse extracted JSON block: %s. Raw content: %s", e, json_match.group(1)
            )
    else:
        logger.warning("No JSON array block found in LLM response: %s", full_text)

    # 3. Validate balance for each entry
    for entry in entries:
        # Accept amount-based balanced entries or explicit debit_amount/credit_amount
        debit = (
            entry.get("debit_amount")
            if entry.get("debit_amount") is not None
            else entry.get("amount", 0.0)
        )
        credit = (
            entry.get("credit_amount")
            if entry.get("credit_amount") is not None
            else entry.get("amount", 0.0)
        )

        try:
            validate_balance(float(debit), float(credit))
        except (ValueError, TypeError) as e:
            raise UnbalancedJEError(f"Invalid entry amounts: {debit} or {credit}. Error: {e}") from e

    return entries
