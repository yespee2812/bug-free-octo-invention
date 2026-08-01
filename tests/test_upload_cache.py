"""Tests for upload-content analysis caching."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

CORPUS_SCRIPT = Path("tests/corpus/input/drama_5scene_errors.fountain")


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client with a fresh session store per test.

    Returns:
        Configured ``TestClient`` for the structure API.
    """
    with TestClient(app) as test_client:
        yield test_client


def test_identical_reupload_skips_analysis(client: TestClient) -> None:
    """A second upload of the same bytes reuses the cached session."""
    content = CORPUS_SCRIPT.read_bytes()
    files = {"file": (CORPUS_SCRIPT.name, content, "text/plain")}

    first = client.post("/api/upload", files=files)
    assert first.status_code == 200
    first_payload = first.json()

    with patch(
        "api.routes.upload.analyze_structure_from_bytes",
        side_effect=AssertionError("cache miss should not re-analyse"),
    ) as mocked:
        second = client.post("/api/upload", files=files)
        mocked.assert_not_called()

    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["script_id"] == first_payload["script_id"]
    assert second_payload["scene_count"] == first_payload["scene_count"]
    assert second_payload["orphan_count"] == first_payload["orphan_count"]


def test_different_upload_still_runs_analysis(client: TestClient) -> None:
    """A different file still triggers a fresh analysis."""
    content = CORPUS_SCRIPT.read_bytes()
    first = client.post(
        "/api/upload",
        files={"file": (CORPUS_SCRIPT.name, content, "text/plain")},
    )
    assert first.status_code == 200

    altered = content + b"\n\nINT. NEW ROOM - NIGHT\n\nSomeone enters.\n"
    second = client.post(
        "/api/upload",
        files={"file": ("altered.fountain", altered, "text/plain")},
    )
    assert second.status_code == 200
    assert second.json()["script_id"] != first.json()["script_id"]
