"""Value normalization for the contradiction engine.

Foundation layer (redesign phase P0): converts the messy textual values that
carry contradictions into typed, comparable forms so detection compares values,
not strings. Covers the highest-volume planted-error families:

* counts / quantities  ("three" vs "four", "All four")
* ages                 ("SOFIA, 12", "ten-year-old", "barely forty")
* years / dates        ("1987", "CHRISTMAS '94" -> 1994)
* object descriptors   ("leather" vs "canvas", "red" vs "green")

Dependency-free and fully typed for fast unit testing.
"""

from __future__ import annotations

import re

_UNITS: dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_TENS: dict[str, int] = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}
_SCALES: dict[str, int] = {"hundred": 100, "thousand": 1000, "million": 1_000_000}
_NUMBER_WORDS: frozenset[str] = frozenset(
    set(_UNITS) | set(_TENS) | set(_SCALES) | {"dozen"}
)

# Descriptor vocab grouped by axis. Tokens that name a metal double as the
# material of a prop (a "gold" chip vs a "silver" chip), so they live on the
# material axis rather than colour to keep object-identity comparisons stable.
_MATERIAL_TOKENS: frozenset[str] = frozenset(
    {
        "leather", "canvas", "cloth", "fabric", "wood", "wooden", "iron",
        "steel", "brass", "bronze", "copper", "gold", "golden", "silver",
        "plastic", "glass", "stone", "paper", "rubber", "tin", "aluminum",
        "aluminium", "ceramic", "velvet", "silk", "wool", "denim", "wax",
    }
)
_COLOR_TOKENS: frozenset[str] = frozenset(
    {
        "red", "orange", "yellow", "green", "blue", "purple", "violet",
        "pink", "black", "white", "gray", "grey", "brown", "tan", "beige",
        "maroon", "navy", "teal", "crimson", "scarlet", "amber",
    }
)
_DESCRIPTOR_AXES: dict[str, str] = {
    **{token: "material" for token in _MATERIAL_TOKENS},
    **{token: "color" for token in _COLOR_TOKENS},
}

_TOKEN_RE = re.compile(r"[A-Za-z]+")
_DIGIT_RE = re.compile(r"\d+")
_FOUR_DIGIT_YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
_APOSTROPHE_YEAR_RE = re.compile(r"['\u2019](\d{2})\b")
_AGE_YEAR_OLD_RE = re.compile(
    r"\b(\d{1,3}|[a-z\-]+)[\s\-]year[\s\-]old", re.IGNORECASE
)
_APPOSITIVE_AGE_RE = re.compile(r",\s*(\d{1,3})\b")


def words_to_int(text: str) -> int | None:
    """Convert a run of number words (and/or digits) to an int.

    Handles hyphenated compounds ("twenty-five"), scales ("three hundred"),
    and the informal "dozen" (=12). Returns ``None`` when no number is present.

    Args:
        text: A phrase such as "twenty-five" or "three hundred".

    Returns:
        The integer value, or ``None``.
    """
    raw_tokens = re.split(r"[\s\-]+", text.strip().lower())
    tokens = [token for token in raw_tokens if token]
    if not tokens:
        return None

    result = 0
    current = 0
    found = False
    for token in tokens:
        if token.isdigit():
            current += int(token)
            found = True
        elif token in _UNITS:
            current += _UNITS[token]
            found = True
        elif token in _TENS:
            current += _TENS[token]
            found = True
        elif token == "dozen":
            current = (current or 1) * 12
            found = True
        elif token == "hundred":
            current = (current or 1) * 100
            found = True
        elif token in _SCALES:
            current = (current or 1) * _SCALES[token]
            result += current
            current = 0
            found = True
        elif found:
            break
        else:
            continue
    if not found:
        return None
    return result + current


def extract_count(text: str) -> int | None:
    """Return the first quantity (digit or number-word run) in ``text``.

    Args:
        text: Free text such as "Three runs this month" or "All four".

    Returns:
        The integer quantity, or ``None`` when none is found.
    """
    lowered = text.lower()
    tokens = re.findall(r"\d+|[a-z]+", lowered)
    run: list[str] = []
    run_start_seen = False
    for token in tokens:
        if token.isdigit() or token in _NUMBER_WORDS:
            run.append(token)
            run_start_seen = True
        elif run_start_seen:
            break
    if not run:
        return None
    return words_to_int(" ".join(run))


