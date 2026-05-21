"""RAG retrieval agent — fetches chunks, composes prompt, streams LLM answer."""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

from app.agents.base import AgentBase
from app.agents.citation_validator import CitationValidator
from app.rag.citation import build_citation_list, wrap_chunks_for_prompt
from app.rag.retriever import RetrievedChunk, retrieve

logger = logging.getLogger(__name__)

_validator = CitationValidator()

SYSTEM_PROMPT = """\
You are an expert accounting assistant specialising in Vietnamese Accounting Standards (VAS) \
and International Financial Reporting Standards (IFRS).

Answer ONLY using the provided context blocks below. Cite every factual claim with [Cn] \
where n matches the context block number. Do NOT fabricate information not present in context.

Respond in {lang}. Be concise, structured, and precise.

--- CONTEXT ---
{context}
--- END CONTEXT ---
"""


class RetrievalAgent(AgentBase):
    """Retrieve chunks → compose prompt → stream cited answer."""

    async def arun(  # type: ignore[override]
        self,
        *,
        query: str,
        lang: str = "vi",
        tenant_id: str | None = None,
        tenant_collection: str | None = None,
        scope: str = "both",
        k: int = 8,
        model_hint: str = "qwen",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        # 1. Retrieve from all shared collections + tenant
        import asyncio as _asyncio
        from app.rag.reranker import rerank as _rerank

        tasks = [
            retrieve(query, collection="kb_shared_vas",  scope="shared", lang=lang, k=40, skip_rerank=True),
            retrieve(query, collection="kb_shared_ifrs", scope="shared", lang=lang, k=40, skip_rerank=True),
        ]
        if tenant_collection and tenant_id:
            tasks.append(retrieve(query, collection=tenant_collection, tenant_id=tenant_id, scope="tenant", lang=lang, k=40, skip_rerank=True))

        all_results = await _asyncio.gather(*tasks, return_exceptions=True)
        merged_raw: list[dict[str, Any]] = []
        for res in all_results:
            if isinstance(res, BaseException):
                logger.warning("retrieval partial failure: %s", res)
                continue
            merged_raw.extend({
                "id": c.id, "doc_id": c.doc_id, "text": c.text,
                "score": c.score, "rerank_score": c.rerank_score, "metadata": c.metadata,
            } for c in res)

        reranked = await _rerank(query, merged_raw, top_k=k)
        chunks = [
            RetrievedChunk(
                id=c["id"], doc_id=c["doc_id"], text=c["text"],
                score=c["score"], rerank_score=c.get("rerank_score", c["score"]),
                metadata=c["metadata"], citation_key=f"C{i + 1}",
            )
            for i, c in enumerate(reranked)
        ]

        context_block, citation_map = wrap_chunks_for_prompt(chunks)
        system = SYSTEM_PROMPT.format(lang=lang, context=context_block)

        # 2. Stream from LLM
        collected: list[str] = []
        async for token in _stream_llm(query, system, model_hint):
            collected.append(token)
            yield f"data: {json.dumps({'type': 'token', 'delta': token})}\n\n"

        # 3. Validate citations
        full_answer = "".join(collected)
        is_valid, unresolved, cleaned = _validator.validate(full_answer, citation_map)
        if not is_valid:
            logger.warning("unresolved citations %s — re-prompting once", unresolved)
            # One retry with explicit instruction
            fix_prompt = (
                f"{query}\n\n[SYSTEM: Fix citations. These keys do not exist: "
                f"{unresolved}. Remove them or replace with valid [Cn] keys.]"
            )
            fixed: list[str] = []
            async for token in _stream_llm(fix_prompt, system, model_hint):
                fixed.append(token)
            cleaned = "".join(fixed)

        # 4. Emit citations
        for cite in build_citation_list(cleaned, citation_map):
            payload = {"type": "citation", "key": cite.key, "doc_id": cite.doc_id,
                       "chunk_id": cite.chunk_id, "snippet": cite.snippet,
                       "standard_code": cite.standard_code}
            yield f"data: {json.dumps(payload)}\n\n"

        yield f"data: {json.dumps({'type': 'final', 'content': cleaned})}\n\n"


async def _stream_llm(
    user_msg: str, system: str, model_hint: str
) -> AsyncIterator[str]:
    """Route to Gemini provider (primary). Falls back log on error."""
    try:
        from app.llm.providers.gemini import stream_chat
        async for tok in stream_chat(system=system, user=user_msg, model_hint=model_hint):
            yield tok
    except Exception as exc:
        logger.error("LLM stream error: %s", exc)
        yield f"[LLM error: {exc}]"
