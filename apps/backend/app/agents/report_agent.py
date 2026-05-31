"""Agent that synthesises IFRS-compliant financial report narratives."""

from __future__ import annotations

from typing import Any, AsyncIterator

from app.agents.base import AgentBase


class ReportAgent(AgentBase):
    """Produces IFRS financial statement drafts from adjusted GL data."""

    async def arun(self, report_type: str, period: str, **kwargs: Any) -> AsyncIterator[str]:  # type: ignore[override]
        # TODO: fetch GL data and run report synthesis prompt
        yield ""
