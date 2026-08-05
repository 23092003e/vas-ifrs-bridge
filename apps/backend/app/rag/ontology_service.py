"""Ontology service: loads JSON ontology mappings, performs topic detection and query expansion."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_TOPICS: list[dict] = []
_TERMS: list[dict] = []
_RELATIONS: list[dict] = []

def load_ontology() -> None:
    global _TOPICS, _TERMS, _RELATIONS
    if _TOPICS:
        return

    # Located in backend app: apps/backend/app/rag/ontology_service.py
    # 5 levels up to repo root: apps/backend/app/rag/ontology_service.py -> app/rag -> app -> backend -> apps -> root
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    ontology_dir = repo_root / "ingestion" / "metadata" / "ontology"

    topics_path = ontology_dir / "accounting_topics.json"
    terms_path = ontology_dir / "accounting_terms.json"
    relations_path = ontology_dir / "vas_ifrs_relations.json"

    try:
        if topics_path.exists():
            with open(topics_path, encoding="utf-8") as f:
                _TOPICS = json.load(f)
        if terms_path.exists():
            with open(terms_path, encoding="utf-8") as f:
                _TERMS = json.load(f)
        if relations_path.exists():
            with open(relations_path, encoding="utf-8") as f:
                _RELATIONS = json.load(f)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("Failed to load ontology: %s", e)

def detect_topics(query: str) -> list[dict]:
    """Find all ontology topics matching terms/aliases mentioned in the query."""
    load_ontology()
    matched_topics = []
    query_lower = query.lower()

    # Check terms
    matched_topic_ids = set()
    for term in _TERMS:
        term_word = term["term"].lower()
        term_pattern = r"(?<!\w)" + re.escape(term_word) + r"(?!\w)"
        matched = bool(re.search(term_pattern, query_lower))
        if not matched:
            for alias in term.get("aliases", []):
                alias_pattern = r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)"
                if re.search(alias_pattern, query_lower):
                    matched = True
                    break

        if matched:
            matched_topic_ids.add(term["topic_id"])

    # Check topics directly
    for topic in _TOPICS:
        if topic["topic_id"] in matched_topic_ids:
            if topic not in matched_topics:
                matched_topics.append(topic)
            continue

        topic_name = topic["topic_name"].lower()
        topic_pattern = r"(?<!\w)" + re.escape(topic_name) + r"(?!\w)"
        matched = bool(re.search(topic_pattern, query_lower))
        if not matched:
            for alias in topic.get("aliases", []):
                alias_pattern = r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)"
                if re.search(alias_pattern, query_lower):
                    matched = True
                    break
        if matched:
            matched_topic_ids.add(topic["topic_id"])
            if topic not in matched_topics:
                matched_topics.append(topic)

    return matched_topics

def get_standards_for_topics(topic_ids: list[str]) -> list[str]:
    """Get all standard codes (e.g. IFRS-15, VAS-14) corresponding to topic IDs."""
    load_ontology()
    standards = set()
    topic_ids_set = set(topic_ids)

    # Cross-reference with vas_ifrs_relations
    for rel in _RELATIONS:
        topic_name = rel["topic"].lower()
        matched_topic_id = None
        for t in _TOPICS:
            if t["topic_name"].lower() == topic_name:
                matched_topic_id = t["topic_id"]
                break

        if matched_topic_id in topic_ids_set:
            for key in ["vas", "ifrs", "ias"]:
                std = rel.get(key)
                if std and std != "None":
                    standards.add(std.upper().strip())

    return list(standards)

def expand_query(query: str, matched_topics: list[dict]) -> str:
    """Expand user query with matching topics, standard codes, and relevant terms from ontology."""
    load_ontology()
    if not matched_topics:
        return query

    expansion_terms = set()
    topic_ids = [t["topic_id"] for t in matched_topics]

    for topic in matched_topics:
        expansion_terms.add(topic["topic_name"])
        for alias in topic.get("aliases", []):
            expansion_terms.add(alias)

    # Find associated terms
    for term in _TERMS:
        if term["topic_id"] in topic_ids:
            expansion_terms.add(term["term"])
            for alias in term.get("aliases", []):
                expansion_terms.add(alias)

    # Find associated standards
    stds = get_standards_for_topics(topic_ids)
    for std in stds:
        expansion_terms.add(std)
        expansion_terms.add(std.replace("-", " "))

    unique_terms = [t for t in expansion_terms if t.lower() not in query.lower()]
    if unique_terms:
        expanded_query = query + " " + " ".join(unique_terms)
        return expanded_query

    return query
