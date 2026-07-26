"""Customer-facing PDF ingest helpers and metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from docx_to_fountain import DocxScreenplayError, convert_numbered_prose_pdf_to_fountain
from pdf_screenplay_loader import PdfScreenplayError, load_screenplay_from_pdf
from pdf_to_fountain import ConversionStage, convert_pdf_text

IngestMethod = Literal["slugline_extract", "numbered_prose_fallback"]
StructureMode = Literal["full", "limited"]

_SCENE_HEADING_PATTERN = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s+",
    re.IGNORECASE | re.MULTILINE,
)


class ScreenplayLoadError(ValueError):
    """Raised when an uploaded screenplay cannot be loaded for analysis."""


@dataclass(frozen=True)
class PdfIngestResult:
    """Metadata-rich result from converting one PDF upload."""

    text: str
    conversion_stage: ConversionStage
    ingest_method: IngestMethod
    slugline_count: int
    warnings: list[str] = field(default_factory=list)


def count_sluglines(text: str) -> int:
    """Return how many INT./EXT. sluglines appear in screenplay text.

    Args:
        text: Fountain-style screenplay plain text.

    Returns:
        Number of slugline matches in document order.
    """
    return len(_SCENE_HEADING_PATTERN.findall(text))


def _whitelist_source_path(
    pdf_path: Path,
    source_filename: str | None,
) -> Path:
    """Prefer the original upload filename for script-specific cleanup rules."""
    if source_filename:
        return Path(source_filename)
    return pdf_path


def _compose_load_error(
    primary_error: PdfScreenplayError,
    fallback_error: DocxScreenplayError | None = None,
) -> str:
    """Build a plain-English upload failure message.

    Args:
        primary_error: Error from standard slugline PDF extraction.
        fallback_error: Error from numbered-prose fallback, if attempted.

    Returns:
        User-facing guidance string.
    """
    primary_text = str(primary_error)
    parts: list[str] = []

    if "No extractable text" in primary_text:
        parts.append(
            "This PDF looks scanned or image-only, so ScriptLens could not read "
            "the screenplay text."
        )
    elif "No scene headings" in primary_text:
        parts.append(
            "This PDF has text, but no INT./EXT. scene headings were detected."
        )
    else:
        parts.append("This PDF could not be converted into a readable screenplay.")

    if fallback_error is not None:
        parts.append(
            "A numbered-scene fallback also failed — we did not find markers "
            "like '1.' and '2.' that split the script into scenes."
        )

    parts.append(
        "Try exporting from Final Draft, WriterDuet, or Celtx as Fountain "
        "(.fountain) or as a text-based PDF (not a scan)."
    )
    return " ".join(parts)


def ingest_pdf(
    pdf_path: str | Path,
    *,
    stage: ConversionStage = "refined",
    source_filename: str | None = None,
) -> PdfIngestResult:
    """Convert a PDF upload to Fountain text and capture ingest metadata.

    Args:
        pdf_path: Path to the uploaded PDF on disk.
        stage: Cleanup depth — ``raw``, ``clean``, or ``refined``.
        source_filename: Original upload filename for script-specific cleanup.

    Returns:
        Converted screenplay text plus ingest metadata and warnings.

    Raises:
        ScreenplayLoadError: When neither slugline extraction nor numbered-prose
            fallback can produce parseable scene structure.
        FileNotFoundError: When the PDF path does not exist.
    """
    path = Path(pdf_path).resolve()
    whitelist_path = _whitelist_source_path(path, source_filename)
    warnings: list[str] = []
    ingest_method: IngestMethod = "slugline_extract"

    try:
        raw_text = load_screenplay_from_pdf(path)
    except PdfScreenplayError as primary_error:
        try:
            fallback_raw = convert_numbered_prose_pdf_to_fountain(path)
        except DocxScreenplayError as fallback_error:
            raise ScreenplayLoadError(
                _compose_load_error(primary_error, fallback_error),
            ) from fallback_error

        ingest_method = "numbered_prose_fallback"
        warnings.append(
            "We could not find INT./EXT. headings, so scenes were split using "
            "numbered markers. Scene locations may show as generic placeholders."
        )
        text = convert_pdf_text(
            fallback_raw,
            stage=stage,
            source_path=whitelist_path,
        )
        slugline_count = count_sluglines(text)
        return PdfIngestResult(
            text=text,
            conversion_stage=stage,
            ingest_method=ingest_method,
            slugline_count=slugline_count,
            warnings=warnings,
        )

    text = convert_pdf_text(
        raw_text,
        stage=stage,
        source_path=whitelist_path,
    )
    slugline_count = count_sluglines(text)
    if stage == "refined" and ingest_method == "slugline_extract":
        warnings.append(
            "PDF cleaned automatically. For best results, upload Fountain when "
            "your writing app supports it."
        )

    return PdfIngestResult(
        text=text,
        conversion_stage=stage,
        ingest_method=ingest_method,
        slugline_count=slugline_count,
        warnings=warnings,
    )


def build_upload_ingest_warnings(
    ingest: PdfIngestResult | None,
    *,
    structure_mode: StructureMode,
    scene_count: int,
) -> list[str]:
    """Merge PDF ingest warnings with structure-mode guidance.

    Args:
        ingest: PDF ingest metadata when the upload was a PDF, else ``None``.
        structure_mode: Parsed structure mode from analysis.
        scene_count: Number of parsed scenes.

    Returns:
        Ordered list of user-facing warning strings (may be empty).
    """
    warnings: list[str] = []
    if ingest is not None:
        warnings.extend(ingest.warnings)

    if structure_mode == "limited":
        warnings.append(
            "Scene breaks were not detected. Upload Fountain or export a "
            "text-based PDF with INT./EXT. headings."
        )
    elif ingest is not None and scene_count == 0:
        warnings.append(
            "No scenes were parsed from this PDF. Try uploading a .fountain file."
        )

    deduped: list[str] = []
    seen: set[str] = set()
    for warning in warnings:
        if warning in seen:
            continue
        seen.add(warning)
        deduped.append(warning)
    return deduped
