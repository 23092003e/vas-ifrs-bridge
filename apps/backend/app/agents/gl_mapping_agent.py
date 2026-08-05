"""Agent that maps VAS chart-of-accounts codes to IFRS equivalents."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.agents.base import AgentBase
from app.agents.citation_validator import CitationValidator
from app.rag.citation import build_citation_list, wrap_chunks_for_prompt
from app.rag.retriever import retrieve_multi

logger = logging.getLogger(__name__)
_validator = CitationValidator()

MAPPING_SYSTEM = """\
You are an expert VAS-IFRS Mapping Specialist.

Your task is to analyze the requested Vietnamese Accounting Standards (VAS) accounts and map them to their corresponding International Financial Reporting Standards (IFRS) equivalents.

Structure your response as follows:
1. **Overview**: A brief paragraph explaining the mapping approach for the requested accounts.
2. **Account Mapping Table**: A markdown table with the following columns:
   VAS Code | VAS Account Name | IFRS Equivalent Line Item | Category | Confidence | Rationale
3. **Key Adjustments / Notes**: Highlight any significant adjustment considerations or lease/financial instrument implications.

Cite every factual claim with [Cn] where possible. Respond in {lang}.

--- CONTEXT ---
{context}
--- END CONTEXT ---
"""


class GLMappingAgent(AgentBase):
    """Maps a batch of VAS GL accounts to IFRS classification using RAG + LLM."""

    async def arun(  # type: ignore[override]
        self,
        *,
        query: str,
        lang: str = "vi",
        tenant_id: str | None = None,
        tenant_collection: str | None = None,
        scope: str = "both",
        model_hint: str = "openai",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        # 1. Retrieve relevant standards context
        chunks = await retrieve_multi(
            query,
            tenant_collection=tenant_collection,
            tenant_id=tenant_id,
            scope=scope,
            lang=lang,
            k=8,
        )

        context_block, citation_map = wrap_chunks_for_prompt(chunks)
        system = MAPPING_SYSTEM.format(lang=lang, context=context_block)

        # 2. Stream tokens from LLM
        collected: list[str] = []
        async for token in _call_llm(query, system, model_hint):
            collected.append(token)
            yield f"data: {json.dumps({'type': 'token', 'delta': token})}\n\n"

        # 3. Citation validation
        full = "".join(collected)
        is_valid, unresolved, cleaned = _validator.validate(full, citation_map)
        if not is_valid:
            logger.warning("mapping agent unresolved citations: %s", unresolved)

        for cite in build_citation_list(cleaned, citation_map):
            payload = {
                "type": "citation",
                "key": cite.key,
                "doc_id": cite.doc_id,
                "chunk_id": cite.chunk_id,
                "snippet": cite.snippet,
                "standard_code": cite.standard_code,
            }
            yield f"data: {json.dumps(payload)}\n\n"

        yield f"data: {json.dumps({'type': 'final', 'content': cleaned})}\n\n"


async def _call_llm(user: str, system: str, model_hint: str) -> AsyncIterator[str]:
    from app.llm.router import stream_chat

    async for tok in stream_chat(system=system, user=user, model_hint=model_hint):
        yield tok
