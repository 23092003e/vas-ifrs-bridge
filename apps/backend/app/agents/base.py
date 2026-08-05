"""Abstract base class for all VAS-IFRS agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any


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
    async def arun(self, **kwargs: Any) -> AsyncGenerator[str, None]:
        """Execute agent and stream token events as JSON strings."""
        # This is an abstract async generator; subclasses must use `yield`.
        raise NotImplementedError
        yield  # make this an async generator at the type level

    async def _safe_run(self, **kwargs: Any) -> AsyncIterator[str]:
        """Wrap arun() with top-level error handling."""
        try:
            async for token in self.arun(**kwargs):
                yield token
        except Exception:
            self.logger.exception("agent %s failed", self.__class__.__name__)
            yield 'data: {"type":"error","message":"Agent execution failed"}\n\n'
