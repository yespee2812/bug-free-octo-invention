"""Golden tests for the five-scene action simulate demo script."""

from __future__ import annotations

from pathlib import Path

from scriptlens_structure import (
    analyze_structure_from_path,
    get_simulate_cut_impact,
    get_simulate_edit_impact,
)

DEMO_SCRIPT = Path("docs/demo_scripts/action_5scene_simulate_demo.fountain")

EDITED_SCENE_ONE = """INT. ABANDONED WAREHOUSE - NIGHT

GINA VASQUEZ, 32, ex-driver, pries open an EMPTY CRATE on a crate. Nothing inside.

GINA
Still heavy. Good.
"""


def test_action_demo_orphan_scene_two() -> None:
    """Scene 2 (motorcycle alley) is a hard orphan."""
    results = analyze_structure_from_path(DEMO_SCRIPT, include_engine=True)
    orphan_ids = {record["scene_id"] for record in results["structure"]["orphans"]}
    assert orphan_ids == {"scene_002"}


def test_action_demo_simulate_cut_scene_one() -> None:
    """Cutting scene 1 breaks the briefcase chain through scene 5."""
    results = analyze_structure_from_path(DEMO_SCRIPT, include_engine=True)
    engine = results["engine"]
    impact = get_simulate_cut_impact(engine, "scene_001", engine._scene_lookup)
    impacted = {row["scene_id"] for row in impact["impacted_scenes"]}
    assert impacted == {"scene_003", "scene_004", "scene_005"}
    assert impact["risk_level"] == "high"


def test_action_demo_simulate_edit_scene_one() -> None:
    """Removing the briefcase from scene 1 drops dependency edges."""
    results = analyze_structure_from_path(DEMO_SCRIPT, include_engine=True)
    engine = results["engine"]
    screenplay_text = DEMO_SCRIPT.read_text(encoding="utf-8")
    impact = get_simulate_edit_impact(
        engine,
        screenplay_text,
        "scene_001",
        EDITED_SCENE_ONE,
    )
    assert len(impact["edge_diff"]["removed"]) >= 1
    assert impact["risk_level"] in {"medium", "high"}
    assert impact["orphan_delta"]["before"] == 1
    assert impact["orphan_delta"]["after"] == 1
