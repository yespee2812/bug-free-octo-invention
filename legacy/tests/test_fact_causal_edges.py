"""Tests for fact and causal dependency edges (Caveat D6).

Fact edges link a scene that establishes plot state to later scenes that
reference the same entity. Causal edges link dialogue with explicit backward
temporal references to the most recent prior scene sharing a speaker.
"""

from legacy.plot_contradiction import ContradictionEngine
from scene_dependency import SceneDependencyEngine

_dependency_engine = SceneDependencyEngine()
_contradiction_engine = ContradictionEngine()


def _build(
    script: str,
    *,
    include_fact_edges: bool = True,
    include_causal_edges: bool = True,
) -> SceneDependencyEngine:
    """Parse a script, extract facts, and build the dependency graph."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(script)
    fact_store = _contradiction_engine.extract_facts(scenes)
    engine.build_graph(
        scenes,
        fact_store=fact_store,
        include_fact_edges=include_fact_edges,
        include_causal_edges=include_causal_edges,
    )
    return engine


def _edge_types(
    engine: SceneDependencyEngine, from_scene: str, to_scene: str
) -> list[str]:
    """Return merged edge types between two scenes, or an empty list."""
    if not engine.graph.has_edge(from_scene, to_scene):
        return []
    return list(engine.graph[from_scene][to_scene]["edge_types"])


FACT_SCRIPT = """INT. HOSPITAL - DAY

MARCUS is a surgeon at the city hospital.

INT. ALLEY - NIGHT

Rain falls on empty crates.

INT. CLINIC - DAY

MARCUS
We need to operate now.
"""

CAUSAL_SCRIPT = """INT. WAREHOUSE - NIGHT

MARCUS
I'm sorry about everything.

INT. APARTMENT - DAY

MARCUS
After what you did, I can't trust anyone.
"""

NEUTRAL_DIALOGUE_SCRIPT = """INT. CAFE - DAY

MARCUS
Good morning.

INT. OFFICE - DAY

MARCUS
See you tomorrow.
"""


def test_fact_edge_links_establishing_scene_to_later_reference() -> None:
    """A trait fact in scene 1 creates a fact edge to scene 3 referencing MARCUS."""
    engine = _build(FACT_SCRIPT)
    assert "fact" in _edge_types(engine, "scene_001", "scene_003")


def test_causal_edge_links_speaker_prior_scene() -> None:
    """'After what you did' links to the most recent prior scene with MARCUS."""
    engine = _build(CAUSAL_SCRIPT)
    assert "causal" in _edge_types(engine, "scene_001", "scene_002")


def test_neutral_dialogue_creates_no_causal_edge() -> None:
    """Ordinary dialogue without causal phrasing must not add causal edges."""
    engine = _build(NEUTRAL_DIALOGUE_SCRIPT)
    assert "causal" not in _edge_types(engine, "scene_001", "scene_002")


def test_fact_edges_can_be_disabled() -> None:
    """include_fact_edges=False skips fact edge construction."""
    engine = _build(FACT_SCRIPT, include_fact_edges=False)
    assert "fact" not in _edge_types(engine, "scene_001", "scene_003")


def test_causal_edges_can_be_disabled() -> None:
    """include_causal_edges=False skips causal edge construction."""
    engine = _build(CAUSAL_SCRIPT, include_causal_edges=False)
    assert "causal" not in _edge_types(engine, "scene_001", "scene_002")


def test_causal_delete_impact_reaches_referencing_scene() -> None:
    """Deleting the prior scene surfaces the causal-dialogue scene downstream."""
    engine = _build(CAUSAL_SCRIPT)
    impacted = {record["scene_id"] for record in engine.get_delete_impact("scene_001")}
    assert "scene_002" in impacted
