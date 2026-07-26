"""Regression tests for adventure five-scene orphan and simulate-cut behaviour."""

from __future__ import annotations

from pathlib import Path

from scriptlens_structure import analyze_structure_from_path, get_simulate_cut_impact

ADVENTURE_SCRIPT = Path("tests/corpus/input/adventure_5scene_errors.fountain")


def test_adventure_backstory_scene_is_not_orphan() -> None:
    """Scene 2 feeds forward into the June thread and must not be a hard orphan."""
    results = analyze_structure_from_path(ADVENTURE_SCRIPT, include_engine=True)
    orphan_ids = {record["scene_id"] for record in results["structure"]["orphans"]}
    assert orphan_ids == set()


def test_adventure_cut_backstory_scene_has_story_function_impact() -> None:
    """Cutting the father backstory beat is not blankly safe under SFI D-lite."""
    results = analyze_structure_from_path(ADVENTURE_SCRIPT, include_engine=True)
    engine = results["engine"]
    impact = get_simulate_cut_impact(engine, "scene_002", engine._scene_lookup)
    assert impact["risk_level"] != "none"
    assert "Safe to cut" not in impact["summary"]
