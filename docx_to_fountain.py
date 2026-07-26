"""Convert Hollywood-format Word screenplays to Fountain text."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.text.paragraph import Paragraph

SCENE_HEADING_START = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s+",
    re.IGNORECASE | re.MULTILINE,
)
TRANSITION_PATTERN = re.compile(
    r"^(FADE IN\.?|FADE OUT\.?|FADE TO BLACK\.?|CUT TO:|DISSOLVE TO:|"
    r"MATCH CUT TO:|SMASH CUT TO:|TIME CUT:|INTERCUT:|END\.?)$",
    re.IGNORECASE,
)
CHARACTER_CUE_PATTERN = re.compile(r"^[A-Z][A-Z0-9 .'\-@()]+$")
SCENE_SLUG_START = re.compile(
    r"^(?:"
    r"PAN\b|"
    r"We (?:see|TILT|PAN|PULL|PUSH|hear|MOVE|CUT)\b|"
    r"The (?:front|door|end|next|following|basement|bedroom|kitchen|school|house|"
    r"party|mall|gym|office|living|dining|hall|street|parking|locker|cafeteria|"
    r"auditorium|classroom|bathroom|shower|pool|field|campus|library|store|shop|"
    r"restaurant|bar|club|room|apartment|hotel|church|hospital|station|airport|"
    r"high school|parking lot|gym)\b|"
    r"INTERCUT\b|"
    r"A few (?:days|weeks|months|hours|minutes)\b|"
    r"That (?:night|morning|evening|afternoon)\b|"
    r"Later that\b|"
    r"The next (?:day|morning|evening|afternoon)\b"
    r")",
    re.IGNORECASE,
)
SCENE_NUMBER_LINE = re.compile(r"^(\d{1,3})\.\s*$")
SUPPORTED_DOCX_SUFFIXES: frozenset[str] = frozenset({".docx"})


class DocxScreenplayError(Exception):
    """Raised when a Word document cannot be converted to Fountain."""


def _left_indent_inches(paragraph: Paragraph) -> float:
    """Return the paragraph left indent in inches."""
    indent = paragraph.paragraph_format.left_indent
    if indent is None:
        return 0.0
    return float(indent.inches)


def _is_transition(line: str) -> bool:
    """Return True when the line is a screenplay transition."""
    stripped = line.strip()
    if TRANSITION_PATTERN.match(stripped):
        return True
    return stripped.endswith(":") and stripped == stripped.upper() and len(stripped) > 1


def _is_character_cue(line: str) -> bool:
    """Return True when the line is an all-caps character cue."""
    stripped = line.strip()
    if not stripped or SCENE_HEADING_START.match(stripped) or _is_transition(stripped):
        return False
    if stripped.startswith("(") and stripped.endswith(")"):
        return False
    if not CHARACTER_CUE_PATTERN.match(stripped):
        return False
    letters = [char for char in stripped if char.isalpha()]
    if not letters:
        return False
    return all(char.isupper() for char in letters)


def _is_scene_slug(line: str) -> bool:
    """Return True when an action line likely starts a new scene block."""
    stripped = line.strip()
    if not stripped or SCENE_HEADING_START.match(stripped):
        return False
    if _is_transition(stripped) or _is_character_cue(stripped):
        return False
    return bool(SCENE_SLUG_START.match(stripped))


def _heading_from_slug(text: str, scene_number: int) -> str:
    """Build a synthetic Fountain scene heading from a slug action line."""
    stripped = text.strip()
    if SCENE_HEADING_START.match(stripped):
        return stripped.upper()
    location = stripped.split(".")[0].strip()
    if len(location) > 72:
        location = location[:72].rsplit(" ", 1)[0]
    if not location:
        location = f"SCENE {scene_number}"
    return f"INT. {location.upper()} - DAY"


def _classify_paragraph(paragraph: Paragraph) -> str:
    """Classify one Word paragraph as a screenplay element kind."""
    text = paragraph.text.strip()
    if not text:
        return "blank"
    if SCENE_HEADING_START.match(text):
        return "scene"
    if _is_transition(text):
        return "transition"
    if paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER and _is_character_cue(text):
        return "character"
    if text.startswith("(") and text.endswith(")"):
        return "parenthetical"
    left_indent = _left_indent_inches(paragraph)
    if paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER and left_indent >= 0.9:
        return "dialogue"
    if left_indent >= 1.4:
        return "parenthetical"
    if left_indent >= 0.9:
        return "dialogue"
    return "action"


def _needs_scene_heading(
    kind: str,
    text: str,
    *,
    in_body: bool,
    scene_count: int,
) -> bool:
    """Return True when a new Fountain scene heading should be inserted."""
    if kind == "scene":
        return True
    if not in_body:
        return False
    if kind == "transition" and text.strip().upper() != "FADE IN:":
        return True
    if kind == "action" and _is_scene_slug(text):
        return True
    return scene_count == 0 and kind in {"action", "character", "dialogue"}


def _append_fountain_line(lines: list[str], text: str) -> None:
    """Append one Fountain body line with a trailing blank line."""
    if lines and lines[-1] != "":
        lines.append("")
    lines.append(text)


def convert_numbered_prose_text_to_fountain(text: str) -> str:
    """Convert prose PDF/Word text with ``N.`` scene markers to Fountain.

    Some screenplays export as numbered blocks (``1.``, ``2.``, …) without
    ``INT.``/``EXT.`` headings. This inserts synthetic scene headings at each
    marker so ScriptLens can parse scene boundaries.

    Args:
        text: Raw plain text from PDF or Word extraction.

    Returns:
        Fountain-style plain text with one heading per numbered block.

    Raises:
        DocxScreenplayError: If no numbered scene markers are found.
    """
    lines: list[str] = []
    in_body = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue

        marker = SCENE_NUMBER_LINE.match(stripped)
        if marker is not None:
            scene_number = int(marker.group(1))
            _append_fountain_line(lines, f"INT. SCENE {scene_number} - DAY")
            in_body = True
            continue

        if not in_body:
            if stripped.lower().startswith("written by"):
                _append_fountain_line(lines, stripped)
            elif stripped == stripped.upper() and len(stripped.split()) <= 6:
                _append_fountain_line(lines, stripped)
            continue

        if _is_transition(stripped):
            _append_fountain_line(lines, stripped.upper())
            continue
        if _is_character_cue(stripped):
            _append_fountain_line(lines, stripped.upper())
            continue
        if stripped.startswith("(") and stripped.endswith(")"):
            _append_fountain_line(lines, stripped)
            continue
        _append_fountain_line(lines, stripped)

    fountain = "\n".join(lines)
    fountain = re.sub(r"\n{3,}", "\n\n", fountain).strip() + "\n"
    if not SCENE_HEADING_START.search(fountain):
        raise DocxScreenplayError(
            "No numbered scene markers (e.g. '12.') found in prose screenplay text."
        )
    return fountain


def convert_numbered_prose_pdf_to_fountain(pdf_path: str | Path) -> str:
    """Extract a numbered prose PDF and convert it to Fountain text.

    Args:
        pdf_path: Path to a screenplay PDF without ``INT.``/``EXT.`` headings.

    Returns:
        Fountain-style plain text.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        DocxScreenplayError: If extraction or conversion fails.
    """
    from pdf_screenplay_loader import extract_text_from_pdf

    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")
    raw_text = extract_text_from_pdf(path)
    if not raw_text.strip():
        raise DocxScreenplayError(f"No extractable text in PDF: {path.name}")
    return convert_numbered_prose_text_to_fountain(raw_text)


def convert_docx_to_fountain(docx_path: str | Path) -> str:
    """Convert a Hollywood-format Word screenplay to Fountain plain text.

    Word exports often omit ``INT.``/``EXT.`` headings. This converter preserves
    dialogue and action structure, then synthesizes scene headings at transitions
    and location-establishing slug lines so ScriptLens can parse scenes.

    Args:
        docx_path: Path to a ``.docx`` screenplay file.

    Returns:
        Fountain-style plain text.

    Raises:
        FileNotFoundError: If the path does not exist.
        DocxScreenplayError: If the file is not a supported Word document.
    """
    path = Path(docx_path)
    if not path.is_file():
        raise FileNotFoundError(f"Word document not found: {path}")
    if path.suffix.lower() not in SUPPORTED_DOCX_SUFFIXES:
        raise DocxScreenplayError(f"Expected a .docx file, got: {path.suffix}")

    document = Document(str(path))
    lines: list[str] = []
    scene_count = 0
    body_started = False
    preamble_done = False

    for paragraph in document.paragraphs:
        kind = _classify_paragraph(paragraph)
        text = paragraph.text.strip()

        if kind == "blank":
            if lines and lines[-1] != "":
                lines.append("")
            continue

        if not preamble_done:
            if text.lower().startswith("written by"):
                lines.extend([text, ""])
                continue
            if text.lower() in {"address phone number", "address", "phone number"}:
                continue
            if kind != "action":
                if (
                    paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER
                    and text == text.upper()
                ):
                    lines.extend([text, ""])
                else:
                    lines.extend([text, ""])
                continue
            preamble_done = True

        if kind in {"action", "character", "dialogue", "transition", "scene"}:
            body_started = True

        if _needs_scene_heading(
            kind,
            text,
            in_body=body_started,
            scene_count=scene_count,
        ):
            if kind == "scene":
                heading = text.upper()
            else:
                scene_count += 1
                heading = _heading_from_slug(text, scene_count)
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(heading)
            lines.append("")
            if kind == "scene":
                continue

        if kind == "transition":
            lines.extend([text.upper(), ""])
            continue
        if kind == "character":
            lines.extend([text.upper(), ""])
            continue
        if kind == "parenthetical":
            inner = text.strip("()")
            lines.extend([f"({inner})", ""])
            continue
        if kind == "dialogue":
            lines.extend([text, ""])
            continue
        lines.extend([text, ""])

    fountain = "\n".join(lines)
    fountain = re.sub(r"\n{3,}", "\n\n", fountain).strip() + "\n"
    if not SCENE_HEADING_START.search(fountain):
        raise DocxScreenplayError(
            f"No scene headings produced from {path.name}. "
            "Re-export with INT./EXT. headings or use a PDF/Fountain source."
        )
    return fountain


def convert_docx_to_fountain_file(
    docx_path: str | Path,
    output_path: str | Path,
) -> Path:
    """Convert a Word screenplay and write Fountain text to disk.

    Args:
        docx_path: Source ``.docx`` file.
        output_path: Destination ``.fountain`` path.

    Returns:
        Resolved path to the written Fountain file.
    """
    fountain = convert_docx_to_fountain(docx_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fountain, encoding="utf-8")
    return out.resolve()
