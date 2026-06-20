"""Tests for shared spaCy loading (D7) and sub-location headings (D8)."""

from plot_contradiction import ContradictionEngine
from nlp_shared import get_shared_nlp
from scene_dependency import (
    SceneDependencyEngine,
    _extract_agentive_subject_characters,
    _extract_locations_from_heading,
    _parse_action_docs,
    _person_entity_keys,
)

SUB_LOCATION_SCRIPT = """INT. HOUSE - KITCHEN - DAY

A kettle whistles.

INT. HOUSE - BEDROOM - NIGHT

The house is quiet.
"""


def test_engines_share_injected_nlp_instance() -> None:
    """Both engines use the same pipeline when one is injected (D7)."""
    nlp = get_shared_nlp()
    dep_engine = SceneDependencyEngine(nlp=nlp)
    con_engine = ContradictionEngine(nlp=nlp)
    assert dep_engine.nlp is con_engine.nlp is nlp


def test_pre_parsed_docs_serve_ner_and_agentive_detection() -> None:
    """Shared docs from _parse_action_docs feed both D3/D7 consumers (D7)."""
    nlp = get_shared_nlp()
    action_text = "KORREK whispers to the shadows."
    raw_doc, title_doc = _parse_action_docs(nlp, action_text)
    _person_entity_keys(raw_doc, title_doc)
    chars = _extract_agentive_subject_characters(
        action_text, raw_doc, title_doc, {}, set()
    )
    assert "KORREK" in chars


def test_sub_locations_are_distinct_per_scene() -> None:
    """Kitchen and bedroom scenes share HOUSE but not each other's sub-key."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(SUB_LOCATION_SCRIPT)
    assert scenes[0].locations == ["HOUSE", "HOUSE KITCHEN"]
    assert scenes[1].locations == ["HOUSE", "HOUSE BEDROOM"]
    assert "HOUSE KITCHEN" not in scenes[1].locations


def test_house_primary_location_still_links_scenes() -> None:
    """Broad HOUSE key still creates location continuity between sub-scenes."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(SUB_LOCATION_SCRIPT)
    engine.build_graph(scenes, include_fact_edges=False, include_causal_edges=False)
    assert engine.graph.has_edge("scene_001", "scene_002")


def test_bedroom_scene_lacks_kitchen_sub_location() -> None:
    """Sub-location keys stay scene-specific (D8)."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(SUB_LOCATION_SCRIPT)
    assert "HOUSE KITCHEN" in scenes[0].locations
    assert "HOUSE KITCHEN" not in scenes[1].locations


def test_single_part_heading_strips_time_of_day() -> None:
    """INT. MOTEL ROOM - DAY yields one location key without DAY."""
    assert _extract_locations_from_heading("INT. MOTEL ROOM - DAY") == ["MOTEL ROOM"]
