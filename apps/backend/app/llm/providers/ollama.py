"""Ollama local LLM provider — Qwen14B primary for VI Q&A."""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen2.5:14b-instruct"
TIMEOUT_S = 120.0


async def stream_chat(
    *,
    system: str,
    user: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> AsyncIterator[str]:
    """Stream tokens from Ollama /api/chat endpoint."""
    payload = {
        "model": model,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": max_tokens},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    url = f"{settings.ollama_base_url}/api/chat"

    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        async with client.stream("POST", url, json=payload) as resp:
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
