"""Tests for Scene Function Impact (SFI) D-lite cut verdicts."""

from __future__ import annotations

from pathlib import Path

from scene_function_impact import (
    evaluate_scene_function_cut,
    extract_scene_functions,
)
from scriptlens_structure import analyze_structure_from_path, get_simulate_cut_impact

ADVENTURE_SCRIPT = Path("tests/corpus/input/adventure_5scene_errors.fountain")


def _adventure_engine() -> tuple[object, object]:
    """Load adventure script structure analysis with engine attached."""
    results = analyze_structure_from_path(ADVENTURE_SCRIPT, include_engine=True)
    return results["engine"], results["engine"]._scene_lookup


def test_adventure_extracts_core_story_functions() -> None:
    """Adventure scenes receive plant / reveal / directive / pursuit / payoff beats."""
    engine, _lookup = _adventure_engine()
    functions = extract_scene_functions(engine.scenes)
    types_by_scene = {
        scene_id: {item.function_type for item in items}
        for scene_id, items in functions.items()
    }

    assert "plant_object" in types_by_scene["scene_001"]
    assert "reveal" in types_by_scene["scene_002"]
    assert "directive" in types_by_scene["scene_003"]
    assert "pursuit" in types_by_scene["scene_004"]
    assert "payoff" in types_by_scene["scene_005"]


def test_adventure_cut_scene_three_not_safe() -> None:
    """Cutting the sketch/directive beat must not report safe."""
    engine, lookup = _adventure_engine()
    impact = get_simulate_cut_impact(engine, "scene_003", lookup)

    assert impact["risk_level"] in {"medium", "high"}
    assert "Safe to cut" not in impact["summary"]
    impacted_ids = {row["scene_id"] for row in impact["impacted_scenes"]}
    assert "scene_004" in impacted_ids or "scene_005" in impacted_ids


def test_adventure_cut_scene_four_not_safe_bridge() -> None:
    """Cutting the pursuit carrier into the cave payoff is not safe."""
    engine, lookup = _adventure_engine()
    impact = get_simulate_cut_impact(engine, "scene_004", lookup)
    sfi = evaluate_scene_function_cut(engine.scenes, "scene_004")

    assert sfi.is_bridge or sfi.lost_functions
    assert impact["risk_level"] in {"medium", "high"}
    assert "Safe to cut" not in impact["summary"]
    impacted_ids = {row["scene_id"] for row in impact["impacted_scenes"]}
    assert "scene_005" in impacted_ids


def test_adventure_cut_scene_two_not_safe() -> None:
    """Father-reveal beat feeds later directive/payoff scenes."""
    engine, lookup = _adventure_engine()
    impact = get_simulate_cut_impact(engine, "scene_002", lookup)

    assert impact["risk_level"] in {"low", "medium", "high"}
    assert "Safe to cut" not in impact["summary"]


def test_adventure_cut_scene_five_can_be_safe() -> None:
    """Terminal payoff scene may still be structurally safe to cut."""
    engine, lookup = _adventure_engine()
    impact = get_simulate_cut_impact(engine, "scene_005", lookup)

    assert impact["risk_level"] == "none"
    assert "Safe to cut" in impact["summary"]


COMING_OF_AGE_SCRIPT = Path("tests/corpus/input/coming_of_age_5scene_errors.fountain")


def _coming_of_age_engine() -> tuple[object, object]:
    """Load coming-of-age structure analysis with engine attached."""
    results = analyze_structure_from_path(COMING_OF_AGE_SCRIPT, include_engine=True)
    return results["engine"], results["engine"]._scene_lookup


def test_coming_of_age_extracts_relationship_arc() -> None:
    """Senior-week script maps onto promise → decision → pursuit → crisis → payoff."""
    engine, _lookup = _coming_of_age_engine()
    functions = extract_scene_functions(engine.scenes)
    types_by_scene = {
        scene_id: {item.function_type for item in items}
        for scene_id, items in functions.items()
    }

    assert "promise" in types_by_scene["scene_001"]
    assert "decision" in types_by_scene["scene_002"]
    assert "pursuit" in types_by_scene["scene_003"]
    assert "crisis" in types_by_scene["scene_004"]
    assert "payoff" in types_by_scene["scene_005"]


def test_coming_of_age_middle_scenes_not_safe_to_cut() -> None:
    """Decision / show / backstage beats are not blankly cuttable."""
    engine, lookup = _coming_of_age_engine()
    for scene_id in ("scene_002", "scene_003", "scene_004"):
        impact = get_simulate_cut_impact(engine, scene_id, lookup)
        assert impact["risk_level"] in {"medium", "high"}, scene_id
        assert "Safe to cut" not in impact["summary"], scene_id
        assert impact["impacted_scenes"], scene_id


def test_coming_of_age_terminal_payoff_not_called_safe() -> None:
    """Closing relationship landing warns instead of saying safe to cut."""
    engine, lookup = _coming_of_age_engine()
    impact = get_simulate_cut_impact(engine, "scene_005", lookup)
    assert impact["risk_level"] == "low"
    assert "Safe to cut" not in impact["summary"]
    assert "payoff" in impact["summary"].lower() or "landing" in impact["summary"].lower()
