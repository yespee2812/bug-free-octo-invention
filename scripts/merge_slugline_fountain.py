"""Merge slugline structure with an error-bearing prose Fountain export."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pdf_screenplay_loader import SCENE_HEADING_LINE
from scene_dependency import SceneDependencyEngine

SYNTHETIC_SCENE_HEADING = re.compile(r"^INT\.\s+SCENE\s+\d+\b", re.IGNORECASE)
TITLE_PAGE_LINE = re.compile(
    r"^(AMERICAN PIE|Written by|Adam Herz|Address|Phone Number)$",
    re.IGNORECASE,
)


def _normalize_for_anchor(text: str) -> str:
    """Lowercase and collapse whitespace for fuzzy anchor matching."""
    lowered = text.lower().replace("\u2019", "'")
    return re.sub(r"\s+", " ", lowered).strip()


def _anchor_words(body: str, word_count: int = 12) -> str:
    """Return the first N words of body text as a normalized anchor phrase."""
    tokens = re.findall(r"\S+", _normalize_for_anchor(body))
    return " ".join(tokens[:word_count])


def _build_norm_index(source: str) -> tuple[str, list[int]]:
    """Build a normalized string and map each norm char to a source index."""
    norm_chars: list[str] = []
    index_map: list[int] = []
    previous_was_space = True
    for index, char in enumerate(source):
        if char.isspace():
            if not previous_was_space and norm_chars:
                norm_chars.append(" ")
                index_map.append(index)
            previous_was_space = True
            continue
        norm_chars.append(char.lower())
        index_map.append(index)
        previous_was_space = False
    return "".join(norm_chars).strip(), index_map


def _slice_source_from_norm_range(
    source: str,
    norm_text: str,
    index_map: list[int],
    start: int,
    end: int,
) -> str:
    """Map a normalized [start:end) range back to the original source substring."""
    if start >= len(index_map):
        return ""
    if end <= start:
        return ""
    end = min(end, len(index_map))
    start_index = index_map[start]
    end_index = index_map[end - 1] + 1
    return source[start_index:end_index].strip()


def split_slugline_scenes(text: str) -> list[tuple[str, str]]:
    """Split a slugline Fountain file into ``(heading, body)`` scene tuples."""
    scenes: list[tuple[str, str]] = []
    heading: str | None = None
    body_lines: list[str] = []
    started = False

    for line in text.splitlines():
        stripped = line.strip()
        if SCENE_HEADING_LINE.match(stripped) and not SYNTHETIC_SCENE_HEADING.match(stripped):
            if heading is not None:
                scenes.append((heading, "\n".join(body_lines).strip()))
            heading = stripped.upper()
            body_lines = []
            started = True
            continue
        if not started:
            continue
        if heading is not None:
            body_lines.append(line)

    if heading is not None:
        scenes.append((heading, "\n".join(body_lines).strip()))
    return scenes


def extract_title_page(text: str) -> list[str]:
    """Return title-page lines that appear before the first slugline scene."""
    title_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if SCENE_HEADING_LINE.match(stripped) and not SYNTHETIC_SCENE_HEADING.match(stripped):
            break
        title_lines.append(line)
    return title_lines


def strip_error_body(text: str) -> str:
    """Remove synthetic headings and title noise from an error-bearing Fountain file."""
    lines: list[str] = []
    started = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if started:
                lines.append("")
            continue
        if SYNTHETIC_SCENE_HEADING.match(stripped):
            continue
        if SCENE_HEADING_LINE.match(stripped):
            continue
        if not started and TITLE_PAGE_LINE.match(stripped):
            continue
        started = True
        lines.append(line)
    return "\n".join(lines).strip()


def _find_anchor(norm_text: str, anchor: str, start: int) -> int:
    """Find an anchor phrase in normalized text at or after ``start``."""
    if not anchor:
        return -1
    match = norm_text.find(anchor, start)
    if match >= 0:
        return match
    short_anchor = " ".join(anchor.split()[:6])
    return norm_text.find(short_anchor, start)


def merge_slugline_fountain(slugline_base: str, error_body_source: str) -> str:
    """Merge 210-scene sluglines with body text extracted from an error export.

    Args:
        slugline_base: Fountain text with real ``INT./EXT.`` sluglines (clean).
        error_body_source: Fountain or prose export containing planted errors.

    Returns:
        Combined Fountain text with slugline headings and error-bearing bodies.
    """
    scenes = split_slugline_scenes(slugline_base)
    if not scenes:
        raise ValueError("Slugline base contains no INT./EXT. scene headings.")

    error_body = strip_error_body(error_body_source)
    norm_error, norm_index = _build_norm_index(error_body)

    output_lines = extract_title_page(slugline_base)
    if output_lines and output_lines[-1].strip():
        output_lines.append("")

    cursor = 0
    for scene_index, (heading, clean_body) in enumerate(scenes):
        output_lines.append(heading)
        output_lines.append("")

        anchor = _anchor_words(clean_body)
        start = _find_anchor(norm_error, anchor, cursor)
        if start < 0:
            output_lines.append(clean_body)
            output_lines.append("")
            continue

        if scene_index + 1 < len(scenes):
            next_anchor = _anchor_words(scenes[scene_index + 1][1])
            end = _find_anchor(norm_error, next_anchor, start + len(anchor))
            if end < 0:
                end = len(norm_error)
        else:
            end = len(norm_error)

        segment = _slice_source_from_norm_range(error_body, norm_error, norm_index, start, end)
        output_lines.append(segment)
        output_lines.append("")
        cursor = end

    merged = "\n".join(output_lines)
    return re.sub(r"\n{3,}", "\n\n", merged).strip() + "\n"


def merge_slugline_files(
    slugline_path: Path,
    error_path: Path,
    output_path: Path,
) -> Path:
    """Read two Fountain files, merge them, and write the hybrid output.

    Args:
        slugline_path: Clean slugline Fountain source.
        error_path: Error-bearing Fountain export.
        output_path: Destination path for merged Fountain text.

    Returns:
        Resolved path to the written file.
    """
    slugline_text = slugline_path.read_text(encoding="utf-8")
    error_text = error_path.read_text(encoding="utf-8")
    merged = merge_slugline_fountain(slugline_text, error_text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged, encoding="utf-8")
    return output_path.resolve()


def _parse_args() -> argparse.Namespace:
    """Parse command-line options for slugline/error Fountain merge."""
    parser = argparse.ArgumentParser(
        description=(
            "Merge slugline structure from a clean Fountain file with body text "
            "from an error-bearing prose/OCR Fountain export."
        )
    )
    parser.add_argument(
        "slugline_base",
        type=Path,
        help="Clean Fountain file with INT./EXT. sluglines.",
    )
    parser.add_argument(
        "error_body",
        type=Path,
        help="Error-bearing Fountain export (e.g. ocred_refined.fountain).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output Fountain path (default: <error_stem>_merged.fountain).",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point for hybrid slugline merge."""
    args = _parse_args()
    slugline_path = args.slugline_base.resolve()
    error_path = args.error_body.resolve()
    output_path = args.output or error_path.with_name(f"{error_path.stem}_merged.fountain")

    written = merge_slugline_files(slugline_path, error_path, output_path)
    scene_count = len(SceneDependencyEngine().parse_fountain_text(written.read_text(encoding="utf-8")))
    print(f"Wrote merged Fountain: {written}")
    print(f"Engine scene count:    {scene_count}")


if __name__ == "__main__":
    main()
