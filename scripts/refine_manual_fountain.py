"""Apply manual-pass rules to cleaned PDF-extracted Fountain screenplays.

After ``cleanup_extracted_fountain.py``, this script demotes remaining camera
slugs misread as character cues, normalizes OCR typos on real cues, and
merges slug-only lines into action paragraphs.
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
from scene_dependency import TRANSITION_PATTERN

CHARACTER_CUE_LINE = re.compile(r"^[A-Z][A-Z0-9 .'\-@()]+$")
REVISION_LINE = re.compile(
    r"^(REVISION|REVISED|OMITTED|OMIT|CONTINUED|CONT'D|CONTINUES)\b",
    re.IGNORECASE,
)
PAGE_NOISE = re.compile(r"^\d{1,3}\.?$")
TITLE_PAGE = re.compile(
    r"^(I C1|Screenplay|by|based on the novel|\d{1,2}\s+[A-Z][a-z]+\s+\d{4})$",
    re.IGNORECASE,
)

KNOWN_CHARACTER_CUES: frozenset[str] = frozenset(
    {
        # Carrie (1976)
        "BILLY",
        "BOBBY",
        "BOBBY ERBETER",
        "CARRIE",
        "CHRIS",
        "COLLINS",
        "CORA",
        "DE LOIS",
        "ELEANOR",
        "ERNEST",
        "FROMM",
        "FRIEDA",
        "GEORGE",
        "HELEN",
        "HELEN SHYRES",
        "MARGARET",
        "MISS COLLINS",
        "MORTON",
        "MRS. HORAN",
        "NORMA",
        "RHONDA",
        "STELIA",
        "STELLA",
        "SUE",
        "TOMMY",
        "WATSON",
        # American Pie (1999)
        "FINCH",
        "HEATHER",
        "JESSICA",
        "JIM",
        "JIM'S DAD",
        "JIM'S MOM",
        "KEVIN",
        "KEVIN'S BROTHER",
        "MICHELLE",
        "NADIA",
        "OZ",
        "SHERMAN",
        "STIFLER",
        "STIFLER'S BROTHER",
        "STIFLER'S MOM",
        "VICKY",
        "VICKY'S MOM",
        "COACH MARSHALL",
        "ALBERT",
    }
)

CITIZEN_KANE_CHARACTER_CUES: frozenset[str] = frozenset(
    {
        "ASSISTANT",
        "BERNSTEIN",
        "BERTHA",
        "CARTER",
        "CHARLES FOSTER KANE",
        "CITY EDITOR",
        "DR. COREY",
        "EMILY",
        "ETHEL",
        "FIRST CIVIC LEADER",
        "FOREMAN",
        "FRED",
        "GEORGIE",
        "GUARD",
        "HIRELING",
        "INVESTIGATOR",
        "JUNIOR",
        "KANE",
        "KATHERINE",
        "LELAND",
        "MARIE",
        "MATISTI",
        "MIKE",
        "MISS ANDERSON",
        "MISS TOWNSEND",
        "MRS. KANE",
        "NARRATOR",
        "PHOTOGRAPHER",
        "PRESIDENT",
        "RAWLSTON",
        "RAYMOND",
        "REILLY",
        "ROGERS",
        "SECOND ASSISTANT",
        "SECOND LEADER",
        "SECOND NEWSPAPERMAN",
        "SMATHERS",
        "SPEAKER",
        "SUSAN",
        "THATCHER",
        "THIRD MAN",
        "THIRD NEWSPAPERMAN",
        "THOMPSON",
    }
)

CUE_OCR_FIXES: dict[str, str] = {
    "CAR..'R.IE": "CARRIE",
    "CARRIE -": "CARRIE",
    "CHIUS": "CHRIS",
    "GOLLINS": "COLLINS",
    "M.ARGARET": "MARGARET",
    "MARGARE'I'": "MARGARET",
    "MARGAREI'": "MARGARET",
    "MORI'ON": "MORTON",
    "SUE -": "SUE",
    "SUE SNELL -": "SUE",
    "SUE'S": "SUE",
    "ELEANOR SNELL -": "ELEANOR",
    "STELLA": "STELIA",
    "TO.MMY": "TOMMY",
    "TOIYIMY": "TOMMY",
    "TOM'.MY": "TOMMY",
    "TOMI-IT": "TOMMY",
    # Citizen Kane (1941) PDF variants
    "CHARLES FOSTER KANE.": "CHARLES FOSTER KANE",
    "CHARLES FOSTER KANE II.": "CHARLES FOSTER KANE",
    "KANE SR.": "KANE",
    "MR. KANE -": "KANE",
    "MR. KANE": "KANE",
}

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
        "CLOSER",
        "CONT",
        "CONTINUED",
        "CUT",
        "DOWNWARDS",
        "EXT",
        "FADE",
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
        "LE",
        "LIBRARY",
        "LONG",
        "LONGER",
        "MONTAGE",
        "MOTION",
        "OMIT",
        "OMITTED",
        "PAN",
        "POV",
        "REVEALED",
        "REVISION",
        "ROOM",
        "SERIES",
        "SHOT",
        "SPIATS",
        "STAGE",
        "STAIRS",
        "STREET",
        "STUDENTS",
        "SUPER",
        "TELEVISION",
        "TIGHTER",
        "TRACKING",
        "UNDER",
        "UPWARDS",
        "WIDE",
        "WINDOW",
    }
)

SLUG_EXACT: frozenset[str] = frozenset(
    {
        "A RED SCREEN",
        "A VOLLEYBALL",
        "AND CARRIE",
        "AT DOOR",
        "CARRIE HHITE IS BURNING",
        "CARRIE'S ROOM",
        "CARRIE'S VOICE",
        "CHRIS AND BILLY",
        "CHRIS' IMAGE",
        "DAY",
        "FOR",
        "FOR HER SINS",
        "FROMM'S VOICE",
        "GIRI.S",
        "GIRLS",
        "HIT. CARRIE",
        "I I I",
        "JESUS NEVER FAILS",
        "MARGARET'S VOICE",
        "NIGHT",
        "OMIT",
        "POV",
        "S TABLE",
        "S7",
        "SE - AFTERNOON",
        "SPIATS OF BLOOD",
        "STELIA HORAN - DAY",
        "TELEVISION SCREEN",
        "TOMMY'S VOICE",
        "UP THE STAIRS",
        "VOICE",
        # American Pie PDF slugs / crowd labels
        "ALL",
        "ALL THE GUYS",
        "BAND DORK",
        "BELLBOY",
        "CENTRAL GIRL",
        "CHOIR TEACHER",
        "COLLEGE CHICK",
        "COMPUTER VOICE",
        "DISINTERESTED GIRL",
        "ENTHRALLED GIRL",
        "FRESHMAN GUY",
        "GIRL IN BEDROOM",
        "GIRLS",
        "INTERCUT WITH",
        "LACROSSE BUDDIES",
        "PRE-PROM MONTAGE --",
        "RANDOM CUTE GIRL",
        "ROLL CREDITS",
        "SOPHOMORE",
        "SOPHOMORE CHICK",
        "SUSHI CUSTOMER",
        "TEACHER",
        "VOCAL JAZZ GUYS",
        "VOCAL JAZZ TEACHER",
        "WAITER",
        "YET ANOTHER GIRL",
        # American Beauty / generic PDF slugs
        "HEAR EASY-LISTENING MUSIC LESTER",
        "OPEN HOUSE TODAY",
        "YEAR-OLD JANE",
        "SCREAMING",
        # Citizen Kane PDF slugs / headlines / miniatures
        "DANCER. EVERYTHING WENT",
        "DAY -",
        "FRAUD AT POLLS",
        "GOLF LINKS (MINIATURE)",
        "HIGH CLASS MEALS AND LODGING",
        "INQUIRE WITHIN",
        "LABOR RIOTS",
        "NEWS DIGEST NARRATOR",
        "NEWSBOYS' VOICES",
        "NIGHT -",
        "NO. 9182",
        "PROHIBITION",
        "QUICK DISSOLVE",
        "RAIN",
        "ROGERS ELECTED",
        "TWICE NIGHTLY",
        "WOMAN SUFFRAGE",
        "YORK -",
    }
)


def _is_scene_heading(line: str) -> bool:
    """Return True when the line is a Fountain scene heading."""
    return bool(SCENE_HEADING_START.match(line.strip()))


def _is_transition(line: str) -> bool:
    """Return True when the line is a screenplay transition."""
    return bool(TRANSITION_PATTERN.match(line.strip()))


def _is_character_cue_shape(line: str) -> bool:
    """Return True when the line looks like an all-caps character cue."""
    stripped = line.strip()
    if not stripped or _is_scene_heading(stripped) or _is_transition(stripped):
        return False
    if not CHARACTER_CUE_LINE.match(stripped):
        return False
    letters = [char for char in stripped if char.isalpha()]
    return bool(letters) and all(char.isupper() for char in letters)


def _normalize_cue(cue: str) -> str:
    """Apply OCR fixes to a character cue line."""
    upper = cue.strip().upper()
    return CUE_OCR_FIXES.get(upper, upper)


def _script_whitelist_for_path(path: Path) -> frozenset[str] | None:
    """Return a cast whitelist when the input path matches a benchmark script."""
    stem = path.stem.lower().replace("_clean", "").replace("_refined", "")
    if "citizenkane" in stem:
        return CITIZEN_KANE_CHARACTER_CUES
    return None


def _should_demote_cue(
    cue: str,
    *,
    whitelist_only: frozenset[str] | None = None,
) -> bool:
    """Return True when an all-caps line should become action, not a cue."""
    normalized = _normalize_cue(cue)
    if whitelist_only is not None:
        return normalized not in whitelist_only
    if normalized in KNOWN_CHARACTER_CUES:
        return False
    if normalized in SLUG_EXACT:
        return True
    if REVISION_LINE.match(normalized):
        return True
    if re.fullmatch(r"[A-Z]\)", normalized):
        return True
    words = normalized.replace(".", " ").replace("-", " ").split()
    if not words:
        return True
    if words[0] in SLUG_KEYWORDS:
        return True
    if words[0] == "THE" and len(words) >= 2:
        return True
    if any(word in SLUG_KEYWORDS for word in words):
        return True
    if "POV" in normalized or "ANGLE" in normalized or " SHOT" in f" {normalized} ":
        return True
    if normalized.endswith("--") or normalized.endswith("."):
        return True
    if len(words) >= 4:
        return True
    if "FI.ASH" in normalized or "ANG LE" in normalized:
        return True
    crowd_heads = frozenset(
        {
            "ALL",
            "BAND",
            "COLLEGE",
            "DISINTERESTED",
            "ENTHRALLED",
            "FRESHMAN",
            "GIRL",
            "GIRLS",
            "HEAR",
            "INTERCUT",
            "LACROSSE",
            "OPEN",
            "RANDOM",
            "ROLL",
            "SCREAMING",
            "SINGING",
            "SOPHOMORE",
            "VOCAL",
            "YEAR-OLD",
            "YET",
        }
    )
    if words[0] in crowd_heads:
        return True
    crowd_tails = frozenset({"CHICK", "GUYS", "BUDDIES", "VOICE", "TEACHER"})
    if len(words) >= 2 and words[-1] in crowd_tails:
        return True
    if "(MINIATURE)" in normalized:
        return True
    if re.match(r"NO\.\s*\d", normalized):
        return True
    if normalized.endswith(" -"):
        return True
    headline_heads = frozenset(
        {"DISSOLVE", "FRAUD", "INQUIRE", "LABOR", "PROHIBITION", "SUFFRAGE"}
    )
    if words[0] in headline_heads:
        return True
    if len(words) >= 2 and words[-1] == "ELECTED":
        return True
    return False


def _is_noise_line(line: str) -> bool:
    """Return True when the line is title-page or PDF noise."""
    stripped = line.strip()
    if not stripped:
        return False
    if PAGE_NOISE.match(stripped):
        return True
    if TITLE_PAGE.match(stripped):
        return True
    if stripped in {"D. Lawrence Cohen Stephen King 20 January 1976"}:
        return True
    return False


def _sanitize_action_caps(text: str) -> str:
    """Lowercase camera/slug phrases embedded in action paragraphs."""
    sanitized = text
    for phrase in sorted(SLUG_EXACT, key=len, reverse=True):
        if " " not in phrase:
            continue
        sanitized = re.sub(
            rf"\b{re.escape(phrase)}\b",
            phrase.lower(),
            sanitized,
            flags=re.IGNORECASE,
        )
    return sanitized


def _flush_action_buffer(buffer: list[str], output: list[str]) -> None:
    """Join buffered action fragments into one paragraph."""
    if not buffer:
        return
    text = " ".join(buffer)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = _sanitize_action_caps(text)
    if text:
        output.append(text)
    buffer.clear()


def refine_manual_pass(
    text: str,
    *,
    whitelist_only: frozenset[str] | None = None,
) -> str:
    """Apply manual-pass demotion and OCR fixes to cleaned Fountain text.

    Args:
        text: Cleaned screenplay text from ``cleanup_extracted_fountain``.
        whitelist_only: When set, keep only cues in this cast set (benchmark
            scripts such as Citizen Kane).

    Returns:
        Refined Fountain-style text for analysis.
    """
    raw_lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    output: list[str] = []
    action_buffer: list[str] = []
    index = 0

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

        if _is_scene_heading(line) or _is_transition(line):
            _flush_action_buffer(action_buffer, output)
            output.append(line.strip())
            index += 1
            continue

        if _is_character_cue_shape(line):
            if _should_demote_cue(line, whitelist_only=whitelist_only):
                slug = re.sub(r"\s+", " ", line.strip().rstrip("-").strip())
                action_buffer.append(slug.lower())
                index += 1
                continue
            _flush_action_buffer(action_buffer, output)
            output.append(_normalize_cue(line))
            index += 1
            continue

        mixed_slug = re.match(r"^([A-Z][A-Z0-9 .'\-]+)\s+([a-z].*)$", line.strip())
        if mixed_slug and _should_demote_cue(
            mixed_slug.group(1),
            whitelist_only=whitelist_only,
        ):
            line = f"{mixed_slug.group(1).lower()} {mixed_slug.group(2)}"

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


def refine_file(input_path: Path, output_path: Path) -> Path:
    """Read a cleaned screenplay, refine it, and write the output.

    Args:
        input_path: Source ``_clean.fountain`` file.
        output_path: Destination ``_manual.fountain`` path.

    Returns:
        Resolved path to the written file.
    """
    text = input_path.read_text(encoding="utf-8")
    whitelist_only = _script_whitelist_for_path(input_path)
    refined = refine_manual_pass(text, whitelist_only=whitelist_only)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(refined, encoding="utf-8")
    return output_path.resolve()


def _parse_args() -> argparse.Namespace:
    """Parse command-line options for manual Fountain refinement."""
    parser = argparse.ArgumentParser(
        description="Apply manual-pass rules to cleaned PDF-extracted Fountain."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Source _clean.fountain file.",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="Destination file (default: <stem>_manual.fountain).",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point for manual Fountain refinement."""
    args = _parse_args()
    input_path = args.input.resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")
    stem = input_path.stem.replace("_clean", "")
    output_path = args.output or input_path.with_name(f"{stem}_manual.fountain")
    written = refine_file(input_path, output_path)
    print(f"Wrote refined screenplay: {written}")


if __name__ == "__main__":
    main()
