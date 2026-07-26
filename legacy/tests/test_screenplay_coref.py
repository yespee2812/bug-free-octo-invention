"""Tests for lightweight screenplay coreference (no ML)."""

import pathlib
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from legacy.entity_canonicalization import EntityRegistry
from nlp_shared import get_shared_nlp
from legacy.plot_contradiction import ContradictionEngine
from scene_dependency import SceneDependencyEngine
from legacy.screenplay_coref import (
    RoleRegistry,
    SceneMentionTracker,
    build_role_registry,
    index_roles_from_line,
    register_characters_from_scenes,
)


@pytest.fixture(scope="module")
def engines() -> tuple[SceneDependencyEngine, ContradictionEngine]:
    """Return shared dependency and contradiction engines for the module."""
    nlp = get_shared_nlp()
    return SceneDependencyEngine(nlp=nlp), ContradictionEngine(nlp=nlp)


def test_role_registry_links_gardener_to_tomas() -> None:
    """Intro line 'TOMAS, 22, gardener' maps the role to Tomas, not Quinn."""
    line = (
        "Quinn interviews TOMAS, 22, gardener, mud on his boots. "
        "A silver locket peeks from his shirt."
    )
    registry = EntityRegistry()
    registry.register("TOMAS")
    registry.register("DETECTIVE MAYA QUINN")
    roles = RoleRegistry()
    index_roles_from_line(line, registry, roles)
    assert roles.resolve("gardener") == "TOMAS"


def test_pronoun_subject_skips_current_speaker() -> None:
    """'she' in Alma's line resolves to Sofia, not Alma."""
    tracker = SceneMentionTracker(scene_characters={"ALMA", "SOFIA", "RICHARD"})
    tracker.note_action_mentions(
        "Richard watches Sofia swim laps from the bleachers. Coach ALMA approaches.",
        EntityRegistry.from_cues(["ALMA", "SOFIA", "RICHARD"]),
    )
    tracker.set_speaker("ALMA")
    subject = tracker.resolve_subject(
        "She's the fastest ten-year-old in the lane when she's not looking over her shoulder."
    )
    assert subject == "SOFIA"


def test_year_old_dialogue_links_to_sofia(engines) -> None:
    """'ten-year-old' in dialogue resolves to Sofia via scene mentions."""
    text = (
        "EXT. POOL - DAY\n\n"
        "Richard watches Sofia swim. Coach ALMA joins him.\n"
        "ALMA\n"
        "She's the fastest ten-year-old in the lane.\n"
    )
    dependency_engine, contradiction_engine = engines
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    ages = [fact for fact in store.get_all_facts() if fact.fact_type == "age"]
    assert any(fact.entity == "SOFIA" and fact.value == "10" for fact in ages)


def test_for_eleven_mid_dialogue(engines) -> None:
    """'For eleven, she…' mid-line links to Sofia, not the speaker."""
    text = (
        "EXT. POOL - DAY\n\n"
        "Richard watches Sofia swim. Coach ALMA joins him.\n"
        "ALMA\n"
        "She flinches near the lane line. For eleven, she carries too much.\n"
    )
    dependency_engine, contradiction_engine = engines
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    ages = {fact.entity: fact.value for fact in store.get_all_facts() if fact.fact_type == "age"}
    assert ages.get("SOFIA") == "11"


def test_first_person_age_from_speaker(engines) -> None:
    """'when I was twelve' attributes the age to the dialogue speaker."""
    text = (
        "INT. BASEMENT - NIGHT\n\n"
        "LEAH\n"
        "That wasn't here when I was twelve.\n\n"
        "INT. BASEMENT - LATER\n\n"
        "LEAH\n"
        "Not since I was eight. Did I?\n"
    )
    dependency_engine, contradiction_engine = engines
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    found = contradiction_engine.run_tier1(store, scenes)
    ages = [c for c in found if c.contradiction_type == "character_age"]
    assert len(ages) == 1


def test_payment_fare_material_conflict(engines) -> None:
    """Silver thimble vs brass coin surfaces as a payment material conflict."""
    text = (
        "INT. FERRY - DAY\n\n"
        "A STRANGER pays with a silver thimble.\n"
        "STRANGER\nFare paid.\n\n"
        "INT. FERRY - NIGHT\n\n"
        "MIRA\nYou paid with a brass coin, not a true fare.\n"
    )
    dependency_engine, contradiction_engine = engines
    scenes = dependency_engine.parse_fountain_text(text)
    store = contradiction_engine.extract_facts(scenes)
    found = contradiction_engine.run_tier1(store, scenes)
    identity = [c for c in found if c.contradiction_type == "object_identity"]
    assert any("payment_fare" in c.explanation.lower() for c in identity)


def test_register_characters_merges_cue_and_intro() -> None:
    """Scene parser characters merge cue names with action intros."""
    registry = EntityRegistry()
    registry.register("HALE")

    class FakeScene:
        characters = ["HALE", "SERGEANT TOM HALE"]

    register_characters_from_scenes(registry, [FakeScene()])  # type: ignore[list-item]
    assert registry.resolve("Hale") == "HALE"
