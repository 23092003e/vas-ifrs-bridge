"""Adjustment journal entry generator and balance validator."""

from __future__ import annotations

import json
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.core.errors import UnbalancedJEError

logger = logging.getLogger(__name__)


AccountCode = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class JournalLine(BaseModel):
    account: AccountCode
    type: Literal["debit", "credit"]
    amount: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=2, allow_inf_nan=False)]


def validate_balance(debit: Decimal, credit: Decimal) -> None:
    """Require equal, finite, positive totals."""
    if not debit.is_finite() or not credit.is_finite() or debit <= 0 or debit != credit:
        raise UnbalancedJEError(f"Debit {debit} must equal Credit {credit} and be positive")


def journal_totals(lines: list[JournalLine]) -> tuple[Decimal, Decimal]:
    debit = sum((line.amount for line in lines if line.type == "debit"), Decimal(0))
    credit = sum((line.amount for line in lines if line.type == "credit"), Decimal(0))
    validate_balance(debit, credit)
    return debit, credit


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
        json_fallback_match = re.search(
            r"(\{\s*\"adjustments\".*\}\s*|\[\s*\{.*\}\s*\])", full_text, re.DOTALL
        )
        if json_fallback_match:
            raw_json = json_fallback_match.group(1).strip()

    if not raw_json:
        raise ValueError("LLM response did not contain a valid adjustment JSON structure")

    try:
        parsed = json.loads(raw_json, parse_float=Decimal)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM returned an invalid adjustment JSON block") from exc

    raw_list = parsed.get("adjustments") if isinstance(parsed, dict) else parsed
    if (
        not isinstance(raw_list, list)
        or not raw_list
        or not all(isinstance(entry, dict) for entry in raw_list)
    ):
        raise ValueError("LLM adjustment JSON must be a non-empty list of objects")

    normalized_entries: list[dict[str, Any]] = []
    for i, entry in enumerate(raw_list):
        if "entries" in entry:
            items = entry["entries"]
            if not isinstance(items, list):
                raise ValueError("Journal entries must be a list")
            lines = [JournalLine.model_validate(item) for item in items]
        else:
            amount = entry.get("amount")
            try:
                debit = Decimal(str(entry.get("debit_amount", amount)))
                credit = Decimal(str(entry.get("credit_amount", amount)))
            except InvalidOperation as exc:
                raise ValueError("Debit and credit amounts must be valid decimals") from exc
            validate_balance(debit, credit)
            lines = [
                JournalLine(
                    account=entry.get("debit_account") or entry.get("debit"),
                    type="debit",
                    amount=debit,
                ),
                JournalLine(
                    account=entry.get("credit_account") or entry.get("credit"),
                    type="credit",
                    amount=credit,
                ),
            ]
        debit, credit = journal_totals(lines)
        normalized_entries.append(
            {
                "entry_id": entry.get("entry_id") or f"ADJ-{i + 1:03d}",
                "debit_account": ", ".join(line.account for line in lines if line.type == "debit"),
                "credit_account": ", ".join(
                    line.account for line in lines if line.type == "credit"
                ),
                "amount": debit,
                "debit_amount": debit,
                "credit_amount": credit,
                "lines": [line.model_dump() for line in lines],
                "rationale": entry.get("rationale") or entry.get("description") or "",
                "standard": entry.get("standard") or "",
            }
        )

    return normalized_entries
