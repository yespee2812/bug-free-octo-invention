"""Run simulate demo analysis on the five-scene action script."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scriptlens_structure import (
    analyze_structure_from_path,
    get_simulate_cut_impact,
    get_simulate_edit_impact,
)


def main() -> None:
    """Print orphan, simulate cut, and simulate edit results for the demo script."""
    path = Path("docs/demo_scripts/action_5scene_simulate_demo.fountain")
    results = analyze_structure_from_path(path, include_engine=True)
    engine = results["engine"]
    lookup = engine._scene_lookup
    structure = results["structure"]
    screenplay_text = path.read_text(encoding="utf-8")

    print("=== SCENES ===")
    for scene in engine.scenes:
        print(f"  {scene.scene_id} #{scene.scene_number}: {scene.heading[:50]}")

    print("\n=== ORPHANS ===")
    orphans = structure["orphans"]
    if not orphans:
        print("  (none)")
    for record in orphans:
        orphan_type = record.get("orphan_type", "?")
        print(f"  {record['scene_id']} #{record['scene_number']}: {orphan_type} — {record['heading'][:40]}")

    print("\n=== SIMULATE CUT scene_001 (warehouse / briefcase setup) ===")
    cut = get_simulate_cut_impact(engine, "scene_001", lookup)
    print(f"  Risk: {cut['risk_level']}")
    print(f"  Summary: {cut['summary']}")
    impacted = [row["scene_id"] for row in cut["impacted_scenes"]]
    print(f"  Impacted: {impacted}")

    print("\n=== SIMULATE EDIT scene_001 (remove briefcase setup) ===")
    scene_one = lookup["scene_001"]
    edited = scene_one.raw_text.replace("STEEL BRIEFCASE", "EMPTY CRATE").replace(
        "Stacks of banded cash inside.",
        "Nothing inside.",
    )
    edit = get_simulate_edit_impact(engine, screenplay_text, "scene_001", edited)
    print(f"  Risk: {edit['risk_level']}")
    print(f"  Summary: {edit['summary']}")
    removed = edit["edge_diff"]["removed"]
    print(f"  Edges removed: {len(removed)}")
    for edge in removed[:8]:
        print(f"    {edge}")
    print(f"  Orphan delta: {edit['orphan_delta']}")


if __name__ == "__main__":
    main()
