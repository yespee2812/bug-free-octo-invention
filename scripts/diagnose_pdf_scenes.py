"""Diagnose scene structure in screenplay PDF files."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pdf_screenplay_loader import (
    PdfScreenplayError,
    count_final_draft_sluglines,
    extract_text_from_pdf,
    load_screenplay_from_pdf,
)
from scene_dependency import SceneDependencyEngine

_NUMBERED_BLOCK = re.compile(r"^(\d{1,3})\.\s*$")
_INT_EXT_LINE = re.compile(r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s+", re.IGNORECASE)


@dataclass(frozen=True)
class PdfSceneDiagnosis:
    """Scene-structure metrics for one screenplay PDF."""

    pdf_path: Path
    page_count: int
    numbered_blocks: int
    int_ext_sluglines: int
    engine_scene_count: int
    conversion_path: str
    notes: tuple[str, ...]


def diagnose_pdf_scenes(pdf_path: str | Path) -> PdfSceneDiagnosis:
    """Count numbered blocks, sluglines, and parser scenes for a PDF.

    Args:
        pdf_path: Path to a screenplay PDF.

    Returns:
        Structured diagnosis with scene counts and conversion guidance.

    Raises:
        FileNotFoundError: If the PDF does not exist.
    """
    path = Path(pdf_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    import fitz

    with fitz.open(path) as document:
        page_count = document.page_count

    raw_text = extract_text_from_pdf(path)
    lines = [line.strip() for line in raw_text.splitlines()]
    numbered_blocks = sum(1 for line in lines if _NUMBERED_BLOCK.match(line))
    int_ext_sluglines = max(
        sum(1 for line in lines if _INT_EXT_LINE.match(line)),
        count_final_draft_sluglines(path),
    )

    engine_scene_count = 0
    conversion_path = "unknown"
    notes: list[str] = []

    try:
        fountain_text = load_screenplay_from_pdf(path)
        engine_scene_count = len(SceneDependencyEngine().parse_fountain_text(fountain_text))
        conversion_path = "int_ext_sluglines"
    except PdfScreenplayError:
        from docx_to_fountain import convert_numbered_prose_pdf_to_fountain

        fountain_text = convert_numbered_prose_pdf_to_fountain(path)
        engine_scene_count = len(SceneDependencyEngine().parse_fountain_text(fountain_text))
        conversion_path = "numbered_blocks_only"

    if int_ext_sluglines >= 100:
        notes.append(
            f"Standard screenplay structure: {int_ext_sluglines} INT./EXT. sluglines "
            f"inside {numbered_blocks} numbered section(s)."
        )
    elif numbered_blocks > 0 and int_ext_sluglines == 0:
        notes.append(
            f"Prose-numbered export: {numbered_blocks} blocks but no INT./EXT. sluglines. "
            "Writer scene numbers from a 210-scene edition will not align."
        )
        notes.append(
            "Re-export from Final Draft / WriterDuet with sluglines enabled, or upload "
            "a .fountain file with INT./EXT. headings."
        )
    elif int_ext_sluglines == 0:
        notes.append("No INT./EXT. sluglines or numbered blocks detected.")

    if numbered_blocks > 0 and int_ext_sluglines > numbered_blocks:
        avg = int_ext_sluglines / numbered_blocks
        notes.append(
            f"Average {avg:.1f} sluglines per numbered block "
            f"({numbered_blocks} blocks -> {int_ext_sluglines} scenes)."
        )

    return PdfSceneDiagnosis(
        pdf_path=path,
        page_count=page_count,
        numbered_blocks=numbered_blocks,
        int_ext_sluglines=int_ext_sluglines,
        engine_scene_count=engine_scene_count,
        conversion_path=conversion_path,
        notes=tuple(notes),
    )


def format_diagnosis_report(diagnosis: PdfSceneDiagnosis) -> str:
    """Render a human-readable scene-structure report.

    Args:
        diagnosis: Output from ``diagnose_pdf_scenes``.

    Returns:
        Plain-text report suitable for printing or saving.
    """
    lines = [
        f"PDF SCENE DIAGNOSIS: {diagnosis.pdf_path.name}",
        "=" * 72,
        f"  Pages:              {diagnosis.page_count}",
        f"  Numbered blocks:    {diagnosis.numbered_blocks}  (e.g. '12.' section markers)",
        f"  INT./EXT. sluglines: {diagnosis.int_ext_sluglines}",
        f"  Engine scene count: {diagnosis.engine_scene_count}",
        f"  Conversion path:    {diagnosis.conversion_path}",
        "",
    ]
    if diagnosis.notes:
        lines.append("Notes:")
        for note in diagnosis.notes:
            lines.append(f"  - {note}")
        lines.append("")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    """Parse command-line options for PDF scene diagnosis."""
    parser = argparse.ArgumentParser(
        description="Report numbered blocks, INT./EXT. sluglines, and engine scene count."
    )
    parser.add_argument("pdf", type=Path, help="Screenplay PDF to diagnose.")
    return parser.parse_args()


def main() -> None:
    """CLI entry point for PDF scene diagnosis."""
    args = _parse_args()
    diagnosis = diagnose_pdf_scenes(args.pdf)
    print(format_diagnosis_report(diagnosis))


if __name__ == "__main__":
    main()
