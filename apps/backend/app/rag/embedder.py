"""Text embedding via bge-m3 on local Ollama."""

from __future__ import annotations

import asyncio
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

# Sparse model cache
_sparse_model = None

def _get_sparse_model():
    global _sparse_model
    if _sparse_model is None:
        from fastembed import SparseTextEmbedding
        _sparse_model = SparseTextEmbedding("Qdrant/bm25")
        logger.info("BM25 sparse model loaded in embedder")
    return _sparse_model

async def embed_sparse(texts: list[str]) -> list:
    """Return sparse embeddings (BM25) using FastEmbed, run in a background thread."""
    if not texts:
        return []
    model = _get_sparse_model()
    # model.embed returns a generator, we must consume it in the thread
    # list() consumes the generator and yields a list of SparseEmbedding objects
    return await asyncio.to_thread(lambda: list(model.embed(texts)))



async def embed(texts: list[str], model: str = "bge-m3") -> list[list[float]]:
    """
    Return dense embeddings using local Ollama (bge-m3).
    """
    if not texts:
        return []

    results: list[list[float]] = []
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            results.extend(await _call_ollama(client, batch, model))
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


async def _call_ollama(client: httpx.AsyncClient, texts: list[str], model: str, retries: int = 3) -> list[list[float]]:
    url = f"{OLLAMA_BASE_URL}/api/embed"
    payload = {
        "model": model,
        "input": texts
    }
    
    for attempt in range(1, retries + 1):
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["embeddings"]
        except httpx.TimeoutException as exc:
            if attempt == retries:
                from app.core.errors import EmbedderTimeoutError
                raise EmbedderTimeoutError(f"Ollama timeout after {TIMEOUT_S}s") from exc
            logger.warning("Ollama timeout attempt %d failed. Retrying in 2s...", attempt)
            await asyncio.sleep(2.0)
        except httpx.HTTPStatusError as exc:
            if attempt == retries:
                logger.error("Ollama HTTP error %s: %s", exc.response.status_code, exc.response.text)
                raise
            logger.warning("Ollama HTTP error attempt %d failed. Retrying in 2s...", attempt)
            await asyncio.sleep(2.0)
        except httpx.RequestError as exc:
            if attempt == retries:
                logger.error("Ollama connection error: %s", exc)
                raise
            logger.warning("Ollama connection attempt %d failed. Retrying in 2s...", attempt)
            await asyncio.sleep(2.0)

    # Fallback to satisfy type checker in case loop exits without returning
    raise RuntimeError("Ollama embedding failed unexpectedly.")


def get_active_dim() -> int:
    """Return embedding dimension — always EMBED_DIM (1024)."""
    return EMBED_DIM
