"""
Batch ingestion: parse → chunk → embed → upsert to Qdrant.

Document layout:
  ingestion/raw/shared/vas/{standards,circulars,decisions,adoption}/
  ingestion/raw/shared/ifrs/{standards,ias,ifric,sic,framework,taxonomy}/
  ingestion/raw/tenant/<id>/{fs,audit,contracts,internal}/

Intermediate output:
  ingestion/processed/chunks/    ← chunked JSON (optional two-pass)
  ingestion/processed/embeddings/ ← cached embeddings (optional)

Collections:
  raw/shared/vas   → kb_shared_vas
  raw/shared/ifrs  → kb_shared_ifrs
  raw/tenant/<id>  → tenant_<id>

Usage (run from repo root with PYTHONPATH set):
  # One-shot (parse + embed)
  python ingestion/pipelines/embedders/batch_embed.py --docs ingestion/raw/shared/vas --collection kb_shared_vas --scope shared
  python ingestion/pipelines/embedders/batch_embed.py --docs ingestion/raw/shared/ifrs --collection kb_shared_ifrs --scope shared
  python ingestion/pipelines/embedders/batch_embed.py --docs ingestion/raw/tenant/dev-tenant --collection tenant_dev-tenant --scope tenant --tenant-id dev-tenant

  # From pre-parsed JSON
  python ingestion/pipelines/embedders/batch_embed.py --parsed ingestion/processed/chunks/vas --collection kb_shared_vas --scope shared

  # Clean slate
  python ingestion/pipelines/embedders/batch_embed.py --docs ingestion/raw/shared/vas --collection kb_shared_vas --scope shared --recreate

  # Or just use: .\\ingest.ps1  (from repo root)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import uuid
import warnings
from pathlib import Path
from typing import Optional

# Suppress Python 3.9 EOL warnings from google-auth (cosmetic only, no functional impact)
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

logger = logging.getLogger(__name__)

EMBED_DIM = 1024
BATCH_SIZE = 32   # upsert batch size (Qdrant)
TEI_URL = os.environ.get("TEI_URL", "http://localhost:8080")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


# ---------------------------------------------------------------------------
# Embedding — TEI first, Gemini fallback
# ---------------------------------------------------------------------------

async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Try TEI (bge-m3), fall back to Gemini text-embedding-004."""
    try:
        return await _embed_tei(texts)
    except Exception as exc:
        logger.warning("TEI unavailable (%s), falling back to Gemini embedding", exc)
        return await _embed_gemini(texts)


async def _embed_tei(texts: list[str]) -> list[list[float]]:
    # pyrefly: ignore [missing-import]
    import httpx
    payload = {"inputs": texts, "normalize": True}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{TEI_URL}/embed", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("embeddings", data.get("data", []))


GEMINI_EMBED_MODEL = "models/gemini-embedding-001"
GEMINI_EMBED_DIM = 3072


_GEMINI_RATE_DELAY = 1.5  # seconds between calls → ~40 RPM, safely under free-tier limit


async def _embed_gemini(texts: list[str]) -> list[list[float]]:
    """Gemini gemini-embedding-001 (dim=3072). Used when TEI unavailable."""
    import asyncio as _aio
    # pyrefly: ignore [missing-import]
    from google import genai
    # pyrefly: ignore [missing-import]
    from google.genai.errors import ClientError

    api_key = GEMINI_API_KEY
    if not api_key:
        try:
            repo_root = Path(__file__).parent.parent.parent.parent
            sys.path.insert(0, str(repo_root / "apps" / "backend"))
            # pyrefly: ignore [missing-import]
            from app.settings import settings
            api_key = settings.gemini_api_key
        except Exception:
            pass

    client = genai.Client(api_key=api_key)
    results: list[list[float]] = []
    total = len(texts)
    for i, text in enumerate(texts):
        for attempt in range(8):
            try:
                resp = await client.aio.models.embed_content(
                    model=GEMINI_EMBED_MODEL,
                    contents=text,
                )
                results.append(list(resp.embeddings[0].values))
                if i < total - 1:
                    await _aio.sleep(_GEMINI_RATE_DELAY)
                if (i + 1) % 10 == 0:
                    logger.info("  gemini embed: %d/%d chunks", i + 1, total)
                break
            except (ClientError, Exception) as exc:
                is_rate_limit = (
                    (isinstance(exc, ClientError) and exc.code == 429)
                    or "429" in str(exc)
                    or "RESOURCE_EXHAUSTED" in str(exc)
                )
                if is_rate_limit:
                    wait = min(30 * (attempt + 1), 120)  # 30, 60, 90, 120s
                    logger.warning("rate limit chunk %d/%d, retry %d/%d, waiting %ds...", i + 1, total, attempt + 1, 8, wait)
                    await _aio.sleep(wait)
                else:
                    raise
        else:
            raise RuntimeError(f"Gemini embedding failed after 8 retries for chunk {i}")
    return results