def extract_age(text: str) -> int | None:
    """Return a person's age stated in ``text``, or ``None``.

    Recognizes appositive ages ("SOFIA, 12"), "<n>-year-old" / "<word>-year-old",
    and informal "barely forty" / "fifty now" forms. Values outside 1..120 are
    rejected to avoid mistaking arbitrary counts for ages.

    Args:
        text: A line that may state an age.

    Returns:
        The age as an int within 1..120, or ``None``.
    """
    year_old = _AGE_YEAR_OLD_RE.search(text)
    if year_old:
        value = (
            int(year_old.group(1))
            if year_old.group(1).isdigit()
            else words_to_int(year_old.group(1))
        )
        if value is not None and 1 <= value <= 120:
            return value

    appositive = _APPOSITIVE_AGE_RE.search(text)
    if appositive:
        value = int(appositive.group(1))
        if 1 <= value <= 120:
            return value

    candidate = extract_count(text)
    if candidate is not None and 1 <= candidate <= 120:
        return candidate
    return None


def extract_year(text: str) -> int | None:
    """Return the first full or apostrophe year in ``text``, or ``None``.

    Four-digit years (1500-2099) win over apostrophe years. Two-digit
    apostrophe years map to 2000+yy when ``yy <= 30`` else 1900+yy
    (so "'94" -> 1994 and "'09" -> 2009).

    Args:
        text: A line such as "CHRISTMAS '94" or "expedition, 1987".

    Returns:
        The four-digit year, or ``None``.
    """
    full = _FOUR_DIGIT_YEAR_RE.search(text)
    if full:
        return int(full.group(1))
    apostrophe = _APOSTROPHE_YEAR_RE.search(text)
    if apostrophe:
        two_digit = int(apostrophe.group(1))
        return 2000 + two_digit if two_digit <= 30 else 1900 + two_digit
    return None


def extract_all_years(text: str) -> list[int]:
    """Return every full or apostrophe year in ``text`` in order of appearance.

    Unlike :func:`extract_year` (first match only), this collects all year
    mentions on a line so script-level year-conflict reasoning can see them.

    Args:
        text: A line such as "From 1987 to 1985" or "CHRISTMAS '94".

    Returns:
        A list of four-digit years (possibly empty).
    """
    years: list[int] = []
    for match in _FOUR_DIGIT_YEAR_RE.finditer(text):
        years.append(int(match.group(1)))
    for match in _APOSTROPHE_YEAR_RE.finditer(text):
        two_digit = int(match.group(1))
        years.append(2000 + two_digit if two_digit <= 30 else 1900 + two_digit)
    return years


def descriptor_axis(token: str) -> str | None:
    """Return the descriptor axis ("material"/"color") for a single token.

    Args:
        token: A lowercase-or-any-case word such as "leather" or "Red".

    Returns:
        The axis name, or ``None`` when the token is not a known descriptor.
    """
    return _DESCRIPTOR_AXES.get(token.lower())


def descriptor_axes(text: str) -> dict[str, str]:
    """Return the first recognized descriptor token per axis in ``text``.

    Args:
        text: An object phrase such as "battered leather satchel".

    Returns:
        A mapping like ``{"material": "leather"}`` (axes: "material", "color").
    """
    axes: dict[str, str] = {}
    for token in _TOKEN_RE.findall(text.lower()):
        axis = _DESCRIPTOR_AXES.get(token)
        if axis is not None and axis not in axes:
            axes[axis] = token
    return axes


def descriptors_conflict(text_a: str, text_b: str) -> bool:
    """Return True when two descriptions disagree on a shared descriptor axis.

    "leather satchel" vs "canvas satchel" -> True (material differs);
    "leather satchel" vs "old satchel" -> False (no shared axis).

    Args:
        text_a: First object description.
        text_b: Second object description.

    Returns:
        ``True`` if any shared axis carries different tokens.
    """
    axes_a = descriptor_axes(text_a)
    axes_b = descriptor_axes(text_b)
    for axis, token_a in axes_a.items():
        token_b = axes_b.get(axis)
        if token_b is not None and token_a != token_b:
            return True
    return False
