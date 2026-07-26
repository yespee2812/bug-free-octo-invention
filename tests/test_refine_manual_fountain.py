"""Tests for script-specific manual Fountain refinement."""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.refine_manual_fountain import (
    CITIZEN_KANE_CHARACTER_CUES,
    _script_whitelist_for_path,
    refine_manual_pass,
)


def test_citizen_kane_path_selects_whitelist() -> None:
    """Citizen Kane benchmark paths enable the cast whitelist."""
    path = _REPO_ROOT / "tests/corpus/benchmark/clean_produced/fountain/04_CitizenKane_200_clean.fountain"
    assert _script_whitelist_for_path(path) == CITIZEN_KANE_CHARACTER_CUES


def test_citizen_kane_manual_pass_demotes_headline_slugs() -> None:
    """Kane whitelist-only pass demotes PDF headline cues but keeps real cast."""
    text = (
        "INT. OFFICE - DAY\n\n"
        "FRAUD AT POLLS\n"
        "Headline text here.\n\n"
        "THOMPSON\n"
        "Who is Charles Foster Kane?\n"
    )
    path = _REPO_ROOT / "04_CitizenKane_200_clean.fountain"
    refined = refine_manual_pass(
        text,
        whitelist_only=_script_whitelist_for_path(path),
    )
    assert "FRAUD AT POLLS" not in refined
    assert "THOMPSON" in refined