# ---------------------------------------------------------------------------
# Qdrant helpers
# ---------------------------------------------------------------------------

def _get_qdrant():
    # pyrefly: ignore [missing-import]
    from qdrant_client import QdrantClient
    if QDRANT_URL == ":memory:":
        return QdrantClient(":memory:")
    kwargs = {"url": QDRANT_URL, "check_compatibility": False}
    if QDRANT_API_KEY:
        kwargs["api_key"] = QDRANT_API_KEY
    return QdrantClient(**kwargs)


def ensure_collection(client, collection: str, dim: int, recreate: bool = False) -> None:
    # pyrefly: ignore [missing-import]
    from qdrant_client.models import Distance, VectorParams

    exists = client.collection_exists(collection)
    if exists and recreate:
        logger.info("deleting collection %s", collection)
        client.delete_collection(collection)
        exists = False

    if not exists:
        logger.info("creating collection %s (dim=%d)", collection, dim)
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
    else:
        logger.info("collection %s already exists", collection)


def upsert_batch(client, collection: str, points: list[dict]) -> None:
    # pyrefly: ignore [missing-import]
    from qdrant_client.models import PointStruct
    structs = [
        PointStruct(
            id=p["id"],
            vector=p["vector"],
            payload={k: v for k, v in p.items() if k not in ("id", "vector")},
        )
        for p in points
    ]
    client.upsert(collection_name=collection, points=structs)


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def load_parsed_docs(parsed_dir: Path) -> list[dict]:
    docs = []
    for fp in sorted(parsed_dir.glob("*.json")):
        try:
            docs.append(json.loads(fp.read_text(encoding="utf-8")))
        except Exception as exc:
            logger.error("failed to load %s: %s", fp.name, exc)
    return docs


def load_raw_docs(docs_dir: Path) -> list[dict]:
    """Parse raw documents inline (no intermediate JSON)."""
    # parsers/ is a sibling of embedders/ under pipelines/
    sys.path.insert(0, str(Path(__file__).parent.parent / "parsers"))
    # pyrefly: ignore [missing-import]
    from unstructured_runner import parse_document, _PARSERS
    docs = []
    for fp in sorted(docs_dir.rglob("*")):
        if fp.suffix.lower() not in _PARSERS:
            continue
        try:
            doc = parse_document(fp)
            docs.append(doc)
            logger.info("parsed: %s (%d chars)", fp.name, len(doc["text"]))
        except Exception as exc:
            logger.error("parse failed %s: %s", fp.name, exc)
    return docs


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

