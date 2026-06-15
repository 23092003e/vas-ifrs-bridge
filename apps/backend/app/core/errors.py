"""Domain-specific exception hierarchy."""

from __future__ import annotations


class VASIFRSError(Exception):
    """Base exception for all VAS-IFRS application errors."""


class TenantMismatchError(VASIFRSError):
    """Raised when a resource does not belong to the resolved tenant."""


class QdrantUnavailableError(VASIFRSError):
    """Raised when the Qdrant vector store cannot be reached."""


class EmbedderTimeoutError(VASIFRSError):
    """Raised when the embedding service does not respond in time."""


class UnbalancedJEError(VASIFRSError):
    """Raised when a generated journal entry does not balance (debits != credits)."""


class MissingRuleError(VASIFRSError):
    """Raised when no mapping rule is found for a given GL account code."""
