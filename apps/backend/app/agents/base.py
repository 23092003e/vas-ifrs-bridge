"""Abstract base class for all VAS-IFRS agents."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class AgentBase(ABC):
    """
    All agents inherit from this.
    arun() must be an async generator yielding str token events.
    """

    logger: logging.Logger

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.logger = logging.getLogger(f"agent.{cls.__name__}")

    @abstractmethod
    async def arun(self, **kwargs: Any) -> AsyncIterator[str]:
        """Execute agent and stream token events as JSON strings."""
        ...

    async def _safe_run(self, **kwargs: Any) -> AsyncIterator[str]:
        """Wrap arun() with top-level error handling."""
        try:
            async for token in await self.arun(**kwargs):
                yield token
        except Exception as exc:
            self.logger.error("agent %s failed: %s", self.__class__.__name__, exc, exc_info=True)
            yield f"data: {{\"type\":\"error\",\"message\":\"{exc}\"}}\n\n"
