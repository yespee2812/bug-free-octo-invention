"""Regression tests for comedy five-scene orphan and guest-book linkage."""

from __future__ import annotations

from pathlib import Path

from scriptlens_structure import analyze_structure_from_path, get_simulate_cut_impact

COMEDY_SCRIPT = Path("tests/corpus/input/comedy_5scene_errors.fountain")


def test_magnetic_guest_book_is_prop_not_character() -> None:
    """Scene 2 plants the guest book as a prop, not a speaking character."""
    results = analyze_structure_from_path(COMEDY_SCRIPT, include_engine=True)
    scene_two = results["engine"]._scene_lookup["scene_002"]
    assert "MAGNETIC GUEST BOOK" in scene_two.props_detected
    assert "MAGNETIC GUEST BOOK" not in scene_two.characters


def test_rehearsal_dinner_ban_scene_is_not_orphan() -> None:
    """Diane's no-props beat stays linked into the guest-book story graph."""
    results = analyze_structure_from_path(COMEDY_SCRIPT, include_engine=True)
    orphan_ids = {record["scene_id"] for record in results["structure"]["orphans"]}
    assert "scene_003" not in orphan_ids


def test_cutting_ban_scene_is_not_safe() -> None:
    """Removing the mother-in-law ban must not report a blank safe cut."""
    results = analyze_structure_from_path(COMEDY_SCRIPT, include_engine=True)
    engine = results["engine"]
    impact = get_simulate_cut_impact(engine, "scene_003", engine._scene_lookup)
    assert impact["risk_level"] in {"medium", "high"}
    assert "Safe to cut" not in impact["summary"]
    impacted_ids = {row["scene_id"] for row in impact["impacted_scenes"]}
    assert impacted_ids & {"scene_004", "scene_005"}


def test_cutting_guest_book_chaos_scene_is_not_low_risk() -> None:
    """Scene 4 escalation (stuck guest book) must not read as low structural risk."""
    results = analyze_structure_from_path(COMEDY_SCRIPT, include_engine=True)
    engine = results["engine"]
    impact = get_simulate_cut_impact(engine, "scene_004", engine._scene_lookup)
    assert impact["risk_level"] in {"medium", "high"}
    assert "Low structural risk" not in impact["summary"]
    assert "Safe to cut" not in impact["summary"]
    impacted_ids = {row["scene_id"] for row in impact["impacted_scenes"]}
    assert "scene_005" in impacted_ids
