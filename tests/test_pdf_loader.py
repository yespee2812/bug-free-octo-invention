"""Tests for PDF screenplay loading."""

from pathlib import Path

import pytest

from pdf_screenplay_loader import (
    PdfScreenplayError,
    load_screenplay_from_pdf,
    normalize_extracted_screenplay_text,
    write_screenplay_pdf,
)
from scene_dependency import SceneDependencyEngine
from scriptlens_analyser import analyze_from_path
from test_contradiction_screenplay import CONTRADICTION_SCREENPLAY


def test_normalize_merges_split_scene_heading() -> None:
    """Scene headings split across two lines should be merged."""
    raw = "INT.\nHOSPITAL - DAY\n\nMARCUS enters."
    normalized = normalize_extracted_screenplay_text(raw)
    assert "INT. HOSPITAL - DAY" in normalized


def test_pdf_round_trip_parses_scenes(tmp_path: Path) -> None:
    """PDF written from Fountain text should parse into multiple scenes."""
    pdf_path = tmp_path / "sample.pdf"
    write_screenplay_pdf(CONTRADICTION_SCREENPLAY, pdf_path)
    text = load_screenplay_from_pdf(pdf_path)
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    assert len(scenes) >= 10


def test_analyze_from_path_pdf(tmp_path: Path) -> None:
    """Full analysis pipeline should run on a PDF input."""
    pdf_path = tmp_path / "contradiction.pdf"
    write_screenplay_pdf(CONTRADICTION_SCREENPLAY, pdf_path)
    results = analyze_from_path(pdf_path)
    assert results["input"]["format"] == "pdf"
    assert results["script_summary"]["total_scenes"] >= 10


def test_pdf_with_no_scene_headings_raises(tmp_path: Path) -> None:
    """PDFs without INT./EXT. headings should raise a clear error."""
    pdf_path = tmp_path / "empty_story.pdf"
    write_screenplay_pdf("Chapter One\n\nIt was a dark night.", pdf_path)
    with pytest.raises(PdfScreenplayError, match="No scene headings"):
        load_screenplay_from_pdf(pdf_path)
