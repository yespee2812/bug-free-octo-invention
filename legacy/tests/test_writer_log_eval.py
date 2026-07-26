"""Tests for writer error-log to engine report comparison."""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nlp_shared import get_shared_nlp
from legacy.plot_contradiction import ContradictionEngine, INPUT_PROFILE_STANDARD
from scene_dependency import SceneDependencyEngine
from legacy.writer_log_eval import compare_writer_log_to_results, map_writer_category


def test_map_writer_category_death() -> None:
    """Death/alive writer categories map to character_alive_status."""
    engine_type, mappable = map_writer_category("Character dead then alive")
    assert engine_type == "character_alive_status"
    assert mappable


def test_compare_writer_log_matches_numeric_count() -> None:
    """A planted numeric_count in the log matches engine output on a mini script."""
    text = (
        "INT. OFFICE - DAY\n\n"
        "EDDIE\nThree runs this month, clean.\n\n"
        "INT. OFFICE - NIGHT\n\n"
        "PELL\nFour runs this month and no heat.\n"
    )
    log_data = {
        "writer_name": "Test Writer",
        "script_title": "Mini Crime",
        "planted_errors": [
            {
                "error_number": 1,
                "category": "Numeric count / runs per month",
                "establishing_scene": 1,
                "contradicting_scene": 2,
                "establishing_moment": "Three runs",
                "contradicting_moment": "Four runs",
            }
        ],
    }
    dependency_engine = SceneDependencyEngine(nlp=get_shared_nlp())
    contradiction_engine = ContradictionEngine(
        nlp=get_shared_nlp(),
        input_profile=INPUT_PROFILE_STANDARD,
    )
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    hits = [
        item
        for item in contradiction_engine.run_tier1(store, scenes)
        if item.contradiction_type
    ]
    results = {
        "contradictions": {
            "items": [
                {
                    "scenes_involved": [hit.scene_number_a, hit.scene_number_b],
                    "contradiction_type": hit.contradiction_type,
                    "explanation": hit.explanation,
                }
                for hit in hits
            ]
        }
    }
    comparison = compare_writer_log_to_results(log_data, results)
    assert len(comparison.matched) == 1
    assert not comparison.missed
