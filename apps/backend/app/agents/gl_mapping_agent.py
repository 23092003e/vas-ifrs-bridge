"""Agent that maps VAS chart-of-accounts codes to IFRS equivalents."""
from __future__ import annotations

from app.agents.base import BaseAgent


class GLMappingAgent(BaseAgent):
    """Maps a batch of VAS GL accounts to IFRS classification using rule + LLM fallback."""

    async def arun(self, upload_id: str, **kwargs):  # type: ignore[override]
        # TODO: implement mapping pipeline
        yield ""
