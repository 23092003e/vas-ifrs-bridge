"""Abstract base class for all VAS-IFRS agents."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseAgent(ABC):
    """All agents inherit from this class and implement arun()."""

    @abstractmethod
    async def arun(self, **kwargs) -> AsyncIterator[str]:
        """Execute the agent and stream token events."""
        ...
