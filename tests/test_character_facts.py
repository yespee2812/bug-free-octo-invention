"""Regression tests for character trait/status entity resolution (Caveat C1).

C1 was an entity over-capture bug: the trait/status regexes captured pronouns
("There is a..."), spanned sentence boundaries ("Smoke fills the dock.
DETECTIVE VANCE is dead."), and accepted inanimate nouns ("the engine died").
These tests pin both the shared resolver and the end-to-end extraction path so
the precision fix cannot silently regress.
"""

from plot_contradiction import (
    ContradictionEngine,
    Fact,
    _resolve_character_entity,
)
from scene_dependency import SceneDependencyEngine

_dependency_engine = SceneDependencyEngine()
_contradiction_engine = ContradictionEngine()


def _facts_of_type(script: str, fact_type: str) -> list[Fact]:
    """Parse a Fountain script and return extracted facts of one type."""
    scenes = _dependency_engine.parse_fountain_text(script)
    store = _contradiction_engine.extract_facts(scenes)
    return store.get_facts_by_type(fact_type)


def test_resolver_rejects_pronouns_and_indefinites() -> None:
    """Pronouns / indefinite words never resolve to a character."""
    for raw in ("There", "It", "This", "He", "She", "They", "Someone"):
        assert _resolve_character_entity(raw) is None


def test_resolver_rejects_inanimate_death_nouns() -> None:
    """Inanimate nouns that 'die' idiomatically are not characters."""
    assert _resolve_character_entity("the engine") is None
    assert _resolve_character_entity("The Engine") is None


def test_resolver_isolates_trailing_caps_across_sentences() -> None:
    """A capture that bled across a sentence keeps only the screenplay name."""
    assert _resolve_character_entity("Smoke fills the dock. DETECTIVE VANCE") == (
        "DETECTIVE VANCE"
    )


def test_resolver_accepts_all_caps_and_titlecase_names() -> None:
    """ALL-CAPS cues and single title-case appositive names are characters."""
    assert _resolve_character_entity("MARCUS") == "MARCUS"
    assert _resolve_character_entity("AGENT COLE") == "AGENT COLE"
    assert _resolve_character_entity("Marcus") == "MARCUS"


PRONOUN_TRAIT_SCRIPT = """INT. LAB - NIGHT

There is a similar rig on the real DeLorean.
It is a trap of some kind.
This is a long corridor.
"""

CROSS_SENTENCE_STATUS_SCRIPT = """INT. DOCK - NIGHT

Smoke fills the dock. DETECTIVE VANCE is dead.
"""

INANIMATE_STATUS_SCRIPT = """INT. CAR - NIGHT

Outside, the engine died.
"""

REAL_NAME_SCRIPT = """INT. HOSPITAL - DAY

MARCUS is a surgeon at the city hospital.

INT. WAREHOUSE - NIGHT

AGENT COLE is dead after the ambush.
"""


def test_pronoun_lines_create_no_trait_facts() -> None:
    """The 'THERE is a...' false-positive class must not produce facts."""
    assert _facts_of_type(PRONOUN_TRAIT_SCRIPT, "character_trait") == []


def test_cross_sentence_status_uses_only_the_name() -> None:
    """Status extraction must not span the sentence boundary."""
    facts = _facts_of_type(CROSS_SENTENCE_STATUS_SCRIPT, "character_status")
    assert len(facts) == 1
    assert facts[0].entity == "DETECTIVE VANCE"


def test_inanimate_death_creates_no_status_fact() -> None:
    """'the engine died' must not become a character death fact."""
    assert _facts_of_type(INANIMATE_STATUS_SCRIPT, "character_status") == []


def test_real_names_still_extracted() -> None:
    """Legitimate ALL-CAPS trait and status facts are still captured."""
    trait_facts = _facts_of_type(REAL_NAME_SCRIPT, "character_trait")
    status_facts = _facts_of_type(REAL_NAME_SCRIPT, "character_status")
    assert any(fact.entity == "MARCUS" for fact in trait_facts)
    assert any(fact.entity == "AGENT COLE" for fact in status_facts)
