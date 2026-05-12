"""Top-level orchestrator — routes requests to the correct agent."""
from __future__ import annotations

from typing import AsyncIterator

from app.schemas.chat import ChatRequest


class Orchestrator:
    """Classifies intent and delegates to the appropriate specialised agent."""

    async def run_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """Route request to the best agent and stream its output."""
        # TODO: classify intent, select agent, yield token events
        async def _empty():
            yield ""

        return _empty()
