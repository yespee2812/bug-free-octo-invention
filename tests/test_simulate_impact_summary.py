"""Tests for plain-English simulate impact summaries."""

from __future__ import annotations

from scriptlens_structure import analyze_structure, get_simulate_cut_impact, get_simulate_edit_impact

CHAINED_PROP_SCRIPT = """INT. ROOM ONE - DAY

A REVOLVER lies on the table.

INT. ROOM TWO - DAY

MARCUS grabs the revolver.

INT. ROOM THREE - NIGHT

MARCUS aims the revolver.
"""


def test_simulate_cut_summary_safe_when_no_downstream() -> None:
    """Cutting the last scene in a chain reports a safe summary."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    engine = results["engine"]
    impact = get_simulate_cut_impact(engine, "scene_003", engine._scene_lookup)

    assert impact["risk_level"] == "none"
    assert "Safe to cut" in impact["summary"]
    assert impact["impacted_scenes"] == []


def test_simulate_cut_summary_flags_downstream_scenes() -> None:
    """Cutting a carrier scene reports enriched downstream rows."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    engine = results["engine"]
    impact = get_simulate_cut_impact(engine, "scene_002", engine._scene_lookup)

    assert impact["risk_level"] in {"low", "medium", "high"}
    assert "Scene 2" in impact["summary"]
    assert len(impact["impacted_scenes"]) == 1
    row = impact["impacted_scenes"][0]
    assert row["scene_id"] == "scene_003"
    assert row["impact_reason"]
    assert row["link_hops"] >= 1


def test_simulate_edit_summary_and_downstream_reasons() -> None:
    """Simulate edit returns headline summary and structured at-risk rows."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    engine = results["engine"]

    impact = get_simulate_edit_impact(
        engine,
        CHAINED_PROP_SCRIPT,
        "scene_001",
        "INT. ROOM ONE - DAY\n\nAn empty table.",
    )

    assert impact["summary"]
    assert impact["risk_level"] in {"low", "medium", "high"}
    assert "removes" in impact["summary"]
    assert impact["orphan_delta"]["message"]
    assert impact["downstream_at_risk"]
    at_risk = impact["downstream_at_risk"][0]
    assert at_risk["scene_id"] == "scene_002"
    assert at_risk["reason"]
