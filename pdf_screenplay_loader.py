"""Load Fountain-compatible screenplay text from PDF files."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import fitz

SCENE_PREFIX_PATTERN = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s*$",
    re.IGNORECASE,
)
SCENE_HEADING_START = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s+",
    re.IGNORECASE,
)
PAGE_NUMBER_PATTERN = re.compile(r"^\d{1,3}\.?$")
CONTINUED_PATTERN = re.compile(
    r"^(CONTINUED|CONT'D|CONTINUES|CONTINUED:)\s*:?\s*$",
    re.IGNORECASE,
)

SUPPORTED_PDF_SUFFIXES: frozenset[str] = frozenset({".pdf"})


class PdfScreenplayError(Exception):
    """Raised when a PDF cannot be read or yields no usable screenplay text."""


def load_screenplay_from_pdf(pdf_path: str | Path) -> str:
    """Extract and normalize screenplay text from a PDF file.

    Args:
        pdf_path: Path to a screenplay PDF.

    Returns:
        Plain text suitable for SceneDependencyEngine.parse_fountain_text.

    Raises:
        PdfScreenplayError: If the file is missing, not a PDF, or has no text.
        FileNotFoundError: If the path does not exist.
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() not in SUPPORTED_PDF_SUFFIXES:
        raise PdfScreenplayError(f"Expected a .pdf file, got: {path.suffix}")

    raw_text = extract_text_from_pdf(path)
    if not raw_text.strip():
        raise PdfScreenplayError(
            f"No extractable text in PDF: {path}. "
            "Scanned/image-only PDFs need OCR before analysis."
        )

    normalized = normalize_extracted_screenplay_text(raw_text)
    if not _has_scene_headings(normalized):
        raise PdfScreenplayError(
            f"No scene headings (INT./EXT.) found after extracting {path.name}. "
            "Export the script as text-based PDF or Fountain from your writing app."
        )
    return normalized


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from each PDF page in top-to-bottom reading order.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Raw text with page breaks preserved as blank lines.
    """
    page_texts: list[str] = []
    with fitz.open(pdf_path) as document:
        if document.page_count == 0:
            return ""
        for page in document:
            page_texts.append(_extract_page_text(page))
    return "\n\n".join(page_texts)


def _extract_page_text(page: fitz.Page) -> str:
    """Extract ordered text blocks from a single PDF page."""
    blocks = page.get_text("blocks")
    text_blocks: list[tuple[float, float, str]] = []
    for block in blocks:
        if len(block) < 7:
            continue
        block_type = block[6]
        if block_type != 0:
            continue
        text = str(block[4]).strip()
        if text:
            text_blocks.append((block[1], block[0], text))

    text_blocks.sort(key=lambda item: (round(item[0], 1), item[1]))
    return "\n".join(text for _, _, text in text_blocks)


def normalize_extracted_screenplay_text(text: str) -> str:
    """Clean PDF extraction artifacts and repair common heading line breaks.

    Args:
        text: Raw text from PDF extraction.

    Returns:
        Normalized screenplay plain text.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)

    lines = [line.strip() for line in text.split("\n")]
    merged_lines = _merge_split_scene_headings(lines)
    filtered_lines = _filter_noise_lines(merged_lines)

    cleaned: list[str] = []
    blank_run = 0
    for line in filtered_lines:
        if not line:
            blank_run += 1
            if blank_run <= 2:
                cleaned.append("")
            continue
        blank_run = 0
        cleaned.append(_normalize_scene_heading_line(line))

    return "\n".join(cleaned).strip() + "\n"


def _merge_split_scene_headings(lines: list[str]) -> list[str]:
    """Join scene headings split across lines (common in PDF export)."""
    merged: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if (
            line
            and SCENE_PREFIX_PATTERN.match(line)
            and index + 1 < len(lines)
            and lines[index + 1]
            and not SCENE_HEADING_START.match(lines[index + 1])
            and not _is_character_cue_line(lines[index + 1])
        ):
            merged.append(f"{line} {lines[index + 1]}")
            index += 2
            continue
        merged.append(line)
        index += 1
    return merged


def _filter_noise_lines(lines: list[str]) -> list[str]:
    """Remove page numbers, CONTINUED markers, and empty lines."""
    filtered: list[str] = []
    for line in lines:
        if not line:
            filtered.append("")
            continue
        if PAGE_NUMBER_PATTERN.match(line):
            continue
        if CONTINUED_PATTERN.match(line):
            continue
        if line.lower() in {"fade in:", "fade in", "fade out.", "fade out", "the end"}:
            filtered.append(line.upper() if "fade" in line.lower() else line)
            continue
        filtered.append(line)
    return filtered


def _normalize_scene_heading_line(line: str) -> str:
    """Normalize spacing in scene heading lines."""
    if not SCENE_HEADING_START.match(line):
        return line
    match = SCENE_HEADING_START.match(line)
    if not match:
        return line
    prefix = match.group(1).upper()
    if prefix == "I/E.":
        prefix = "INT/EXT."
    remainder = line[match.end() :].strip()
    remainder = re.sub(r"\s*-\s*", " - ", remainder)
    return f"{prefix} {remainder}".strip()


def _has_scene_headings(text: str) -> bool:
    """Return True when text contains at least one INT./EXT. scene heading line."""
    for line in text.splitlines():
        if SCENE_HEADING_START.match(line.strip()):
            return True
    return False


def _is_character_cue_line(line: str) -> bool:
    """Return True when a line looks like an all-caps character cue."""
    stripped = line.strip()
    if not stripped or stripped.startswith("("):
        return False
    if re.search(
        r" - (DAY|NIGHT|EVENING|MORNING|AFTERNOON|DUSK|DAWN|SUNRISE|SUNSET)\s*$",
        stripped,
        re.IGNORECASE,
    ):
        return False
    letters = [char for char in stripped if char.isalpha()]
    if not letters:
        return False
    return all(char.isupper() for char in letters) and len(stripped) < 40


def write_screenplay_pdf(screenplay_text: str, pdf_path: str | Path) -> Path:
    """Write plain screenplay text to a simple PDF (used for tests).

    Args:
        screenplay_text: Fountain-style plain text.
        pdf_path: Output PDF path.

    Returns:
        Resolved path to the written PDF.
    """
    path = Path(pdf_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open()
    page = document.new_page(width=612, height=792)
    cursor_y = 72.0
    line_height = 12.0
    bottom_margin = 720.0
    left_margin = 72.0

    for line in screenplay_text.splitlines():
        if cursor_y > bottom_margin:
            page = document.new_page(width=612, height=792)
            cursor_y = 72.0
        page.insert_text(
            (left_margin, cursor_y),
            line or " ",
            fontsize=10,
            fontname="courier",
        )
        cursor_y += line_height

    document.save(path)
    document.close()
    return path.resolve()
