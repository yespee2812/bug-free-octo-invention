"""Reflow and clean PDF-extracted screenplay text into analysis-friendly Fountain.

PDF extraction often puts one phrase per line and leaves camera slugs as
standalone ALL-CAPS lines. The parser then treats those slugs as character
names, which causes false positives. This script merges action prose, keeps
real scene headings and character cues, and demotes slug lines to action.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pdf_screenplay_loader import SCENE_HEADING_START

SCENE_PREFIX_ONLY = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s*$",
    re.IGNORECASE,
)
TRANSITION_LINE = re.compile(
    r"^(FADE IN\.?|FADE OUT\.?|FADE TO BLACK\.?|CUT TO:|DISSOLVE TO:|"
    r"MATCH CUT TO:|SMASH CUT TO:|TIME CUT:|INTERCUT:|END\.?)$",
    re.IGNORECASE,
)
CHARACTER_CUE_LINE = re.compile(r"^[A-Z][A-Z0-9 .'\-@()]+$")
REVISION_LINE = re.compile(
    r"^(REVISION|REVISED|OMITTED|OMIT|CONTINUED|CONT'D|CONTINUES)\b",
    re.IGNORECASE,
)
REVISION_PAGE = re.compile(r"^REVISION\s+PAGES?\s+\d", re.IGNORECASE)
PAGE_NOISE = re.compile(r"^\d{1,3}\.?$")
DRAFT_TITLE = re.compile(
    r"^(SECOND DRAFT|SHOOTING SCRIPT|FINAL DRAFT|\d{1,2}\s+[A-Z][a-z]+\s+\d{4})$",
    re.IGNORECASE,
)

SLUG_KEYWORDS: frozenset[str] = frozenset(
    {
        "ANGLE",
        "ANOTHER",
        "APPLAUSE",
        "BACK",
        "BENEATH",
        "BLACK",
        "CACOPHONY",
        "CEILING",
        "CLOSE",
        "CLOSEUP",
        "CONT",
        "CONTINUED",
        "DOWNWARDS",
        "EXT",
        "FANFARE",
        "FEATURING",
        "FIASH",
        "FLASH",
        "FULL",
        "GROUP",
        "GYM",
        "GYMNASIUM",
        "HALLWAY",
        "HOLD",
        "INSERT",
        "INT",
        "LIBRARY",
        "LONG",
        "MONTAGE",
        "MOTION",
        "OMIT",
        "OMITTED",
        "PAN",
        "POV",
        "REVEALED",
        "REVISION",
        "ROLL",
        "INTERCUT",
        "CREDITS",
        "SERIES",
        "SHOT",
        "STAGE",
        "STREET",
        "STUDENTS",
        "SUPER",
        "TIGHTER",
        "TRACKING",
        "UNDER",
        "UPWARDS",
        "WIDE",
        "WINDOW",
    }
)

SLUG_PHRASES: tuple[str, ...] = (
    "THE BAND",
    "THE END",
    "THE HOSE",
    "THE HOUSE",
    "THE GYM",
    "THE STAGE",
    "THE HILL",
    "THE CHEVY",
    "THE DOORS",
    "THE LIGHT",
    "THE BOYS",
    "THE GIRLS",
    "THE STUDENTS",
    "THE WHITE HOUSE",
    "THE HORAN HOUSE",
    "CARRIE AND TOMMY",
    "CARRIE AND TOHMY",
    "GEORGE DAWSON",
    "ROLL CREDITS",
    "INTERCUT WITH",
    "ALL THE GUYS",
    "PRE-PROM MONTAGE",
    "VOCAL JAZZ GUYS",
)


def _is_scene_heading(line: str) -> bool:
    """Return True when the line is a Fountain scene heading."""
    return bool(SCENE_HEADING_START.match(line.strip()))


def _is_transition(line: str) -> bool:
    """Return True when the line is a screenplay transition."""
    return bool(TRANSITION_LINE.match(line.strip()))


def _is_noise_line(line: str) -> bool:
    """Return True when the line is title-page or PDF noise."""
    stripped = line.strip()
    if not stripped:
        return False
    if PAGE_NOISE.match(stripped):
        return True
    if REVISION_PAGE.match(stripped):
        return True
    if DRAFT_TITLE.match(stripped):
        return True
    if stripped in {"/", ")", "r", "Screenplay", "by", "based on the novel"}:
        return True
    if stripped.startswith('"') and stripped.endswith('"'):
        return True
    return False


def _is_slug_caps_line(line: str) -> bool:
    """Return True when an ALL-CAPS line is a camera slug, not a character cue."""
    stripped = line.strip()
    if not stripped or _is_scene_heading(stripped) or _is_transition(stripped):
        return False
    if not CHARACTER_CUE_LINE.match(stripped):
        return False
    upper = stripped.upper()
    if REVISION_LINE.match(upper):
        return True
    if any(phrase in upper for phrase in SLUG_PHRASES):
        return True
    words = upper.replace(".", " ").replace("-", " ").split()
    if not words:
        return False
    if words[0] in SLUG_KEYWORDS:
        return True
    if words[0] == "THE" and len(words) >= 2:
        return True
    if any(word in SLUG_KEYWORDS for word in words):
        return True
    if upper.endswith("--") or upper.endswith("."):
        return True
    if len(words) >= 4:
        return True
    return False


def _is_character_cue(line: str, next_line: str | None) -> bool:
    """Return True when the line is a real character cue before dialogue."""
    stripped = line.strip()
    if not stripped or _is_scene_heading(stripped) or _is_transition(stripped):
        return False
    if _is_slug_caps_line(stripped):
        return False
    if not CHARACTER_CUE_LINE.match(stripped):
        return False
    letters = [char for char in stripped if char.isalpha()]
    if not letters or not all(char.isupper() for char in letters):
        return False
    if len(stripped) > 35:
        return False
    if next_line is None:
        return True
    nxt = next_line.strip()
    if not nxt:
        return False
    if _is_scene_heading(nxt) or _is_transition(nxt):
        return False
    if CHARACTER_CUE_LINE.match(nxt) and not _is_slug_caps_line(nxt):
        return False
    return True


def _merge_scene_heading_prefix(lines: list[str], index: int) -> tuple[str, int]:
    """Merge a split scene heading starting at ``index``."""
    first = lines[index].strip()
    if not SCENE_PREFIX_ONLY.match(first):
        return first, index + 1
    parts = [first]
    cursor = index + 1
    while cursor < len(lines):
        part = lines[cursor].strip()
        if not part:
            cursor += 1
            continue
        parts.append(part)
        joined = " ".join(parts)
        if _is_scene_heading(joined):
            return joined, cursor + 1
        if len(parts) >= 4:
            break
        cursor += 1
    return " ".join(parts), cursor


def _flush_action_buffer(buffer: list[str], output: list[str]) -> None:
    """Join buffered action fragments into one or more action paragraphs."""
    if not buffer:
        return
    text = " ".join(buffer)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    if text:
        output.append(text)
    buffer.clear()


def reflow_extracted_screenplay(text: str) -> str:
    """Reflow PDF-extracted plain text into cleaner Fountain-style lines.

    Args:
        text: Raw extracted screenplay text.

    Returns:
        Reflowed plain text suitable for ``parse_fountain_text``.
    """
    raw_lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    output: list[str] = []
    action_buffer: list[str] = []
    index = 0
    started = False

    while index < len(raw_lines):
        line = raw_lines[index]
        if _is_noise_line(line):
            index += 1
            continue
        if not line:
            _flush_action_buffer(action_buffer, output)
            if output and output[-1] != "":
                output.append("")
            index += 1
            continue

        if SCENE_PREFIX_ONLY.match(line):
            _flush_action_buffer(action_buffer, output)
            merged, index = _merge_scene_heading_prefix(raw_lines, index)
            output.append(merged)
            started = True
            continue

        if _is_scene_heading(line) or _is_transition(line):
            _flush_action_buffer(action_buffer, output)
            output.append(line.strip())
            started = True
            index += 1
            continue

        next_line = raw_lines[index + 1] if index + 1 < len(raw_lines) else None
        if _is_character_cue(line, next_line):
            _flush_action_buffer(action_buffer, output)
            cue = re.sub(r"\s+", " ", line.strip())
            output.append(cue)
            index += 1
            continue

        if _is_slug_caps_line(line):
            action_buffer.append(line.strip().rstrip("-").strip())
            index += 1
            continue

        if not started and line.upper() in {"FADE IN:", "FADE IN"}:
            _flush_action_buffer(action_buffer, output)
            output.append("FADE IN:")
            started = True
            index += 1
            continue

        action_buffer.append(line.strip())
        index += 1

    _flush_action_buffer(action_buffer, output)
    cleaned: list[str] = []
    blank_run = 0
    for line in output:
        if not line:
            blank_run += 1
            if blank_run <= 2:
                cleaned.append("")
            continue
        blank_run = 0
        cleaned.append(line)
    return "\n".join(cleaned).strip() + "\n"


def cleanup_file(input_path: Path, output_path: Path) -> Path:
    """Read a screenplay file, reflow it, and write the cleaned output.

    Args:
        input_path: Source ``.fountain`` or ``.txt`` file.
        output_path: Destination path for cleaned text.

    Returns:
        Resolved path to the written file.
    """
    text = input_path.read_text(encoding="utf-8")
    cleaned = reflow_extracted_screenplay(text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(cleaned, encoding="utf-8")
    return output_path.resolve()


def _parse_args() -> argparse.Namespace:
    """Parse command-line options for screenplay cleanup."""
    parser = argparse.ArgumentParser(
        description="Reflow PDF-extracted Fountain text for ScriptLens analysis."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Source .fountain or .txt file extracted from PDF.",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="Destination file (default: <stem>_clean.fountain beside input).",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point for extracted Fountain cleanup."""
    args = _parse_args()
    input_path = args.input.resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")
    output_path = args.output or input_path.with_name(f"{input_path.stem}_clean.fountain")
    written = cleanup_file(input_path, output_path)
    print(f"Wrote cleaned screenplay: {written}")


if __name__ == "__main__":
    main()
