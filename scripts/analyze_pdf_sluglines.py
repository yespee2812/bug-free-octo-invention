"""Detect Final Draft-style slugline rows in screenplay PDFs."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import fitz

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pdf_screenplay_loader import (
    _group_page_rows,
    _slugline_heading_from_parts,
    count_final_draft_sluglines,
)

_LEFT_NUMBER = re.compile(r"^\d{1,3}$")
_RIGHT_NUMBER = re.compile(r"^\d{1,3}\.?$")


@dataclass(frozen=True)
class SluglineRow:
    """One Final Draft-style slugline row with margin scene numbers."""

    page: int
    scene_number: int
    heading: str
    left_number: str
    right_number: str
    y_position: float


@dataclass(frozen=True)
class SluglineAnalysis:
    """Slugline-structure metrics for one screenplay PDF."""

    pdf_path: Path
    page_count: int
    slugline_rows: tuple[SluglineRow, ...]
    reference_matches: tuple[tuple[int, str, bool], ...]


def detect_final_draft_sluglines(pdf_path: str | Path) -> list[SluglineRow]:
    """Find slugline rows formatted as ``N  INT./EXT. ...  N``.

    Final Draft often places the left scene number, slugline, and right scene
    number on separate PDF line objects that share the same y-coordinate.

    Args:
        pdf_path: Path to a screenplay PDF.

    Returns:
        Ordered slugline rows detected via positioned text extraction.
    """
    path = Path(pdf_path).resolve()
    rows: list[SluglineRow] = []

    with fitz.open(path) as document:
        for page_index, page in enumerate(document):
            for y_position, parts in _group_page_rows(page.get_text("dict")):
                parts.sort(key=lambda item: item[0])
                heading_text = _slugline_heading_from_parts(parts)
                if heading_text is None:
                    continue

                heading_x = next(
                    x_pos for x_pos, text in parts if text == heading_text
                )
                left_number = ""
                right_number = ""
                for x_pos, text in parts:
                    if x_pos < heading_x and _LEFT_NUMBER.match(text):
                        left_number = text
                    if x_pos > heading_x and _RIGHT_NUMBER.match(text):
                        right_number = text.rstrip(".")

                scene_number = 0
                if left_number.isdigit():
                    scene_number = int(left_number)
                elif right_number.isdigit():
                    scene_number = int(right_number)

                rows.append(
                    SluglineRow(
                        page=page_index + 1,
                        scene_number=scene_number,
                        heading=heading_text.upper(),
                        left_number=left_number,
                        right_number=right_number,
                        y_position=y_position,
                    )
                )

    rows.sort(key=lambda item: (item.scene_number or 0, item.page, item.y_position))
    return rows


def analyze_sluglines(
    pdf_path: str | Path,
    reference_headings: tuple[tuple[int, str], ...] | None = None,
) -> SluglineAnalysis:
    """Analyze Final Draft slugline rows and optional reference headings.

    Args:
        pdf_path: Path to a screenplay PDF.
        reference_headings: Optional ``(scene_number, heading)`` pairs to verify.

    Returns:
        Structured slugline analysis for reporting.
    """
    path = Path(pdf_path).resolve()
    with fitz.open(path) as document:
        page_count = document.page_count

    slugline_rows = tuple(detect_final_draft_sluglines(path))
    default_reference = (
        (2, "EXT. EAST GREAT FALLS - DAY"),
        (3, "EXT. FRONT OF SCHOOL - DAY"),
    )
    refs = reference_headings if reference_headings is not None else default_reference

    by_scene = {row.scene_number: row.heading for row in slugline_rows if row.scene_number}
    reference_matches = tuple(
        (scene_number, heading, by_scene.get(scene_number) == heading.upper())
        for scene_number, heading in refs
    )
    return SluglineAnalysis(
        pdf_path=path,
        page_count=page_count,
        slugline_rows=slugline_rows,
        reference_matches=reference_matches,
    )


def format_slugline_report(analysis: SluglineAnalysis) -> str:
    """Render a human-readable slugline analysis report.

    Args:
        analysis: Output from ``analyze_sluglines``.

    Returns:
        Plain-text report suitable for printing or saving.
    """
    lines = [
        f"SLUGLINE ANALYSIS: {analysis.pdf_path.name}",
        "=" * 72,
        f"  Pages:                 {analysis.page_count}",
        f"  Final Draft slug rows: {len(analysis.slugline_rows)}",
        "",
        "Reference check (screenshot scenes 2 and 3):",
    ]
    for scene_number, heading, matched in analysis.reference_matches:
        status = "FOUND" if matched else "MISSING"
        actual = next(
            (row.heading for row in analysis.slugline_rows if row.scene_number == scene_number),
            "(not detected)",
        )
        lines.append(f"  Scene {scene_number}: {status}")
        lines.append(f"    expected: {heading}")
        lines.append(f"    actual:   {actual}")
        lines.append("")

    if analysis.slugline_rows:
        lines.append("First 12 slugline rows:")
        for row in analysis.slugline_rows[:12]:
            lines.append(
                f"  Scene {row.scene_number:>3} | p{row.page:>3} | "
                f"{row.left_number!r} | {row.heading} | {row.right_number!r}"
            )
        if len(analysis.slugline_rows) > 12:
            lines.append(f"  ... and {len(analysis.slugline_rows) - 12} more")
        lines.append("")
    else:
        lines.extend(
            [
                "No Final Draft slugline rows detected.",
                "",
                "Expected row format (from screenshot):",
                "  2          EXT. EAST GREAT FALLS - DAY          2",
                "  3          EXT. FRONT OF SCHOOL - DAY           3",
                "",
                "This PDF appears to be a prose-numbered export without INT./EXT. rows.",
                "Planted-error scene numbers in the writer log will not align until a",
                "slugline-enabled Final Draft PDF is used.",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for Final Draft slugline analysis."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_pdf_sluglines.py <screenplay.pdf>")
        raise SystemExit(1)

    analysis = analyze_sluglines(sys.argv[1])
    print(format_slugline_report(analysis))


if __name__ == "__main__":
    main()
