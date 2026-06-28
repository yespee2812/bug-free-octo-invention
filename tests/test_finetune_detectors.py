"""Regression tests for fine-tuning detectors (90% → 95% recall).

Covers mother-in-law relationship inference, possessive age phrases,
school-destination character facts, and footprint fact consistency.
"""

import pathlib
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nlp_shared import get_shared_nlp
from plot_contradiction import ContradictionEngine
from scene_dependency import SceneDependencyEngine


@pytest.fixture(scope="module")
def engines() -> tuple[SceneDependencyEngine, ContradictionEngine]:
    """Return shared dependency and contradiction engines for the module."""
    nlp = get_shared_nlp()
    return SceneDependencyEngine(nlp=nlp), ContradictionEngine(nlp=nlp)


def _detect(
    engines: tuple[SceneDependencyEngine, ContradictionEngine], text: str
) -> list:
    """Parse a screenplay string and return Tier 1 contradictions."""
    dependency_engine, contradiction_engine = engines
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    return contradiction_engine.run_tier1(store, scenes)


def _scenes(
    contradictions: list, contradiction_type: str, expected: tuple[int, int]
) -> None:
    """Assert one contradiction of a type matches the expected scene pair."""
    hits = [
        c
        for c in contradictions
        if c.contradiction_type == contradiction_type
        and {c.scene_number_a, c.scene_number_b} == set(expected)
    ]
    assert len(hits) >= 1


def test_mil_dialogue_links_diane_to_maya_as_in_law(engines) -> None:
    """MIL dialogue plus rehearsal dinner cues an in-law vs sibling conflict."""
    text = (
        "INT. APARTMENT - DAY\n\n"
        "MAYA\nYour mother-in-law will love this.\n\n"
        "INT. REHEARSAL DINNER - NIGHT\n\n"
        "DIANE\nWelcome, everyone.\n\n"
        "INT. BACKYARD - DAY\n\n"
        "Maya's sister Diane waves from the porch.\n"
    )
    found = _detect(engines, text)
    _scenes(found, "relationship_fact", (2, 3))


def test_possessive_years_old_age_conflict(engines) -> None:
    """'Nina's ... Twenty years old' resolves to the named character."""
    text = (
        "INT. POOL - DAY\n\n"
        "NINA, 22, dives in.\n\n"
        "INT. DORM - NIGHT\n\n"
        "Coach reads Nina's file. Twenty years old.\n"
    )
    found = _detect(engines, text)
    _scenes(found, "character_age", (1, 2))


def test_school_destination_character_fact(engines) -> None:
    """State school vs coast school for the same character is flagged."""
    text = (
        "INT. KITCHEN - DAY\n\n"
        "JORDAN packs for state school.\n\n"
        "INT. PORCH - NIGHT\n\n"
        "JORDAN\nI'm heading to the coast school after all.\n"
    )
    found = _detect(engines, text)
    _scenes(found, "character_fact", (1, 2))


def test_footprint_size_fact_consistency(engines) -> None:
    """A print smaller than a boot conflicts with an exact match later."""
    text = (
        "INT. STAIRS - NIGHT\n\n"
        "The print is smaller than Reed's boot.\n\n"
        "INT. LIBRARY - DAY\n\n"
        "The print matched Reed exactly.\n"
    )
    found = _detect(engines, text)
    _scenes(found, "fact_consistency", (1, 2))
