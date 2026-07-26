"""Convert screenplay PDFs to analysis-friendly Fountain text."""

from __future__ import annotations

import importlib.util
from enum import Enum
from pathlib import Path
from typing import Literal

from pdf_screenplay_loader import PdfScreenplayError, load_screenplay_from_pdf

from docx_to_fountain import convert_numbered_prose_pdf_to_fountain

ConversionStage = Literal["raw", "clean", "refined"]


class PdfConversionStage(str, Enum):
    """Stages of PDF-to-Fountain conversion."""

    RAW = "raw"
    CLEAN = "clean"
    REFINED = "refined"


def _load_scripts_module(module_name: str):
    """Load a Python module from the repo ``scripts/`` folder.

    Args:
        module_name: Basename without ``.py`` (e.g. ``cleanup_extracted_fountain``).

    Returns:
        Loaded module object.

    Raises:
        ImportError: If the script file cannot be loaded.
    """
    script_path = Path(__file__).resolve().parent / "scripts" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script module: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def convert_pdf_text(
    raw_text: str,
    *,
    stage: ConversionStage = "clean",
    source_path: Path | None = None,
) -> str:
    """Apply Fountain cleanup stages to PDF-extracted plain text.

    Args:
        raw_text: Normalized text from ``load_screenplay_from_pdf``.
        stage: ``raw`` (no change), ``clean`` (reflow + slug demotion), or
            ``refined`` (clean + manual-pass demotion rules).
        source_path: Optional PDF path used to select script-specific cast
            whitelists (e.g. Citizen Kane) during the refined stage.

    Returns:
        Fountain-style plain text ready for ScriptLens analysis.
    """
    if stage == "raw":
        return raw_text

    cleanup = _load_scripts_module("cleanup_extracted_fountain")
    cleaned = cleanup.reflow_extracted_screenplay(raw_text)

    if stage == "clean":
        return cleaned

    refine = _load_scripts_module("refine_manual_fountain")
    whitelist_only = None
    if source_path is not None:
        whitelist_only = refine._script_whitelist_for_path(source_path)
    return refine.refine_manual_pass(cleaned, whitelist_only=whitelist_only)


def convert_pdf_to_fountain(
    pdf_path: str | Path,
    *,
    stage: ConversionStage = "clean",
    source_filename: str | None = None,
) -> str:
    """Extract a PDF and convert it to Fountain-style plain text.

    Args:
        pdf_path: Path to a screenplay PDF.
        stage: Conversion depth — see ``convert_pdf_text``.
        source_filename: Original upload filename for script-specific cleanup.

    Returns:
        Fountain-style plain text.

    Raises:
        ScreenplayLoadError: When the PDF cannot be converted.
    """
    from pdf_ingest import ingest_pdf

    return ingest_pdf(
        pdf_path,
        stage=stage,
        source_filename=source_filename,
    ).text


def convert_pdf_to_fountain_file(
    pdf_path: str | Path,
    output_path: str | Path | None = None,
    *,
    stage: ConversionStage = "clean",
) -> Path:
    """Convert a PDF to a ``.fountain`` file on disk.

    Args:
        pdf_path: Source screenplay PDF.
        output_path: Destination path. Defaults beside the PDF with a stage
            suffix: ``<stem>.fountain`` (raw), ``<stem>_clean.fountain``,
            or ``<stem>_manual.fountain`` (refined).
        stage: Conversion depth — see ``convert_pdf_text``.

    Returns:
        Resolved path to the written Fountain file.
    """
    path = Path(pdf_path).resolve()
    if output_path is None:
        if stage == "raw":
            suffix = ".fountain"
        elif stage == "clean":
            suffix = "_clean.fountain"
        else:
            suffix = "_manual.fountain"
        output_path = path.with_name(f"{path.stem}{suffix}")
    destination = Path(output_path).resolve()
    fountain_text = convert_pdf_to_fountain(path, stage=stage)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(fountain_text, encoding="utf-8")
    return destination


def default_output_path(pdf_path: str | Path, stage: ConversionStage = "clean") -> Path:
    """Return the default Fountain output path for a PDF and conversion stage.

    Args:
        pdf_path: Source screenplay PDF.
        stage: Conversion depth.

    Returns:
        Default output file path (not written until conversion runs).
    """
    path = Path(pdf_path).resolve()
    if stage == "raw":
        return path.with_name(f"{path.stem}.fountain")
    if stage == "clean":
        return path.with_name(f"{path.stem}_clean.fountain")
    return path.with_name(f"{path.stem}_manual.fountain")
