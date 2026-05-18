"""
Batch ingestion: parse → chunk → embed → upsert to Qdrant.

Reads parsed JSON from ingestion/parsed/ (produced by unstructured_runner.py),
or can parse+embed in one pass from raw documents.

Collections:
  shared/vas   → kb_shared_vas
  shared/ifrs  → kb_shared_ifrs
  tenant/<id>  → tenant_<id>

Usage:
  # Parse first, then embed
  python ingestion/unstructured_runner.py --input ingestion/documents/shared/vas --output ingestion/parsed/shared/vas
  python ingestion/batch_embed.py --parsed ingestion/parsed/shared/vas --collection kb_shared_vas --scope shared

  # Or one-shot (parse + embed)
  python ingestion/batch_embed.py --docs ingestion/documents/shared/vas --collection kb_shared_vas --scope shared

  # Tenant ingestion
  python ingestion/batch_embed.py --docs ingestion/documents/tenant/dev-tenant --collection tenant_dev-tenant --scope tenant --tenant-id dev-tenant

  # Delete collection and re-ingest (clean slate)
  python ingestion/batch_embed.py --docs ingestion/documents/shared/vas --collection kb_shared_vas --scope shared --recreate
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

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
    import httpx
    payload = {"inputs": texts, "normalize": True}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{TEI_URL}/embed", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return data.get("embeddings", data.get("data", []))


async def _embed_gemini(texts: list[str]) -> list[list[float]]:
    """
    Gemini text-embedding-004 (dim=768).
    NOTE: dim differs from bge-m3 (1024). If mixing, use consistent model.
    Qdrant collection must be created with matching dim.
    """
    from google import genai
    api_key = GEMINI_API_KEY
    if not api_key:
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))
            from app.settings import settings
            api_key = settings.gemini_api_key
        except Exception:
            pass

    client = genai.Client(api_key=api_key)
    results: list[list[float]] = []
    # Gemini embedding API: one call per text (no batching in SDK yet)
    for text in texts:
        resp = await client.aio.models.embed_content(
            model="models/text-embedding-004",
            contents=text,
        )
        results.append(resp.embeddings[0].values)
    return results


# ---------------------------------------------------------------------------
# Qdrant helpers
# ---------------------------------------------------------------------------

def _get_qdrant():
    from qdrant_client import QdrantClient
    kwargs = {"url": QDRANT_URL}
    if QDRANT_API_KEY:
        kwargs["api_key"] = QDRANT_API_KEY
    return QdrantClient(**kwargs)


def ensure_collection(client, collection: str, dim: int, recreate: bool = False) -> None:
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
    sys.path.insert(0, str(Path(__file__).parent))
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
    # Import chunker from backend
    sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))
    from app.rag.chunker import chunk_document

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
        logger.info("%s → %d chunks", doc["filename"], len(chunks))
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            all_chunks_meta.append({
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
            })

    logger.info("total chunks to embed: %d", len(all_chunks_meta))

    if dry_run:
        print(f"[DRY RUN] Would upsert {len(all_chunks_meta)} chunks to {collection}")
        for m in all_chunks_meta[:3]:
            print(f"  {m['doc_id'][:8]}.. chunk[{m['chunk_index']}] {m['token_count']} tokens: {m['text_preview'][:80]}")
        return 0

    # Embed in batches
    texts = [m["text"] for m in all_chunks_meta]
    vectors: list[list[float]] = []
    for i in range(0, len(texts), 64):
        batch = texts[i : i + 64]
        logger.info("embedding batch %d/%d ...", i // 64 + 1, (len(texts) + 63) // 64)
        batch_vecs = await embed_texts(batch)
        vectors.extend(batch_vecs)

    # Detect actual dim from first vector
    actual_dim = len(vectors[0]) if vectors else EMBED_DIM
    embed_model = "bge-m3" if actual_dim == 1024 else "text-embedding-004"
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

    print(f"\nIngestion complete: {total} chunks → collection '{collection}'")
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
    parser.add_argument("--tei-url", default=None)

    args = parser.parse_args()

    global QDRANT_URL, TEI_URL
    if args.qdrant_url:
        QDRANT_URL = args.qdrant_url
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
