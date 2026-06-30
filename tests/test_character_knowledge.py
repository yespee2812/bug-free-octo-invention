"""Tests for character-knowledge detection (redesign phase P3.3)."""

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


def _knowledge_hits(
    engines: tuple[SceneDependencyEngine, ContradictionEngine], text: str
) -> list[tuple[int, int]]:
    """Parse a script and return character_knowledge scene pairs."""
    dependency_engine, contradiction_engine = engines
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    results = contradiction_engine.run_tier1(store, scenes)
    return [
        (hit.scene_number_a, hit.scene_number_b)
        for hit in results
        if hit.contradiction_type == "character_knowledge"
    ]


@pytest.mark.parametrize(
    "script_name, expected_pair",
    [
        ("horror_5scene_errors.fountain", (4, 5)),
        ("mystery_5scene_errors.fountain", (1, 3)),
        ("heist_5scene_errors.fountain", (2, 5)),
        ("heist_10scene_errors.fountain", (3, 9)),
        ("scifi_5scene_errors.fountain", (2, 5)),
        ("western_10scene_errors.fountain", (3, 8)),
    ],
)
def test_planted_character_knowledge_slips(
    engines: tuple[SceneDependencyEngine, ContradictionEngine],
    script_name: str,
    expected_pair: tuple[int, int],
) -> None:
    """Deterministic knowledge patterns from the planted-error corpus."""
    path = _REPO_ROOT / "tests/corpus/input" / script_name
    hits = _knowledge_hits(engines, path.read_text(encoding="utf-8"))
    assert expected_pair in hits


def test_clean_horror_starter_has_no_knowledge_conflict(
    engines: tuple[SceneDependencyEngine, ContradictionEngine],
) -> None:
    """Clean genre starters must not emit spurious character-knowledge flags."""
    path = _REPO_ROOT / "docs/genre_starter_scripts/horror_starter_5scene.fountain"
    hits = _knowledge_hits(engines, path.read_text(encoding="utf-8"))
    assert hits == []


@pytest.mark.parametrize(
    "starter_name",
    [
        "scifi_starter_5scene.fountain",
        "western_starter_10scene.fountain",
    ],
)
def test_clean_starters_have_no_knowledge_conflict(
    engines: tuple[SceneDependencyEngine, ContradictionEngine],
    starter_name: str,
) -> None:
    """Clean sci-fi and western starters must not emit knowledge false positives."""
    path = _REPO_ROOT / "docs/genre_starter_scripts" / starter_name
    hits = _knowledge_hits(engines, path.read_text(encoding="utf-8"))
    assert hits == []
