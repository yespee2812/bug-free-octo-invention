"""Tests for name-consistency / name-drift detection (redesign phase P3.1)."""

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


def _name_hits(
    engines: tuple[SceneDependencyEngine, ContradictionEngine], text: str
) -> list[tuple[int, int, str, str]]:
    """Parse a script and return name_consistency scene pairs and spellings."""
    dependency_engine, contradiction_engine = engines
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    results = contradiction_engine.run_tier1(store, scenes)
    hits = [
        item
        for item in results
        if item.contradiction_type == "name_consistency"
    ]
    return [
        (
            hit.scene_number_a,
            hit.scene_number_b,
            hit.fact_a.entity,
            hit.fact_a.value,
        )
        for hit in hits
    ]


def test_action_10_catches_osei_oshea_drift(
    engines: tuple[SceneDependencyEngine, ContradictionEngine],
) -> None:
    """Osei (sc3) vs Oshea (sc7) in the action starter with errors."""
    path = _REPO_ROOT / "tests/corpus/input/action_10scene_errors.fountain"
    hits = _name_hits(engines, path.read_text(encoding="utf-8"))
    assert (3, 7, "OSEI", "OSHEA") in hits


def test_adventure_10_catches_tenzin_tensing_drift(
    engines: tuple[SceneDependencyEngine, ContradictionEngine],
) -> None:
    """Tenzin (sc2) vs Tensing (sc9) in the adventure starter with errors."""
    path = _REPO_ROOT / "tests/corpus/input/adventure_10scene_errors.fountain"
    hits = _name_hits(engines, path.read_text(encoding="utf-8"))
    assert (2, 9, "TENZIN", "TENSING") in hits


def test_clean_action_starter_has_no_name_drift(
    engines: tuple[SceneDependencyEngine, ContradictionEngine],
) -> None:
    """Clean genre starters must not emit spurious name-drift flags."""
    path = _REPO_ROOT / "docs/genre_starter_scripts/action_starter_10scene.fountain"
    hits = _name_hits(engines, path.read_text(encoding="utf-8"))
    assert hits == []
