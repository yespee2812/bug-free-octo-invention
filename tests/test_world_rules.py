"""Feature tests for world-rule capture and violation detection (Phase 4).

Declared rules of the fiction are extracted as world_rule facts. A later scene
that affirmatively breaks a concrete-subject "cannot" rule is flagged as a
conservative (possible) world_rule_violation. "Can only" rules and
indefinite-subject rules ("no one can leave") are captured but not evaluated
for violations. These tests pin both the capture and the violation behavior.
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


def test_world_rule_violation_detected() -> None:
    """A later scene that breaks a 'cannot' rule is flagged as a violation."""
    contradictions = _analyze(WORLD_RULES_SCRIPT)
    violations = [
        c for c in contradictions if c.contradiction_type == "world_rule_violation"
    ]
    assert len(violations) == 1
    violation = violations[0]
    assert violation.status == "possible"
    assert violation.fact_a.entity == "TIME MACHINE"
    assert violation.scene_number_b > violation.scene_number_a


def test_can_only_and_indefinite_rules_not_violated() -> None:
    """'Can only' and indefinite-subject rules are captured but never flagged."""
    contradictions = _analyze(WORLD_RULES_SCRIPT)
    violations = [
        c for c in contradictions if c.contradiction_type == "world_rule_violation"
    ]
    assert all(c.fact_a.entity == "TIME MACHINE" for c in violations)


def test_respected_cannot_rule_has_no_violation() -> None:
    """A 'cannot' rule that is never broken raises no violation."""
    script = (
        "INT. LAB - NIGHT\n\n"
        "The portal cannot open during daylight.\n\n"
        "INT. LAB - DAY\n\n"
        "The portal stays sealed as the sun rises.\n"
    )
    contradictions = _analyze(script)
    assert all(
        c.contradiction_type != "world_rule_violation" for c in contradictions
    )


def test_subject_articles_are_stripped() -> None:
    """The rule subject is normalized with leading articles removed."""
    facts = _rule_facts("INT. LAB - NIGHT\n\nThe serum can only work once.\n")
    assert any(fact.entity == "SERUM" for fact in facts)
