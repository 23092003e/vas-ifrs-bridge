"""Domain-specific exception hierarchy."""

from __future__ import annotations


class VASIFRSError(Exception):
    """Base exception for all VAS-IFRS application errors."""


class TenantMismatch(VASIFRSError):
    """Raised when a resource does not belong to the resolved tenant."""


class QdrantUnavailable(VASIFRSError):
    """Raised when the Qdrant vector store cannot be reached."""


class EmbedderTimeout(VASIFRSError):
    """Raised when the embedding service does not respond in time."""


class UnbalancedJE(VASIFRSError):
    """Raised when a generated journal entry does not balance (debits != credits)."""


class MissingRule(VASIFRSError):
    """Raised when no mapping rule is found for a given GL account code."""
