"""Tests for draft undo and export."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.draft_export import draft_export_filename
from api.main import app
from api.sessions import (
    AnalysisSession,
    can_undo_draft,
    record_draft_snapshot,
    undo_draft,
)
from scriptlens_structure import analyze_structure, count_scene_headings, delete_scene_block

CHAINED_PROP_SCRIPT = """INT. ROOM ONE - DAY

A REVOLVER lies on the table.

INT. ROOM TWO - DAY

MARCUS grabs the revolver.

INT. ROOM THREE - NIGHT

MARCUS aims the revolver.
"""

CORPUS_SCRIPT = Path("tests/corpus/input/drama_5scene_errors.fountain")


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client with a fresh session store per test."""
    with TestClient(app) as test_client:
        yield test_client


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


def test_draft_export_filename_includes_revision() -> None:
    """Export filenames reflect the current draft revision."""
    assert draft_export_filename("MyScript.pdf", 0) == "MyScript_working.fountain"
    assert draft_export_filename("MyScript.pdf", 2) == "MyScript_draft_rev2.fountain"


def test_undo_draft_restores_previous_text() -> None:
    """Undo restores the prior draft snapshot and decrements revision."""
    session = _session_from_script(CHAINED_PROP_SCRIPT)
    original_text = session.draft_text

    record_draft_snapshot(session)
    session.draft_text = delete_scene_block(session.draft_text, 2)
    session.draft_revision = 1

    undo_draft(session)
    assert session.draft_text == original_text
    assert session.draft_revision == 0
    assert count_scene_headings(session.draft_text) == 3
    assert not can_undo_draft(session)


def test_draft_delete_then_undo_via_api(client: TestClient) -> None:
    """Delete and undo round-trip through the draft API."""
    content = CORPUS_SCRIPT.read_bytes()
    upload_response = client.post(
        "/api/upload",
        files={"file": (CORPUS_SCRIPT.name, content, "text/plain")},
    )
    script_id = upload_response.json()["script_id"]
    original_count = upload_response.json()["scene_count"]

    delete_response = client.post(
        f"/api/scripts/{script_id}/draft/delete",
        json={"scene_id": "scene_003"},
    )
    assert delete_response.status_code == 200
    delete_payload = delete_response.json()
    assert delete_payload["scene_count"] == original_count - 1
    assert delete_payload["can_undo"] is True

    undo_response = client.post(f"/api/scripts/{script_id}/draft/undo")
    assert undo_response.status_code == 200
    undo_payload = undo_response.json()
    assert undo_payload["scene_count"] == original_count
    assert undo_payload["draft_revision"] == 0
    assert undo_payload["can_undo"] is False


def test_draft_export_downloads_fountain_text(client: TestClient) -> None:
    """Export returns the current working draft as a downloadable file."""
    content = CORPUS_SCRIPT.read_bytes()
    upload_response = client.post(
        "/api/upload",
        files={"file": (CORPUS_SCRIPT.name, content, "text/plain")},
    )
    script_id = upload_response.json()["script_id"]

    export_response = client.get(f"/api/scripts/{script_id}/draft/export")
    assert export_response.status_code == 200
    assert "INT." in export_response.text
    assert export_response.headers["content-disposition"].endswith(
        'filename="drama_5scene_errors_working.fountain"'
    )

    client.post(
        f"/api/scripts/{script_id}/draft/delete",
        json={"scene_id": "scene_001"},
    )
    export_after_delete = client.get(f"/api/scripts/{script_id}/draft/export")
    assert "scene_001" not in export_after_delete.text.lower() or export_after_delete.status_code == 200
    assert "draft_rev1" in export_after_delete.headers["content-disposition"]


def test_draft_undo_without_history_returns_422(client: TestClient) -> None:
    """Undo on a fresh upload returns HTTP 422."""
    content = CORPUS_SCRIPT.read_bytes()
    upload_response = client.post(
        "/api/upload",
        files={"file": (CORPUS_SCRIPT.name, content, "text/plain")},
    )
    script_id = upload_response.json()["script_id"]

    undo_response = client.post(f"/api/scripts/{script_id}/draft/undo")
    assert undo_response.status_code == 422
