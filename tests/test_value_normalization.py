"""Unit tests for the value normalization foundation (redesign P0).

Covers number-word parsing, count extraction, ages, years (full and
apostrophe), and object-descriptor conflict detection.
"""

from value_normalization import (
    descriptor_axes,
    descriptors_conflict,
    extract_age,
    extract_count,
    extract_year,
    words_to_int,
)


def test_words_to_int_simple_and_compound() -> None:
    """Units, teens, tens, hyphenated compounds, and scales parse correctly."""
    assert words_to_int("three") == 3
    assert words_to_int("twelve") == 12
    assert words_to_int("twenty-five") == 25
    assert words_to_int("three hundred") == 300
    assert words_to_int("a dozen") == 12
    assert words_to_int("nothing here") is None


def test_extract_count_first_quantity() -> None:
    """The first quantity in a phrase is returned, word or digit."""
    assert extract_count("Three runs this month") == 3
    assert extract_count("All four.") == 4
    assert extract_count("We lose half the herd") is None
    assert extract_count("Count them. All 4.") == 4


def test_extract_age_forms() -> None:
    """Appositive, year-old, and informal ages are recognized."""
    assert extract_age("SOFIA, 12, does homework") == 12
    assert extract_age("the fastest ten-year-old in the lane") == 10
    assert extract_age("Pell slides near Eddie, barely forty") == 40
    assert extract_age("For eleven, she carries too much") == 11


def test_extract_age_rejects_out_of_range() -> None:
    """Counts that cannot be ages are rejected."""
    assert extract_age("three hundred meters of mud") is None


def test_extract_year_full_and_apostrophe() -> None:
    """Full years win; apostrophe years map across the century boundary."""
    assert extract_year("British expedition, 1987") == 1987
    assert extract_year("a tape labeled CHRISTMAS '94") == 1994
    assert extract_year("lost with her in '09") == 2009
    assert extract_year("no year here") is None


def test_descriptor_axes() -> None:
    """Material and color tokens are bucketed onto the right axis."""
    assert descriptor_axes("battered leather satchel") == {"material": "leather"}
    assert descriptor_axes("woman in a red hat") == {"color": "red"}
    assert descriptor_axes("plain bag") == {}


def test_descriptors_conflict() -> None:
    """Conflicts fire only when a shared axis disagrees."""
    assert descriptors_conflict("leather satchel", "canvas satchel") is True
    assert descriptors_conflict("brass compass", "iron compass") is True
    assert descriptors_conflict("red hat", "green hat") is True
    assert descriptors_conflict("gold data chip", "silver data chip") is True
    assert descriptors_conflict("leather satchel", "old satchel") is False
    assert descriptors_conflict("red hat", "leather hat") is False
