"""Feature tests for the relationship contradiction checks (Phase 3).

Only immutable blood-relation contradictions are flagged (confirmed); social
and romantic ties legitimately change over a story (enemies -> friends,
married -> divorced) and must stay unflagged. Each rule ships with a positive
case and a negative case that proves a legitimate arc is left alone.
"""

from legacy.plot_contradiction import (
    STATUS_CONFIRMED,
    Contradiction,
    ContradictionEngine,
    Fact,
    _parse_relationship_value,
)
from scene_dependency import SceneDependencyEngine

_dependency_engine = SceneDependencyEngine()
_contradiction_engine = ContradictionEngine()


def _analyze(script: str) -> list[Contradiction]:
    """Parse a Fountain script and run full contradiction analysis."""
    scenes = _dependency_engine.parse_fountain_text(script)
    return _contradiction_engine.run_analysis(scenes)


def _rel_facts(script: str) -> list[Fact]:
    """Parse a Fountain script and return relationship facts."""
    scenes = _dependency_engine.parse_fountain_text(script)
    store = _contradiction_engine.extract_facts(scenes)
    return store.get_facts_by_type("relationship")


def _of_type(
    contradictions: list[Contradiction], contradiction_type: str
) -> list[Contradiction]:
    """Filter contradictions to a single type."""
    return [c for c in contradictions if c.contradiction_type == contradiction_type]


def test_parse_relationship_value() -> None:
    """Value parsing recovers category and parent_child direction."""
    assert _parse_relationship_value("sibling") == ("sibling", None)
    assert _parse_relationship_value("parent_child MARCUS>ELENA") == (
        "parent_child",
        ("MARCUS", "ELENA"),
    )


SIBLING_THEN_SPOUSE = """INT. HOUSE - DAY

MARCUS and ELENA are siblings.

INT. CHAPEL - DAY

MARCUS and ELENA are married.
"""

PARENT_ROLE_INVERSION = """INT. HOUSE - DAY

MARCUS is ELENA's father.

INT. PARK - DAY

ELENA is MARCUS's father.
"""

ENEMIES_THEN_FRIENDS = """INT. ARENA - DAY

MARCUS and ELENA are enemies.

INT. BAR - NIGHT

MARCUS and ELENA are friends.
"""

CONSISTENT_SIBLINGS = """INT. HOUSE - DAY

MARCUS is ELENA's brother.

INT. KITCHEN - DAY

ELENA is MARCUS's sister.
"""

SISTER_THEN_COUSIN = """INT. LIVING ROOM - DAY

Antonio's sister DIANA hangs photos.

INT. OFFICE - DAY

Antonio's cousin Diana reads the deed.
"""


def test_sibling_then_spouse_is_flagged() -> None:
    """Siblings later described as married is a confirmed conflict."""
    found = _of_type(_analyze(SIBLING_THEN_SPOUSE), "relationship_fact")
    assert len(found) == 1
    assert found[0].status == STATUS_CONFIRMED


def test_parent_role_inversion_is_flagged() -> None:
    """A parent/child role asserted in both directions is flagged."""
    found = _of_type(_analyze(PARENT_ROLE_INVERSION), "relationship_fact")
    assert len(found) == 1
    assert found[0].status == STATUS_CONFIRMED


def test_enemies_to_friends_is_not_flagged() -> None:
    """A social-tie arc (enemies -> friends) is a valid change, not a conflict."""
    contradictions = _analyze(ENEMIES_THEN_FRIENDS)
    assert _of_type(contradictions, "relationship_fact") == []


def test_consistent_siblings_are_not_flagged() -> None:
    """The same sibling relation stated twice is consistent."""
    assert _of_type(_analyze(CONSISTENT_SIBLINGS), "relationship_fact") == []


def test_relationship_facts_are_extracted() -> None:
    """Both phrasings produce relationship facts keyed on the character pair."""
    facts = _rel_facts(CONSISTENT_SIBLINGS)
    assert facts
    assert all(fact.entity == "ELENA|MARCUS" for fact in facts)
    assert all(fact.value == "sibling" for fact in facts)


def test_sister_then_cousin_is_flagged() -> None:
    """The same person cannot be both sister and cousin to one character."""
    found = _of_type(_analyze(SISTER_THEN_COUSIN), "relationship_fact")
    assert len(found) == 1
    assert found[0].status == STATUS_CONFIRMED


COACH_THEN_SISTER = """INT. POOL - DAY

Richard watches Sofia swim. Coach ALMA joins him.

INT. POOL - NIGHT

Richard arrives with coffee for Alma, his sister.
"""


def test_coach_then_sister_is_flagged() -> None:
    """A coach role later contradicted by a sibling relation is flagged."""
    found = _of_type(_analyze(COACH_THEN_SISTER), "relationship_fact")
    assert len(found) == 1
    assert found[0].status == STATUS_CONFIRMED
