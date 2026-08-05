"""Metadata enrichment — extracts standard codes, article numbers, dates."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

# Load topic terms and relations for keyword-based matching
_ONTOLOGY_TOPICS: list[dict] = []
_ONTOLOGY_TERMS: list[dict] = []
logger = logging.getLogger(__name__)

def _load_ontology():
    global _ONTOLOGY_TOPICS, _ONTOLOGY_TERMS
    if _ONTOLOGY_TOPICS:
        return

    # Locate ontology folder
    # Apps/backend/app/ingestion/enrichment.py is 5 levels up to repo root
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    ontology_dir = repo_root / "ingestion" / "metadata" / "ontology"

    topics_path = ontology_dir / "accounting_topics.json"
    terms_path = ontology_dir / "accounting_terms.json"

    if topics_path.exists():
        try:
            with open(topics_path, encoding="utf-8") as f:
                _ONTOLOGY_TOPICS = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Unable to load ontology topics: %s", exc)

    if terms_path.exists():
        try:
            with open(terms_path, encoding="utf-8") as f:
                _ONTOLOGY_TERMS = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Unable to load ontology terms: %s", exc)

# Predefined effective dates for standards
EFFECTIVE_DATES = {
    # IFRS / IAS
    "IFRS-1": "2009-07-01",
    "IFRS-2": "2005-01-01",
    "IFRS-3": "2009-07-01",
    "IFRS-9": "2018-01-01",
    "IFRS-10": "2013-01-01",
    "IFRS-15": "2018-01-01",
    "IFRS-16": "2019-01-01",
    "IAS-1": "2005-01-01",
    "IAS-2": "2005-01-01",
    "IAS-16": "2005-01-01",
    "IAS-17": "2005-01-01",
    "IAS-18": "2005-01-01",
    "IAS-27": "2005-01-01",
    "IAS-36": "2005-01-01",
    "IAS-38": "2005-01-01",
    # VAS
    "VAS-01": "2002-01-01",
    "VAS-02": "2002-01-01",
    "VAS-03": "2002-01-01",
    "VAS-04": "2002-01-01",
    "VAS-06": "2003-01-01",
    "VAS-14": "2003-01-01",
    "VAS-15": "2003-01-01",
    "VAS-17": "2003-01-01",
    "VAS-21": "2003-01-01",
    "VAS-25": "2005-01-01",
}

def enrich(chunk: dict) -> dict:
    """Add structured metadata fields to a text chunk."""
    _load_ontology()

    text = chunk.get("text", "")
    source_uri = chunk.get("source_uri") or chunk.get("source_path", "")

    # 1. standard_code
    std_code = chunk.get("standard_code")
    if not std_code:
        # Try to parse standard code from text/source_uri
        m = re.search(r"\b(VAS|IAS|IFRS|VFRS)[\s\-]?(\d+[A-Z]?)\b", source_uri + " " + text[:1000], re.IGNORECASE)
        if m:
            std_code = f"{m.group(1).upper()}-{m.group(2)}"

    if std_code:
        std_code = std_code.upper().strip()
    chunk["standard_code"] = std_code

    # 2. topic detection (check matching aliases or terms from ontology)
    detected_topic = None
    # Check terms first
    text_lower = text.lower()
    for term in _ONTOLOGY_TERMS:
        matched = False
        term_word = term["term"].lower()
        if re.search(r"(?<!\w)" + re.escape(term_word) + r"(?!\w)", text_lower):
            matched = True
        else:
            for alias in term.get("aliases", []):
                alias_pattern = r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)"
                if re.search(alias_pattern, text_lower):
                    matched = True
                    break
        if matched:
            topic_id = term["topic_id"]
            for topic in _ONTOLOGY_TOPICS:
                if topic["topic_id"] == topic_id:
                    detected_topic = topic["topic_name"]
                    break
            if detected_topic:
                break

    # If not found, check topic aliases directly
    if not detected_topic:
        for topic in _ONTOLOGY_TOPICS:
            matched = False
            topic_name = topic["topic_name"].lower()
            if re.search(r"(?<!\w)" + re.escape(topic_name) + r"(?!\w)", text_lower):
                matched = True
            else:
                for alias in topic.get("aliases", []):
                    alias_pattern = r"(?<!\w)" + re.escape(alias.lower()) + r"(?!\w)"
                    if re.search(alias_pattern, text_lower):
                        matched = True
                        break
            if matched:
                detected_topic = topic["topic_name"]
                break

    chunk["topic"] = detected_topic

    # 3. source_type
    uri_lower = source_uri.lower()
    source_type = "standard"
    if "/standards/" in uri_lower or "/ias/" in uri_lower:
        source_type = "standard"
    elif "/examples/" in uri_lower:
        source_type = "example"
    elif "/basis_for_conclusions/" in uri_lower or "/basis-for-conclusions/" in uri_lower:
        source_type = "basis_for_conclusions"
    elif "/interpretations/" in uri_lower or "/ifric/" in uri_lower or "/sic/" in uri_lower:
        source_type = "interpretation"
    else:
        # Best effort check from name
        if "example" in uri_lower or "illustrative" in uri_lower:
            source_type = "example"
        elif "conclusion" in uri_lower:
            source_type = "basis_for_conclusions"
        elif "interpretation" in uri_lower or "ifric" in uri_lower or "sic" in uri_lower:
            source_type = "interpretation"

    chunk["source_type"] = source_type

    # 4. paragraph
    para_num = None
    text_strip = text.strip()
    m = re.match(r"^(?:Paragraph|para\.|section|Khoản|Điều)?\s*\b(B\d+|IE\d+|\d+)\b", text_strip, re.IGNORECASE)
    if m:
        para_num = m.group(1)
    chunk["paragraph"] = para_num

    # 5. section
    chunk["section"] = chunk.get("heading") or chunk.get("section_path") or None

    # 6. jurisdiction
    if std_code and std_code.startswith("VAS"):
        jurisdiction = "VN"
    elif std_code and std_code.startswith(("IFRS", "IAS", "IFRIC", "SIC")):
        jurisdiction = "IFRS"
    elif "/vas/" in uri_lower:
        jurisdiction = "VN"
    elif "/ifrs/" in uri_lower:
        jurisdiction = "IFRS"
    else:
        jurisdiction = "VN" if chunk.get("lang") == "vi" else "IFRS"
    chunk["jurisdiction"] = jurisdiction

    # 7. language
    chunk["language"] = chunk.get("lang") or "en"

    # 8. effective_date
    effective_date = None
    if std_code:
        std_key = std_code.upper()
        if std_key in EFFECTIVE_DATES:
            effective_date = EFFECTIVE_DATES[std_key]
        else:
            year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
            if year_match:
                effective_date = f"{year_match.group(1)}-01-01"
    chunk["effective_date"] = effective_date

    return chunk
