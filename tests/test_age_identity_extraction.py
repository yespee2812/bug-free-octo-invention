"""Tests for the age and object-identity detectors (redesign phase P1).

Covers the strict appositive age head-parser (which must reject pronouns such
as "this one"), end-to-end age-conflict detection with name resolution, and
object-identity descriptor conflicts including the no-double-count guarantee.
"""

import pathlib
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nlp_shared import get_shared_nlp
from plot_contradiction import ContradictionEngine, _parse_head_age
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


@pytest.mark.parametrize(
    "clause, expected",
    [
        ("12, does homework", 12),
        ("twenty, settles in", 20),
        ("barely twenty-five, rides hard", 25),
        ("50s, steers by radar", 50),
        ("barely forty, hunched", 40),
        ("fifty now and tired", 50),
        ("don't rewind this one", None),
        ("you died on a Tuesday", None),
        ("and the walls keep moving", None),
    ],
)
def test_parse_head_age(clause: str, expected: int | None) -> None:
    """Age must be the clause head; trailing pronouns are not ages."""
    assert _parse_head_age(clause) == expected


def test_age_conflict_with_name_resolution(engines) -> None:
    """An establishing age and a later restated age resolve to one character."""
    text = (
        "INT. DOCK - DAY\n\n"
        "CAPTAIN TOM HALE, 28, checks the lines.\n"
        "HALE\nWe move at dawn.\n\n"
        "INT. DOCK - NIGHT\n\n"
        "Hale, thirty-one, hauls the last crate.\n"
        "HALE\nAlmost there.\n"
    )
    found = _detect(engines, text)
    ages = [c for c in found if c.contradiction_type == "character_age"]
    assert len(ages) == 1
    assert {ages[0].scene_number_a, ages[0].scene_number_b} == {1, 2}


def test_pronoun_one_is_not_an_age(engines) -> None:
    """'this one' must not register as age 1 and create a contradiction."""
    text = (
        "INT. ROOM - DAY\n\n"
        "LEAH PARK, 30s, clears boxes.\n"
        "LEAH\nLast thing I need is home movies.\n\n"
        "INT. ROOM - NIGHT\n\n"
        "Leah plays a tape.\n"
        "LEAH\nLeah, don't rewind this one.\n"
    )
    found = _detect(engines, text)
    assert not [c for c in found if c.contradiction_type == "character_age"]


def test_object_identity_material_conflict(engines) -> None:
    """A prop whose material changes between scenes is flagged once."""
    text = (
        "INT. STUDY - DAY\n\n"
        "MARA grips a battered LEATHER SATCHEL.\n"
        "MARA\nEverything I own.\n\n"
        "INT. STUDY - NIGHT\n\n"
        "She drops the canvas satchel on the desk.\n"
        "MARA\nStill heavy.\n"
    )
    found = _detect(engines, text)
    identity = [c for c in found if c.contradiction_type == "object_identity"]
    assert len(identity) == 1
    assert {identity[0].scene_number_a, identity[0].scene_number_b} == {1, 2}


def test_object_identity_no_double_count_on_recurring_descriptor(engines) -> None:
    """A baseline descriptor repeated before the conflict yields one report."""
    text = (
        "INT. DOCK - DAY\n\n"
        "MIRA ties a BRASS COMPASS to her belt.\n"
        "MIRA\nReady.\n\n"
        "INT. FERRY - DAY\n\n"
        "Mira's BRASS COMPASS spins wildly.\n"
        "MIRA\nNot north.\n\n"
        "EXT. SHORE - DUSK\n\n"
        "Mira steps off, iron compass steady now.\n"
        "MIRA\nWe made it.\n"
    )
    found = _detect(engines, text)
    identity = [c for c in found if c.contradiction_type == "object_identity"]
    assert len(identity) == 1
    assert identity[0].scene_number_a == 1
    assert identity[0].scene_number_b == 3
