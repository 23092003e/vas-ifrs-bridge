from __future__ import annotations

import httpx


async def embed_text(
    text: str,
    *,
    target_dim: int,
    base_url: str,
    client: httpx.AsyncClient,
) -> list[float]:
    response = await client.post(
        f"{base_url.rstrip('/')}/api/embed",
        json={"model": "bge-m3", "input": [text]},
    )
    response.raise_for_status()
    data = response.json()
    embeddings = data.get("embeddings") if isinstance(data, dict) else None
    if not isinstance(embeddings, list) or not embeddings or not isinstance(embeddings[0], list):
        raise ValueError("Ollama response does not contain an embedding vector")

    vector = embeddings[0]
    if len(vector) != target_dim:
        raise ValueError(
            f"Ollama returned dimension {len(vector)}, expected {target_dim}"
        )
    return vector
