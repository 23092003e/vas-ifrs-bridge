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
  python ingestion/pipelines/embedders/batch_embed.py --docs ingestion/raw/tenant/00000000-0000-4000-8000-000000000001 --collection tenant_00000000-0000-4000-8000-000000000001 --scope tenant --tenant-id 00000000-0000-4000-8000-000000000001

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
from datetime import UTC, datetime
from pathlib import Path

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
except ImportError:
    QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


# ---------------------------------------------------------------------------
# Embedding — Ollama (bge-m3) and FastEmbed (BM25)
# ---------------------------------------------------------------------------

# pyrefly: ignore [missing-import]
import httpx
from fastembed import SparseTextEmbedding

OLLAMA_CONCURRENCY = int(os.environ.get("OLLAMA_CONCURRENCY", "1"))
OLLAMA_SEMAPHORE = asyncio.Semaphore(OLLAMA_CONCURRENCY)

async def embed_batch_with_retry(
    client: httpx.AsyncClient, 
    texts: list[str], 
    model: str = "bge-m3", 
    retries: int = 3
) -> list[list[float]]:
    """Embed texts using local Ollama bge-m3 model with retry logic and semaphore."""
    url = f"{OLLAMA_BASE_URL}/api/embed"
    payload = {
        "model": model,
        "input": texts
    }
    
    async with OLLAMA_SEMAPHORE:
        for attempt in range(1, retries + 1):
            try:
                resp = await client.post(url, json=payload, timeout=600.0)
                resp.raise_for_status()
                data = resp.json()
                return data["embeddings"]
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                if attempt == retries:
                    logger.error("Failed to embed batch after %d attempts", retries)
                    raise
                logger.warning("Embedding attempt %d failed: %s. Retrying in 2s...", attempt, exc)
                await asyncio.sleep(2.0)


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
        
        # Configure both dense and sparse vectors
        from qdrant_client.models import SparseVectorParams
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            sparse_vectors_config={
                "bm25": SparseVectorParams(
                    modifier=None,
                )
            }
        )
    else:
        logger.info("collection %s already exists", collection)


