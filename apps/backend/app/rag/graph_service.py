"""
Graph Service: loads serialized NetworkX graph and provides lookup APIs for retrieval expansion.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)

_GRAPH: nx.DiGraph | None = None


def get_graph() -> nx.DiGraph:
    """Load graph into memory (singleton pattern)."""
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH

    # Locate the graph file relative to this file
    # File is at: apps/backend/app/rag/graph_service.py
    # 5 levels up to repo root: apps/backend/app/rag/graph_service.py -> app/rag/ -> app/ -> backend/ -> apps/ -> root/
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    graph_path = (
        repo_root / "ingestion" / "metadata" / "paragraph_graph" / "cross_reference_graph.json"
    )

    if not graph_path.exists():
        logger.warning("Graph file not found at %s. Initialising empty graph.", graph_path)
        _GRAPH = nx.DiGraph()
        return _GRAPH

    try:
        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _GRAPH = json_graph.node_link_graph(data)
        logger.info(
            "Graph loaded successfully: %d nodes, %d edges",
            _GRAPH.number_of_nodes(),
            _GRAPH.number_of_edges(),
        )
    except Exception as exc:
        logger.error("Failed to load graph: %s. Fallback to empty graph.", exc)
        _GRAPH = nx.DiGraph()

    return _GRAPH


def get_related_sections(section_id: str, depth: int = 1) -> list[str]:
    """
    Find section node IDs (UUIDs) connected to the given section_id.
    Follows REFERS_TO and MAPS_TO relations.
    """
    G = get_graph()
    if section_id not in G:
        return []

    related = set()
    # Queue for BFS traversal
    queue = [(section_id, 0)]
    visited = {section_id}

    while queue:
        curr, curr_depth = queue.pop(0)
        if curr_depth >= depth:
            continue

        # Look at outgoing edges
        for neighbor in G.successors(curr):
            if neighbor in visited:
                continue
            edge_data = G.get_edge_data(curr, neighbor) or {}
            rel = edge_data.get("relation")

            if rel in ("REFERS_TO", "MAPS_TO", "HAS_SECTION"):
                visited.add(neighbor)
                node_data = G.nodes[neighbor]
                if node_data.get("type") == "section":
                    related.add(neighbor)
                queue.append((neighbor, curr_depth + 1))

    return list(related)


def get_ifrs_equivalents(vas_section_id: str) -> list[str]:
    """
    Find IFRS sections mapped to a given VAS section.
    """
    G = get_graph()
    if vas_section_id not in G:
        return []

    equivalents = []
    for neighbor in G.successors(vas_section_id):
        edge_data = G.get_edge_data(vas_section_id, neighbor) or {}
        if edge_data.get("relation") == "MAPS_TO":
            node_data = G.nodes[neighbor]
            if node_data.get("type") == "section":
                equivalents.append(neighbor)
            elif node_data.get("type") == "document":
                # If mapped to a document, fetch all sections of that document
                for child in G.successors(neighbor):
                    child_edge = G.get_edge_data(neighbor, child) or {}
                    if child_edge.get("relation") == "HAS_SECTION":
                        equivalents.append(child)

    return list(set(equivalents))


def get_governed_sections_for_account(account_code: str) -> list[str]:
    """
    Find section IDs governing a given account code.
    """
    G = get_graph()
    acc_node_id = f"acc_{account_code}"
    if acc_node_id not in G:
        return []

    sections = []
    for neighbor in G.successors(acc_node_id):
        edge_data = G.get_edge_data(acc_node_id, neighbor) or {}
        if edge_data.get("relation") == "GOVERNED_BY":
            node_data = G.nodes[neighbor]
            if node_data.get("type") == "section":
                sections.append(neighbor)
            elif node_data.get("type") == "document":
                # If governed by document, fetch all its sections
                for child in G.successors(neighbor):
                    child_edge = G.get_edge_data(neighbor, child) or {}
                    if child_edge.get("relation") == "HAS_SECTION":
                        sections.append(child)

    return list(set(sections))
