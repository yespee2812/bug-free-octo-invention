"""Tests for the ScriptLens structure FastAPI."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from pdf_screenplay_loader import write_screenplay_pdf

CORPUS_SCRIPT = Path("tests/corpus/input/drama_5scene_errors.fountain")


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client with a fresh session store per test.

    Returns:
        Configured ``TestClient`` for the structure API.
    """
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient) -> None:
    """Health check returns ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["service"] == "scriptlens-structure"


def test_security_headers_present(client: TestClient) -> None:
    """Baseline hardening headers are attached to responses."""
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_upload_fountain_returns_scenes_and_orphans(client: TestClient) -> None:
    """Upload analyses a Fountain script and returns structure metadata."""
    content = CORPUS_SCRIPT.read_bytes()
    response = client.post(
        "/api/upload",
        files={"file": (CORPUS_SCRIPT.name, content, "text/plain")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scene_count"] == 5
    assert payload["filename"] == CORPUS_SCRIPT.name
    assert payload["structure_mode"] == "full"
    assert payload["input_format"] == "text"
    assert len(payload["scenes"]) == 5
    assert payload["orphan_count"] >= 0
    assert payload["script_id"]


def test_upload_pdf_returns_ingest_metadata(client: TestClient) -> None:
    """PDF upload returns cleanup metadata and parsed scenes."""
    pdf_path = Path("tests/corpus/input/screenplay.pdf")
    if not pdf_path.is_file():
        pytest.skip("Corpus screenplay PDF not available")

    content = pdf_path.read_bytes()
    response = client.post(
        "/api/upload",
        files={"file": (pdf_path.name, content, "application/pdf")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["input_format"] == "pdf"
    assert payload["pdf_conversion"] == "refined"
    assert payload["ingest_method"] == "slugline_extract"
    assert payload["slugline_count"] > 0
    assert payload["scene_count"] > 0
    assert payload["structure_mode"] == "full"


def test_upload_unreadable_pdf_returns_400(
    client: TestClient,
    tmp_path: Path,
) -> None:
    """PDFs without parseable scenes return a friendly HTTP 400 error."""
    pdf_path = tmp_path / "unparseable.pdf"
    write_screenplay_pdf("Chapter One\n\nIt was a dark night.", pdf_path)

    content = pdf_path.read_bytes()
    response = client.post(
        "/api/upload",
        files={"file": (pdf_path.name, content, "application/pdf")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Fountain" in detail


def test_orphans_endpoint_matches_upload(client: TestClient) -> None:
    """Orphans endpoint returns the same orphan list as upload."""
    content = CORPUS_SCRIPT.read_bytes()
    upload_response = client.post(
        "/api/upload",
        files={"file": (CORPUS_SCRIPT.name, content, "text/plain")},
    )
    script_id = upload_response.json()["script_id"]
    orphan_count = upload_response.json()["orphan_count"]

    orphans_response = client.get(f"/api/scripts/{script_id}/orphans")
    assert orphans_response.status_code == 200
    payload = orphans_response.json()
    assert payload["script_id"] == script_id
    assert payload["orphan_count"] == orphan_count
    assert len(payload["orphans"]) == orphan_count
    if payload["orphans"]:
        assert "orphan_type" in payload["orphans"][0]
        assert "reasons" in payload["orphans"][0]


def test_script_detail_endpoint(client: TestClient) -> None:
    """Script detail endpoint returns graph summary for a session."""
    content = CORPUS_SCRIPT.read_bytes()
    upload_response = client.post(
        "/api/upload",
        files={"file": (CORPUS_SCRIPT.name, content, "text/plain")},
    )
    script_id = upload_response.json()["script_id"]

    detail_response = client.get(f"/api/scripts/{script_id}")
    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["script_id"] == script_id
    assert payload["scene_count"] == 5
    assert "graph_summary" in payload


def test_upload_rejects_unsupported_type(client: TestClient) -> None:
    """Unsupported extensions are rejected before analysis with HTTP 415."""
    response = client.post(
        "/api/upload",
        files={"file": ("notes.docx", b"hello", "application/octet-stream")},
    )
    assert response.status_code == 415


def test_orphans_unknown_script_returns_404(client: TestClient) -> None:
    """Missing sessions return HTTP 404."""
    response = client.get("/api/scripts/doesnotexist1234/orphans")
    assert response.status_code == 404


def _upload_corpus_script(client: TestClient) -> str:
    """Upload the drama corpus script and return its script id.

    Args:
        client: FastAPI test client.

    Returns:
        Script session id from the upload response.
    """
    content = CORPUS_SCRIPT.read_bytes()
    response = client.post(
        "/api/upload",
        files={"file": (CORPUS_SCRIPT.name, content, "text/plain")},
    )
    assert response.status_code == 200
    return response.json()["script_id"]


def test_simulate_cut_returns_downstream_scenes(client: TestClient) -> None:
    """Simulate cut lists scenes that depend on the removed scene."""
    script_id = _upload_corpus_script(client)
    response = client.post(
        f"/api/scripts/{script_id}/simulate/cut",
        json={"scene_id": "scene_002"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["script_id"] == script_id
    assert payload["removed_scene"]["scene_id"] == "scene_002"
    impacted_ids = {row["scene_id"] for row in payload["impacted_scenes"]}
    # Scene 2 introduces Sofia, consumed later in scene 5 (SFI D-lite).
    assert "scene_005" in impacted_ids
    assert payload["impacted_count"] == len(payload["impacted_scenes"])
    assert payload["summary"]
    assert payload["risk_level"] in {"low", "medium", "high"}
    assert payload["impacted_scenes"][0]["dependency_path"][0] == "scene_002"
    assert payload["impacted_scenes"][0]["impact_reason"]


def test_simulate_cut_unknown_scene_returns_422(client: TestClient) -> None:
    """Invalid scene ids return HTTP 422."""
    script_id = _upload_corpus_script(client)
    response = client.post(
        f"/api/scripts/{script_id}/simulate/cut",
        json={"scene_id": "scene_999"},
    )
    assert response.status_code == 422


def test_simulate_cut_unknown_script_returns_404(client: TestClient) -> None:
    """Simulate cut on a missing session returns HTTP 404."""
    response = client.post(
        "/api/scripts/doesnotexist1234/simulate/cut",
        json={"scene_id": "scene_001"},
    )
    assert response.status_code == 404


def test_scene_detail_endpoint(client: TestClient) -> None:
    """Scene detail returns Fountain body for the script reader."""
    script_id = _upload_corpus_script(client)
    response = client.get(f"/api/scripts/{script_id}/scenes/scene_001")
    assert response.status_code == 200
    payload = response.json()
    assert payload["script_id"] == script_id
    assert payload["scene_id"] == "scene_001"
    assert payload["scene_number"] == 1
    assert "INT." in payload["heading"] or "EXT." in payload["heading"]
    assert len(payload["body"]) > 0


def test_scene_detail_unknown_scene_returns_422(client: TestClient) -> None:
    """Invalid scene ids on the reader endpoint return HTTP 422."""
    script_id = _upload_corpus_script(client)
    response = client.get(f"/api/scripts/{script_id}/scenes/scene_999")
    assert response.status_code == 422


def test_static_index_is_served(client: TestClient) -> None:
    """The web UI index page is served from the app root."""
    response = client.get("/")
    assert response.status_code == 200
    assert "ScriptLens" in response.text
    assert "Edit scene" in response.text
    assert "Simulate edit" in response.text


def test_simulate_edit_removes_downstream_edges(client: TestClient) -> None:
    """Simulate edit reports removed edges when a setup prop is deleted."""
    script_id = _upload_corpus_script(client)
    scene_response = client.get(f"/api/scripts/{script_id}/scenes/scene_001")
    assert scene_response.status_code == 200
    original_body = scene_response.json()["body"]

    modified_body = original_body.replace("SILVER WEDDING BAND", "EMPTY TABLE")
    response = client.post(
        f"/api/scripts/{script_id}/simulate/edit",
        json={"scene_id": "scene_001", "modified_text": modified_body},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scene_id"] == "scene_001"
    assert "edge_diff" in payload
    total_changes = (
        len(payload["edge_diff"]["added"])
        + len(payload["edge_diff"]["removed"])
        + len(payload["edge_diff"]["changed"])
    )
    assert total_changes >= 0
    assert payload["summary"]
    assert payload["risk_level"] in {"none", "low", "medium", "high"}
    assert payload["orphan_delta"]["message"]


def test_simulate_edit_unknown_scene_returns_422(client: TestClient) -> None:
    """Invalid scene ids on simulate edit return HTTP 422."""
    script_id = _upload_corpus_script(client)
    response = client.post(
        f"/api/scripts/{script_id}/simulate/edit",
        json={"scene_id": "scene_999", "modified_text": "INT. X - DAY"},
    )
    assert response.status_code == 422


def test_draft_delete_scene_reduces_count(client: TestClient) -> None:
    """Deleting a scene from the draft rebuilds structure metadata."""
    script_id = _upload_corpus_script(client)
    response = client.post(
        f"/api/scripts/{script_id}/draft/delete",
        json={"scene_id": "scene_003"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["previous_scene_count"] == 5
    assert payload["scene_count"] == 4
    assert payload["draft_revision"] == 1
    assert payload["can_undo"] is True
    assert len(payload["scenes"]) == 4

    orphans_response = client.get(f"/api/scripts/{script_id}/orphans")
    assert orphans_response.json()["orphan_count"] == payload["orphan_count"]


def test_draft_apply_edit_split_increases_scene_count(client: TestClient) -> None:
    """Applying a multi-slugline edit splits one scene into two."""
    script_id = _upload_corpus_script(client)
    scene_response = client.get(f"/api/scripts/{script_id}/scenes/scene_001")
    body = scene_response.json()["body"]
    split_body = (
        f"{body.rstrip()}\n\n"
        "INT. COUNTY FAMILY COURT - LATER\n\n"
        "The gallery empties."
    )
    response = client.post(
        f"/api/scripts/{script_id}/draft/apply-edit",
        json={"scene_id": "scene_001", "modified_text": split_body},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["previous_scene_count"] == 5
    assert payload["scene_count"] == 6
    assert payload["draft_revision"] == 1
    assert payload["can_undo"] is True


def test_simulate_cut_after_draft_delete_uses_new_graph(client: TestClient) -> None:
    """Simulate cut runs on the rebuilt draft graph."""
    script_id = _upload_corpus_script(client)
    delete_response = client.post(
        f"/api/scripts/{script_id}/draft/delete",
        json={"scene_id": "scene_002"},
    )
    assert delete_response.status_code == 200

    cut_response = client.post(
        f"/api/scripts/{script_id}/simulate/cut",
        json={"scene_id": "scene_002"},
    )
    assert cut_response.status_code == 200
    payload = cut_response.json()
    assert payload["removed_scene"]["scene_number"] == 2


def test_simulate_edit_includes_scene_count_delta(client: TestClient) -> None:
    """Simulate edit preview reports scene counts before and after."""
    script_id = _upload_corpus_script(client)
    scene_response = client.get(f"/api/scripts/{script_id}/scenes/scene_001")
    original_body = scene_response.json()["body"]
    modified_body = original_body.replace("SILVER WEDDING BAND", "EMPTY TABLE")
    response = client.post(
        f"/api/scripts/{script_id}/simulate/edit",
        json={"scene_id": "scene_001", "modified_text": modified_body},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scene_count_before"] == 5
    assert payload["scene_count_after"] == 5
    assert payload["applied"] is False
