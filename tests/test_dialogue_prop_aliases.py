"""Phase A dialogue-as-structure: closed prop nickname aliases."""

from __future__ import annotations

from scene_dependency import (
    SceneDependencyEngine,
    _match_prop_soft_mentions,
    _props_for_dialogue_aliases,
)

PIECE_WITH_PLANT = """INT. WAREHOUSE - NIGHT

A REVOLVER sits on the crate.

INT. ALLEY - NIGHT

MARCUS
Bring the piece.
"""

PIECE_WITHOUT_PLANT = """INT. ALLEY - NIGHT

MARCUS
Bring the piece.
"""

WHEELS_WITH_PLANT = """INT. GARAGE - DAY

A black CAR waits with the engine running.

EXT. STREET - NIGHT

LENA
Get in. I brought the wheels.
"""


def test_alias_maps_piece_to_planted_revolver() -> None:
    """Dialogue 'piece' attaches only to an already-planted gun-family prop."""
    hits = _match_prop_soft_mentions("Bring the piece.", {"REVOLVER"})
    assert hits == ["REVOLVER"]


def test_alias_does_not_create_prop_without_plant() -> None:
    """Dialogue nickname alone must not invent a prop."""
    assert _match_prop_soft_mentions("Bring the piece.", set()) == []
    assert _props_for_dialogue_aliases("Bring the piece.", set()) == []
    assert _match_prop_soft_mentions("Bring the piece.", {"GUEST BOOK"}) == []


def test_alias_ignores_unrelated_planted_props() -> None:
    """Gun slang must not attach to non-gun props."""
    assert _props_for_dialogue_aliases("Bring the piece.", {"LEDGER"}) == []


def test_existing_soft_match_still_works() -> None:
    """Last-two-word soft match remains for multi-word planted props."""
    hits = _match_prop_soft_mentions(
        "No one touches the guest book.",
        {"MAGNETIC GUEST BOOK"},
    )
    assert "MAGNETIC GUEST BOOK" in hits


def test_parse_piece_dialogue_after_revolver_plant() -> None:
    """Later scene dialogue 'piece' records the planted REVOLVER on that scene."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(PIECE_WITH_PLANT)
    assert len(scenes) == 2
    assert "REVOLVER" in scenes[0].objects or "REVOLVER" in scenes[0].props_detected
    scene_two_props = set(scenes[1].props_detected or scenes[1].objects)
    assert "REVOLVER" in scene_two_props


def test_parse_piece_dialogue_without_plant_adds_nothing() -> None:
    """Without a prior gun plant, 'piece' does not become a prop."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(PIECE_WITHOUT_PLANT)
    assert len(scenes) == 1
    props = set(scenes[0].props_detected or scenes[0].objects)
    assert "REVOLVER" not in props
    assert "PIECE" not in props
    assert "GUN" not in props


def test_parse_wheels_dialogue_after_car_plant() -> None:
    """Dialogue 'wheels' attaches to a planted CAR."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(WHEELS_WITH_PLANT)
    scene_two_props = set(scenes[1].props_detected or scenes[1].objects)
    assert "CAR" in scene_two_props


def test_shooter_alias_maps_to_gun() -> None:
    """'shooter' is in the gun-family alias set."""
    assert _props_for_dialogue_aliases("Where is the shooter?", {"GUN"}) == ["GUN"]
