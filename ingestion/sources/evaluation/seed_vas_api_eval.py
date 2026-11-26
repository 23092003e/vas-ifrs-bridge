"""Seed only the dedicated loopback Qdrant instance for the VAS API benchmark."""

import asyncio
import json
import subprocess
import uuid

import httpx
from app.rag.chunker import chunk_document
from app.rag.embedder import embed, embed_sparse, get_active_dim
from app.settings import settings
from qdrant_client import AsyncQdrantClient, models
from run_vas_benchmark import ROOT, SOURCES, sha

QDRANT = "http://127.0.0.1:16333"
OLLAMA = "http://127.0.0.1:11436"
COLLECTIONS = (
    "kb_shared_vas",
    "kb_shared_ifrs",
    "kb_shared_mapping",
    "kb_shared_guidance",
)


async def seed():
    if settings.qdrant_url != QDRANT or settings.ollama_base_url != OLLAMA:
        raise ValueError("Benchmark seeding requires the dedicated loopback endpoints")
    expected = {
        r["file"]: r["sha256"]
        for r in json.loads((ROOT / "downloads.json").read_text())
        if "sha256" in r
    }
    repo = ROOT.parents[1]

    client = AsyncQdrantClient(url=QDRANT)
    try:
        present = {c.name for c in (await client.get_collections()).collections}
        if present.intersection(COLLECTIONS):
            raise ValueError("Refusing to seed an existing benchmark collection")

        records = []
        for filename in [*SOURCES, "12-2005-QD-BTC.doc"]:
            path = ROOT / "vas" / filename
            assert sha(path) == expected[f"vas/{filename}"]
            command = (
                ["pdftotext", "-layout", path, "-"]
                if path.suffix == ".pdf"
                else ["textutil", "-convert", "txt", "-stdout", path]
            )
            raw = await asyncio.to_thread(subprocess.check_output, command, text=True)
            # shortcut: chunk whole source files; use section metadata for graph benchmarks.
            text = " ".join(raw.split())
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(path.relative_to(repo))))
            for chunk in chunk_document(text):
                records.append((filename, doc_id, chunk.chunk_index, chunk.text))

        texts = [row[3] for row in records]
        dense = await embed(texts)
        sparse = await embed_sparse(texts)
        for collection in COLLECTIONS:
            await client.create_collection(
                collection,
                vectors_config=models.VectorParams(
                    size=get_active_dim(), distance=models.Distance.COSINE
                ),
                sparse_vectors_config={"bm25": models.SparseVectorParams()},
            )
        for i in range(0, len(records), 32):
            points = []
            for row, vector, bm25 in zip(
                records[i : i + 32], dense[i : i + 32], sparse[i : i + 32], strict=True
            ):
                filename, doc_id, index, text = row
                points.append(
                    models.PointStruct(
                        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{index}")),
                        vector={
                            "": vector,
                            "bm25": models.SparseVector(
                                indices=bm25.indices.tolist(),
                                values=bm25.values.tolist(),
                            ),
                        },
                        payload={
                            "doc_id": doc_id,
                            "source_uri": filename,
                            "chunk_index": index,
                            "text": text,
                            "text_preview": text[:200],
                            "scope": "shared",
                            "lang": "vi",
                        },
                    )
                )
            await client.upsert("kb_shared_vas", points, wait=True)
        count = (await client.count("kb_shared_vas", exact=True)).count
        assert count == len(records)
    finally:
        await client.close()
    async with httpx.AsyncClient(base_url=OLLAMA) as client:
        tags = (await client.get("/api/tags")).raise_for_status().json()["models"]
    print(
        json.dumps(
            {
                "seeded": count,
                "collections": COLLECTIONS,
                "models": {row["name"]: row["digest"] for row in tags},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(seed())
