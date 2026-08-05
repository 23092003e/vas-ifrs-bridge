"""
Graph Builder: scans raw documents, parses/chunks them, extracts cross-references,
aligns VAS and IFRS, and serializes the NetworkX graph to JSON.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import uuid
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)

# Standard mappings VAS -> IFRS
VAS_IFRS_MAPPING = {
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
    return sorted(set(refs))


def _extract_paragraph_number(text: str) -> str | None:
    """Match starting pattern of paragraph numbers like '31.', 'B34.', 'IE47.'"""
    text_strip = text.strip()
    m = re.match(r"^(?:Paragraph|para\.|section|Khoản|Điều)?\s*\b(B\d+|IE\d+|\d+)\b", text_strip, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def _load_metadata(path: Path, label: str) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"failed to load graph {label}: {path}") from exc
    if not isinstance(data, list):
        raise TypeError(f"graph {label} must contain a JSON array: {path}")
    return data


def build_graph(docs_dir: Path) -> nx.DiGraph:
    # 1. Setup paths to import unstructured_runner and backend modules
    parsers_dir = Path(__file__).parent / "parsers"
    sys.path.insert(0, str(parsers_dir))
    # pyrefly: ignore [missing-import]
    from unstructured_runner import _PARSERS, parse_document

    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "apps" / "backend"))
    # pyrefly: ignore [missing-import]
    from app.gl.coa_loader import load_coa

    # pyrefly: ignore [missing-import]
    from app.rag.chunker import chunk_document

    G = nx.DiGraph()

    # Load topic ontology from json files
    metadata_dir = Path(__file__).parent.parent / "metadata" / "ontology"
    topics_path = metadata_dir / "accounting_topics.json"
    relations_path = metadata_dir / "vas_ifrs_relations.json"

    topics = _load_metadata(topics_path, "topics")

    # Add Topic Nodes to Graph
    for topic in topics:
        topic_node_id = f"topic_{topic['topic_id']}"
        G.add_node(
            topic_node_id,
            id=topic_node_id,
            type="topic",
            topic_name=topic["topic_name"],
            aliases=topic.get("aliases", []),
        )

    # Link topic nodes with related_topic relations
    for topic in topics:
        topic_node_id = f"topic_{topic['topic_id']}"
        for rel_topic_id in topic.get("related_topics", []):
            rel_node_id = f"topic_{rel_topic_id}"
            G.add_edge(topic_node_id, rel_node_id, relation="related_topic")

    # 2. Parse all documents in the directories
    parsed_docs: list[dict] = []
    parse_errors: list[tuple[Path, Exception]] = []
    for fp in sorted(docs_dir.rglob("*")):
        if fp.suffix.lower() not in _PARSERS:
            continue
        try:
            doc = parse_document(fp)
            parsed_docs.append(doc)
            logger.info("Parsed %s for graph", fp.name)
        # Parser adapters can raise heterogeneous third-party exceptions.
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed parsing %s for graph: %s", fp.name, exc)
            parse_errors.append((fp, exc))

    if parse_errors:
        count = len(parse_errors)
        raise RuntimeError(
            f"failed to parse {count} graph document{'s' if count != 1 else ''}"
        ) from parse_errors[0][1]

    # 3. Add nodes and edges
    standard_nodes: dict[str, str] = {}  # standard_code -> doc_node_id
    chunk_nodes: list[dict] = []         # temp storage to build links later
    paragraph_to_chunk_id: dict[str, str] = {} # standard_code.paragraph -> chunk_id

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
            chunk_id = str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{chunk.chunk_index}")
            )
            
            para_num = _extract_paragraph_number(chunk.text)
            para_code = None
            if para_num and std_code:
                para_code = f"{std_code.upper()}.{para_num.upper()}"
                paragraph_to_chunk_id[para_code] = chunk_id

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
                paragraph=para_num,
                paragraph_code=para_code,
            )

            # HAS_SECTION edge
            G.add_edge(doc_id, chunk_id, relation="HAS_SECTION")

            chunk_nodes.append({
                "id": chunk_id,
                "text": chunk.text,
                "standard_code": std_code,
            })

    logger.info("Added %d document nodes and %d section nodes", len(parsed_docs), len(chunk_nodes))

    # Add standard-level equivalent_standard relations from ontology relations
    relations = _load_metadata(relations_path, "relations")

    for rel in relations:
        vas_std = rel.get("vas")
        ifrs_std = rel.get("ifrs")
        ias_std = rel.get("ias")
        stds = [std for std in [vas_std, ifrs_std, ias_std] if std and std != "None"]
        for i in range(len(stds)):
            for j in range(i + 1, len(stds)):
                node_a = stds[i].upper()
                node_b = stds[j].upper()
                if node_a in standard_nodes and node_b in standard_nodes:
                    G.add_edge(standard_nodes[node_a], standard_nodes[node_b], relation="equivalent_standard")
                    G.add_edge(standard_nodes[node_b], standard_nodes[node_a], relation="equivalent_standard")

        # Link document to matched topic node
        matched_topic_id = None
        topic_name_lower = rel["topic"].lower()
        for topic in topics:
            if topic["topic_name"].lower() == topic_name_lower:
                matched_topic_id = f"topic_{topic['topic_id']}"
                break
        if matched_topic_id:
            for std in stds:
                std_upper = std.upper()
                if std_upper in standard_nodes:
                    G.add_edge(standard_nodes[std_upper], matched_topic_id, relation="related_topic")

    # Add standard-level supersedes relations
    SUPERSEDES_MAPPING = {
        "IFRS-15": ["IAS-18", "IAS-11"],
        "IFRS-16": ["IAS-17"],
        "IFRS-10": ["IAS-27", "SIC-12"],
    }
    for new_std, old_stds in SUPERSEDES_MAPPING.items():
        if new_std in standard_nodes:
            new_doc_id = standard_nodes[new_std]
            for old_std in old_stds:
                if old_std in standard_nodes:
                    old_doc_id = standard_nodes[old_std]
                    G.add_edge(new_doc_id, old_doc_id, relation="supersedes")

    # 4. Add REFERS_TO, MAPS_TO, references, and example_of edges
    for c_node in chunk_nodes:
        # Cross references inside text (document-level)
        refs = _extract_references(c_node["text"])
        for ref in refs:
            ref_upper = ref.upper()
            if ref_upper in standard_nodes:
                target_doc_id = standard_nodes[ref_upper]
                # Add REFERS_TO relation to the target document
                G.add_edge(c_node["id"], target_doc_id, relation="REFERS_TO")

        # Explicit VAS -> IFRS Mapping alignment (document-level)
        curr_std = c_node["standard_code"]
        if curr_std:
            curr_std_upper = curr_std.upper()
            if curr_std_upper in VAS_IFRS_MAPPING:
                target_std = VAS_IFRS_MAPPING[curr_std_upper]
                if target_std in standard_nodes:
                    target_doc_id = standard_nodes[target_std]
                    G.add_edge(c_node["id"], target_doc_id, relation="MAPS_TO")
                    
                    # Also link standard documents with equivalent_standard
                    curr_doc_id = standard_nodes[curr_std_upper]
                    G.add_edge(curr_doc_id, target_doc_id, relation="equivalent_standard")
                    G.add_edge(target_doc_id, curr_doc_id, relation="equivalent_standard")

            # Section-level paragraph cross-references
            # Matches paragraph numbers in text e.g., "...paragraph B34..."
            ref_pattern = r"\b(?:paragraph|para\.|section|Khoản|Điều|Ví dụ|IE|B)\s*(B\d+|IE\d+|\d+)\b"
            found_paras = re.findall(ref_pattern, c_node["text"], re.IGNORECASE)
            for para_ref in found_paras:
                ref_para_code = f"{curr_std_upper}.{para_ref.upper()}"
                if ref_para_code in paragraph_to_chunk_id:
                    target_chunk_id = paragraph_to_chunk_id[ref_para_code]
                    if target_chunk_id != c_node["id"]:
                        relation = "example_of" if para_ref.upper().startswith("IE") else "references"
                        G.add_edge(c_node["id"], target_chunk_id, relation=relation)

            # Cross-standard paragraph references e.g. "IFRS 15.31"
            cross_pattern = r"\b(VAS|IAS|IFRS|VFRS)[\s\-]?(\d+[A-Z]?)\b\.((?:IE|B)?\d+)\b"
            for m in re.finditer(cross_pattern, c_node["text"], re.IGNORECASE):
                prefix = m.group(1).upper()
                num = m.group(2)
                para = m.group(3).upper()
                cross_para_code = f"{prefix}-{num}.{para}"
                if cross_para_code in paragraph_to_chunk_id:
                    target_chunk_id = paragraph_to_chunk_id[cross_para_code]
                    if target_chunk_id != c_node["id"]:
                        G.add_edge(c_node["id"], target_chunk_id, relation="references")

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
            elif acc_code.startswith(("111", "112")):
                gov_std = "IAS-1"    # Cash Presentation
            elif acc_code.startswith("511"):
                gov_std = "IFRS-15"   # Revenue

            if gov_std and gov_std in standard_nodes:
                target_doc_id = standard_nodes[gov_std]
                G.add_edge(acc_node_id, target_doc_id, relation="GOVERNED_BY")
    # COA enrichment is optional and depends on external workbook parsers.
    except Exception as e:  # noqa: BLE001
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
