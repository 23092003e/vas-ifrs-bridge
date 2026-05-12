"""Retrieval evaluation — measures recall@k and MRR against labelled datasets."""
from __future__ import annotations


def evaluate_retrieval(dataset_path: str, top_k: int = 5) -> dict:
    """Run retrieval eval and return recall@k and MRR metrics."""
    # TODO: load dataset, run retrieve(), compute metrics
    return {"recall_at_k": 0.0, "mrr": 0.0}
