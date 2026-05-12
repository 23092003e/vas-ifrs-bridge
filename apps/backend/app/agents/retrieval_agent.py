"""RAG retrieval agent — fetches relevant chunks and synthesises an answer."""
from __future__ import annotations

from app.agents.base import BaseAgent


class RetrievalAgent(BaseAgent):
    """Retrieves chunks from shared + tenant KB and synthesises a cited answer."""

    async def arun(self, query: str, **kwargs):  # type: ignore[override]
        # TODO: implement retrieval pipeline
        yield ""
