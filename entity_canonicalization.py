"""Entity canonicalization for the contradiction engine.

This is a foundation layer (redesign phase P0): it unifies the many surface
forms a character or prop can take ("Eddie", "Captain Eddie Moran", "Eddie's",
"EDDIE") onto a single canonical id so downstream facts from different scenes
can line up. It also surfaces likely *name-drift* pairs (e.g. "OSEI" vs
"OSHEA") for reporting rather than silently merging them.

The module is intentionally dependency-free (no spaCy, no project imports) so it
stays fast and trivially unit-testable. Heavier NER-based resolution can feed
this registry later without changing its public surface.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# Professional / honorific titles that precede a name and should be stripped
# when resolving ("CAPTAIN EDDIE" and "EDDIE" are the same person).
TITLE_WORDS: frozenset[str] = frozenset(
    {
        "DETECTIVE", "CAPTAIN", "SERGEANT", "LIEUTENANT", "COLONEL", "GENERAL",
        "CORPORAL", "PRIVATE", "MAJOR", "ADMIRAL", "OFFICER", "AGENT", "DEPUTY",
        "DR", "DOCTOR", "PROFESSOR", "PROF", "MR", "MRS", "MS", "MISS", "SIR",
        "LADY", "LORD", "FATHER", "SISTER", "BROTHER", "REVEREND", "RABBI",
        "JUDGE", "MAYOR", "PRESIDENT", "SENATOR", "GOVERNOR", "PRINCESS",
        "PRINCE", "KING", "QUEEN", "COACH", "PILOT", "RANCHER", "PRINCIPAL",
        "HAUPTMANN", "MADAME", "MADAM", "MONSIEUR", "SENORA", "SENOR",
        "INSPECTOR", "CONSTABLE", "CHIEF", "COMMANDER", "NURSE",
    }
)

_LEADING_ARTICLES: tuple[str, ...] = ("THE", "A", "AN")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
_PAREN_RE = re.compile(r"\([^)]*\)")


def normalize_name(raw: str) -> str:
    """Return an uppercase, punctuation-stripped key for a name mention.

    Removes parentheticals, possessive ``'s``/``s'``, surrounding punctuation,
    and collapses whitespace. Does not strip titles or articles (callers that
    want those removed use :func:`strip_titles_and_articles`).

    Args:
        raw: A raw name span such as "Eddie's" or "CAPTAIN RICO SANTOS,".

    Returns:
        A normalized key like "EDDIE" or "CAPTAIN RICO SANTOS" (may be empty).
    """
    without_parens = _PAREN_RE.sub(" ", raw)
    upper = without_parens.upper()
    upper = re.sub(r"['\u2019]S\b", "", upper)
    upper = re.sub(r"S['\u2019]\b", "S", upper)
    tokens = _WORD_RE.findall(upper)
    return " ".join(tokens)


def strip_titles_and_articles(name: str) -> str:
    """Return a normalized name with leading titles and articles removed.

    Args:
        name: An already-normalized name key (see :func:`normalize_name`).

    Returns:
        The name without any leading title/article tokens; if every token is a
        title/article the original name is returned unchanged.
    """
    tokens = name.split()
    index = 0
    while index < len(tokens) - 1 and (
        tokens[index] in TITLE_WORDS
        or tokens[index].rstrip(".") in TITLE_WORDS
        or tokens[index] in _LEADING_ARTICLES
    ):
        index += 1
    stripped = " ".join(tokens[index:])
    return stripped or name


def levenshtein(a: str, b: str) -> int:
    """Return the Levenshtein edit distance between two strings.

    A small, allocation-light dynamic-programming implementation used for
    name-drift detection (typo-level differences between character names).
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            cost = 0 if char_a == char_b else 1
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            )
        previous = current
    return previous[-1]


@dataclass
class Entity:
    """A canonical character or prop with all known surface aliases."""

    canonical_id: str
    aliases: set[str] = field(default_factory=set)


