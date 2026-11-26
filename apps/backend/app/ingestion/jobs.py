"""Ingestion job definitions — called by Celery workers or inline async tasks."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document
from app.db.session import AsyncSessionLocal, engine
from app.ingestion.normalizer import normalize
from app.ingestion.parsers.docx import parse_docx
from app.ingestion.parsers.html import parse_html
from app.ingestion.parsers.pdf import parse_pdf
from app.ingestion.parsers.xlsx import parse_xlsx
from app.rag.chunker import chunk_document
from app.rag.embedder import embed, embed_sparse, get_active_dim
from app.rag.retriever import _qdrant_client

logger = logging.getLogger(__name__)


def _point_id(document_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"vas-ifrs:{document_id}:{chunk_index}"))


async def _parse_document(filename: str, local_path: str) -> str:
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        text = parse_pdf(local_path)
    elif lowered.endswith(".docx"):
        text = parse_docx(local_path)
    elif lowered.endswith((".xlsx", ".xls")):
        text = parse_xlsx(local_path)
    else:
        async with await anyio.open_file(local_path, encoding="utf-8", errors="ignore") as file:
            content = await file.read()
        text = parse_html(content) if lowered.endswith((".html", ".htm")) else content
    return normalize(text)


@asynccontextmanager
async def _ingestion_session(document_id: str) -> AsyncIterator[AsyncSession | None]:
    lock_id = uuid.UUID(document_id).int >> 65
    async with engine.connect() as connection:
        acquired = await connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": lock_id})
        if not acquired:
            yield None
            return
        try:
            # Keep one physical connection checked out across status commits.
            await connection.commit()
            async with AsyncSession(bind=connection, expire_on_commit=False) as db:
                yield db
        finally:
            with anyio.CancelScope(shield=True):
                try:
                    await connection.rollback()
                    await connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": lock_id})
                except BaseException:
                    await connection.invalidate()
                    raise


async def recover_ingestion() -> None:
    """Resume interrupted uploads whose source file is available to this process."""
    async with AsyncSessionLocal() as db:
        documents = (await db.execute(
            select(Document.id, Document.gcs_path, Document.tenant_id)
            .where(Document.status.in_(("pending", "processing")))
            .order_by(Document.created_at)
        )).all()
    for document_id, local_path, tenant_id in documents:
        if not await anyio.Path(local_path).is_file():
            continue
        try:
            await ingest_document(document_id, local_path, tenant_id, recovering=True)
        except Exception:
            logger.exception("Could not recover ingestion for document %s", document_id)


async def ingest_document(
    document_id: str, local_path: str, tenant_id: str, *, recovering: bool = False,
) -> None:
    """Full ingestion pipeline: parse -> chunk -> embed -> Qdrant upsert."""
    async with _ingestion_session(document_id) as db:
        if db is None:
            return

        # 1. Fetch document metadata
        stmt = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        doc = res.scalar_one_or_none()
        if not doc:
            logger.error("Document not found in DB: %s", document_id)
            return
        if doc.status == "ready" or (recovering and doc.status not in {"pending", "processing"}):
            return

        collection = f"tenant_{tenant_id}"
        doc.status = "processing"
        await db.commit()

        try:
            # 2. Extract text from document
            text = await _parse_document(doc.filename, local_path)

            if not text.strip():
                raise ValueError("Parsed document text is empty")

            # 3. Chunk text into segments
            lang = "vi" if any(x in text.lower() for x in ["chuẩn mực", "kế toán", "báo cáo", "thông tư"]) else "en"
            chunks = chunk_document(text, lang=lang)
            if not chunks:
                raise ValueError("Document did not yield any text chunks")

            # 4. Embed chunks using local Ollama bge-m3
            # 4. Embed chunks using local Ollama bge-m3 and FastEmbed BM25
            chunk_texts = [c.text for c in chunks]
            embeddings = await embed(chunk_texts)
            sparse_embeddings = await embed_sparse(chunk_texts)

            # 5. Connect and upload points to Qdrant
            client = _qdrant_client()
            try:
                dim = get_active_dim()

                # Check and create collection if missing
                collections = await client.get_collections()
                exists = any(c.name == collection for c in collections.collections)
                if not exists:
                    from qdrant_client.models import SparseVectorParams
                    try:
                        await client.create_collection(
                            collection_name=collection,
                            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
                            sparse_vectors_config={"bm25": SparseVectorParams(modifier=None)},
                        )
                    except UnexpectedResponse:
                        if not await client.collection_exists(collection):
                            raise

                # Assemble Qdrant points
                # Pre-calculate global standard_code
                import re

                from app.ingestion.enrichment import enrich
                full_sample_text = (doc.filename + " " + text)[:2000]
                doc_meta_std = doc.doc_metadata.get("standard_code") if (doc.doc_metadata and isinstance(doc.doc_metadata, dict)) else None
                global_std = doc_meta_std
                if not global_std:
                    m = re.search(r"\b(VAS|IAS|IFRS|VFRS)[\s\-]?(\d+[A-Z]?)\b", full_sample_text, re.IGNORECASE)
                    if m:
                        global_std = f"{m.group(1).upper()}-{m.group(2)}"

                points = []
                for idx, (chunk, vector, sparse_vec) in enumerate(zip(chunks, embeddings, sparse_embeddings, strict=True)):
                    chunk_payload = {
                        "doc_id": document_id,
                        "chunk_index": idx,
                        "text": chunk.text,
                        "text_preview": chunk.text[:300],
                        "heading": chunk.heading,
                        "section_path": chunk.section_path,
                        "lang": lang,
                        "scope": "tenant",
                        "tenant_id": doc.tenant_id,
                        "standard_code": global_std,
                        "source_uri": doc.filename,
                    }
                    chunk_payload = enrich(chunk_payload)
                    
                    from qdrant_client.models import SparseVector
                    point_vector = {
                        "": vector,
                        "bm25": SparseVector(
                            indices=sparse_vec.indices.tolist(),
                            values=sparse_vec.values.tolist(),
                        )
                    }
                    
                    points.append(
                        PointStruct(
                            id=_point_id(document_id, idx),
                            vector=point_vector,
                            payload=chunk_payload
                        )
                    )

                # Bulk upload
                await client.upsert(
                    collection_name=collection,
                    points=points,
                    wait=True,
                )
            finally:
                await client.close()

            # 6. Update DB record to ready
            doc.status = "ready"
            doc.error_message = None
            doc.chunk_count = len(chunks)
            doc.qdrant_collection = collection
            await db.commit()
            logger.info("Ingestion completed for document %s (%d chunks)", document_id, len(chunks))

        except Exception as exc:
            logger.error("Ingestion failed for document %s: %s", document_id, exc)
            doc.status = "failed"
            doc.error_message = str(exc)
            await db.commit()
            raise
