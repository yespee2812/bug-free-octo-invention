"""Diagnose orphan and simulate-cut behaviour on adventure 5-scene script."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scriptlens_structure import analyze_structure_from_path, get_simulate_cut_impact

SCRIPT = _REPO_ROOT / "tests/corpus/input/adventure_5scene_errors.fountain"


def main() -> None:
    """Print orphan, OSD, continuity, and simulate-cut diagnostics."""
    results = analyze_structure_from_path(SCRIPT, include_engine=True)
    engine = results["engine"]
    lookup = engine._scene_lookup

    print("=== SCENES ===")
    for scene in engine.scenes:
        print(f"  {scene.scene_id} #{scene.scene_number}: {scene.heading}")

    print("\n=== ORPHANS ===")
    for record in results["structure"]["orphans"]:
        print(f"  {record['scene_id']} type={record['orphan_type']}")
        for reason in record.get("reasons", []):
            print(f"    - {reason}")

    orphan_graph = getattr(engine, "orphan_graph", None)
    if orphan_graph is not None:
        print("\n=== OSD GRAPH EDGES ===")
        for source, target, data in orphan_graph.edges(data=True):
            weight = data.get("weight", "?")
            print(f"  {source} -> {target}  W={weight}")

    print("\n=== CONTINUITY GRAPH EDGES ===")
    for source, target, data in engine.graph.edges(data=True):
        explanation = data.get("explanation", "")[:100]
        print(f"  {source} -> {target} ({data.get('edge_type')}): {explanation}")

    print("\n=== SIMULATE CUT scene_002 ===")
    cut = get_simulate_cut_impact(engine, "scene_002", lookup)
    print(f"  risk={cut['risk_level']} summary={cut['summary']}")
    for row in cut["impacted_scenes"]:
        print(f"    {row['scene_id']}: {row.get('impact_reason', '')}")


if __name__ == "__main__":
    main()
