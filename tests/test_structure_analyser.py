"""Tests for structure-only ScriptLens analysis (v3 product path)."""

from __future__ import annotations

from pathlib import Path

from scriptlens_structure import (
    analyze_structure,
    analyze_structure_from_path,
    detect_structure_mode,
    get_simulate_cut_impact,
)

CHAINED_PROP_SCRIPT = """INT. ROOM ONE - DAY

A REVOLVER lies on the table.

INT. ROOM TWO - DAY

MARCUS grabs the revolver.

INT. ROOM THREE - NIGHT

MARCUS aims the revolver.
"""


def test_structure_report_excludes_contradictions() -> None:
    """Structure analysis must not include a contradictions block."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    assert "contradictions" not in results
    assert "structure" in results
    assert results["script_summary"]["total_scenes"] == 3


def test_orphan_detection_in_structure_path() -> None:
    """Orphan scenes are reported in the structure block."""
    script = (
        "INT. A - DAY\n\nMARCUS holds a LEDGER.\n\n"
        "INT. B - DAY\n\nA lone STATUE sits in the dark.\n\n"
        "INT. C - DAY\n\nMARCUS reads the ledger.\n"
    )
    results = analyze_structure(script)
    orphan_ids = [item["scene_id"] for item in results["structure"]["orphans"]]
    assert "scene_002" in orphan_ids
    assert results["structure"]["orphan_count"] == len(orphan_ids)


def test_detect_structure_mode_full() -> None:
    """INT/EXT headings yield full structure mode."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    assert results["script_summary"]["structure_mode"] == "full"


def test_detect_structure_mode_limited_without_sluglines() -> None:
    """Scripts without sluglines are marked limited."""
    results = analyze_structure("MARCUS enters.\n\nMARCUS leaves.\n")
    assert results["script_summary"]["structure_mode"] == "limited"


def test_simulate_cut_impact_via_structure_engine() -> None:
    """Simulate cut returns downstream scenes for an intermediate carrier."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    engine = results["engine"]
    impact = get_simulate_cut_impact(engine, "scene_002", engine._scene_lookup)
    impacted_ids = {row["scene_id"] for row in impact["impacted_scenes"]}
    assert impact["removed_scene"]["scene_id"] == "scene_002"
    assert "scene_003" in impacted_ids


def test_analyze_structure_from_path_on_corpus_script() -> None:
    """File-based structure analysis works on a corpus Fountain script."""
    path = Path("tests/corpus/input/drama_5scene_errors.fountain")
    results = analyze_structure_from_path(path)
    assert results["script_summary"]["total_scenes"] >= 5
    assert "contradictions" not in results
    assert results["input"]["filename"] == path.name
