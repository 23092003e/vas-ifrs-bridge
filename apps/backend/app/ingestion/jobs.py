"""Ingestion job definitions — called by Celery workers or inline async tasks."""

from __future__ import annotations

import logging
import uuid

import anyio
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.db.models import Document
from app.db.session import AsyncSessionLocal
from app.ingestion.parsers.docx import parse_docx
from app.ingestion.parsers.pdf import parse_pdf
from app.ingestion.parsers.xlsx import parse_xlsx
from app.rag.chunker import chunk_document
from app.rag.embedder import embed, get_active_dim
from app.rag.retriever import _qdrant_client

logger = logging.getLogger(__name__)


def _point_id(document_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"vas-ifrs:{document_id}:{chunk_index}"))


async def ingest_document(document_id: str, local_path: str, tenant_id: str) -> None:
    """Full ingestion pipeline: parse -> chunk -> embed -> Qdrant upsert."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

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

        collection = f"tenant_{tenant_id}"
        doc.status = "processing"
        await db.commit()

        try:
            # 2. Extract text from document
            filename = doc.filename.lower()
            text = ""
            if filename.endswith(".pdf"):
                text = parse_pdf(local_path)
            elif filename.endswith(".docx"):
                text = parse_docx(local_path)
            elif filename.endswith((".xlsx", ".xls")):
                text = parse_xlsx(local_path)
            else:
                # Text fallback
                async with await anyio.open_file(
                    local_path, encoding="utf-8", errors="ignore"
                ) as file:
                    text = await file.read()

            if not text.strip():
                raise ValueError("Parsed document text is empty")

            # 3. Chunk text into segments
            lang = "vi" if any(x in text.lower() for x in ["chuẩn mực", "kế toán", "báo cáo", "thông tư"]) else "en"
            chunks = chunk_document(text, lang=lang)
            if not chunks:
                raise ValueError("Document did not yield any text chunks")

            # 4. Embed chunks using TEI (fallback Gemini)
            chunk_texts = [c.text for c in chunks]
            embeddings = await embed(chunk_texts)

            # 5. Connect and upload points to Qdrant
            client = _qdrant_client()
            try:
                dim = get_active_dim()

                # Check and create collection if missing
                collections = await client.get_collections()
                exists = any(c.name == collection for c in collections.collections)
                if not exists:
                    await client.create_collection(
                        collection_name=collection,
                        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
                    )

                # Assemble Qdrant points
                from app.ingestion.enrichment import enrich
                points = []
                for idx, (chunk, vector) in enumerate(zip(chunks, embeddings, strict=True)):
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
                        "standard_code": doc.doc_metadata.get("standard_code") if (doc.doc_metadata and isinstance(doc.doc_metadata, dict)) else None,
                        "source_uri": doc.filename,
                    }
                    chunk_payload = enrich(chunk_payload)
                    points.append(
                        PointStruct(
                            id=_point_id(document_id, idx),
                            vector=vector,
                            payload=chunk_payload
                        )
                    )

                # Bulk upload
                await client.upsert(
                    collection_name=collection,
                    points=points,
                )
            finally:
                await client.close()

            # 6. Update DB record to ready
            doc.status = "ready"
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