class EntityRegistry:
    """Registry that maps name mentions onto canonical entity ids.

    Strong aliases (full name, title-stripped, article-stripped) map directly to
    one canonical id and are used both to merge variants on registration and to
    resolve mentions. Single name tokens (first/last name) are tracked
    separately and only resolve when they uniquely identify one entity, so two
    different people who share a first name are never collapsed.
    """

    def __init__(self) -> None:
        """Create an empty registry."""
        self._entities: dict[str, Entity] = {}
        self._alias_to_id: dict[str, str] = {}
        self._token_to_ids: dict[str, set[str]] = {}

    @classmethod
    def from_cues(cls, cues: Iterable[str]) -> "EntityRegistry":
        """Build a registry by registering each cue/name in ``cues``."""
        registry = cls()
        for cue in cues:
            registry.register(cue)
        return registry

    def _strong_aliases(self, name: str) -> set[str]:
        """Return the strong-alias variants used for direct lookup/merge."""
        variants = {name, strip_titles_and_articles(name)}
        return {variant for variant in variants if variant}

    def register(self, raw_name: str) -> str | None:
        """Register a name mention and return its canonical id.

        If any strong-alias variant already belongs to an entity, the mention is
        merged into that entity; otherwise a new entity is created with the
        longest strong alias as its canonical id.

        Args:
            raw_name: A raw name span (may include titles, possessives, parens).

        Returns:
            The canonical id, or ``None`` when ``raw_name`` has no name tokens.
        """
        name = normalize_name(raw_name)
        if not name:
            return None
        aliases = self._strong_aliases(name)

        existing_id: str | None = None
        for alias in aliases:
            if alias in self._alias_to_id:
                existing_id = self._alias_to_id[alias]
                break
        # Merge cue-style last names ("HALE") onto a full intro ("CAPTAIN TOM HALE")
        # when the token already uniquely identifies one registered entity.
        if existing_id is None and len(name.split()) == 1:
            token_ids = self._token_to_ids.get(name)
            if token_ids and len(token_ids) == 1:
                existing_id = next(iter(token_ids))

        if existing_id is None:
            canonical_id = max(aliases, key=len)
            self._entities[canonical_id] = Entity(canonical_id, set(aliases))
        else:
            canonical_id = existing_id
            self._entities[canonical_id].aliases.update(aliases)

        for alias in aliases:
            self._alias_to_id.setdefault(alias, canonical_id)
            for token in alias.split():
                self._token_to_ids.setdefault(token, set()).add(canonical_id)
        return canonical_id

    def resolve(self, mention: str) -> str | None:
        """Resolve a name mention to a canonical id, or ``None``.

        Resolution order: exact strong alias, title/article-stripped alias, then
        unique single-token (first/last name) match. Ambiguous tokens that point
        at more than one entity do not resolve.

        Args:
            mention: A raw name span (may include titles/possessives/parens).

        Returns:
            The canonical id, or ``None`` if it cannot be resolved unambiguously.
        """
        name = normalize_name(mention)
        if not name:
            return None
        if name in self._alias_to_id:
            return self._alias_to_id[name]
        stripped = strip_titles_and_articles(name)
        if stripped in self._alias_to_id:
            return self._alias_to_id[stripped]
        for token in stripped.split():
            ids = self._token_to_ids.get(token)
            if ids and len(ids) == 1:
                return next(iter(ids))
        return None

    @property
    def canonical_ids(self) -> list[str]:
        """Return all canonical ids currently registered, sorted."""
        return sorted(self._entities)

    def near_duplicate_pairs(
        self, max_distance: int = 2, min_length: int = 4
    ) -> list[tuple[str, str, int]]:
        """Return canonical-id pairs that look like name drift / typos.

        Compares distinct canonical ids by Levenshtein distance and returns
        those within ``max_distance`` (ignoring spaces, both names at least
        ``min_length`` long). These are *candidates to report* as
        ``name_consistency`` issues, not facts to merge.

        Args:
            max_distance: Maximum edit distance to consider a drift pair.
            min_length: Minimum compressed length for both names, to avoid
                flagging unrelated short names.

        Returns:
            Sorted list of ``(name_a, name_b, distance)`` tuples.
        """
        ids = self.canonical_ids
        pairs: list[tuple[str, str, int]] = []
        for i, first in enumerate(ids):
            compact_first = first.replace(" ", "")
            for second in ids[i + 1 :]:
                compact_second = second.replace(" ", "")
                if (
                    len(compact_first) < min_length
                    or len(compact_second) < min_length
                ):
                    continue
                distance = levenshtein(compact_first, compact_second)
                if 0 < distance <= max_distance:
                    pairs.append((first, second, distance))
        return sorted(pairs)