def upsert_batch(client, collection: str, points: list[dict]) -> None:
    # pyrefly: ignore [missing-import]
    from qdrant_client.models import PointStruct
    structs = []
    for p in points:
        vector = p["vector"]
        if "sparse_vector" in p:
            # Multi-vector format: dense is default name "", sparse is named
            vector = {
                "": p["vector"],
                "bm25": p["sparse_vector"]
            }
        
        structs.append(
            PointStruct(
                id=p["id"],
                vector=vector,
                payload={k: v for k, v in p.items() if k not in ("id", "vector", "sparse_vector")},
            )
        )
    client.upsert(collection_name=collection, points=structs)


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def load_parsed_docs(parsed_dir: Path) -> list[dict]:
    docs = []
    errors: list[tuple[Path, Exception]] = []
    for fp in sorted(parsed_dir.rglob("*.json")):
        try:
            docs.append(json.loads(fp.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("failed to load %s: %s", fp.name, exc)
            errors.append((fp, exc))
    if errors:
        count = len(errors)
        raise RuntimeError(
            f"failed to load {count} parsed document{'s' if count != 1 else ''}"
        ) from errors[0][1]
    return docs


def load_raw_docs(docs_dir: Path) -> list[dict]:
    """Parse raw documents inline (no intermediate JSON)."""
    # parsers/ is a sibling of embedders/ under pipelines/
    sys.path.insert(0, str(Path(__file__).parent.parent / "parsers"))
    # pyrefly: ignore [missing-import]
    from unstructured_runner import _PARSERS, parse_document
    docs = []
    errors: list[tuple[Path, Exception]] = []
    for fp in sorted(docs_dir.rglob("*")):
        if fp.suffix.lower() not in _PARSERS:
            continue
        try:
            doc = parse_document(fp)
            docs.append(doc)
            logger.info("parsed: %s (%d chars)", fp.name, len(doc["text"]))
        except Exception as exc:  # noqa: BLE001
            logger.error("parse failed %s: %s", fp.name, exc)
            errors.append((fp, exc))
    if errors:
        count = len(errors)
        raise RuntimeError(
            f"failed to parse {count} raw document{'s' if count != 1 else ''}"
        ) from errors[0][1]
    return docs


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

async def ingest(
    docs: list[dict],
    *,
    collection: str,
    scope: str,
    tenant_id: str | None = None,
    recreate: bool = False,
    dry_run: bool = False,
) -> int:
    """Chunk, embed, and upsert all docs. Returns total chunks upserted."""
    if scope not in {"shared", "tenant"}:
        raise ValueError("scope must be either 'shared' or 'tenant'")
    if scope == "tenant" and not tenant_id:
        raise ValueError("tenant_id is required for tenant-scoped ingestion")

    # Import chunker from backend (repo_root/apps/backend)
    # File lives at ingestion/pipelines/embedders/batch_embed.py → 3 levels up = repo root
    repo_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(repo_root / "apps" / "backend"))
    # pyrefly: ignore [missing-import]
    from app.ingestion.enrichment import enrich

    # pyrefly: ignore [missing-import]
    from app.rag.chunker import chunk_document

    # First pass: collect all chunks to determine embedding dim
    all_chunks_meta: list[dict] = []  # holds doc metadata + chunk
    ingested_at = datetime.now(UTC).isoformat()
    for doc in docs:
        # If the doc is a list, it's already pre-chunked
        if isinstance(doc, list):
            all_chunks_meta.extend(doc)
            continue

        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, doc["source_path"]))
        
        # Pre-calculate global standard_code for the document
        import re
        full_sample_text = (doc["filename"] + " " + doc.get("text", ""))[:2000]
        global_std_code = doc.get("standard_code")
        if not global_std_code:
            m = re.search(r"\b(VAS|IAS|IFRS|VFRS)[\s\-]?(\d+[A-Z]?)\b", full_sample_text, re.IGNORECASE)
            if m:
                global_std_code = f"{m.group(1).upper()}-{m.group(2)}"

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
            chunk_id = str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{chunk.chunk_index}")
            )
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
                "standard_code": global_std_code,
                "source_uri": doc["source_path"],
                "embedding_model": "unknown",
                "token_count": chunk.token_count,
                "ingested_at": ingested_at,
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
            except OSError as exc:
                logger.error("Failed to save chunks to %s: %s", output_file, exc)

    logger.info("total chunks to embed: %d", len(all_chunks_meta))

    if dry_run:
        print(f"[DRY RUN] Would upsert {len(all_chunks_meta)} chunks to {collection}")
        for m in all_chunks_meta[:3]:
            print(f"  {m['doc_id'][:8]}.. chunk[{m['chunk_index']}] {m['token_count']} tokens: {m['text_preview'][:80]}")
        return 0

    # Embed in batches concurrently
    texts = [f"[{m.get('standard_code') or 'Unknown'}] {m.get('heading', '')}\n{m['text']}".strip() for m in all_chunks_meta]
    vectors: list[list[float]] = []
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            tasks.append(embed_batch_with_retry(client, batch))
        
        logger.info("embedding %d chunks in %d batches concurrently...", len(texts), len(tasks))
        results = await asyncio.gather(*tasks)
        for batch_vecs in results:
            vectors.extend(batch_vecs)

    if len(vectors) != len(all_chunks_meta):
        raise ValueError(
            "embedding count does not match chunk count: "
            f"received {len(vectors)} vectors for {len(all_chunks_meta)} chunks"
        )
        
    # Generate Sparse Vectors (BM25)
    logger.info("generating sparse vectors for %d chunks using fastembed...", len(texts))
    # Load model once
    sparse_model = SparseTextEmbedding("Qdrant/bm25")
    # fastembed yields a generator, list() materializes it. Run in thread to avoid blocking.
    sparse_vectors_raw = await asyncio.to_thread(lambda: list(sparse_model.embed(texts)))
    
    # fastembed returns SparseEmbedding objects, Qdrant client needs models.SparseVector
    # but the python client accepts dicts or SparseVector objects. 
    # Qdrant client expects models.SparseVector(indices=..., values=...)
    from qdrant_client.models import SparseVector
    sparse_vectors = [
        SparseVector(indices=sv.indices.tolist(), values=sv.values.tolist())
        for sv in sparse_vectors_raw
    ]

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
        batch_sparse = sparse_vectors[i : i + BATCH_SIZE]
        points = []
        for meta, vec, sp_vec in zip(batch_meta, batch_vecs, batch_sparse):
            # Qdrant needs uint64 or UUID string ID
            point_id = str(uuid.UUID(meta["chunk_id"]))
            points.append({**meta, "id": point_id, "vector": vec, "sparse_vector": sp_vec})
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
