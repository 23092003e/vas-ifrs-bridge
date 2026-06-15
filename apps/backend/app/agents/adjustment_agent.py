"""Agent that generates IFRS adjustment journal entries from mapping results."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.agents.base import AgentBase

logger = logging.getLogger(__name__)

ADJUSTMENT_SYSTEM = """\
You are an expert VAS-IFRS Adjustment Specialist.

Your task is to analyze the provided General Ledger (GL) mapping results and generate IFRS adjustment journal entries (double-entry: Debit and Credit) to restate the accounts from VAS to IFRS compliance.

Common adjustment scenarios include:
1. **IFRS 16 (Leases)**: Capitalising operating leases as Right-of-Use (ROU) Assets and Lease Liabilities, and replacing lease expenses with depreciation and interest.
2. **IFRS 9 (Financial Instruments)**: Recording Expected Credit Loss (ECL) provisions instead of VAS general provisions, or adjusting financial assets to Fair Value.
3. **IAS 16 / IAS 38 (Fixed Assets / Intangibles)**: Component depreciation, capitalising development costs, or adjusting revaluation surpluses.

Structure your response strictly as follows:
1. **Overview**: A brief summary explaining the adjustments being made.
2. **Adjustment Entries Table**: A markdown table with the following columns:
   Entry ID | Debit Account | Credit Account | Amount | Rationale | Standard Reference
3. **Accounting Entries JSON Block**: Output a clean, valid JSON block containing the structural entries, so that downstream systems can parse it. Format it exactly as:
```json
[
  {{
    "entry_id": "ADJ-001",
    "debit_account": "IFRS ROU Asset",
    "credit_account": "IFRS Lease Liability",
    "amount": 100000.0,
    "rationale": "Capitalise lease under IFRS 16",
    "standard": "IFRS 16"
  }}
]
```
Ensure that all Debit and Credit entries are fully balanced and mathematically correct. Respond in {lang}.
"""


class AdjustmentAgent(AgentBase):
    """Generates balanced double-entry adjustments for IFRS restatement."""

    async def arun(  # type: ignore[override]
        self,
        *,
        query: str | None = None,
        upload_id: str | None = None,
        mapping_results: list[dict[str, Any]] | None = None,
        lang: str = "vi",
        model_hint: str = "openai",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        # 1. Prepare user prompt based on input data
        user_prompt = ""
        if mapping_results:
            user_prompt += "--- MAPPING RESULTS ---\n"
            user_prompt += json.dumps(mapping_results, ensure_ascii=False, indent=2)
            user_prompt += "\n-----------------------\n"

        if upload_id:
            user_prompt += f"Generate adjustments for Upload ID: {upload_id}\n"

        if query:
            user_prompt += f"User Request / Scenario: {query}\n"

        if not user_prompt:
            user_prompt = "Generate general standard VAS to IFRS restatement adjustment entries."

        system = ADJUSTMENT_SYSTEM.format(lang=lang)

        # 2. Stream tokens from LLM
        async for token in _call_llm(user_prompt, system, model_hint):
            yield f"data: {json.dumps({'type': 'token', 'delta': token})}\n\n"

        yield f"data: {json.dumps({'type': 'final', 'content': 'Adjustment generation complete.'})}\n\n"


async def _call_llm(user: str, system: str, model_hint: str) -> AsyncIterator[str]:
    from app.llm.providers.gemini import stream_chat

    try:
        async for tok in stream_chat(system=system, user=user, model_hint=model_hint):
            yield tok
    except Exception as exc:
        logger.error("Adjustment LLM stream error: %s", exc)
        yield f"[LLM error: {exc}]"
