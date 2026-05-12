"""Langfuse LLM trace integration."""
from __future__ import annotations


def trace_llm_call(
    tenant_id: str,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
) -> None:
    """Send LLM call trace to Langfuse."""
    # TODO: use langfuse SDK to record generation
