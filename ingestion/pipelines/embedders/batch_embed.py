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
# Load settings from app.settings (loads .env automatically)
try:
    _repo_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(_repo_root / "apps" / "backend"))
    # pyrefly: ignore [missing-import]
    from app.settings import settings
    QDRANT_URL = os.environ.get("QDRANT_URL", settings.qdrant_url)
    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", settings.qdrant_api_key)
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", settings.ollama_base_url)
except Exception:
    QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


# ---------------------------------------------------------------------------
# Embedding — Ollama (bge-m3)
# ---------------------------------------------------------------------------

async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts using local Ollama bge-m3 model."""
    # pyrefly: ignore [missing-import]
    import httpx
    url = f"{OLLAMA_BASE_URL}/api/embed"
    payload = {
        "model": "bge-m3",
        "input": texts
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["embeddings"]


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
        # If the doc is a list, it's already pre-chunked
        if isinstance(doc, list):
            all_chunks_meta.extend(doc)
            continue

        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, doc["source_path"]))
        
        # If the document has structured sections (from parser), chunk them individually
        # to preserve section boundaries and correctly map headings/paths.
        if doc.get("sections"):
            chunks = []
            chunk_idx = 0
            for sec in doc["sections"]:
                sec_chunks = chunk_document(
                    sec["text"],
                    section_path=sec["heading"],
                    heading=sec["heading"],
                    lang=doc.get("lang", "bi"),
                )
                for c in sec_chunks:
                    c.chunk_index = chunk_idx
                    chunks.append(c)
                    chunk_idx += 1
        else:
            chunks = chunk_document(
                doc["text"],
                section_path="",
                heading="",
                lang=doc.get("lang", "bi"),
            )
            
        logger.info("%s -> %d chunks", doc["filename"], len(chunks))
        doc_chunks_meta = []
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
            doc_chunks_meta.append(chunk_payload)
            all_chunks_meta.append(chunk_payload)

        # Cache the chunks as a JSON file if not running a dry run
        if not dry_run and doc_chunks_meta:
            doc_stem = Path(doc["filename"]).stem
            processed_dir = repo_root / "ingestion" / "processed" / "chunks" / collection
            processed_dir.mkdir(parents=True, exist_ok=True)
            output_file = processed_dir / f"{doc_stem}_chunks.json"
            try:
                output_file.write_text(json.dumps(doc_chunks_meta, ensure_ascii=False, indent=2), encoding="utf-8")
                logger.info("Saved %d chunks to %s", len(doc_chunks_meta), output_file.relative_to(repo_root))
            except Exception as exc:
                logger.error("Failed to save chunks to %s: %s", output_file, exc)

    logger.info("total chunks to embed: %d", len(all_chunks_meta))

    if dry_run:
        print(f"[DRY RUN] Would upsert {len(all_chunks_meta)} chunks to {collection}")
        for m in all_chunks_meta[:3]:
            print(f"  {m['doc_id'][:8]}.. chunk[{m['chunk_index']}] {m['token_count']} tokens: {m['text_preview'][:80]}")
        return 0

    # Embed in batches
    texts = [m["text"] for m in all_chunks_meta]
    vectors: list[list[float]] = []
    batch_size = 32
    i = 0
    batch_num = 0
    total_batches = (len(texts) + batch_size - 1) // batch_size
    while i < len(texts):
        batch = texts[i : i + batch_size]
        batch_num += 1
        logger.info("embedding batch %d/%d (~%d remaining) ...", batch_num, total_batches, len(texts) - i)
        batch_vecs = await embed_texts(batch)
        vectors.extend(batch_vecs)
        i += len(batch)

    # Detect actual dim from first vector
    actual_dim = len(vectors[0]) if vectors else EMBED_DIM
    embed_model = "bge-m3"
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
    parser.add_argument("--ollama-url", default=None)

    args = parser.parse_args()

    global QDRANT_URL, OLLAMA_BASE_URL
    if args.qdrant_url:
        QDRANT_URL = args.qdrant_url
    if args.qdrant_memory:
        QDRANT_URL = ":memory:"
    if args.ollama_url:
        OLLAMA_BASE_URL = args.ollama_url

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
