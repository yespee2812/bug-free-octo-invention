"""Serialize the OSD orphan graph for client-side visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from orphan_scene_detector import LINK_THRESHOLD

if TYPE_CHECKING:
    from scene_dependency import SceneDependencyEngine


def build_orphan_graph_view_payload(
    engine: SceneDependencyEngine,
    orphans: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build API-ready orphan graph nodes and edges for the web viewer.

    Args:
        engine: Session engine with ``orphan_graph`` populated.
        orphans: Stored orphan finding records for the session.

    Returns:
        Dictionary with ``nodes``, ``edges``, and ``stats`` keys.
    """
    graph = engine.orphan_graph
    orphan_lookup = {record["scene_id"]: record for record in orphans}

    nodes: list[dict[str, Any]] = []
    for scene_id in sorted(
        graph.nodes,
        key=lambda node_id: graph.nodes[node_id].get("scene_number", 0),
    ):
        node_data = graph.nodes[scene_id]
        orphan_record = orphan_lookup.get(scene_id)
        nodes.append(
            {
                "scene_id": scene_id,
                "scene_number": int(node_data.get("scene_number", 0)),
                "heading": str(node_data.get("heading", "")),
                "is_orphan": orphan_record is not None,
                "orphan_type": orphan_record.get("orphan_type") if orphan_record else None,
                "in_degree": graph.in_degree(scene_id),
                "out_degree": graph.out_degree(scene_id),
            }
        )

    edges: list[dict[str, Any]] = []
    for source_id, target_id, data in graph.edges(data=True):
        edges.append(
            {
                "from_scene_id": source_id,
                "to_scene_id": target_id,
                "weight": float(data.get("weight", 0.0)),
                "explanation": str(data.get("explanation", "")),
                "character": float(data.get("character", 0.0)),
                "spatial": float(data.get("spatial", 0.0)),
                "prop": float(data.get("prop", 0.0)),
                "semantic": float(data.get("semantic", 0.0)),
            }
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "scene_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "orphan_count": len(orphans),
            "link_threshold": LINK_THRESHOLD,
        },
    }
