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
            retrieve(
                query, collection="kb_shared_vas", scope="shared", lang=lang, k=40, skip_rerank=True
            ),
            retrieve(
                query,
                collection="kb_shared_ifrs",
                scope="shared",
                lang=lang,
                k=40,
                skip_rerank=True,
            ),
        ]
        if tenant_collection and tenant_id:
            tasks.append(
                retrieve(
                    query,
                    collection=tenant_collection,
                    tenant_id=tenant_id,
                    scope="tenant",
                    lang=lang,
                    k=40,
                    skip_rerank=True,
                )
            )
        results = await _asyncio.gather(*tasks, return_exceptions=True)
        original_chunks: list[RetrievedChunk] = []
        for res in results:
            if isinstance(res, BaseException):
                logger.warning("retrieval partial failure: %s", res)
                continue
            original_chunks.extend(res)

        merged_raw: list[dict[str, Any]] = [
            {
                "id": c.id,
                "doc_id": c.doc_id,
                "text": c.text,
                "score": c.score,
                "rerank_score": c.rerank_score,
                "metadata": c.metadata,
            }
            for c in original_chunks
        ]

        # Graph Expansion
        try:
            from app.rag import graph_service

            G = graph_service.get_graph()
        except Exception as e:
            logger.error("Failed to load graph service: %s", e)
            G = None

        if G is not None and G.number_of_nodes() > 0:
            top_chunks = original_chunks[:5]
            expanded_node_ids = set()

            for c in top_chunks:
                node_id = None
                if c.id in G:
                    node_id = c.id
                else:
                    # Match by doc_id and text preview
                    text_prefix = c.text[:200]
                    for n, attrs in G.nodes(data=True):
                        if attrs.get("type") == "section" and attrs.get("doc_id") == c.doc_id:
                            tp = attrs.get("text_preview", "")
                            if tp == text_prefix or text_prefix.startswith(tp) or tp in c.text:
                                node_id = n
                                break

                if node_id:
                    related = graph_service.get_related_sections(node_id, depth=1)
                    equivs = graph_service.get_ifrs_equivalents(node_id)
                    expanded_node_ids.update(related)
                    expanded_node_ids.update(equivs)

            # Identify account codes in user query
            import re

            account_codes = re.findall(r"\b\d{3,4}\b", query)
            for acc in account_codes:
                gov_sections = graph_service.get_governed_sections_for_account(acc)
                expanded_node_ids.update(gov_sections)
                for gov_sec in gov_sections:
                    expanded_node_ids.update(graph_service.get_related_sections(gov_sec, depth=1))

            # Deduplication set of doc_id + prefix
            existing_doc_text_prefixes = {c.doc_id + c.text[:100] for c in original_chunks}

            # Group expanded node IDs by collection
            collections_to_nodes: dict[str, list[tuple[str, str, str]]] = {
                "kb_shared_vas": [],
                "kb_shared_ifrs": [],
            }
            if tenant_collection:
                collections_to_nodes[tenant_collection] = []

            for n_id in expanded_node_ids:
                if n_id not in G:
                    continue
                node_attrs = G.nodes[n_id]
                if node_attrs.get("type") != "section":
                    continue

                std_code = node_attrs.get("standard_code", "")
                doc_id = node_attrs.get("doc_id", "")
                text_preview = node_attrs.get("text_preview", "")

                if tenant_collection and not std_code:
                    coll = tenant_collection
                else:
                    code_upper = std_code.upper() if std_code else ""
                    if any(x in code_upper for x in ["IFRS", "IAS", "IFRIC", "SIC"]):
                        coll = "kb_shared_ifrs"
                    else:
                        coll = "kb_shared_vas"

                if coll in collections_to_nodes:
                    collections_to_nodes[coll].append((n_id, doc_id, text_preview))

            # Fetch expanded point payloads using client.retrieve or fallback
            try:
                from app.rag.retriever import _qdrant_client
                from qdrant_client.models import Filter, FieldCondition, MatchValue

                client = _qdrant_client()
                try:
                    for coll, node_tuples in collections_to_nodes.items():
                        if not node_tuples:
                            continue

                        # Try direct retrieve
                        direct_ids = [t[0] for t in node_tuples]
                        try:
                            records = await client.retrieve(
                                collection_name=coll, ids=direct_ids, with_payload=True
                            )
                        except Exception as e:
                            logger.warning("Qdrant direct retrieve failed: %s", e)
                            records = []

                        retrieved_ids = set()
                        for r in records:
                            retrieved_ids.add(str(r.id))
                            payload = r.payload or {}
                            text = payload.get("text_preview", "") or payload.get("text", "")
                            doc_id = payload.get("doc_id", "")

                            if doc_id + text[:100] in existing_doc_text_prefixes:
                                continue
                            existing_doc_text_prefixes.add(doc_id + text[:100])

                            merged_raw.append(
                                {
                                    "id": str(r.id),
                                    "doc_id": doc_id,
                                    "text": text,
                                    "score": 0.8,
                                    "metadata": payload,
                                }
                            )

                        # Fallback for remaining nodes: match by doc_id scroll
                        remaining_nodes = [t for t in node_tuples if t[0] not in retrieved_ids]
                        if remaining_nodes:
                            for n_id, doc_id, text_preview in remaining_nodes:
                                if not doc_id:
                                    continue
                                flt = Filter(
                                    must=[
                                        FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                                    ]
                                )
                                try:
                                    search_res = await client.scroll(
                                        collection_name=coll,
                                        scroll_filter=flt,
                                        limit=100,
                                        with_payload=True,
                                    )
                                    points = search_res[0] if search_res else []
                                except Exception as e:
                                    logger.warning("Qdrant scroll failed for doc %s: %s", doc_id, e)
                                    points = []

                                for p in points:
                                    payload = p.payload or {}
                                    text = payload.get("text_preview", "") or payload.get(
                                        "text", ""
                                    )
                                    if (
                                        text_preview == text[:200]
                                        or text[:200].startswith(text_preview)
                                        or text_preview in text
                                    ):
                                        if doc_id + text[:100] in existing_doc_text_prefixes:
                                            break
                                        existing_doc_text_prefixes.add(doc_id + text[:100])

                                        merged_raw.append(
                                            {
                                                "id": str(p.id),
                                                "doc_id": doc_id,
                                                "text": text,
                                                "score": 0.8,
                                                "metadata": payload,
                                            }
                                        )
                                        break
                finally:
                    await client.close()
            except Exception as e:
                logger.error("Failed to connect or query Qdrant for graph expansion: %s", e)

        # Rerank merged chunks
        reranked: list[dict[str, Any]]
        try:
            reranked = await _rerank(query, merged_raw, top_k=k)
        except Exception as e:
            logger.error("Reranking failed: %s. Using top chunks by score.", e)
            merged_raw.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            reranked = merged_raw[:k]

        chunks = [
            RetrievedChunk(
                id=str(c["id"]),
                doc_id=str(c["doc_id"]),
                text=str(c["text"]),
                score=float(c["score"]),
                rerank_score=float(c["rerank_score"])
                if ("rerank_score" in c and c["rerank_score"] is not None)
                else float(c["score"]),
                metadata=c["metadata"] if isinstance(c["metadata"], dict) else {},
                citation_key=f"C{i + 1}",
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


async def _stream_llm(user_msg: str, system: str, model_hint: str) -> AsyncIterator[str]:
    """Route to Gemini provider (primary). Falls back log on error."""
    try:
        from app.llm.providers.gemini import stream_chat

        async for tok in stream_chat(system=system, user=user_msg, model_hint=model_hint):
            yield tok
    except Exception as exc:
        logger.error("LLM stream error: %s", exc)
        yield f"[LLM error: {exc}]"
