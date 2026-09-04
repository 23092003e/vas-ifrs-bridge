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
    # Try finding markdown code block ```json ... ``` first
    raw_json = None
    json_code_match = re.search(r"```(?:json)?\s*([\[\{].*?[\]\}])\s*```", full_text, re.DOTALL)
    if json_code_match:
        raw_json = json_code_match.group(1).strip()
    else:
        # Fallback to finding outermost JSON array or object
        json_fallback_match = re.search(r"(\[\s*\{.*\}\s*\]|\{\s*\"adjustments\".*\}\s*)", full_text, re.DOTALL)
        if json_fallback_match:
            raw_json = json_fallback_match.group(1).strip()

    if not raw_json:
        raise ValueError("LLM response did not contain a valid adjustment JSON structure")

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM returned an invalid adjustment JSON block") from exc

    raw_list: list[dict[str, Any]] = []

    # Normalize parsed data into raw_list of entries
    if isinstance(parsed, list):
        raw_list = parsed
    elif isinstance(parsed, dict) and "adjustments" in parsed and isinstance(parsed["adjustments"], list):
        # Handle nested object format: {"adjustments": [...]}
        for i, adj in enumerate(parsed["adjustments"]):
            if not isinstance(adj, dict):
                continue
            desc = adj.get("description") or adj.get("rationale") or ""
            entry_id = adj.get("entry_id") or f"ADJ-{i+1:03d}"
            std = adj.get("standard") or ""

            if "entries" in adj and isinstance(adj["entries"], list):
                debits = [e for e in adj["entries"] if str(e.get("type", "")).lower() == "debit"]
                credits = [e for e in adj["entries"] if str(e.get("type", "")).lower() == "credit"]

                total_dr = sum(float(e.get("amount") or 0.0) for e in debits)
                total_cr = sum(float(e.get("amount") or 0.0) for e in credits)
                validate_balance(total_dr, total_cr)

                dr_acct = ", ".join(str(e.get("account", "")) for e in debits)
                cr_acct = ", ".join(str(e.get("account", "")) for e in credits)

                raw_list.append({
                    "entry_id": entry_id,
                    "debit_account": dr_acct,
                    "credit_account": cr_acct,
                    "amount": total_dr,
                    "rationale": desc,
                    "standard": std,
                })
            else:
                raw_list.append(adj)
    else:
        raise ValueError("LLM adjustment JSON must be a list of objects or an adjustments object")

    if not raw_list or not all(isinstance(entry, dict) for entry in raw_list):
        raise ValueError("LLM adjustment JSON must be a non-empty list of objects")

    # 3. Validate balance and normalize each entry
    normalized_entries: list[dict[str, Any]] = []
    for i, entry in enumerate(raw_list):
        raw_debit = entry.get("debit_amount")
        debit = float(raw_debit) if raw_debit is not None else float(entry.get("amount") or 0.0)

        raw_credit = entry.get("credit_amount")
        credit = float(raw_credit) if raw_credit is not None else float(entry.get("amount") or 0.0)

        try:
            validate_balance(debit, credit)
        except (ValueError, TypeError) as e:
            raise UnbalancedJEError(f"Invalid entry amounts: {debit} or {credit}. Error: {e}") from e

        entry_id = entry.get("entry_id") or f"ADJ-{i+1:03d}"
        dr_acct = entry.get("debit_account") or entry.get("debit") or ""
        cr_acct = entry.get("credit_account") or entry.get("credit") or ""

        normalized_entries.append({
            "entry_id": entry_id,
            "debit_account": dr_acct,
            "credit_account": cr_acct,
            "amount": debit,
            "debit_amount": debit,
            "credit_amount": credit,
            "rationale": entry.get("rationale") or entry.get("description") or "",
            "standard": entry.get("standard") or "",
        })

    return normalized_entries