async def ingest(
    docs: list[dict],
    *,
    collection: str,
    scope: str,
    tenant_id: Optional[str] = None,
    recreate: bool = False,
    dry_run: bool = False,
) -> int:
    """Chunk, embed, and upsert all docs. Returns total chunks upserted."""
    # Import chunker from backend (repo_root/apps/backend)
    # File lives at ingestion/pipelines/embedders/batch_embed.py → 3 levels up = repo root
    repo_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(repo_root / "apps" / "backend"))
    # pyrefly: ignore [missing-import]
    from app.rag.chunker import chunk_document
    # pyrefly: ignore [missing-import]
    from app.ingestion.enrichment import enrich

    # First pass: collect all chunks to determine embedding dim
    all_chunks_meta: list[dict] = []  # holds doc metadata + chunk
    for doc in docs:
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, doc["source_path"]))
        chunks = chunk_document(
            doc["text"],
            section_path="",
            heading="",
            lang=doc.get("lang", "bi"),
        )
        logger.info("%s -> %d chunks", doc["filename"], len(chunks))
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            chunk_payload = {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "text_preview": chunk.text[:200],
                "section_path": chunk.section_path,
                "heading": chunk.heading,
                "lang": chunk.lang,
                "scope": scope,
                "tenant_id": tenant_id,
                "standard_code": doc.get("standard_code"),
                "source_uri": doc["source_path"],
                "embedding_model": "unknown",
                "token_count": chunk.token_count,
                "ingested_at": "2026-05-18T00:00:00Z",
            }
            chunk_payload = enrich(chunk_payload)
            all_chunks_meta.append(chunk_payload)

    logger.info("total chunks to embed: %d", len(all_chunks_meta))

    if dry_run:
        print(f"[DRY RUN] Would upsert {len(all_chunks_meta)} chunks to {collection}")
        for m in all_chunks_meta[:3]:
            print(f"  {m['doc_id'][:8]}.. chunk[{m['chunk_index']}] {m['token_count']} tokens: {m['text_preview'][:80]}")
        return 0

    # Embed in batches
    texts = [m["text"] for m in all_chunks_meta]
    vectors: list[list[float]] = []
    # TEI: large batches OK. Gemini: small batches to avoid front-loading RPM.
    # We don't know backend yet — start with batch=10; TEI will handle any size, Gemini stays safe.
    gemini_batch = 10
    tei_batch = 64
    batch_size = tei_batch  # will shrink to gemini_batch after first TEI failure detected
    _tei_failed = False
    i = 0
    batch_num = 0
    while i < len(texts):
        if _tei_failed:
            batch_size = gemini_batch
        batch = texts[i : i + batch_size]
        batch_num += 1
        total_batches = (len(texts) + batch_size - 1) // batch_size
        logger.info("embedding batch %d/%d (~%d remaining) ...", batch_num, total_batches, len(texts) - i)
        try:
            batch_vecs = await _embed_tei(batch)
        except Exception as exc:
            if not _tei_failed:
                logger.warning("TEI unavailable (%s), switching to Gemini (slower)", exc)
                _tei_failed = True
                batch_size = gemini_batch
                batch = texts[i : i + batch_size]
            batch_vecs = await _embed_gemini(batch)
        vectors.extend(batch_vecs)
        i += len(batch)

    # Detect actual dim from first vector
    actual_dim = len(vectors[0]) if vectors else EMBED_DIM
    if actual_dim == 1024:
        embed_model = "bge-m3"
    elif actual_dim == 3072:
        embed_model = "gemini-embedding-001"
    else:
        embed_model = f"unknown-dim{actual_dim}"
    logger.info("embedding dim: %d (%s)", actual_dim, embed_model)
    for m in all_chunks_meta:
        m["embedding_model"] = embed_model

    # Setup Qdrant
    qdrant = _get_qdrant()
    ensure_collection(qdrant, collection, actual_dim, recreate=recreate)

    # Upsert in batches
    total = 0
    for i in range(0, len(all_chunks_meta), BATCH_SIZE):
        batch_meta = all_chunks_meta[i : i + BATCH_SIZE]
        batch_vecs = vectors[i : i + BATCH_SIZE]
        points = []
        for meta, vec in zip(batch_meta, batch_vecs):
            # Qdrant needs uint64 or UUID string ID
            point_id = str(uuid.UUID(meta["chunk_id"]))
            points.append({**meta, "id": point_id, "vector": vec})
        upsert_batch(qdrant, collection, points)
        total += len(points)
        logger.info("upserted %d/%d chunks", total, len(all_chunks_meta))

    print(f"\nIngestion complete: {total} chunks -> collection '{collection}'")
    return total


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(description="VAS-IFRS batch ingestion")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--docs", help="Directory of raw documents (PDF/DOCX/XLSX/TXT)")
    src.add_argument("--parsed", help="Directory of pre-parsed JSON files")

    parser.add_argument("--collection", required=True, help="Qdrant collection name (e.g. kb_shared_vas)")
    parser.add_argument("--scope", choices=["shared", "tenant"], default="shared")
    parser.add_argument("--tenant-id", default=None)
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate collection")
    parser.add_argument("--dry-run", action="store_true", help="Parse+chunk only, skip embed+upsert")
    parser.add_argument("--qdrant-url", default=None)
    parser.add_argument("--qdrant-memory", action="store_true", help="Use in-memory Qdrant (testing)")
    parser.add_argument("--tei-url", default=None)

    args = parser.parse_args()

    global QDRANT_URL, TEI_URL
    if args.qdrant_url:
        QDRANT_URL = args.qdrant_url
    if args.qdrant_memory:
        QDRANT_URL = ":memory:"
    if args.tei_url:
        TEI_URL = args.tei_url

    # Load docs
    if args.docs:
        docs = load_raw_docs(Path(args.docs))
    else:
        docs = load_parsed_docs(Path(args.parsed))

    if not docs:
        print("No documents found. Check --docs or --parsed path.")
        sys.exit(1)

    print(f"Loaded {len(docs)} documents")

    total = asyncio.run(ingest(
        docs,
        collection=args.collection,
        scope=args.scope,
        tenant_id=args.tenant_id,
        recreate=args.recreate,
        dry_run=args.dry_run,
    ))

    sys.exit(0 if total >= 0 else 1)


if __name__ == "__main__":
    main()
