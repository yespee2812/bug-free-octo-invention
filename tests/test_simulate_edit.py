"""Tests for simulate-edit structure analysis."""

from __future__ import annotations

import pytest

from scriptlens_structure import analyze_structure, get_simulate_edit_impact

CHAINED_PROP_SCRIPT = """INT. ROOM ONE - DAY

A REVOLVER lies on the table.

INT. ROOM TWO - DAY

MARCUS grabs the revolver.

INT. ROOM THREE - NIGHT

MARCUS aims the revolver.
"""


def test_simulate_edit_removing_prop_drops_edges() -> None:
    """Removing a prop from the introducing scene drops downstream edges."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    engine = results["engine"]

    impact = get_simulate_edit_impact(
        engine,
        CHAINED_PROP_SCRIPT,
        "scene_001",
        "INT. ROOM ONE - DAY\n\nAn empty table.",
    )

    removed_pairs = {
        (row["from_scene_id"], row["to_scene_id"])
        for row in impact["edge_diff"]["removed"]
    }
    assert ("scene_001", "scene_002") in removed_pairs
    assert "scene_002" in {
        row["scene_id"] for row in impact["downstream_at_risk"]
    }


def test_simulate_edit_unknown_scene_raises() -> None:
    """Unknown scene ids raise ValueError."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    engine = results["engine"]

    with pytest.raises(ValueError, match="Unknown scene_id"):
        get_simulate_edit_impact(engine, CHAINED_PROP_SCRIPT, "scene_999", "INT. A - DAY")


def test_simulate_edit_without_slugline_prepends_heading() -> None:
    """Modified text without a slugline keeps the original heading."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    engine = results["engine"]

    impact = get_simulate_edit_impact(
        engine,
        CHAINED_PROP_SCRIPT,
        "scene_001",
        "An empty table.",
    )

    assert impact["scene_id"] == "scene_001"
    assert impact["edge_diff"]["removed"]
