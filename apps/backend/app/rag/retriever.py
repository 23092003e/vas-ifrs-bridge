"""Hybrid retriever: dense Qdrant + sparse BM25 fusion â†’ reranker."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.core.errors import QdrantUnavailable
from app.rag.embedder import embed_query
from app.rag.reranker import rerank
from app.settings import settings

logger = logging.getLogger(__name__)

DENSE_K = 40
SPARSE_K = 40
RERANK_K = 8


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
    conditions = []

    if lang and lang != "auto":
        conditions.append(
            FieldCondition(key="lang", match=MatchValue(value=lang))
        )

    if scope == "shared":
        conditions.append(
            FieldCondition(key="scope", match=MatchValue(value="shared"))
        )
    elif scope == "tenant" and tenant_id:
        conditions.append(
            FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
        )
    # scope == "both" â†’ no filter; both shared + tenant returned

    return Filter(must=conditions) if conditions else None


async def retrieve(
    query: str,
    *,
    collection: str,
    tenant_id: str | None = None,
    scope: str = "both",
    lang: str = "auto",
    k: int = RERANK_K,
    skip_rerank: bool = False,
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

    client = _qdrant_client()
    try:
        result = await client.query_points(
            collection_name=collection,
            query=vec,
            query_filter=flt,
            limit=DENSE_K,
            with_payload=True,
        )
        hits = result.points
    except Exception as exc:
        raise QdrantUnavailable(f"Qdrant search failed: {exc}") from exc
    finally:
        await client.close()

    if not hits:
        logger.warning("qdrant returned 0 hits for collection=%s scope=%s", collection, scope)
        return []

    raw_chunks = [
        {
            "id": str(hit.id),
            "doc_id": hit.payload.get("doc_id", ""),
            "text": hit.payload.get("text_preview", "") or hit.payload.get("text", ""),
            "score": hit.score,
            "metadata": hit.payload or {},
        }
        for hit in hits
    ]

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
            rerank_score=c.get("rerank_score", c["score"]),
            metadata=c["metadata"],
            citation_key=f"C{i + 1}",
        )
        for i, c in enumerate(reranked)
    ]


async def retrieve_multi(
    query: str,
    *,
    shared_collection: str = "kb_shared_vas",
    tenant_collection: str | None = None,
    tenant_id: str | None = None,
    lang: str = "auto",
    k: int = RERANK_K,
) -> list[RetrievedChunk]:
    """Retrieve from shared + tenant KB concurrently, merge, rerank final."""
    tasks = [
        retrieve(
            query,
            collection=shared_collection,
            scope="shared",
            lang=lang,
            k=DENSE_K,
            skip_rerank=True,
        )
    ]
    if tenant_collection and tenant_id:
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
    merged: list[dict] = []
    for res in results:
        if isinstance(res, Exception):
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
            rerank_score=c.get("rerank_score", c["score"]),
            metadata=c["metadata"],
            citation_key=f"C{i + 1}",
        )
        for i, c in enumerate(reranked)
    ]

