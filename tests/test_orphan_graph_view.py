"""Tests for orphan graph export and API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from orphan_graph_export import build_orphan_graph_view_payload
from scriptlens_structure import analyze_structure

STATUE_DEMO = Path("docs/demo_scripts/orphan_statue_demo.fountain")
CORPUS_SCRIPT = Path("tests/corpus/input/drama_5scene_errors.fountain")


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client with a fresh session store per test."""
    with TestClient(app) as test_client:
        yield test_client


def test_build_orphan_graph_view_payload_marks_orphan_node() -> None:
    """Graph export flags the orphan scene and includes OSD edges."""
    text = STATUE_DEMO.read_text(encoding="utf-8")
    results = analyze_structure(text)
    engine = results.pop("engine")
    orphans = results["structure"]["orphans"]
    payload = build_orphan_graph_view_payload(engine, orphans)

    assert payload["stats"]["scene_count"] == 3
    assert payload["stats"]["orphan_count"] == 1
    orphan_nodes = [node for node in payload["nodes"] if node["is_orphan"]]
    assert len(orphan_nodes) == 1
    assert orphan_nodes[0]["scene_id"] == "scene_002"
    assert payload["edges"]


def test_orphan_graph_endpoint_returns_nodes_and_edges(client: TestClient) -> None:
    """API exposes the orphan graph for the web viewer."""
    content = CORPUS_SCRIPT.read_bytes()
    upload_response = client.post(
        "/api/upload",
        files={"file": (CORPUS_SCRIPT.name, content, "text/plain")},
    )
    script_id = upload_response.json()["script_id"]

    response = client.get(f"/api/scripts/{script_id}/orphan-graph")
    assert response.status_code == 200
    payload = response.json()
    assert payload["script_id"] == script_id
    assert len(payload["nodes"]) == upload_response.json()["scene_count"]
    assert payload["stats"]["scene_count"] == len(payload["nodes"])
    assert "edges" in payload
