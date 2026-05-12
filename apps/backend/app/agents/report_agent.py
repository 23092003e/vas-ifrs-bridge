"""Agent that synthesises IFRS-compliant financial report narratives."""
from __future__ import annotations

from app.agents.base import BaseAgent


class ReportAgent(BaseAgent):
    """Produces IFRS financial statement drafts from adjusted GL data."""

    async def arun(self, report_type: str, period: str, **kwargs):  # type: ignore[override]
        # TODO: fetch GL data and run report synthesis prompt
        yield ""
