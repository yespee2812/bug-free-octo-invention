"""Tests for customer-facing PDF ingest metadata and errors."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdf_ingest import ScreenplayLoadError, build_upload_ingest_warnings, ingest_pdf
from pdf_screenplay_loader import write_screenplay_pdf
from screenplay_io import load_screenplay_with_meta
from scriptlens_structure import analyze_structure_from_bytes

CORPUS_PDF = Path("tests/corpus/input/screenplay.pdf")


def test_ingest_pdf_returns_slugline_metadata() -> None:
    """Standard PDF uploads report slugline extraction metadata."""
    if not CORPUS_PDF.is_file():
        pytest.skip("Corpus screenplay PDF not available")

    result = ingest_pdf(CORPUS_PDF, stage="refined", source_filename=CORPUS_PDF.name)
    assert result.ingest_method == "slugline_extract"
    assert result.slugline_count > 0
    assert result.text.strip()
    assert any("cleaned automatically" in warning for warning in result.warnings)


def test_load_screenplay_with_meta_for_pdf() -> None:
    """Loader returns ingest metadata alongside converted text."""
    if not CORPUS_PDF.is_file():
        pytest.skip("Corpus screenplay PDF not available")

    text, input_format, meta = load_screenplay_with_meta(
        CORPUS_PDF,
        pdf_conversion="refined",
        source_filename=CORPUS_PDF.name,
    )
    assert input_format == "pdf"
    assert meta["ingest_method"] == "slugline_extract"
    assert meta["slugline_count"] > 0
    assert "INT." in text


def test_scanned_pdf_raises_screenplay_load_error(tmp_path: Path) -> None:
    """PDFs without parseable scene structure return ScreenplayLoadError."""
    pdf_path = tmp_path / "unparseable.pdf"
    write_screenplay_pdf("Chapter One\n\nIt was a dark night.", pdf_path)

    with pytest.raises(ScreenplayLoadError, match="Fountain"):
        ingest_pdf(pdf_path, stage="refined")


def test_numbered_prose_fallback_reports_warning(tmp_path: Path) -> None:
    """Prose PDFs without sluglines use numbered-scene fallback with a warning."""
    pdf_path = tmp_path / "prose_script.pdf"
    prose = (
        "MY SCRIPT\n\n"
        "Written by Example Writer\n\n"
        "1.\n\n"
        "MARCUS enters the room.\n\n"
        "MARCUS\n"
        "Hello.\n\n"
        "2.\n\n"
        "MARCUS leaves.\n"
    )
    write_screenplay_pdf(prose, pdf_path)

    result = ingest_pdf(pdf_path, stage="clean")
    assert result.ingest_method == "numbered_prose_fallback"
    assert result.slugline_count >= 2
    assert any("numbered markers" in warning for warning in result.warnings)


def test_build_upload_ingest_warnings_for_limited_mode() -> None:
    """Limited structure mode adds guidance to ingest warnings."""
    warnings = build_upload_ingest_warnings(
        None,
        structure_mode="limited",
        scene_count=0,
    )
    assert any("Scene breaks were not detected" in warning for warning in warnings)


def test_analyze_structure_from_bytes_pdf_upload_metadata() -> None:
    """Byte upload path returns ingest metadata for PDF files."""
    if not CORPUS_PDF.is_file():
        pytest.skip("Corpus screenplay PDF not available")

    content = CORPUS_PDF.read_bytes()
    results, _engine, _text = analyze_structure_from_bytes(
        content,
        CORPUS_PDF.name,
    )
    assert results["script_summary"]["total_scenes"] > 0
    assert results["input"]["format"] == "pdf"
    assert results["input"]["ingest_method"] == "slugline_extract"
    assert results["input"]["slugline_count"] > 0
