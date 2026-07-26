"""Phase C: structure-bearing dialogue filtering for semantic embeddings."""

from __future__ import annotations

from osd_semantic import (
    SEMANTIC_DIALOGUE_CHAR_CAP,
    scene_semantic_text,
)
from scene_dependency import SceneBlock, SceneDependencyEngine

SLANG_WALL_SCRIPT = """INT. PUB - NIGHT

The REVOLVER sits under the bar towel.

DAVE
Blimey mate you what I'm proper knackered innit yeah nah leave it out
you muppet sort yourself out before I lose me rag you get me bruv
that whole carry-on was well out of order mate absolute scenes.

INT. ALLEY - NIGHT

DAVE
Bring the piece. Meet me at the docks after what you did.
"""


def test_semantic_text_prefers_action_over_slang_wall() -> None:
    """Dense slang dialogue is capped; action and structure lines remain."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(SLANG_WALL_SCRIPT)
    scene_one = scenes[0]
    blob = scene_semantic_text(scene_one)

    assert "INT. PUB - NIGHT" in blob
    assert "REVOLVER" in blob.upper() or "revolver" in blob.lower()
    # Slang wall must not appear in full.
    assert blob.lower().count("muppet") == 0 or len(blob) < len(scene_one.raw_text)


def test_semantic_text_keeps_structure_bearing_dialogue() -> None:
    """Prop alias / causal / location callouts stay in the embed blob."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(SLANG_WALL_SCRIPT)
    scene_two = scenes[1]
    # Plant revolver onto scene 2 props via prior known soft path after parse.
    # Scene 2 should already have REVOLVER from piece alias if plant carried.
    blob = scene_semantic_text(scene_two).lower()
    assert "bring the piece" in blob or "after what you did" in blob


def test_semantic_text_excludes_emotion_parenthetical_only() -> None:
    """Bare emotion parentheticals are not structure-bearing."""
    scene = SceneBlock(
        scene_id="scene_001",
        scene_number=1,
        heading="INT. ROOM - DAY",
        raw_text="INT. ROOM - DAY\n\nMARCUS\n(laughing)\nHello there.\n",
        characters=["MARCUS"],
        characters_speaking=["MARCUS"],
    )
    blob = scene_semantic_text(scene)
    assert "(laughing)" not in blob
    # Fallback may still include a short spoken sample.
    assert "INT. ROOM - DAY" in blob


def test_semantic_dialogue_char_cap_enforced() -> None:
    """Spoken portion of the blob stays within the configured cap."""
    long_line = "word " * 200
    scene = SceneBlock(
        scene_id="scene_001",
        scene_number=1,
        heading="INT. ROOM - DAY",
        raw_text=f"INT. ROOM - DAY\n\nAction beat.\n\nMARCUS\n{long_line}\n",
        characters=["MARCUS"],
        characters_speaking=["MARCUS"],
    )
    blob = scene_semantic_text(scene)
    # Everything after heading+action is dialogue; ensure total blob is bounded
    # relative to an uncapped dump of the spoken wall.
    assert len(blob) < len(scene.raw_text)
    spoken = blob.split("Action beat.", 1)[-1]
    assert len(spoken.strip()) <= SEMANTIC_DIALOGUE_CHAR_CAP + 5


def test_action_only_scene_still_embeds() -> None:
    """Scenes with no dialogue still produce heading + action text."""
    scene = SceneBlock(
        scene_id="scene_001",
        scene_number=1,
        heading="INT. ROOFTOP - DAY",
        raw_text="INT. ROOFTOP - DAY\n\nNEGOTIATOR speaks calmly.\n",
    )
    blob = scene_semantic_text(scene)
    assert "INT. ROOFTOP - DAY" in blob
    assert "NEGOTIATOR speaks calmly" in blob
