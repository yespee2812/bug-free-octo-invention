"""Tests for the numeric_count and date_year detectors (redesign phase P1).

Covers count noun selection / singularization, the appositive-comma guard that
keeps person ages out of counts, identifier noun-before-number forms, and the
"exactly two close years" date-year rule with its guards.
"""

import pathlib
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nlp_shared import get_shared_nlp
from plot_contradiction import ContradictionEngine, _singularize
from scene_dependency import SceneDependencyEngine


@pytest.fixture(scope="module")
def engines() -> tuple[SceneDependencyEngine, ContradictionEngine]:
    """Return shared dependency and contradiction engines for the module."""
    nlp = get_shared_nlp()
    return SceneDependencyEngine(nlp=nlp), ContradictionEngine(nlp=nlp)


def _types(
    engines: tuple[SceneDependencyEngine, ContradictionEngine],
    text: str,
    wanted: str,
) -> list:
    """Return Tier 1 contradictions of a given type for a screenplay string."""
    dependency_engine, contradiction_engine = engines
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    found = contradiction_engine.run_tier1(store, scenes)
    return [c for c in found if c.contradiction_type == wanted]


@pytest.mark.parametrize(
    "word, expected",
    [("runs", "run"), ("families", "family"), ("years", "year"),
     ("second", "second"), ("glass", "glass"), ("rules", "rule")],
)
def test_singularize(word: str, expected: str) -> None:
    """Plural counts collapse to a shared singular key."""
    assert _singularize(word) == expected


def test_numeric_count_conflict(engines) -> None:
    """The same counted noun with two quantities is flagged once."""
    text = (
        "INT. OFFICE - DAY\n\n"
        "EDDIE\nThree runs this month, clean.\n\n"
        "INT. OFFICE - NIGHT\n\n"
        "PELL\nFour runs this month and no heat.\n"
    )
    counts = _types(engines, text, "numeric_count")
    assert len(counts) == 1
    assert {counts[0].scene_number_a, counts[0].scene_number_b} == {1, 2}


def test_numeric_count_room_identifier(engines) -> None:
    """Noun-before-number identifiers ("Room 514") are counted."""
    text = (
        "INT. HOTEL - NIGHT\n\n"
        "She slips into Room 514 down the hall.\n"
        "GUEST\nQuiet floor.\n\n"
        "INT. HOTEL - LATER\n\n"
        "He knocks on room 415 instead.\n"
        "GUEST\nWrong door.\n"
    )
    counts = _types(engines, text, "numeric_count")
    assert len(counts) == 1


def test_appositive_age_is_not_a_count(engines) -> None:
    """'DAWSON, 45' / 'Dawson, fifty' is an age, never a numeric_count."""
    text = (
        "EXT. RANCH - DAY\n\n"
        "WILL DAWSON, 45, rides the fence line.\n"
        "DAWSON\nLong day.\n\n"
        "EXT. RANCH - DUSK\n\n"
        "Dawson, fifty now and tired, climbs down.\n"
        "DAWSON\nLonger year.\n"
    )
    assert not _types(engines, text, "numeric_count")
    assert len(_types(engines, text, "character_age")) == 1


def test_clock_digits_do_not_leak_as_counts(engines) -> None:
    """Clock times map to CLOCK hour facts; minute digits must not leak."""
    dependency_engine, contradiction_engine = engines
    text = (
        "INT. ROOM - NIGHT\n\n"
        "The watch reads 11:58 PM.\n"
        "LENA\nAlmost time.\n"
    )
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    clock_facts = [
        fact
        for fact in store.get_facts_by_type("numeric_count")
        if fact.entity == "CLOCK"
    ]
    stray = [
        fact
        for fact in store.get_facts_by_type("numeric_count")
        if fact.entity != "CLOCK"
    ]
    assert len(clock_facts) == 1
    assert clock_facts[0].value == "11"
    assert not any(fact.value == "58" for fact in stray)


def test_date_year_conflict(engines) -> None:
    """Two close-but-different years are flagged as a date_year contradiction."""
    text = (
        "INT. ARCHIVE - DAY\n\n"
        "A tin box reads M. OKAFOR, 1987.\n"
        "JUNE\nHe was here.\n\n"
        "INT. ARCHIVE - NIGHT\n\n"
        "The crate bears British expedition labels, 1985.\n"
        "JUNE\nThat does not add up.\n"
    )
    years = _types(engines, text, "date_year")
    assert len(years) == 1
    assert {years[0].scene_number_a, years[0].scene_number_b} == {1, 2}


def test_date_year_apostrophe_form(engines) -> None:
    """Apostrophe years ('94 vs '93) normalize and conflict."""
    text = (
        "INT. BASEMENT - NIGHT\n\n"
        "A tape labeled CHRISTMAS '94 plays.\n"
        "LEAH\nThat is Dad.\n\n"
        "INT. BASEMENT - LATER\n\n"
        "She checks the label again: CHRISTMAS '93.\n"
        "LEAH\nThat is wrong.\n"
    )
    assert len(_types(engines, text, "date_year")) == 1


def test_three_years_not_flagged(engines) -> None:
    """An intentional multi-period story (3+ distinct years) is not flagged."""
    text = (
        "INT. ROOM - 1990\n\nA child plays.\n"
        "MAN\nThen.\n\n"
        "INT. ROOM - 2000\n\nThe child is grown.\n"
        "MAN\nLater.\n\n"
        "INT. ROOM - 2010\n\nAn old man sits.\n"
        "MAN\nNow.\n"
    )
    assert not _types(engines, text, "date_year")


def test_large_year_gap_not_flagged(engines) -> None:
    """Years far apart read as a deliberate time jump, not a slip."""
    text = (
        "INT. HALL - 1960\n\nA wedding.\n"
        "MAN\nWe begin.\n\n"
        "INT. HALL - 2005\n\nA funeral.\n"
        "MAN\nWe end.\n"
    )
    assert not _types(engines, text, "date_year")


def test_clock_time_conflict(engines) -> None:
    """A clock reading past hour X conflicts with 'not even X yet'."""
    text = (
        "INT. GARAGE - NIGHT\n\n"
        "She checks her watch — 11:58 PM.\n"
        "LENA\nReady.\n\n"
        "INT. SUV - MOVING - NIGHT\n\n"
        "LENA\nIt's not even eleven yet.\n"
    )
    counts = _types(engines, text, "numeric_count")
    assert len(counts) == 1
    assert {counts[0].scene_number_a, counts[0].scene_number_b} == {1, 2}
