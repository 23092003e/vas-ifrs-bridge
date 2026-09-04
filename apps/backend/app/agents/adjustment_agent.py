"""Agent that generates IFRS adjustment journal entries from mapping results."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.agents.base import AgentBase
from app.agents.citation_validator import CitationValidator
from app.prompts.composer import render
from app.rag.citation import build_citation_list, wrap_chunks_for_prompt
from app.rag.retriever import retrieve_multi

logger = logging.getLogger(__name__)
_validator = CitationValidator()


class AdjustmentAgent(AgentBase):
    """Generates balanced double-entry adjustments for IFRS restatement."""

    async def arun(  # type: ignore[override]
        self,
        *,
        query: str | None = None,
        upload_id: str | None = None,
        mapping_results: list[dict[str, Any]] | None = None,
        lang: str = "vi",
        tenant_id: str | None = None,
        tenant_collection: str | None = None,
        scope: str = "both",
        model_hint: str = "openai",
        messages: list[dict[str, str]] | None = None,
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

        # 2. Retrieve relevant standards context
        search_query = query if query else "IFRS adjustment restatement rules"
        chunks = await retrieve_multi(
            search_query,
            tenant_collection=tenant_collection,
            tenant_id=tenant_id,
            scope=scope,
            lang=lang,
            k=8,
        )

        context_block, citation_map = wrap_chunks_for_prompt(chunks)
        system = render(
            "system/adjustment_entry.j2",
            lang=lang,
            context=context_block,
            tenant_name=kwargs.get("tenant_name")
        )

        # 3. Stream tokens from LLM
        collected: list[str] = []
        async for token in _call_llm(user_prompt, system, model_hint, messages):
            collected.append(token)
            yield f"data: {json.dumps({'type': 'token', 'delta': token})}\n\n"

        # 4. Citation validation
        full = "".join(collected)
        is_valid, unresolved, cleaned = _validator.validate(full, citation_map)
        if not is_valid:
            logger.warning("adjustment agent unresolved citations: %s", unresolved)

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


async def _call_llm(user: str, system: str, model_hint: str, messages: list[dict[str, str]] | None = None) -> AsyncIterator[str]:
    from app.llm.router import stream_chat

    async for tok in stream_chat(system=system, user=user, messages=messages, model_hint=model_hint):
        yield tok
