"""
Graph Builder: scans raw documents, parses/chunks them, extracts cross-references,
aligns VAS and IFRS, and serializes the NetworkX graph to JSON.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import uuid
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)

# Standard mappings VAS -> IFRS
VAS_IFRS_MAPPING = {
    "VAS-01": "IFRS-1",
    "VAS-14": "IFRS-15",
    "VAS-15": "IFRS-15",
    "VAS-17": "IAS-12",
    "VAS-21": "IAS-1",
}


def _extract_references(text: str) -> list[str]:
    """Scan text for standard codes like VAS 15, IFRS 15, IAS 12."""
    refs = []
    # Matches 'VAS 15', 'IFRS 15', 'IAS-12', etc.
    pattern = r"\b(VAS|IAS|IFRS|VFRS)[\s\-]?(\d+[A-Z]?)\b"
    for m in re.finditer(pattern, text, re.IGNORECASE):
        prefix = m.group(1).upper()
        num = m.group(2)
        refs.append(f"{prefix}-{num}")
    return list(set(refs))


def build_graph(docs_dir: Path) -> nx.DiGraph:
    # 1. Setup paths to import unstructured_runner and backend modules
    parsers_dir = Path(__file__).parent / "parsers"
    sys.path.insert(0, str(parsers_dir))
    # pyrefly: ignore [missing-import]
    from unstructured_runner import parse_document, _PARSERS

    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "apps" / "backend"))
    # pyrefly: ignore [missing-import]
    from app.rag.chunker import chunk_document
    # pyrefly: ignore [missing-import]
    from app.gl.coa_loader import load_coa

    G = nx.DiGraph()

    # 2. Parse all documents in the directories
    parsed_docs: list[dict] = []
    for fp in sorted(docs_dir.rglob("*")):
        if fp.suffix.lower() not in _PARSERS:
            continue
        try:
            doc = parse_document(fp)
            parsed_docs.append(doc)
            logger.info("Parsed %s for graph", fp.name)
        except Exception as exc:
            logger.error("Failed parsing %s for graph: %s", fp.name, exc)

    # 3. Add nodes and edges
    standard_nodes: dict[str, str] = {}  # standard_code -> doc_node_id
    chunk_nodes: list[dict] = []         # temp storage to build links later

    for doc in parsed_docs:
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, doc["source_path"]))
        std_code = doc.get("standard_code")

        # Document Node
        G.add_node(
            doc_id,
            id=doc_id,
            type="document",
            filename=doc["filename"],
            standard_code=std_code,
            lang=doc.get("lang", "bi"),
        )

        if std_code:
            standard_nodes[std_code.upper()] = doc_id

        # Chunks (Sections)
        chunks = chunk_document(
            doc["text"],
            section_path="",
            heading="",
            lang=doc.get("lang", "bi"),
        )

        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            
            # Section Node
            G.add_node(
                chunk_id,
                id=chunk_id,
                type="section",
                text_preview=chunk.text[:200],
                heading=chunk.heading,
                lang=chunk.lang,
                standard_code=std_code,
                doc_id=doc_id,
            )

            # HAS_SECTION edge
            G.add_edge(doc_id, chunk_id, relation="HAS_SECTION")

            chunk_nodes.append({
                "id": chunk_id,
                "text": chunk.text,
                "standard_code": std_code,
            })

    logger.info("Added %d document nodes and %d section nodes", len(parsed_docs), len(chunk_nodes))

    # 4. Add REFERS_TO and MAPS_TO edges
    for c_node in chunk_nodes:
        # Cross references inside text
        refs = _extract_references(c_node["text"])
        for ref in refs:
            ref_upper = ref.upper()
            if ref_upper in standard_nodes:
                target_doc_id = standard_nodes[ref_upper]
                # Add REFERS_TO relation to the target document
                G.add_edge(c_node["id"], target_doc_id, relation="REFERS_TO")

        # Explicit VAS -> IFRS Mapping alignment
        curr_std = c_node["standard_code"]
        if curr_std:
            curr_std_upper = curr_std.upper()
            if curr_std_upper in VAS_IFRS_MAPPING:
                target_std = VAS_IFRS_MAPPING[curr_std_upper]
                if target_std in standard_nodes:
                    target_doc_id = standard_nodes[target_std]
                    G.add_edge(c_node["id"], target_doc_id, relation="MAPS_TO")

    # 5. Add Account Nodes & GOVERNED_BY edges from COA loader
    try:
        vas_coa = load_coa("VAS")
        for acc_code, meta in vas_coa.items():
            acc_node_id = f"acc_{acc_code}"
            
            # Account Node
            G.add_node(
                acc_node_id,
                id=acc_node_id,
                type="account",
                account_code=acc_code,
                name_vi=meta.get("name_vi"),
                name_en=meta.get("name_en"),
                category=meta.get("category"),
            )

            # Map account to governing standards
            # Best effort logic based on account categories
            gov_std = None
            if acc_code.startswith("242"):
                gov_std = "IFRS-16"  # Leases / Prepaid
            elif acc_code.startswith("111") or acc_code.startswith("112"):
                gov_std = "IAS-1"    # Cash Presentation
            elif acc_code.startswith("511"):
                gov_std = "IFRS-15"   # Revenue

            if gov_std and gov_std in standard_nodes:
                target_doc_id = standard_nodes[gov_std]
                G.add_edge(acc_node_id, target_doc_id, relation="GOVERNED_BY")
    except Exception as e:
        logger.warning("Could not add COA accounts to graph: %s", e)

    return G


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Build VAS-IFRS Cross-reference Graph")
    parser.add_argument("--docs", required=True, help="Directory containing raw PDF/DOCX standards")
    parser.add_argument("--output", required=True, help="Output JSON path for NetworkX serialization")
    args = parser.parse_args()

    docs_path = Path(args.docs)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Building graph from documents in: {docs_path}")
    G = build_graph(docs_path)

    # Serialize using node_link_data format
    data = json_graph.node_link_data(G)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Graph serialized successfully to: {output_path}")
    print(f"Graph Stats: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")


if __name__ == "__main__":
    main()
