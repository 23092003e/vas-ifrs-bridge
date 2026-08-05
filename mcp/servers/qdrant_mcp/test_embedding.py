from __future__ import annotations

import httpx
import pytest

from . import server
from .embedding import embed_text


@pytest.mark.asyncio
async def test_embed_text_uses_ollama_batch_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://ollama.test/api/embed"
        assert request.read() == b'{"model":"bge-m3","input":["revenue"]}'
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        vector = await embed_text(
            "revenue",
            target_dim=3,
            base_url="http://ollama.test",
            client=client,
        )

    assert vector == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_embed_text_rejects_wrong_vector_dimension() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="dimension 2.*expected 3"):
            await embed_text(
                "revenue",
                target_dim=3,
                base_url="http://ollama.test",
                client=client,
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "client_method", "arguments"),
    [
        ("qdrant_list_collections", "get_collections", ()),
        ("qdrant_get_collection_info", "get_collection", ("kb_shared_vas",)),
        ("qdrant_retrieve_points", "retrieve", ("kb_shared_vas", ["1"])),
        ("qdrant_search", "get_collection", ("kb_shared_vas", "revenue", 5)),
    ],
)
async def test_qdrant_tools_propagate_failures_and_close_clients(
    monkeypatch: pytest.MonkeyPatch,
    tool_name: str,
    client_method: str,
    arguments: tuple[object, ...],
) -> None:
    class FailingClient:
        closed = False

        def __getattr__(self, name: str):
            if name != client_method:
                raise AttributeError(name)

            async def fail(*_args: object, **_kwargs: object) -> None:
                raise RuntimeError("qdrant unavailable")

            return fail

        async def close(self) -> None:
            self.closed = True

    client = FailingClient()
    monkeypatch.setattr(server, "_get_qdrant_client", lambda: client)

    with pytest.raises(RuntimeError, match="qdrant unavailable"):
        await getattr(server, tool_name)(*arguments)

    assert client.closed is True
