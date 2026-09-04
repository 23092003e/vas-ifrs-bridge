"""Ollama local LLM provider — Qwen14B primary for VI Q&A."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen2.5:14b-instruct"
TIMEOUT_S = 120.0


async def stream_chat(
    *,
    system: str,
    user: str,
    messages: list[dict[str, str]] | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> AsyncIterator[str]:
    """Stream tokens from Ollama /api/chat endpoint."""
    payload_messages = [{"role": "system", "content": system}]
    if messages:
        payload_messages.extend(messages)
    payload_messages.append({"role": "user", "content": user})
    
    payload = {
        "model": model,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": max_tokens},
        "messages": payload_messages,
    }
    url = f"{settings.ollama_base_url}/api/chat"

    async with (
        httpx.AsyncClient(timeout=TIMEOUT_S) as client,
        client.stream("POST", url, json=payload) as resp,
    ):
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            delta = data.get("message", {}).get("content", "")
            if delta:
                yield delta
            if data.get("done"):
                break
