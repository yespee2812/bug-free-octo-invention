"""Tests for PDF-to-Fountain conversion pipeline."""

from pathlib import Path

import pytest

from pdf_screenplay_loader import write_screenplay_pdf
from pdf_to_fountain import (
    convert_pdf_text,
    convert_pdf_to_fountain,
    convert_pdf_to_fountain_file,
    default_output_path,
)
from scene_dependency import SceneDependencyEngine
from legacy.scriptlens_analyser import analyze_from_path, load_screenplay_text

NOISY_PDF_SCREENPLAY = """FADE IN:
INT. HOUSE - DAY
ANGLE ON JIM
Jim enters the room.
JIM
Hello.
EXT. STREET - NIGHT
ANGLE ON KEVIN
Kevin walks down the block.
KEVIN
Hi there."""


def _character_count(text: str) -> int:
    """Return the number of parsed characters in screenplay text."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    return len({character for scene in scenes for character in scene.characters})


def test_convert_pdf_text_clean_reduces_slug_characters() -> None:
    """Clean stage should demote camera slugs so they are not parsed as cast."""
    raw_count = _character_count(NOISY_PDF_SCREENPLAY)
    clean_count = _character_count(convert_pdf_text(NOISY_PDF_SCREENPLAY, stage="clean"))
    assert raw_count > clean_count
    assert clean_count == 2


def test_convert_pdf_to_fountain_file(tmp_path: Path) -> None:
    """Conversion should write a Fountain file beside the PDF by default."""
    pdf_path = tmp_path / "noisy.pdf"
    write_screenplay_pdf(NOISY_PDF_SCREENPLAY, pdf_path)
    written = convert_pdf_to_fountain_file(pdf_path, stage="clean")
    assert written == default_output_path(pdf_path, "clean")
    assert written.is_file()
    assert _character_count(written.read_text(encoding="utf-8")) == 2


def test_load_screenplay_text_pdf_uses_clean_stage(tmp_path: Path) -> None:
    """PDF loads should apply clean conversion by default."""
    pdf_path = tmp_path / "noisy.pdf"
    write_screenplay_pdf(NOISY_PDF_SCREENPLAY, pdf_path)
    text, input_format = load_screenplay_text(pdf_path)
    assert input_format == "pdf"
    assert _character_count(text) == 2


def test_load_screenplay_text_pdf_raw_stage(tmp_path: Path) -> None:
    """Raw PDF conversion should preserve slug lines as character cues."""
    pdf_path = tmp_path / "noisy.pdf"
    write_screenplay_pdf(NOISY_PDF_SCREENPLAY, pdf_path)
    text, _ = load_screenplay_text(pdf_path, pdf_conversion="raw")
    assert _character_count(text) > 2


def test_analyze_from_path_records_pdf_conversion(tmp_path: Path) -> None:
    """Analysis metadata should record the PDF conversion stage used."""
    pdf_path = tmp_path / "noisy.pdf"
    write_screenplay_pdf(NOISY_PDF_SCREENPLAY, pdf_path)
    results = analyze_from_path(pdf_path, pdf_conversion="clean")
    assert results["input"]["format"] == "pdf"
    assert results["input"]["pdf_conversion"] == "clean"


def test_convert_pdf_to_fountain_missing_file_raises() -> None:
    """Missing PDF paths should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        convert_pdf_to_fountain("does_not_exist.pdf")
