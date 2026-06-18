"""Text embedding via bge-m3 on local Ollama."""

from __future__ import annotations

import logging

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

# Ollama endpoint for embeddings
OLLAMA_BASE_URL = getattr(settings, "ollama_base_url", "http://localhost:11434")
EMBED_DIM = 1024
BATCH_SIZE = 32
TIMEOUT_S = 60.0

# Track active backend (always ollama now)
_active_backend: str = "ollama"
_query_cache: dict[str, list[float]] = {}
_QUERY_CACHE_MAX = 512


async def embed(texts: list[str], model: str = "bge-m3") -> list[list[float]]:
    """
    Return dense embeddings using local Ollama (bge-m3).
    """
    if not texts:
        return []

    results: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        results.extend(await _call_ollama(batch, model))
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


async def _call_ollama(texts: list[str], model: str) -> list[list[float]]:
    url = f"{OLLAMA_BASE_URL}/api/embed"
    payload = {
        "model": model,
        "input": texts
    }
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["embeddings"]
        except httpx.TimeoutException as exc:
            from app.core.errors import EmbedderTimeoutError
            raise EmbedderTimeoutError(f"Ollama timeout after {TIMEOUT_S}s") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("Ollama HTTP error %s: %s", exc.response.status_code, exc.response.text)
            raise


def get_active_dim() -> int:
    """Return embedding dimension — always EMBED_DIM (1024)."""
    return EMBED_DIM
