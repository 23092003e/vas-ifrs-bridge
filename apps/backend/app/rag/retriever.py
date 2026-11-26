"""Hybrid retriever: dense Qdrant + sparse BM25 fusion â†’ reranker."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from dataclasses import dataclass

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Condition, FieldCondition, Filter, MatchAny, MatchValue

from app.core.errors import QdrantUnavailableError
from app.rag.embedder import embed_query
from app.rag.reranker import rerank
from app.settings import settings

logger = logging.getLogger(__name__)

DENSE_K = 40
SPARSE_K = 40
RERANK_K = 8

# Lazy singleton for BM25 sparse model — loaded once, reused across all requests.
_sparse_model = None


def _get_sparse_model():
    """Return a cached SparseTextEmbedding instance (loaded once on first call)."""
    global _sparse_model
    if _sparse_model is None:
        from fastembed import SparseTextEmbedding
        _sparse_model = SparseTextEmbedding("Qdrant/bm25")
        logger.info("BM25 sparse model loaded (singleton)")
    return _sparse_model


@dataclass
class RetrievedChunk:
    id: str
    doc_id: str
    text: str
    score: float
    rerank_score: float
    metadata: dict
    citation_key: str = ""


def _qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
        check_compatibility=False,
    )


def _build_filter(
    *,
    lang: str | None,
    scope: str,
    tenant_id: str | None,
) -> Filter | None:
    conditions: list[Condition] = []

    if scope not in {"shared", "tenant", "both"}:
        raise ValueError(f"Invalid retrieval scope: {scope}")
    if scope == "tenant" and not tenant_id:
        raise ValueError("tenant_id is required for tenant retrieval scope")

    # Disable language filtering to allow cross-lingual retrieval (e.g., retrieving
    # English IFRS documents for Vietnamese user queries). Semantic matching is handled
    # by the multilingual embedding model, and language output is managed by the LLM.

    if scope == "shared":
        conditions.append(FieldCondition(key="scope", match=MatchValue(value="shared")))
    elif scope == "tenant" and tenant_id:
        conditions.append(FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)))
    elif scope == "both" and tenant_id:
        # Include shared data OR data belonging to the current tenant.
        # Use should (OR) with min_should to prevent cross-tenant leakage.
        from qdrant_client.models import Filter as QFilter
        tenant_filter = QFilter(
            should=[
                FieldCondition(key="scope", match=MatchValue(value="shared")),
                FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
            ]
        )
        if conditions:
            # Combine lang filter (must) with scope filter (should)
            return Filter(must=conditions + [tenant_filter])
        return tenant_filter
    # scope == "both" without tenant_id → only shared data for safety
    elif scope == "both" and not tenant_id:
        conditions.append(FieldCondition(key="scope", match=MatchValue(value="shared")))

    return Filter(must=conditions) if conditions else None


async def _dense_only_search(client, collection: str, vec, flt) -> list:
    """Fallback: dense-only search when sparse index is unavailable."""
    result = await client.query_points(
        collection_name=collection,
        query=vec,
        query_filter=flt,
        limit=DENSE_K,
        with_payload=True,
    )
    return result.points


async def _hybrid_search(client, collection: str, vec, query: str, flt) -> list:
    """
    Attempt hybrid Dense+BM25 RRF search.
    Falls back to dense-only if the collection lacks a "bm25" sparse index.
    """
    from qdrant_client.models import Fusion, FusionQuery, Prefetch, SparseVector

    # Generate sparse query vector using cached BM25 model
    sparse_model = _get_sparse_model()
    # query_embed is synchronous and CPU-bound, run it in a thread to avoid blocking the event loop
    sparse_gen = await asyncio.to_thread(lambda: list(sparse_model.query_embed(query)))
    sparse_vec = sparse_gen[0] if sparse_gen else None

    if not sparse_vec:
        logger.warning("BM25 sparse embedding returned empty — falling back to dense-only")
        return await _dense_only_search(client, collection, vec, flt)

    sp_query = SparseVector(
        indices=sparse_vec.indices.tolist(),
        values=sparse_vec.values.tolist(),
    )

    try:
        result = await client.query_points(
            collection_name=collection,
            prefetch=[
                Prefetch(query=vec, limit=DENSE_K, filter=flt),
                Prefetch(query=sp_query, using="bm25", limit=SPARSE_K, filter=flt),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=DENSE_K,
            with_payload=True,
        )
        return result.points
    except Exception as exc:
        error_msg = str(exc)
        if "bm25" in error_msg.lower() or "not existing vector name" in error_msg.lower():
            logger.warning(
                "Collection '%s' lacks sparse index 'bm25' — falling back to dense-only: %s",
                collection,
                exc,
            )
            return await _dense_only_search(client, collection, vec, flt)
        raise

async def retrieve(
    query: str,
    *,
    collection: str,
    tenant_id: str | None = None,
    scope: str = "both",
    lang: str = "auto",
    k: int = RERANK_K,
    skip_rerank: bool = False,
    standard_codes: tuple[str, ...] = (),
) -> list[RetrievedChunk]:
    """
    Full retrieval pipeline:
      1. embed query
      2. dense search in Qdrant (top DENSE_K)
      3. rerank â†’ top k
    Returns list of RetrievedChunk with citation_key assigned.
    """
    vec = await embed_query(query)
    flt = _build_filter(lang=lang, scope=scope, tenant_id=tenant_id)
    if standard_codes:
        must: list[Condition] = [FieldCondition(
            key="standard_code", match=MatchAny(any=list(standard_codes))
        )]
        if flt is not None:
            must.append(flt)
        flt = Filter(must=must)

    client = _qdrant_client()
    try:
        hits = await _hybrid_search(client, collection, vec, query, flt)
    except Exception as exc:
        raise QdrantUnavailableError(f"Qdrant search failed: {exc}") from exc
    finally:
        await client.close()

    if not hits:
        logger.warning("qdrant returned 0 hits for collection=%s scope=%s", collection, scope)
        return []

    raw_chunks = []
    for hit in hits:
        payload = hit.payload or {}
        std = payload.get("standard_code") or "Unknown"
        hd = payload.get("heading", "")
        t = payload.get("text") or payload.get("text_preview", "")
        context_text = f"[{std}] {hd}\n{t}".strip()
        raw_chunks.append({
            "id": str(hit.id),
            "doc_id": payload.get("doc_id", ""),
            "text": context_text,
            "score": hit.score,
            "metadata": payload,
        })

    if skip_rerank:
        reranked = raw_chunks[:k]
    else:
        reranked = await rerank(query, raw_chunks, top_k=k)

    return [
        RetrievedChunk(
            id=c["id"],
            doc_id=c["doc_id"],
            text=c["text"],
            score=c["score"],
            rerank_score=c["rerank_score"] if c.get("rerank_score") is not None else c["score"],
            metadata=c["metadata"],
            citation_key=f"C{i + 1}",
        )
        for i, c in enumerate(reranked)
    ]


async def retrieve_multi(
    query: str,
    *,
    tenant_collection: str | None = None,
    tenant_id: str | None = None,
    scope: str = "both",
    lang: str = "auto",
    k: int = RERANK_K,
    require_available: bool = False,
) -> list[RetrievedChunk]:
    """Retrieve from mappings, standards (vas, ifrs), guidance and tenant KB concurrently, merge, rerank final."""
    if scope not in {"shared", "tenant", "both"}:
        raise ValueError(f"Invalid retrieval scope: {scope}")
    if scope == "tenant" and (not tenant_collection or not tenant_id):
        raise ValueError("tenant_collection and tenant_id are required for tenant scope")

    tasks: list[Awaitable[list[RetrievedChunk]]] = []
    if scope in {"shared", "both"}:
        tasks.extend(
            retrieve(
                query,
                collection=collection,
                scope="shared",
                lang=lang,
                k=DENSE_K,
                skip_rerank=True,
            )
            for collection in (
                "kb_shared_mapping",
                "kb_shared_vas",
                "kb_shared_ifrs",
                "kb_shared_guidance",
            )
        )
    if scope in {"tenant", "both"} and tenant_collection and tenant_id:
        tasks.append(
            retrieve(
                query,
                collection=tenant_collection,
                tenant_id=tenant_id,
                scope="tenant",
                lang=lang,
                k=DENSE_K,
                skip_rerank=True,
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)
    if require_available and results and all(isinstance(res, BaseException) for res in results):
        raise QdrantUnavailableError("All knowledge retrieval requests failed")

    merged: list[dict] = []
    for res in results:
        if isinstance(res, BaseException):
            logger.warning("retrieval partial failure: %s", res)
            continue
        merged.extend(
            {
                "id": c.id,
                "doc_id": c.doc_id,
                "text": c.text,
                "score": c.score,
                "rerank_score": c.rerank_score,
                "metadata": c.metadata,
            }
            for c in res
        )

    reranked = await rerank(query, merged, top_k=k)
    return [
        RetrievedChunk(
            id=c["id"],
            doc_id=c["doc_id"],
            text=c["text"],
            score=c["score"],
            rerank_score=c["rerank_score"] if c.get("rerank_score") is not None else c["score"],
            metadata=c["metadata"],
            citation_key=f"C{i + 1}",
        )
        for i, c in enumerate(reranked)
    ]
