"""Prometheus metrics definitions."""
from __future__ import annotations

from prometheus_client import Counter, Histogram

request_count = Counter("vasifrs_requests_total", "Total HTTP requests", ["method", "path", "status"])
token_usage = Counter("vasifrs_tokens_total", "LLM tokens consumed", ["tenant", "provider", "type"])
retrieval_latency = Histogram("vasifrs_retrieval_seconds", "Qdrant retrieval latency")
llm_latency = Histogram("vasifrs_llm_seconds", "LLM first-token latency", ["provider"])
