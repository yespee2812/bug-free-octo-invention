"""Unit tests for the entity canonicalization foundation (redesign P0).

Covers name normalization, title/possessive handling, alias merging, unique
partial-name resolution, ambiguity safety, and name-drift detection.
"""

from entity_canonicalization import (
    EntityRegistry,
    levenshtein,
    normalize_name,
    strip_titles_and_articles,
)


def test_normalize_strips_possessive_and_punctuation() -> None:
    """Possessives, parentheticals, and trailing punctuation are removed."""
    assert normalize_name("Eddie's") == "EDDIE"
    assert normalize_name("CAPTAIN RICO SANTOS,") == "CAPTAIN RICO SANTOS"
    assert normalize_name("ELENA (V.O.)") == "ELENA"


def test_strip_titles_and_articles() -> None:
    """Leading titles and articles are dropped but the core name is kept."""
    assert strip_titles_and_articles("CAPTAIN EDDIE MORAN") == "EDDIE MORAN"
    assert strip_titles_and_articles("THE INFORMANT") == "INFORMANT"
    assert strip_titles_and_articles("DETECTIVE") == "DETECTIVE"


def test_title_variant_merges_into_one_entity() -> None:
    """A titled mention and a bare mention resolve to the same id."""
    registry = EntityRegistry()
    full = registry.register("CAPTAIN EDDIE MORAN")
    assert registry.resolve("Eddie") == full
    assert registry.resolve("EDDIE MORAN") == full
    assert registry.resolve("Captain Moran") == full
    assert len(registry.canonical_ids) == 1


def test_possessive_mention_resolves() -> None:
    """A possessive mention resolves to the registered entity."""
    registry = EntityRegistry.from_cues(["RICHARD"])
    assert registry.resolve("Richard's") == "RICHARD"


def test_ambiguous_first_name_does_not_resolve() -> None:
    """A shared first name pointing at two people resolves to None."""
    registry = EntityRegistry.from_cues(["EDDIE MORAN", "EDDIE VANCE"])
    assert registry.resolve("Eddie") is None
    assert registry.resolve("EDDIE MORAN") == "EDDIE MORAN"


def test_unknown_mention_returns_none() -> None:
    """A mention with no matching entity resolves to None."""
    registry = EntityRegistry.from_cues(["MARIA"])
    assert registry.resolve("ANTONIO") is None
    assert registry.register("  ") is None


def test_levenshtein_basic() -> None:
    """Edit distance matches known small cases."""
    assert levenshtein("OSEI", "OSEI") == 0
    assert levenshtein("OSEI", "OSHEA") == 2
    assert levenshtein("TENZIN", "TENSING") == 2


def test_name_drift_pairs_detected() -> None:
    """Typo-level name variants are surfaced as drift candidates."""
    registry = EntityRegistry.from_cues(["OSEI", "OSHEA", "MARIA"])
    pairs = registry.near_duplicate_pairs(max_distance=2)
    assert ("OSEI", "OSHEA", 2) in pairs
    assert all("MARIA" not in (a, b) for a, b, _ in pairs)


def test_name_drift_ignores_distinct_names() -> None:
    """Clearly different names are not flagged as drift."""
    registry = EntityRegistry.from_cues(["ELENA", "RICHARD", "SOFIA"])
    assert registry.near_duplicate_pairs(max_distance=2) == []
