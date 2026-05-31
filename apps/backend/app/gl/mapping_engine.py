"""Rule-based mapping engine with LLM fallback for unknown accounts."""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from app.gl.coa_loader import load_coa

logger = logging.getLogger(__name__)


async def map_accounts(
    accounts: list[dict[str, Any]], tenant_id: str | None = None
) -> list[dict[str, Any]]:
    """
    Apply rule-based mapping; fall back to LLM for unmatched codes.
    Returns list of mapped dictionaries with keys:
    [src_account_code, src_account_name, target_standard, target_account_code, target_account_name, confidence, rationale]
    """
    # 1. Load standard VAS Chart of Accounts
    vas_coa = load_coa("VAS")

    results: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []

    # 2. Try rule-based prefix mapping first
    for acct in accounts:
        code = str(acct.get("account_code", "")).strip()
        name = str(acct.get("account_name", "")).strip()
        if not code:
            continue

        # Check standard code directly or by prefix (e.g. 1111 -> 111, 1121 -> 112)
        matched_prefix = None
        for length in (len(code), 3, 2, 1):
            prefix = code[:length]
            if prefix in vas_coa:
                matched_prefix = prefix
                break

        if matched_prefix:
            meta = vas_coa[matched_prefix]
            results.append(
                {
                    "src_account_code": code,
                    "src_account_name": name,
                    "target_standard": "IFRS",
                    "target_account_code": meta["ifrs_equivalent"].upper().replace(" ", "_"),
                    "target_account_name": meta["ifrs_equivalent"],
                    "confidence": 0.95,
                    "rationale": f"Matched standard account code prefix '{matched_prefix}' ({meta['name_vi']})",
                }
            )
        else:
            unmatched.append(acct)

    # 3. Fall back to LLM for any unmatched accounts
    if unmatched:
        logger.info("GL mapping: calling LLM fallback for %d unmatched accounts", len(unmatched))
        llm_results = await _map_with_llm(unmatched)
        results.extend(llm_results)

    return results


async def _map_with_llm(unmatched_accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use GLMappingAgent to resolve mappings for unknown accounts."""
    from app.agents.gl_mapping_agent import GLMappingAgent

    agent = GLMappingAgent()

    # Construct query list
    accts_str = "\n".join(
        [
            f"- Code: {a.get('account_code')}, Name: {a.get('account_name')}"
            for a in unmatched_accounts
        ]
    )
    query = (
        f"Please map the following unknown accounts to their corresponding IFRS equivalents:\n"
        f"{accts_str}"
    )

    tokens: list[str] = []
    async for event in agent.arun(query=query, lang="en"):
        if event.startswith("data: "):
            try:
                payload = json.loads(event[6:].strip())
                if payload.get("type") == "token":
                    tokens.append(payload.get("delta", ""))
            except Exception as e:
                logger.warning("Failed to parse stream event in mapping engine: %s", e)
                continue

    full_text = "".join(tokens)

    # Parse markdown table from response
    # Expected columns: VAS Code | VAS Account Name | IFRS Equivalent Line Item | Category | Confidence | Rationale
    parsed_mappings: list[dict[str, Any]] = []
    lines = full_text.split("\n")

    for line in lines:
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        # Skip header separators (e.g. |---|---|)
        if len(parts) >= 6 and not any(c == "-" for c in parts[1]):
            code = parts[1]
            name = parts[2]
            ifrs_equiv = parts[3]
            category = parts[4]
            confidence_str = parts[5]
            rationale = parts[6] if len(parts) > 6 else ""

            # Skip the actual table headers
            if code.lower() in ("vas code", "code", "mã"):
                continue

            try:
                confidence = float(re.sub(r"[^\d\.]", "", confidence_str))
            except ValueError:
                confidence = 0.70

            # Find matching original account from the unmatched list
            orig = next((a for a in unmatched_accounts if str(a.get("account_code")) == code), None)
            if orig:
                parsed_mappings.append(
                    {
                        "src_account_code": code,
                        "src_account_name": name or orig.get("account_name"),
                        "target_standard": "IFRS",
                        "target_account_code": ifrs_equiv.upper().replace(" ", "_"),
                        "target_account_name": ifrs_equiv,
                        "confidence": confidence,
                        "rationale": rationale
                        or f"LLM suggested mapping under category {category}",
                    }
                )

    # Fallback for accounts that were sent but not returned in the table
    for orig in unmatched_accounts:
        code = str(orig.get("account_code"))
        if not any(m["src_account_code"] == code for m in parsed_mappings):
            parsed_mappings.append(
                {
                    "src_account_code": code,
                    "src_account_name": orig.get("account_name"),
                    "target_standard": "IFRS",
                    "target_account_code": "UNMAPPED",
                    "target_account_name": "Unmapped Account",
                    "confidence": 0.0,
                    "rationale": "Mapping failed: standard prefix rules not matched and LLM did not return a valid row.",
                }
            )

    return parsed_mappings
