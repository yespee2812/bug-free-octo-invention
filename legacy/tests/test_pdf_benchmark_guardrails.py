"""Tests for pdf_benchmark guardrails on Hollywood PDF-derived scripts."""

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


def _tier1_hits(text: str, input_profile: str, contradiction_type: str) -> list:
    """Return Tier 1 contradictions of one type for a screenplay string."""
    dependency_engine = SceneDependencyEngine(nlp=get_shared_nlp())
    contradiction_engine = ContradictionEngine(
        nlp=get_shared_nlp(),
        input_profile=input_profile,
    )
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    found = contradiction_engine.run_tier1(store, scenes)
    return [item for item in found if item.contradiction_type == contradiction_type]


def test_pdf_benchmark_skips_natural_aging() -> None:
    """Later-scene older age is not flagged in pdf_benchmark (biographical scripts)."""
    text = (
        "INT. OFFICE - DAY\n\n"
        "ALFRED DRIVES, 50, opens the garage.\n\n"
        "INT. MANOR - NIGHT\n\n"
        "Alfred, 62, pours tea.\n"
    )
    hits = _tier1_hits(text, INPUT_PROFILE_PDF_BENCHMARK, "character_age")
    assert not hits


def test_pdf_benchmark_keeps_impossible_younger_age() -> None:
    """Getting younger between scenes still flags in pdf_benchmark mode."""
    text = (
        "INT. ROOM - DAY\n\n"
        "NINA VASQUEZ, 22, stretches.\n\n"
        "INT. GYM - NIGHT\n\n"
        "Nina, twenty, ties her shoes.\n"
    )
    hits = _tier1_hits(text, INPUT_PROFILE_PDF_BENCHMARK, "character_age")
    assert len(hits) == 1


def test_standard_still_flags_later_older_age() -> None:
    """Writer corpus profile still reports any age mismatch."""
    text = (
        "INT. DOCK - DAY\n\n"
        "CAPTAIN TOM HALE, 28, checks the lines.\n\n"
        "INT. DOCK - NIGHT\n\n"
        "Hale, thirty-one, hauls the last crate.\n"
    )
    hits = _tier1_hits(text, INPUT_PROFILE_STANDARD, "character_age")
    assert len(hits) == 1


def test_pdf_benchmark_skips_pov_ownership_chain() -> None:
    """Camera POV fragments must not produce object_ownership flags."""
    text = (
        "INT. KITCHEN - DAY\n\n"
        "Lester's POV on the counter.\n\n"
        "INT. BEDROOM - NIGHT\n\n"
        "Carolyn has POV on the mirror.\n"
    )
    hits = _tier1_hits(text, INPUT_PROFILE_PDF_BENCHMARK, "object_ownership")
    assert not hits


def test_pdf_benchmark_skips_hyphen_name_drift() -> None:
    """PDF line-break hyphen cues (GORDON-) must not flag against GORDON."""
    text = (
        "INT. OFFICE - DAY\n\n"
        "GORDON\nWe need answers.\n\n"
        "INT. ROOF - NIGHT\n\n"
        "GORDON-\nThe signal is gone.\n"
    )
    hits = _tier1_hits(text, INPUT_PROFILE_PDF_BENCHMARK, "name_consistency")
    assert not hits
