"""Tests for location-continuity detection (redesign phase P3.2)."""

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


def _location_hits(
    engines: tuple[SceneDependencyEngine, ContradictionEngine], text: str
) -> list[tuple[int, int]]:
    """Parse a script and return location_continuity scene pairs."""
    dependency_engine, contradiction_engine = engines
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    results = contradiction_engine.run_tier1(store, scenes)
    return [
        (hit.scene_number_a, hit.scene_number_b)
        for hit in results
        if hit.contradiction_type == "location_continuity"
    ]


@pytest.mark.parametrize(
    "script_name, expected_pair",
    [
        ("supernatural_5scene_errors.fountain", (2, 5)),
        ("supernatural_10scene_errors.fountain", (4, 7)),
        ("western_5scene_errors.fountain", (2, 3)),
        ("western_10scene_errors.fountain", (3, 4)),
    ],
)
def test_planted_location_cardinal_conflicts(
    engines: tuple[SceneDependencyEngine, ContradictionEngine],
    script_name: str,
    expected_pair: tuple[int, int],
) -> None:
    """Planted east/west bedroom and north/south land slips are caught."""
    path = _REPO_ROOT / "tests/corpus/input" / script_name
    hits = _location_hits(engines, path.read_text(encoding="utf-8"))
    assert expected_pair in hits


def test_clean_supernatural_starter_has_no_location_conflict(
    engines: tuple[SceneDependencyEngine, ContradictionEngine],
) -> None:
    """Clean genre starters must not emit spurious location-cardinal flags."""
    path = (
        _REPO_ROOT
        / "docs/genre_starter_scripts/supernatural_starter_10scene.fountain"
    )
    hits = _location_hits(engines, path.read_text(encoding="utf-8"))
    assert hits == []
