"""Agent that produces a structured VAS ↔ IFRS standard comparison."""

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

COMPARE_SYSTEM = """\
You are an expert in Vietnamese Accounting Standards (VAS) and IFRS.

Compare the two standards on the topic below. Structure your response as:
1. **Overview** — one paragraph each
2. **Key Differences** — table with columns: Aspect | VAS | IFRS | Practical Impact
3. **Convergence Areas** — what is already aligned
4. **Adoption Implications** — for Vietnamese enterprises

Cite every factual claim with [Cn]. Respond in {lang}.

--- CONTEXT ---
{context}
--- END CONTEXT ---
"""


class IFRSCompareAgent(AgentBase):
    """Retrieves VAS + IFRS content on a topic and generates structured comparison."""

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
        # Retrieve from both VAS and IFRS shared collections
        chunks = await retrieve_multi(
            query,
            tenant_collection=tenant_collection,
            tenant_id=tenant_id,
            scope=scope,
            lang=lang,
            k=10,
        )

        context_block, citation_map = wrap_chunks_for_prompt(chunks)
        system = COMPARE_SYSTEM.format(lang=lang, context=context_block)

        collected: list[str] = []
        async for token in _call_llm(query, system, model_hint):
            collected.append(token)
            yield f"data: {json.dumps({'type': 'token', 'delta': token})}\n\n"

        full = "".join(collected)
        is_valid, unresolved, cleaned = _validator.validate(full, citation_map)
        if not is_valid:
            logger.warning("compare agent unresolved citations: %s", unresolved)

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
