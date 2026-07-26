"""Tests for pdf_benchmark numeric_count guardrails on PDF-derived scripts."""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nlp_shared import get_shared_nlp
from legacy.plot_contradiction import (
    ContradictionEngine,
    INPUT_PROFILE_PDF_BENCHMARK,
    INPUT_PROFILE_STANDARD,
)
from scene_dependency import SceneDependencyEngine


def _numeric_count_hits(
    text: str,
    input_profile: str,
) -> list:
    """Return numeric_count contradictions for a screenplay string."""
    dependency_engine = SceneDependencyEngine(nlp=get_shared_nlp())
    contradiction_engine = ContradictionEngine(
        nlp=get_shared_nlp(),
        input_profile=input_profile,
    )
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    found = contradiction_engine.run_tier1(store, scenes)
    return [item for item in found if item.contradiction_type == "numeric_count"]


def test_pdf_benchmark_skips_generic_prose_count_noise() -> None:
    """Merged PDF action must not produce spurious generic numeric_count chains."""
    text = (
        "INT. GYM - DAY\n\n"
        "One group waits by the door.\n\n"
        "INT. GYM - NIGHT\n\n"
        "Two groups fill the hall.\n"
    )
    standard_hits = _numeric_count_hits(text, INPUT_PROFILE_STANDARD)
    benchmark_hits = _numeric_count_hits(text, INPUT_PROFILE_PDF_BENCHMARK)
    assert len(standard_hits) == 1
    assert not benchmark_hits


def test_pdf_benchmark_keeps_pattern_hostage_count() -> None:
    """Curated count patterns still fire in pdf_benchmark mode."""
    text = (
        "INT. BANK - DAY\n\n"
        "Three hostages circled near the vault.\n\n"
        "INT. BANK - NIGHT\n\n"
        "All four hostages are gone.\n"
    )
    hits = _numeric_count_hits(text, INPUT_PROFILE_PDF_BENCHMARK)
    assert len(hits) == 1


def test_standard_still_detects_family_count_via_pattern() -> None:
    """Family counts use an explicit phrase pattern in standard mode."""
    text = (
        "INT. TOWN - DAY\n\n"
        "Three families left on the block.\n\n"
        "INT. TOWN - NIGHT\n\n"
        "Four families now.\n"
    )
    hits = _numeric_count_hits(text, INPUT_PROFILE_STANDARD)
    assert len(hits) == 1


def test_standard_run_conflict_unchanged() -> None:
    """Standard profile still flags explicit run-count contradictions."""
    text = (
        "INT. OFFICE - DAY\n\n"
        "EDDIE\nThree runs this month, clean.\n\n"
        "INT. OFFICE - NIGHT\n\n"
        "PELL\nFour runs this month and no heat.\n"
    )
    hits = _numeric_count_hits(text, INPUT_PROFILE_STANDARD)
    assert len(hits) == 1
