"""Tests for scene dependency edges, focused on Caveat D4.

D4: reuse edges previously linked only back to the *first* scene that featured
an item, so deleting an intermediate scene under-stated downstream breakage that
conceptually flows through it. The fix links a reuse to *every* prior scene that
featured the item (additively, keeping the original first-occurrence edge), so
an intermediate deletion now ripples downstream. These tests pin the new
intermediate edge, the preserved introducing edge, and that orphans are
unchanged.
"""

from scene_dependency import SceneDependencyEngine

_engine = SceneDependencyEngine()

CHAINED_PROP_SCRIPT = """INT. ROOM ONE - DAY

A REVOLVER lies on the table.

INT. ROOM TWO - DAY

MARCUS grabs the revolver.

INT. ROOM THREE - NIGHT

MARCUS aims the revolver.
"""


def _built_engine(script: str) -> SceneDependencyEngine:
    """Parse a script and build its dependency graph."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(script)
    engine.build_graph(scenes)
    return engine


def test_intermediate_scene_ripples_downstream() -> None:
    """Deleting an intermediate carrier scene now surfaces later reuse scenes."""
    engine = _built_engine(CHAINED_PROP_SCRIPT)
    impacted = {r["scene_id"] for r in engine.get_delete_impact("scene_002")}
    assert "scene_003" in impacted


def test_intermediate_edge_is_created() -> None:
    """An explicit edge links the intermediate scene to the later reuse."""
    engine = _built_engine(CHAINED_PROP_SCRIPT)
    assert engine.graph.has_edge("scene_002", "scene_003")


def test_first_introduction_edge_is_preserved() -> None:
    """The original first-seen edges are still produced (additive change)."""
    engine = _built_engine(CHAINED_PROP_SCRIPT)
    assert engine.graph.has_edge("scene_001", "scene_002")
    assert engine.graph.has_edge("scene_001", "scene_003")


def test_intro_scene_impact_set_unchanged() -> None:
    """The introducing scene still reaches every later occurrence."""
    engine = _built_engine(CHAINED_PROP_SCRIPT)
    impacted = {r["scene_id"] for r in engine.get_delete_impact("scene_001")}
    assert impacted == {"scene_002", "scene_003"}


def test_orphans_only_count_introduction_only_scenes() -> None:
    """A scene that introduces a novel, never-reused item stays an orphan."""
    script = (
        "INT. A - DAY\n\nMARCUS holds a LEDGER.\n\n"
        "INT. B - DAY\n\nA lone STATUE sits in the dark.\n\n"
        "INT. C - DAY\n\nMARCUS reads the ledger.\n"
    )
    engine = _built_engine(script)
    orphans = engine.get_orphan_scenes()
    assert "scene_002" in orphans
    assert "scene_003" not in orphans
