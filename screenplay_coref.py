"""Lightweight screenplay coreference without ML models.

Screenplays are highly structured (ALL-CAPS cues, repeated names, role
introductions), so a small rule layer resolves most continuity mentions without
neural coref libraries such as fastcoref or coreferee — those add PyTorch,
large model downloads (coreferee models alone are tens of GB), and still
underperform on fountain formatting.

This module tracks, per scene:

* dialogue speakers (from character cues)
* capitalized name mentions in action
* role nouns from intros ("TOMAS, 22, gardener" -> gardener -> TOMAS)
* pronoun subjects ("she" -> last person mentioned in the scene)

Dependency-free aside from :mod:`entity_canonicalization`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from entity_canonicalization import EntityRegistry, normalize_name, strip_titles_and_articles
from scene_dependency import SceneBlock, _is_character_cue, _is_transition

# Role/profession head nouns in intro appositives ("NAME, 22, gardener").
ROLE_NOUNS: frozenset[str] = frozenset(
    {
        "gardener", "coach", "detective", "officer", "agent", "pilot", "captain",
        "sergeant", "doctor", "nurse", "teacher", "judge", "lawyer", "therapist",
        "waiter", "bartender", "driver", "pilot", "guide", "foreman", "rancher",
        "stranger", "student", "principal", "partner", "nephew", "niece", "son",
        "daughter", "brother", "sister", "cousin", "uncle", "aunt", "father",
        "mother", "maid", "butler", "sheriff", "deputy", "soldier", "medic",
        "mechanic", "clerk", "reporter", "photographer", "artist", "poet",
        "novelist", "writer", "actor", "singer", "dancer", "athlete", "swimmer",
        "groom", "bride",
    }
)

# Words that look like names but are not people.
NON_NAME_TOKENS: frozenset[str] = frozenset(
    {
        "INT", "EXT", "DAY", "NIGHT", "MORNING", "EVENING", "DUSK", "DAWN",
        "LATER", "CONTINUOUS", "FADE", "CUT", "THE", "END", "ON", "TAPE",
        "SUPER", "TITLE", "MONTAGE", "FLASHBACK", "INTERCUT", "SAME",
    }
)

PRONOUN_RE: re.Pattern[str] = re.compile(
    r"\b(?P<pronoun>she|her|he|him|they|them)\b", re.IGNORECASE
)
ACTION_NAME_RE: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z])(?P<name>[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,3})"
)
# Name token: ALL-CAPS word or Title-case word (no lowercase glue like "interviews").
_NAME_TOKEN = r"(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+)"
INTRO_ROLE_RE: re.Pattern[str] = re.compile(
    rf"(?<![A-Za-z])(?P<name>{_NAME_TOKEN}(?:\s+{_NAME_TOKEN}){{0,3}})\s*,\s*"
    r"(?P<clause>[^,.;:!?\n]{1,60})",
)
YEAR_OLD_AGE_RE: re.Pattern[str] = re.compile(
    r"\b(?P<age>\d{1,3}|[a-z]+(?:-[a-z]+)?)\s*-\s*year\s*-\s*old"
    r"(?:\s+(?P<role>[a-z]{3,}))?",
    re.IGNORECASE,
)
FIRST_PERSON_AGE_RE: re.Pattern[str] = re.compile(
    r"\b(?:when|since|until|not\s+since)\s+I\s+was\s+"
    r"(?P<age>\d{1,3}|[a-z]+(?:-[a-z]+)?)\b",
    re.IGNORECASE,
)
FOR_AGE_DIALOGUE_RE: re.Pattern[str] = re.compile(
    r"\bFor\s+(?P<age>\d{1,3}|[a-z]+(?:-[a-z]+)?)\b", re.IGNORECASE
)
PAYMENT_OBJECT_RE: re.Pattern[str] = re.compile(
    r"\b(?:pay|pays|paid|paying|offer|offers|offered)\s+(?:me\s+)?"
    r"(?:(?:with|using)\s+)?(?:a|an|the|his|her|their|another)?\s*"
    r"(?:(?P<material>silver|gold|brass|bronze|copper|iron|steel|leather|"
    r"canvas|red|green|blue|black|white|gray|grey|wax|iron)\s+)?"
    r"(?P<head>[a-z][a-z0-9\-]{2,})",
    re.IGNORECASE,
)


@dataclass
class RoleRegistry:
    """Maps role nouns (gardener, coach) to canonical character ids."""

    role_to_entity: dict[str, str] = field(default_factory=dict)

    def register(self, role: str, entity_id: str) -> None:
        """Associate a role noun with a canonical character id."""
        key = role.lower()
        if key in ROLE_NOUNS:
            self.role_to_entity.setdefault(key, entity_id)

    def resolve(self, role: str) -> str | None:
        """Return the character for a role noun, if known."""
        return self.role_to_entity.get(role.lower())


@dataclass
class SceneMentionTracker:
    """Tracks mention order within one scene for pronoun-style resolution."""

    scene_characters: set[str]
    mention_stack: list[str] = field(default_factory=list)
    current_speaker: str | None = None

    def set_speaker(self, speaker_id: str | None) -> None:
        """Record the active dialogue speaker."""
        self.current_speaker = speaker_id
        if speaker_id is not None:
            self._push(speaker_id)

    def note_action_mentions(self, line: str, registry: EntityRegistry) -> None:
        """Push characters named in an action line onto the mention stack."""
        for match in ACTION_NAME_RE.finditer(line):
            raw = match.group("name")
            if raw.split()[0] in NON_NAME_TOKENS:
                continue
            entity = registry.resolve(raw)
            if entity is None:
                candidate = strip_titles_and_articles(normalize_name(raw))
                if candidate and candidate.split()[0] not in NON_NAME_TOKENS:
                    entity = candidate
            if entity:
                self._push(entity)

    def resolve_subject(self, line: str) -> str | None:
        """Return the likely subject for an age phrase on ``line``.

        For pronouns, prefers the most recent mentioned character who is not the
        current speaker (so Alma describing "she" resolves to Sofia, not Alma).
        """
        if PRONOUN_RE.search(line):
            for entity in reversed(self.mention_stack):
                if entity != self.current_speaker:
                    return entity
        if re.search(r"\bI\b", line) and self.current_speaker:
            return self.current_speaker
        if self.mention_stack:
            for entity in reversed(self.mention_stack):
                if entity != self.current_speaker:
                    return entity
            return self.mention_stack[-1]
        if len(self.scene_characters) == 1:
            return next(iter(self.scene_characters))
        return None

    def resolve_possessive_pronoun(self, pronoun: str) -> str | None:
        """Resolve ``his/her/their`` to the most recent non-speaker mention."""
        _ = pronoun.lower()
        for entity in reversed(self.mention_stack):
            if entity != self.current_speaker:
                return entity
        if self.mention_stack:
            return self.mention_stack[-1]
        if len(self.scene_characters) == 1:
            return next(iter(self.scene_characters))
        return None

    def _push(self, entity_id: str) -> None:
        """Append an entity to the stack, collapsing consecutive duplicates."""
        if self.mention_stack and self.mention_stack[-1] == entity_id:
            return
        self.mention_stack.append(entity_id)


def register_characters_from_scenes(
    registry: EntityRegistry, scenes: list[SceneBlock]
) -> None:
    """Register every parsed scene character so cues and action intros merge."""
    for scene in scenes:
        characters = sorted(
            (character for character in scene.characters if character != "THE END"),
            key=len,
            reverse=True,
        )
        for character in characters:
            if character.upper() not in NON_NAME_TOKENS:
                registry.register(character)


def index_roles_from_line(
    line: str, registry: EntityRegistry, roles: RoleRegistry
) -> None:
    """Register role nouns from intro lines such as 'TOMAS, 22, gardener'."""
    for match in INTRO_ROLE_RE.finditer(line):
        raw_name = match.group("name")
        entity = registry.resolve(raw_name)
        if entity is None:
            entity = strip_titles_and_articles(normalize_name(raw_name))
        if not entity:
            continue
        clause = match.group("clause").lower()
        tail = line[match.end() :].lower()
        for token in re.findall(r"[a-z]+", f"{clause} {tail}"):
            if token in ROLE_NOUNS:
                roles.register(token, entity)


def iter_scene_lines(
    scene: SceneBlock,
) -> list[tuple[str, str]]:
    """Return ``(kind, text)`` tuples for a scene's non-empty lines.

    Kinds are ``cue``, ``action``, or ``dialogue``. Mirrors fountain parsing
    rules used elsewhere in the engine.
    """
    rows: list[tuple[str, str]] = []
    in_dialogue = False
    for line in scene.raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            in_dialogue = False
            continue
        if _is_transition(stripped):
            in_dialogue = False
            continue
        if _is_character_cue(stripped):
            in_dialogue = True
            rows.append(("cue", re.sub(r"\([^)]*\)", "", stripped)))
            continue
        if in_dialogue and (stripped.startswith("(") or not stripped.isupper()):
            rows.append(("dialogue", stripped))
            continue
        in_dialogue = False
        rows.append(("action", stripped))
    return rows


def build_role_registry(
    scenes: list[SceneBlock], registry: EntityRegistry
) -> RoleRegistry:
    """Scan all scenes and index role nouns from character introductions."""
    roles = RoleRegistry()
    for scene in scenes:
        for kind, text in iter_scene_lines(scene):
            if kind in ("action", "dialogue"):
                index_roles_from_line(text, registry, roles)
    return roles


def scene_character_ids(
    scene: SceneBlock, registry: EntityRegistry
) -> set[str]:
    """Return canonical ids for characters present in a scene."""
    ids: set[str] = set()
    for character in scene.characters:
        if character.upper() in NON_NAME_TOKENS or character == "THE END":
            continue
        resolved = registry.resolve(character)
        ids.add(resolved if resolved else character)
    return ids
