from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from ingestion.pipelines import graph_builder, populate_ontology


def test_graph_section_ids_are_stable_across_rebuilds(tmp_path: Path) -> None:
    source = tmp_path / "IFRS-15.txt"
    source.write_text(
        "IFRS 15 Revenue from Contracts\n31. An entity shall recognize revenue.",
        encoding="utf-8",
    )

    first = graph_builder.build_graph(tmp_path)
    second = graph_builder.build_graph(tmp_path)

    first_sections = {node for node, data in first.nodes(data=True) if data["type"] == "section"}
    second_sections = {node for node, data in second.nodes(data=True) if data["type"] == "section"}
    assert first_sections == second_sections


def test_graph_builder_reports_parser_failures(tmp_path: Path) -> None:
    (tmp_path / "broken.pdf").write_bytes(b"not a pdf")

    with pytest.raises(RuntimeError, match="failed to parse 1 graph document"):
        graph_builder.build_graph(tmp_path)


def _write_ontology(root: Path) -> None:
    ontology = root / "ingestion/metadata/ontology"
    ontology.mkdir(parents=True)
    datasets = {
        "accounting_topics.json": [
            {
                "topic_id": "revenue",
                "topic_name": "Revenue",
                "aliases": ["Doanh thu"],
                "related_topics": [],
            }
        ],
        "accounting_terms.json": [
            {
                "term": "Doanh thu",
                "aliases": ["ghi nhận doanh thu"],
                "language": "vi",
                "topic_id": "revenue",
            }
        ],
        "vas_ifrs_relations.json": [],
        "industry_examples.json": [],
    }
    for filename, data in datasets.items():
        (ontology / filename).write_text(json.dumps(data), encoding="utf-8")


class _FakeQdrant:
    def __init__(self) -> None:
        self.points: list[Any] = []

    def collection_exists(self, _collection: str) -> bool:
        return False

    def create_collection(self, **_kwargs: Any) -> None:
        return None

    def upsert(self, *, collection_name: str, points: list[Any]) -> None:
        assert collection_name == "kb_shared_mapping"
        self.points = points


@pytest.mark.asyncio
async def test_populate_ontology_indexes_accounting_terms(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _write_ontology(tmp_path)
    qdrant = _FakeQdrant()

    async def fake_embed(texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]

    monkeypatch.setattr(populate_ontology, "repo_root", tmp_path)
    monkeypatch.setattr(populate_ontology, "embed", fake_embed)
    monkeypatch.setattr(populate_ontology, "_get_qdrant", lambda: qdrant)

    await populate_ontology.main()

    payloads = [point.payload for point in qdrant.points]
    assert any(
        payload["source_type"] == "terminology" and payload["term"] == "Doanh thu"
        for payload in payloads
    )


@pytest.mark.asyncio
async def test_populate_ontology_rejects_missing_vectors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _write_ontology(tmp_path)

    async def missing_embed(_texts: list[str]) -> list[list[float]]:
        return []

    monkeypatch.setattr(populate_ontology, "repo_root", tmp_path)
    monkeypatch.setattr(populate_ontology, "embed", missing_embed)
    monkeypatch.setattr(
        populate_ontology,
        "_get_qdrant",
        lambda: pytest.fail("Qdrant must not be mutated after incomplete embedding"),
    )

    with pytest.raises(ValueError, match="embedding count"):
        await populate_ontology.main()
