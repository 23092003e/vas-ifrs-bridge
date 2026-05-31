"""Token usage metering — increments Redis counters per tenant."""

from __future__ import annotations


async def record_usage(tenant_id: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Increment per-tenant token counters in Redis."""
    # TODO: INCRBY redis keys tenant:{id}:tokens:prompt and :completion
