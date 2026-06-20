"""Feature tests for world-rule capture (Phase 4).

World rules are capture-only: declared rules of the fiction are extracted as
world_rule facts for later Tier 3 violation reasoning, but no Tier 1
contradiction is raised from them. These tests pin both behaviors.
"""

from plot_contradiction import Contradiction, ContradictionEngine, Fact
from scene_dependency import SceneDependencyEngine

_dependency_engine = SceneDependencyEngine()
_contradiction_engine = ContradictionEngine()


def _rule_facts(script: str) -> list[Fact]:
    """Parse a Fountain script and return world_rule facts."""
    scenes = _dependency_engine.parse_fountain_text(script)
    store = _contradiction_engine.extract_facts(scenes)
    return store.get_facts_by_type("world_rule")


def _analyze(script: str) -> list[Contradiction]:
    """Parse a Fountain script and run full contradiction analysis."""
    scenes = _dependency_engine.parse_fountain_text(script)
    return _contradiction_engine.run_analysis(scenes)


WORLD_RULES_SCRIPT = """INT. LAB - NIGHT

The time machine cannot travel to the future.

INT. CRYPT - NIGHT

Vampires can only enter when invited.

INT. DOME - DAY

No one can leave the dome.

INT. ROOFTOP - NIGHT

The machine travels to the future anyway.
"""


def test_world_rules_are_captured() -> None:
    """Capability/permission rules are stored as world_rule facts."""
    facts = _rule_facts(WORLD_RULES_SCRIPT)
    values = {fact.value for fact in facts}
    entities = {fact.entity for fact in facts}
    assert "cannot: travel to the future" in values
    assert any(value.startswith("can only:") for value in values)
    assert "TIME MACHINE" in entities
    assert "VAMPIRES" in entities


def test_world_rules_raise_no_tier1_contradiction() -> None:
    """Capture-only: even an obvious rule break is not flagged in Tier 1."""
    contradictions = _analyze(WORLD_RULES_SCRIPT)
    assert all(
        c.contradiction_type not in ("world_rule", "world_rule_violation")
        for c in contradictions
    )


def test_subject_articles_are_stripped() -> None:
    """The rule subject is normalized with leading articles removed."""
    facts = _rule_facts("INT. LAB - NIGHT\n\nThe serum can only work once.\n")
    assert any(fact.entity == "SERUM" for fact in facts)
