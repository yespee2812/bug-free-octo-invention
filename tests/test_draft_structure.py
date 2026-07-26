"""Tests for draft screenplay mutations in scriptlens_structure."""

from __future__ import annotations

from api.sessions import AnalysisSession, refresh_session_structure
from scriptlens_structure import (
    analyze_structure,
    count_scene_headings,
    delete_scene_block,
    get_simulate_edit_impact,
)

CHAINED_PROP_SCRIPT = """INT. ROOM ONE - DAY

A REVOLVER lies on the table.

INT. ROOM TWO - DAY

MARCUS grabs the revolver.

INT. ROOM THREE - NIGHT

MARCUS aims the revolver.
"""


def _session_from_script(script: str) -> AnalysisSession:
    """Build a minimal analysis session for draft helper tests."""
    results = analyze_structure(script)
    engine = results.pop("engine")
    structure = results["structure"]
    return AnalysisSession(
        script_id="testsession0001",
        filename="test.fountain",
        original_text=script,
        draft_text=script,
        draft_revision=0,
        input_format="fountain",
        structure_mode=results["script_summary"]["structure_mode"],
        scenes=results["scenes"],
        orphan_count=structure["orphan_count"],
        orphans=structure["orphans"],
        graph_summary=structure["graph_summary"],
        high_risk_scenes=structure["high_risk_scenes"],
        engine=engine,
    )


def test_count_scene_headings_matches_parser() -> None:
    """Slugline count matches parsed scene total."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    assert count_scene_headings(CHAINED_PROP_SCRIPT) == results["script_summary"]["total_scenes"]


def test_delete_scene_block_reduces_scene_count() -> None:
    """Deleting one slugline block removes exactly one scene."""
    updated = delete_scene_block(CHAINED_PROP_SCRIPT, 2)
    assert count_scene_headings(updated) == 2
    assert "ROOM TWO" not in updated
    assert "ROOM THREE" in updated


def test_structure_refresh_is_idempotent() -> None:
    """Rebuilding from unchanged draft text preserves orphan count."""
    session = _session_from_script(CHAINED_PROP_SCRIPT)
    before_orphans = session.orphan_count
    refresh_session_structure(session, increment_revision=False)
    assert session.orphan_count == before_orphans
    assert session.draft_revision == 0


def test_simulate_edit_reports_scene_count_delta_on_split() -> None:
    """Adding a slugline in an edit preview increases the after scene count."""
    results = analyze_structure(CHAINED_PROP_SCRIPT)
    engine = results["engine"]
    split_text = (
        "INT. ROOM ONE - DAY\n\n"
        "A REVOLVER lies on the table.\n\n"
        "INT. ROOM ONE - LATER\n\n"
        "The table is empty."
    )
    impact = get_simulate_edit_impact(
        engine,
        CHAINED_PROP_SCRIPT,
        "scene_001",
        split_text,
    )
    assert impact["scene_count_before"] == 3
    assert impact["scene_count_after"] == 4


def test_refresh_session_after_delete_updates_orphans() -> None:
    """Deleting a scene from the draft rebuilds the session graph."""
    session = _session_from_script(CHAINED_PROP_SCRIPT)
    session.draft_text = delete_scene_block(session.draft_text, 2)
    refresh_session_structure(session, increment_revision=True)
    assert session.draft_revision == 1
    assert len(session.scenes) == 2
    assert count_scene_headings(session.draft_text) == 2
