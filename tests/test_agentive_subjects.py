"""Tests for grammatical-role (agentive-subject) character detection.

This is the Signal 3 fix for Caveat D3: ALL-CAPS is where spaCy NER is weakest,
so a cue-less, title-less invented name is missed or mis-typed as a prop. Signal
3 recovers it by treating the caps subject of an animate-only verb (communication,
expression, gesture, cognition) as a character, while keeping action props that
take motion/machine verbs ("the DELOREAN races", "the PHONE rings") out. These
tests pin both the recall win and the precision guards.
"""

from scene_dependency import (
    SceneDependencyEngine,
    _extract_agentive_subject_characters,
    _parse_action_docs,
)

_engine = SceneDependencyEngine()


def _first_scene(script: str):
    """Parse a Fountain script and return its first scene block."""
    return _engine.parse_fountain_text(script)[0]


CUE_LESS_AGENT_SCRIPT = """INT. CAVE - NIGHT

KORREK whispers to the shadows. The DELOREAN races past. The PHONE rings.
"""


def test_cue_less_agent_becomes_character_not_prop() -> None:
    """A caps name that whispers is a character, not an object."""
    scene = _first_scene(CUE_LESS_AGENT_SCRIPT)
    assert "KORREK" in scene.characters
    assert "KORREK" not in scene.objects


def test_motion_verb_subject_is_not_promoted() -> None:
    """A prop that 'races' must not be misread as a character."""
    scene = _first_scene(CUE_LESS_AGENT_SCRIPT)
    assert "DELOREAN" not in scene.characters


def test_machine_verb_subject_stays_a_prop() -> None:
    """A prop that 'rings' stays an object and is not a character."""
    scene = _first_scene(CUE_LESS_AGENT_SCRIPT)
    assert "PHONE" not in scene.characters
    assert "PHONE" in scene.objects


def test_cognition_verb_promotes_subject() -> None:
    """The caps subject of a cognition verb is a character."""
    scene = _first_scene("INT. ROOM - DAY\n\nVESPER realizes the door is open.\n")
    assert "VESPER" in scene.characters


def test_lowercase_subject_is_not_promoted() -> None:
    """A lowercase common-noun subject is not a screenplay name."""
    scene = _first_scene("INT. ROOM - DAY\n\nThe man whispers a warning.\n")
    assert scene.characters == []


def test_pronoun_subject_is_not_promoted() -> None:
    """A pronoun subject of a person verb never names a character."""
    action_text = "IT whispers in the dark."
    raw_doc, title_doc = _parse_action_docs(_engine.nlp, action_text)
    chars = _extract_agentive_subject_characters(
        action_text,
        raw_doc,
        title_doc,
        {},
        set(),
    )
    assert chars == set()
