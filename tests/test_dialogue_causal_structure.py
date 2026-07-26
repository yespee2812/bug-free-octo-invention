"""Phase B: causal dialogue edges on the v3 structure path."""

from __future__ import annotations

from scene_dependency import _has_causal_dialogue
from scriptlens_structure import analyze_structure, get_simulate_cut_impact

CAUSAL_STRUCTURE_SCRIPT = """INT. WAREHOUSE - NIGHT

MARCUS
I'm sorry about everything.

INT. APARTMENT - DAY

MARCUS
After what you did, I can't trust anyone.
"""

INFORMAL_CAUSAL_SCRIPT = """INT. PUB - NIGHT

LENA
We should never have gone back.

INT. FLAT - DAY

LENA
After what you done, we're finished.
"""

YA_DID_CAUSAL_SCRIPT = """INT. YARD - DAY

TOM
Keep your mouth shut.

INT. KITCHEN - NIGHT

TOM
After what ya did, stay away from her.
"""

NEUTRAL_STRUCTURE_SCRIPT = """INT. CAFE - DAY

MARCUS
Good morning.

INT. OFFICE - DAY

MARCUS
See you tomorrow.
"""

NO_SHARED_SPEAKER_SCRIPT = """INT. OFFICE - DAY

MARCUS
The deal is done.

INT. ROOFTOP - NIGHT

LENA
After what you did, I can't sleep.
"""


def test_structure_path_builds_causal_edge() -> None:
    """analyze_structure includes causal edges for callback dialogue."""
    results = analyze_structure(CAUSAL_STRUCTURE_SCRIPT)
    engine = results["engine"]
    edge_types = list(engine.graph["scene_001"]["scene_002"]["edge_types"])
    assert "causal" in edge_types


def test_structure_simulate_cut_follows_causal_dialogue() -> None:
    """Simulate cut on the prior scene surfaces the causal-dialogue scene."""
    results = analyze_structure(CAUSAL_STRUCTURE_SCRIPT)
    engine = results["engine"]
    impact = get_simulate_cut_impact(engine, "scene_001", engine._scene_lookup)
    impacted_ids = {row["scene_id"] for row in impact["impacted_scenes"]}
    assert "scene_002" in impacted_ids


def test_informal_after_what_you_done_is_causal() -> None:
    """Literal informal 'after what you done' matches causal patterns."""
    raw = (
        "INT. FLAT - DAY\n\n"
        "LENA\n"
        "After what you done, we're finished.\n"
    )
    assert _has_causal_dialogue(raw)
    results = analyze_structure(INFORMAL_CAUSAL_SCRIPT)
    engine = results["engine"]
    assert "causal" in list(engine.graph["scene_001"]["scene_002"]["edge_types"])


def test_after_what_ya_did_is_causal() -> None:
    """Literal 'after what ya did' matches causal patterns."""
    raw = (
        "INT. KITCHEN - NIGHT\n\n"
        "TOM\n"
        "After what ya did, stay away from her.\n"
    )
    assert _has_causal_dialogue(raw)
    results = analyze_structure(YA_DID_CAUSAL_SCRIPT)
    engine = results["engine"]
    assert "causal" in list(engine.graph["scene_001"]["scene_002"]["edge_types"])


def test_neutral_dialogue_has_no_causal_on_structure_path() -> None:
    """Ordinary dialogue must not create a causal edge via analyze_structure."""
    results = analyze_structure(NEUTRAL_STRUCTURE_SCRIPT)
    engine = results["engine"]
    if engine.graph.has_edge("scene_001", "scene_002"):
        edge_types = list(engine.graph["scene_001"]["scene_002"]["edge_types"])
        assert "causal" not in edge_types
    else:
        assert True


def test_causal_requires_shared_speaker_on_structure_path() -> None:
    """Causal callback without a shared prior speaker does not invent an edge."""
    results = analyze_structure(NO_SHARED_SPEAKER_SCRIPT)
    engine = results["engine"]
    assert not engine.graph.has_edge("scene_001", "scene_002") or (
        "causal"
        not in list(engine.graph["scene_001"]["scene_002"].get("edge_types", []))
    )
