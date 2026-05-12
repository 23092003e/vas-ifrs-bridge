"""Agent that generates IFRS adjustment journal entries from mapping results."""
from __future__ import annotations

from app.agents.base import BaseAgent


class AdjustmentAgent(BaseAgent):
    """Generates balanced double-entry adjustments for IFRS restatement."""

    async def arun(self, upload_id: str, **kwargs):  # type: ignore[override]
        # TODO: generate and validate adjustment entries
        yield ""
