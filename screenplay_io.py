"""Screenplay input loading shared by the v3 structure path and legacy tools.

This module holds the file-ingest helpers that have no dependency on plot
contradiction detection, so the v3 structure engine can load screenplays
without importing the legacy contradiction stack.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pdf_ingest import ingest_pdf
from pdf_to_fountain import ConversionStage

SUPPORTED_TEXT_SUFFIXES: frozenset[str] = frozenset(
    {".fountain", ".fadein", ".txt", ".md", ".screenplay"}
)


def load_screenplay_with_meta(
    input_path: str | Path,
    *,
    pdf_conversion: ConversionStage = "clean",
    source_filename: str | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """Load screenplay text and return ingest metadata for API responses.

    Args:
        input_path: Path to .pdf, .fountain, .txt, or similar.
        pdf_conversion: For PDFs only — ``raw``, ``clean``, or ``refined``.
        source_filename: Original upload filename used for PDF cleanup rules.

    Returns:
        Tuple of screenplay text, input format (``pdf`` or ``text``), and an
        ingest metadata dictionary.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the file type is not supported.
        ScreenplayLoadError: If a PDF cannot be converted.
    """
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        result = ingest_pdf(
            path,
            stage=pdf_conversion,
            source_filename=source_filename or path.name,
        )
        return (
            result.text,
            "pdf",
            {
                "pdf_conversion": pdf_conversion,
                "ingest_method": result.ingest_method,
                "slugline_count": result.slugline_count,
                "ingest_warnings": list(result.warnings),
            },
        )
    if suffix in SUPPORTED_TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8"), "text", {}

    raise ValueError(
        f"Unsupported file type '{suffix}' for {path.name}. "
        f"Use .pdf or one of: {', '.join(sorted(SUPPORTED_TEXT_SUFFIXES))}."
    )


def load_screenplay_text(
    input_path: str | Path,
    *,
    pdf_conversion: ConversionStage = "clean",
    source_filename: str | None = None,
) -> tuple[str, str]:
    """Load screenplay plain text from a PDF or text file.

    PDF inputs are converted to Fountain-style text before return. By default
    the ``clean`` stage reflows action and demotes camera slugs so analysis
    sees fewer false character names.

    Args:
        input_path: Path to .pdf, .fountain, .txt, or similar.
        pdf_conversion: For PDFs only — ``raw``, ``clean`` (default), or
            ``refined``. Ignored for Fountain/text files.
        source_filename: Original upload filename used for PDF cleanup rules.

    Returns:
        Tuple of (screenplay_text, input_format) where input_format is
        ``pdf`` or ``text``.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the file type is not supported.
        ScreenplayLoadError: If a PDF cannot be converted.
    """
    text, input_format, _meta = load_screenplay_with_meta(
        input_path,
        pdf_conversion=pdf_conversion,
        source_filename=source_filename,
    )
    return text, input_format
