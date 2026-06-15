"""Cross-encoder reranker via bge-reranker-v2-m3 on TEI."""

from __future__ import annotations

import logging

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

TEI_URL = getattr(settings, "tei_url", "http://localhost:8080")
TIMEOUT_S = 15.0
MIN_SCORE = 0.35
LOW_RECALL_SCORE = 0.20


async def rerank(
    query: str,
    chunks: list[dict],
    top_k: int = 8,
    min_score: float = MIN_SCORE,
) -> list[dict]:
    """
    Rerank chunks using cross-encoder; fall back to identity sort if TEI unavailable.
    Returns at most top_k chunks with score >= min_score.
    Relaxes to LOW_RECALL_SCORE if fewer than 3 pass the default threshold.
    """
    if not chunks:
        return []

    scores = await _call_reranker(query, [c["text"] for c in chunks])

    if not scores:
        # TEI unavailable — use dense scores already on chunks
        ranked = sorted(chunks, key=lambda c: c.get("score", 0.0), reverse=True)
        return ranked[:top_k]

    scored = sorted(zip(scores, chunks, strict=True), key=lambda x: x[0], reverse=True)

    above = [(s, c) for s, c in scored if s >= min_score]
    if len(above) < 3:
        # Relax threshold — log degraded retrieval
        above = [(s, c) for s, c in scored if s >= LOW_RECALL_SCORE]
        if len(above) < len(scored):
            logger.warning(
                "low_recall: only %d chunks above relaxed %.2f", len(above), LOW_RECALL_SCORE
            )

    result = [{**c, "rerank_score": float(s)} for s, c in above[:top_k]]
    return result


async def _call_reranker(query: str, texts: list[str]) -> list[float]:
    """Return per-text scores from TEI reranker endpoint."""
    payload = {"query": query, "texts": texts, "model": "bge-reranker-v2-m3"}
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        try:
            resp = await client.post(f"{TEI_URL}/rerank", json=payload)
            resp.raise_for_status()
            data = resp.json()
            # TEI returns list of {"index": N, "score": F} or flat list
            if isinstance(data, list) and data and isinstance(data[0], dict):
                ordered = sorted(data, key=lambda x: x["index"])
                return [item["score"] for item in ordered]
            return [float(x) for x in data]
        except httpx.TimeoutException:
            logger.warning("reranker timeout — using dense scores")
            return []
        except Exception as exc:
            logger.warning("reranker unavailable: %s", exc)
            return []
