from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from app.api.v1 import kb


@pytest.mark.asyncio
async def test_list_collections_returns_collection_catalog() -> None:
    class FakeCollection:
        def __init__(self, name: str) -> None:
            self.name = name

    class FakeCollectionsResponse:
        def __init__(self) -> None:
            self.collections = [FakeCollection("kb_shared_vas"), FakeCollection("kb_shared_ifrs")]

    class FakeCollectionInfo:
        points_count = 120
        status = "green"

    class FakeQdrantClient:
        async def get_collections(self) -> FakeCollectionsResponse:
            return FakeCollectionsResponse()

        async def get_collection(self, name: str) -> FakeCollectionInfo:
            return FakeCollectionInfo()

        async def close(self) -> None:
            pass

    with patch("app.api.v1.kb._qdrant_client", return_value=FakeQdrantClient()):
        result = await kb.list_collections()

    assert "collections" in result
    assert len(result["collections"]) == 2
    assert result["collections"][0]["name"] == "kb_shared_vas"
    assert result["collections"][0]["points_count"] == 120


@pytest.mark.asyncio
async def test_list_collections_fallback_on_qdrant_error() -> None:
    class FailingQdrantClient:
        async def get_collections(self) -> Any:
            raise RuntimeError("Connection refused")

        async def close(self) -> None:
            pass

    with patch("app.api.v1.kb._qdrant_client", return_value=FailingQdrantClient()):
        result = await kb.list_collections()

    assert "collections" in result
    assert len(result["collections"]) >= 4
    names = [c["name"] for c in result["collections"]]
    assert "kb_shared_vas" in names
    assert "kb_shared_ifrs" in names


@pytest.mark.asyncio
async def test_list_standards_returns_categorized_lists_and_relations() -> None:
    result = await kb.list_standards()

    assert "vas_standards" in result
    assert "ifrs_standards" in result
    assert "relations" in result
    assert "topics" in result

    assert len(result["vas_standards"]) > 0
    assert len(result["ifrs_standards"]) > 0

    vas_codes = [s["code"] for s in result["vas_standards"]]
    assert "VAS-01" in vas_codes
    assert "VAS-06" in vas_codes
    assert "VAS-14" in vas_codes

    ifrs_codes = [s["code"] for s in result["ifrs_standards"]]
    assert "IFRS-15" in ifrs_codes
    assert "IFRS-16" in ifrs_codes
    assert "IAS-16" in ifrs_codes
