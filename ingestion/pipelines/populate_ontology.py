"""
Populate Ontology: Creates and seeds the kb_shared_mapping collection in Qdrant
with topics, terminology mappings, and standard relations.
"""
from __future__ import annotations

import asyncio
import json
# pyrefly: ignore [missing-import]
import logging
import sys
import uuid
from pathlib import Path

# Setup PYTHONPATH
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "apps" / "backend"))
sys.path.insert(0, str(repo_root / "ingestion"))

logger = logging.getLogger(__name__)

# pyrefly: ignore [missing-import]
from app.rag.embedder import embed  # noqa: E402
# pyrefly: ignore [missing-import]
from qdrant_client import QdrantClient  # noqa: E402
# pyrefly: ignore [missing-import]
from qdrant_client.models import Distance, VectorParams, PointStruct  # noqa: E402
# pyrefly: ignore [missing-import]
from app.settings import settings  # noqa: E402
QDRANT_URL = settings.qdrant_url
QDRANT_API_KEY = settings.qdrant_api_key or ""

def _get_qdrant():
    if QDRANT_URL == ":memory:":
        return QdrantClient(":memory:")
    kwargs = {"url": QDRANT_URL, "check_compatibility": False}
    if QDRANT_API_KEY:
        kwargs["api_key"] = QDRANT_API_KEY
    return QdrantClient(**kwargs)

async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    
    ontology_dir = repo_root / "ingestion" / "metadata" / "ontology"
    topics_path = ontology_dir / "accounting_topics.json"
    terms_path = ontology_dir / "accounting_terms.json"
    relations_path = ontology_dir / "vas_ifrs_relations.json"
    examples_path = ontology_dir / "industry_examples.json"

    # Load data
    topics, terms, relations, examples = [], [], [], []
    if topics_path.exists():
        with open(topics_path, "r", encoding="utf-8") as f:
            topics = json.load(f)
    if terms_path.exists():
        with open(terms_path, "r", encoding="utf-8") as f:
            terms = json.load(f)
    if relations_path.exists():
        with open(relations_path, "r", encoding="utf-8") as f:
            relations = json.load(f)
    if examples_path.exists():
        with open(examples_path, "r", encoding="utf-8") as f:
            examples = json.load(f)

    logger.info("Loaded ontology: %d topics, %d terms, %d relations, %d examples",
                len(topics), len(terms), len(relations), len(examples))

    items = []

    # 1. Relations
    for rel in relations:
        topic_name = rel["topic"]
        vas = rel.get("vas", "None")
        ifrs = rel.get("ifrs", "None")
        ias = rel.get("ias", "None")
        relationship = rel.get("relationship", "")
        differences = rel.get("major_differences", "")
        
        text_rep = f"Topic: {topic_name}. Mapping: {vas} and {ifrs} ({ias}). Relationship: {relationship}. Differences: {differences}"
        
        items.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"relation_{topic_name}_{vas}_{ifrs}")),
            "text": text_rep,
            "topic": topic_name,
            "vas": vas,
            "ifrs": ifrs,
            "ias": ias,
            "relationship": relationship,
            "impact_summary": differences,
            "scope": "shared",
            "source_type": "mapping"
        })

    # 2. Topics
    for topic in topics:
        topic_id = topic["topic_id"]
        topic_name = topic["topic_name"]
        aliases = ", ".join(topic.get("aliases", []))
        related = ", ".join(topic.get("related_topics", []))
        
        text_rep = f"Topic: {topic_name} (ID: {topic_id}). Aliases: {aliases}. Related topics: {related}"
        
        items.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"topic_{topic_id}")),
            "text": text_rep,
            "topic": topic_name,
            "topic_id": topic_id,
            "vas": "None",
            "ifrs": "None",
            "ias": "None",
            "relationship": "topic_definition",
            "impact_summary": f"Core topic definition for {topic_name}. Related to: {related}.",
            "scope": "shared",
            "source_type": "mapping"
        })

    # 3. Examples
    for ex in examples:
        ex_id = ex["example_id"]
        topic_id = ex["topic_id"]
        industry = ex["industry"]
        scenario = ex["scenario"]
        vas_tx = ex["vas_treatment"]
        ifrs_tx = ex["ifrs_treatment"]
        
        text_rep = f"Industry Example: {industry} for {topic_id}. Scenario: {scenario}. VAS treatment: {vas_tx}. IFRS treatment: {ifrs_tx}."
        
        items.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"example_{ex_id}")),
            "text": text_rep,
            "topic": topic_id,
            "industry": industry,
            "scenario": scenario,
            "vas": "None",
            "ifrs": "None",
            "ias": "None",
            "relationship": "industry_example",
            "impact_summary": f"VAS: {vas_tx} | IFRS: {ifrs_tx}",
            "scope": "shared",
            "source_type": "example"
        })

    if not items:
        logger.warning("No ontology items to index.")
        return

    logger.info("Embedding %d ontology items...", len(items))
    texts = [it["text"] for it in items]
    vectors = await embed(texts)
    
    dim = len(vectors[0]) if vectors else 1024
    logger.info("Active embedding dimension: %d", dim)

    # Connect to Qdrant
    qdrant = _get_qdrant()
    collection_name = "kb_shared_mapping"
    
    # Recreate collection
    exists = qdrant.collection_exists(collection_name)
    if exists:
        logger.info("Recreating collection %s", collection_name)
        qdrant.delete_collection(collection_name)
    
    qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    # Upsert points
    points = []
    for it, vec in zip(items, vectors):
        point_id = it["id"]
        payload = {k: v for k, v in it.items() if k not in ("id",)}
        points.append(
            PointStruct(
                id=point_id,
                vector=vec,
                payload=payload
            )
        )

    qdrant.upsert(collection_name=collection_name, points=points)
    logger.info("Successfully populated kb_shared_mapping with %d points.", len(points))

if __name__ == "__main__":
    asyncio.run(main())
