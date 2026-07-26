"""Shared pytest configuration for ScriptLens tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def disable_osd_semantic_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip MiniLM loading in unit tests unless a test opts in explicitly."""
    if os.environ.get("OSD_ENABLE_SEMANTIC_TESTS") == "1":
        return
    monkeypatch.setenv("OSD_DISABLE_SEMANTIC", "1")
