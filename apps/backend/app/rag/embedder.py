"""Text embedding via bge-m3 (TEI) with Gemini text-embedding-004 fallback."""
from __future__ import annotations

import logging
import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

# TEI endpoint is co-located with Ollama node; override via env
TEI_URL = getattr(settings, "tei_url", "http://localhost:8080")
EMBED_DIM = 1024
EMBED_DIM_GEMINI = 3072  # gemini-embedding-001 dimension
BATCH_SIZE = 64
TIMEOUT_S = 30.0

# Track which backend is active so retriever can use correct dim
_active_backend: str = "tei"  # "tei" | "gemini"
_query_cache: dict[str, list[float]] = {}
_QUERY_CACHE_MAX = 512


async def embed(texts: list[str], model: str = "bge-m3") -> list[list[float]]:
    """
    Return dense embeddings. TEI (bge-m3) first, Gemini text-embedding-004 fallback.
    Falls back to chunked serial requests if batch > BATCH_SIZE.
    """
    global _active_backend
    if not texts:
        return []

    results: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        try:
            results.extend(await _call_tei(batch, model))
            _active_backend = "tei"
        except Exception as exc:
            logger.warning("TEI unavailable, using Gemini embedding fallback: %s", exc)
            results.extend(await _call_gemini(batch))
            _active_backend = "gemini"
    return results


async def embed_query(query: str) -> list[float]:
    """Single-query embed with in-process dict cache (max 512 entries)."""
    if query in _query_cache:
        return _query_cache[query]
    vecs = await embed([query])
    vec = vecs[0]
    if len(_query_cache) >= _QUERY_CACHE_MAX:
        _query_cache.pop(next(iter(_query_cache)))
    _query_cache[query] = vec
    return vec


async def _call_tei(texts: list[str], model: str) -> list[list[float]]:
    payload = {"inputs": texts, "model": model, "normalize": True}
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        try:
            resp = await client.post(f"{TEI_URL}/embed", json=payload)
            resp.raise_for_status()
            data = resp.json()
            # TEI returns {"embeddings": [[...]]} or list directly
            if isinstance(data, list):
                return data
            return data.get("embeddings", data.get("data", []))
        except httpx.TimeoutException as exc:
            from app.core.errors import EmbedderTimeout
            raise EmbedderTimeout(f"TEI timeout after {TIMEOUT_S}s") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("TEI HTTP error %s: %s", exc.response.status_code, exc.response.text)
            raise


async def _call_gemini(texts: list[str]) -> list[list[float]]:
    """Fallback: Gemini gemini-embedding-001 (dim=3072)."""
    from google import genai
    client = genai.Client(api_key=settings.gemini_api_key)
    results: list[list[float]] = []
    for text in texts:
        resp = await client.aio.models.embed_content(
            model="models/gemini-embedding-001",
            contents=text,
        )
        results.append(list(resp.embeddings[0].values))
    return results


def get_active_dim() -> int:
    """Return embedding dimension of currently active backend."""
    return EMBED_DIM_GEMINI if _active_backend == "gemini" else EMBED_DIM
