from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from ingestion.pipelines import graph_builder, populate_ontology
from qdrant_client.models import PointStruct


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


def test_graph_does_not_equate_vas_01_with_ifrs_1(tmp_path: Path) -> None:
    (tmp_path / "VAS-01.txt").write_text(
        "VAS 01 Chuẩn mực chung\n01. Các nguyên tắc kế toán cơ bản.",
        encoding="utf-8",
    )
    (tmp_path / "IFRS-1.txt").write_text(
        "IFRS 1 First-time Adoption\n1. First IFRS financial statements.",
        encoding="utf-8",
    )

    graph = graph_builder.build_graph(tmp_path)
    documents = {
        data["standard_code"]: node
        for node, data in graph.nodes(data=True)
        if data["type"] == "document"
    }
    vas_sections = [
        node
        for node, data in graph.nodes(data=True)
        if data["type"] == "section" and data["standard_code"] == "VAS-01"
    ]

    assert not graph.has_edge(documents["VAS-01"], documents["IFRS-1"])
    assert all(
        graph.get_edge_data(section, documents["IFRS-1"]) is None
        for section in vas_sections
    )


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


def test_sync_collection_upserts_before_removing_stale_points() -> None:
    current_id = "00000000-0000-4000-8000-000000000001"
    new_id = "00000000-0000-4000-8000-000000000002"
    stale_id = "00000000-0000-4000-8000-000000000003"
    points = [
        PointStruct(id=current_id, vector=[0.1, 0.2], payload={"text": "current"}),
        PointStruct(id=new_id, vector=[0.3, 0.4], payload={"text": "new"}),
    ]
    events: list[tuple[str, Any]] = []

    class ExistingQdrant:
        def collection_exists(self, _collection: str) -> bool:
            return True

        def get_collection(self, _collection: str) -> Any:
            vectors = SimpleNamespace(size=2)
            return SimpleNamespace(
                config=SimpleNamespace(params=SimpleNamespace(vectors=vectors))
            )

        def scroll(self, **_kwargs: Any) -> tuple[list[Any], None]:
            records = [SimpleNamespace(id=current_id), SimpleNamespace(id=stale_id)]
            return records, None

        def upsert(self, *, collection_name: str, points: list[Any]) -> None:
            events.append(("upsert", [str(point.id) for point in points]))

        def delete(self, *, collection_name: str, points_selector: list[str]) -> None:
            events.append(("delete", points_selector))

        def create_collection(self, **_kwargs: Any) -> None:
            pytest.fail("existing collection must not be recreated")

        def delete_collection(self, _collection: str) -> None:
            pytest.fail("live collection must not be deleted")

    populate_ontology.sync_collection(
        ExistingQdrant(),
        collection_name="kb_shared_mapping",
        points=points,
        dim=2,
    )

    assert events == [
        ("upsert", [current_id, new_id]),
        ("delete", [stale_id]),
    ]


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
