"""Google Gemini provider — primary LLM for Phase 1."""

from __future__ import annotations

import logging
from typing import AsyncIterator

from google import genai
from google.genai import types

from app.settings import settings

logger = logging.getLogger(__name__)

MODEL_FAST = "gemini-2.5-flash"  # Q&A, citation validation
MODEL_BALANCED = "gemini-2.5-flash"  # IFRS compare, GL mapping
MODEL_DEEP = "gemini-2.5-flash"  # Report synthesis (pro if budget allows)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _pick_model(hint: str) -> str:
    return {
        "fast": MODEL_FAST,
        "balanced": MODEL_BALANCED,
        "deep": MODEL_DEEP,
        "qwen": MODEL_FAST,
        "openai": MODEL_BALANCED,
        "claude": MODEL_DEEP,
    }.get(hint, MODEL_BALANCED)


async def stream_chat(
    *,
    system: str,
    user: str,
    model_hint: str = "balanced",
    temperature: float = 0.1,
    max_tokens: int = 8192,
) -> AsyncIterator[str]:
    """Stream tokens from Gemini using the google-genai SDK."""
    client = _get_client()
    model_name = _pick_model(model_hint)

    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        max_output_tokens=max_tokens,
    )

    try:
        async for chunk in await client.aio.models.generate_content_stream(
            model=model_name,
            contents=user,
            config=config,
        ):
            text = chunk.text or ""
            if text:
                yield text
    except Exception as exc:
        logger.error("Gemini stream error (model=%s): %s", model_name, exc)
        raise
