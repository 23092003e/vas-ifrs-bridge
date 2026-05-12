"""Agent that produces a structured VAS ↔ IFRS standard comparison."""
from __future__ import annotations

from app.agents.base import BaseAgent


class IFRSCompareAgent(BaseAgent):
    """Compares a VAS standard against its IFRS counterpart section by section."""

    async def arun(self, vas_code: str, ifrs_code: str, **kwargs):  # type: ignore[override]
        # TODO: retrieve both standards and run diff prompt
        yield ""
