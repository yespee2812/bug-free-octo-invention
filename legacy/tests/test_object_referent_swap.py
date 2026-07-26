"""Tests for same-scene object referent swap detection (E6)."""

import pathlib
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nlp_shared import get_shared_nlp
from legacy.plot_contradiction import ContradictionEngine
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


def test_blanket_towel_swap_in_same_scene(engines) -> None:
    """A burial wrap named blanket then towel in one scene is flagged."""
    text = (
        "INT. SHIP DECK - NIGHT\n\n"
        "ROBERT'S STILL BODY IS BEING SEWN INTO A BLANKET.\n"
        "Once sewn into the TOWEL, the crew lowers him over the rail.\n"
    )
    found = _detect(engines, text)
    swaps = [c for c in found if c.contradiction_type == "object_referent_swap"]
    assert len(swaps) == 1
    assert swaps[0].scene_number_a == swaps[0].scene_number_b == 1


def test_wrapped_in_swap(engines) -> None:
    """Wrapped-in thread detects blanket vs towel."""
    text = (
        "EXT. POOL - DAY\n\n"
        "Alma wraps Sofia in a BLANKET by the deck chairs.\n"
        "Once wrapped in the TOWEL, Sofia stops shivering.\n"
    )
    found = _detect(engines, text)
    swaps = [c for c in found if c.contradiction_type == "object_referent_swap"]
    assert len(swaps) == 1


def test_no_flag_for_single_mention(engines) -> None:
    """One action-thread mention should not produce a swap flag."""
    text = (
        "INT. ROOM - DAY\n\n"
        "She wraps the child in a blanket and sits by the window.\n"
    )
    found = _detect(engines, text)
    assert not [c for c in found if c.contradiction_type == "object_referent_swap"]


def test_no_flag_for_unrelated_nouns(engines) -> None:
    """Different noun classes in the same frame should not flag."""
    text = (
        "INT. OFFICE - DAY\n\n"
        "He places the keys in an envelope on the desk.\n"
        "Once placed in the drawer, the keys are out of sight.\n"
    )
    found = _detect(engines, text)
    assert not [c for c in found if c.contradiction_type == "object_referent_swap"]


def test_drama_5scene_planted_swap(engines) -> None:
    """Planted drama corpus error in scene 3 is detected."""
    path = _REPO_ROOT / "tests" / "corpus" / "input" / "drama_5scene_errors.fountain"
    text = path.read_text(encoding="utf-8")
    found = _detect(engines, text)
    swaps = [c for c in found if c.contradiction_type == "object_referent_swap"]
    assert any(c.scene_number_a == 3 for c in swaps)
