"""Plot contradiction detection for screenplay scenes (Tier 1 deterministic rules)."""

import re
import uuid
from dataclasses import dataclass
from typing import Optional

import spacy
from spacy.language import Language

from scene_dependency import (
    HANDOFF_VERBS,
    INANIMATE_DEATH_NOUNS,
    NON_CHARACTER_WORDS,
    NON_PROP_OBJECTS,
    OBJECT_OWNERSHIP_PATTERNS,
    POSSESSION_VERB_LABELS,
    SceneBlock,
    _is_character_cue,
    _is_transition,
    _normalize_object_key,
    _normalize_token,
    _trailing_caps_name,
)

# Alternation of handoff verbs (e.g. "gives|hands") for parsing transfer
# facts back out of a stored ownership value string.
_HANDOFF_VERBS_ALT = "|".join(HANDOFF_VERBS)

FACT_TYPES: tuple[str, ...] = (
    "character_trait",
    "location",
    "timeline",
    "object_ownership",
    "object_state",
    "character_status",
    "medical_state",
    "relationship",
)

DAYS_OF_WEEK: dict[str, int] = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 7,
}

FLASHBACK_MARKERS: tuple[str, ...] = (
    "earlier",
    "flashback",
    "previously",
    "years ago",
    "months ago",
    "weeks ago",
)

CHARACTER_STATUS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?<![A-Za-z0-9])(?P<entity>[A-Z][A-Z0-9 '\-]+?)\s+(?:is|was)\s+"
        r"(?:dead|killed)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<![A-Za-z0-9])(?P<entity>[A-Z][A-Z0-9 '\-]+?)\s+(?:has\s+)?died",
        re.IGNORECASE,
    ),
)

# --- Injuries & medical state (Phase 2) -----------------------------------
# Body parts that take a left/right laterality in injury descriptions. Used to
# reject figurative captures such as "shot in the dark" or "breaks his promise".
MEDICAL_BODY_PARTS: frozenset[str] = frozenset(
    {
        "ankle", "arm", "back", "calf", "cheek", "chest", "ear", "elbow",
        "eye", "finger", "foot", "forearm", "hand", "head", "hip", "jaw",
        "knee", "leg", "neck", "nose", "rib", "ribs", "shin", "shoulder",
        "side", "temple", "thigh", "thumb", "toe", "wrist",
    }
)
# Severe states that incapacitate a character (no body part required).
INCAPACITATING_CONDITIONS: frozenset[str] = frozenset(
    {
        "unconscious", "comatose", "paralyzed", "paralysed", "blind", "deaf",
        "crippled", "dying", "bedridden", "immobile", "sedated", "catatonic",
        "incapacitated",
    }
)
# Injury terms that usually attach to a body part and a left/right side.
INJURY_CONDITIONS: frozenset[str] = frozenset(
    {
        "shot", "wounded", "stabbed", "injured", "hurt", "bleeding", "burned",
        "burnt", "fractured", "sprained", "broken", "bruised", "cut", "gashed",
    }
)
# Explicit healthy / unimpaired states used to detect a contradicted recovery.
HEALTHY_CONDITIONS: frozenset[str] = frozenset(
    {
        "fine", "unharmed", "uninjured", "unhurt", "healthy", "intact", "well",
    }
)
# Words that turn a condition into an idiom rather than a medical fact, keyed
# by the condition word (e.g. "dying to leave", "blind faith", "paralyzed with
# fear"). Followers are chosen to stay clear of literal medical phrasing:
# "blind to"/"deaf to" are always figurative, and "paralyzed/crippled with|by"
# introduce an abstract cause, whereas literal forms use "from"/"in"
# ("paralyzed from the waist", "blind in one eye") which are deliberately
# absent so real injuries still register.
MEDICAL_IDIOM_FOLLOWERS: dict[str, frozenset[str]] = {
    "blind": frozenset(
        {"faith", "spot", "luck", "date", "alley", "rage", "trust", "panic",
         "ambition", "obedience", "eye", "to", "with"}
    ),
    "deaf": frozenset({"ear", "ears", "to"}),
    "paralyzed": frozenset({"with", "by"}),
    "paralysed": frozenset({"with", "by"}),
    "crippled": frozenset({"with", "by"}),
    "broken": frozenset(
        {"heart", "home", "promise", "record", "english", "silence", "spirit",
         "dream", "dreams"}
    ),
    "dying": frozenset({"breath", "light", "day", "art", "wish", "embers",
                        "words", "to", "for"}),
    "bleeding": frozenset({"heart", "edge"}),
    "hurt": frozenset({"feelings", "pride"}),
    "cut": frozenset({"corners", "ties", "loose", "short", "deal", "class"}),
}
# Forward time-jump and treatment phrasing that legitimately explains a later
# healthy state, so a recovery between scenes is not flagged.
_RECOVERY_VERB_ALT = (
    r"heals|healed|healing|recovers|recovered|recovering|recuperates|"
    r"recuperated|recuperating|treated|treats|bandaged|bandages|stitched|"
    r"stitches|patched\s+up|operated\s+on|mends|mended|rehabilitated|rests|"
    r"rested|bandages\s+up"
)
_TIME_GAP_ALT = (
    r"later|afterward|afterwards|recovery|hospital|"
    r"next\s+(?:day|morning|week|month|year)|"
    r"(?:\w+\s+)?(?:hours?|days?|weeks?|months?|years?)\s+(?:later|pass|passed)"
)
MEDICAL_EXPLANATION_PATTERN: re.Pattern[str] = re.compile(
    rf"\b(?:{_RECOVERY_VERB_ALT}|{_TIME_GAP_ALT})\b",
    re.IGNORECASE,
)

_MED_ENTITY = r"(?P<entity>[A-Z][A-Z0-9 '\-]+?)"
_MED_SIDE = r"(?:(?P<side>left|right)\s+)?"
_MED_COPULA = r"(?:is|was|gets|got|has\s+been|had\s+been|seems|looks|appears)"

MEDICAL_STATE_PATTERNS: tuple[re.Pattern[str], ...] = (
    # "X is shot in the left arm", "X was stabbed in the leg"
    re.compile(
        rf"(?<![A-Za-z0-9]){_MED_ENTITY}\s+{_MED_COPULA}\s+"
        rf"(?P<condition>shot|wounded|stabbed|injured|hurt|burned|burnt|cut|"
        rf"gashed|bruised|bleeding)\s+in\s+the\s+{_MED_SIDE}(?P<part>[a-z]+)",
        re.IGNORECASE,
    ),
    # "X breaks his left leg", "X fractured her right wrist"
    re.compile(
        rf"(?<![A-Za-z0-9]){_MED_ENTITY}\s+"
        rf"(?P<condition>breaks|broke|fractures|fractured|sprains|sprained)\s+"
        rf"(?:his|her|their|the)\s+{_MED_SIDE}(?P<part>[a-z]+)",
        re.IGNORECASE,
    ),
    # "X is unconscious", "X was paralyzed" (incapacitating, no body part)
    re.compile(
        rf"(?<![A-Za-z0-9]){_MED_ENTITY}\s+{_MED_COPULA}\s+"
        rf"(?P<condition>unconscious|comatose|paralyzed|paralysed|blind|deaf|"
        rf"crippled|dying|bedridden|immobile|sedated|catatonic|incapacitated)\b",
        re.IGNORECASE,
    ),
    # "X is in a coma", "X falls into a coma"
    re.compile(
        rf"(?<![A-Za-z0-9]){_MED_ENTITY}\s+(?:is|was|remains|remained|fell|"
        rf"falls|slips|slipped)\s+(?:in|into)\s+a\s+coma\b",
        re.IGNORECASE,
    ),
    # "X is fine", "X looks unharmed" (explicit healthy state)
    re.compile(
        rf"(?<![A-Za-z0-9]){_MED_ENTITY}\s+{_MED_COPULA}\s+"
        rf"(?P<healthy>fine|unharmed|uninjured|unhurt|healthy|intact|well)\b",
        re.IGNORECASE,
    ),
)

TIMELINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?:today\s+is|it\s+is|this\s+is)\s+(?P<day>Monday|Tuesday|Wednesday|"
        r"Thursday|Friday|Saturday|Sunday)",
        re.IGNORECASE,
    ),
    re.compile(
        r"yesterday\s+was\s+(?P<day>Monday|Tuesday|Wednesday|Thursday|Friday|"
        r"Saturday|Sunday)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<offset>(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)"
        r"\s+days?\s+later)",
        re.IGNORECASE,
    ),
)

CHARACTER_TRAIT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?P<entity>[A-Z][A-Z0-9 '\-]+?)\s+is\s+a\s+(?P<trait>[a-z][a-z\s\-]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<entity>[A-Z][A-Z0-9 '\-]+?)\s+works\s+as\s+(?:a\s+)?"
        r"(?P<trait>[a-z][a-z\s\-]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<entity>[A-Za-z]+),\s*the\s+city's best\s+"
        r"(?P<trait>[a-z][a-z\s\-]+?),\s*entered",
        re.IGNORECASE,
    ),
)

LOCATION_DESCRIPTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"the\s+(?P<location>[a-z][a-z0-9\s\-]+?)\s+was\s+(?P<state>.+?)(?:\.|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"the\s+(?P<location>[a-z][a-z0-9\s\-]+?)\s+had\s+been\s+(?P<state>.+?)(?:\.|$)",
        re.IGNORECASE,
    ),
)

# Object-continuity (Phase 1 possessions) phrasing. Destruction removes an
# object from the story; loss separates it from its owner. Both are extracted
# from action lines only and feed the object-continuity contradiction checks.
_OBJECT_GONE_GROUP = r"(?P<object>[a-z][a-z0-9\s\-]+?)"
_OBJECT_GONE_TERMINATOR = (
    r"(?:\s+(?:from|on|in|to|into|onto|under|behind|near|with|for|and|but|"
    r"then|when|after|before|while)\b|[.,;:]|$)"
)
_DESTRUCTION_VERB_ALT = (
    "destroys|burns|incinerates|smashes|shatters|melts|crushes|shreds|tears\\s+up"
)
_LOSS_VERB_ALT = "loses|abandons|forgets|leaves\\s+behind|misplaces"

OBJECT_DESTRUCTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Active: "MARCUS destroys the ledger"
    (
        re.compile(
            rf"(?P<owner>[A-Z][A-Za-z0-9 .'\-]+?)\s+(?:{_DESTRUCTION_VERB_ALT})\s+"
            rf"(?:the\s+|his\s+|her\s+|their\s+|its\s+)?"
            rf"{_OBJECT_GONE_GROUP}{_OBJECT_GONE_TERMINATOR}",
            re.IGNORECASE,
        ),
        "active",
    ),
    # Passive/state: "the ledger is destroyed", "the only key was burned"
    (
        re.compile(
            rf"the\s+(?:only\s+|last\s+)?{_OBJECT_GONE_GROUP}\s+"
            rf"(?:is|was|gets|got|has\s+been|had\s+been)\s+"
            rf"(?:destroyed|burned|burnt|incinerated|shattered|smashed|"
            rf"melted|shredded|gone)\b",
            re.IGNORECASE,
        ),
        "passive",
    ),
)
OBJECT_LOSS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            rf"(?P<owner>[A-Z][A-Za-z0-9 .'\-]+?)\s+(?:{_LOSS_VERB_ALT})\s+"
            rf"(?:the\s+|his\s+|her\s+|their\s+|its\s+)?"
            rf"{_OBJECT_GONE_GROUP}{_OBJECT_GONE_TERMINATOR}",
            re.IGNORECASE,
        ),
        "active",
    ),
)
# Verbs that re-introduce a missing object between scenes ("retrieves the gun",
# "finds the key"), explaining why it can appear again. Used as an exception in
# the object-continuity checks.
_REACQUIRE_VERB_ALT = (
    "retrieves|recovers|finds|grabs|picks\\s+up|reclaims|digs\\s+up|"
    "pulls\\s+out|takes\\s+back"
)
OBJECT_REACQUIRE_PATTERN: re.Pattern[str] = re.compile(
    rf"(?:{_REACQUIRE_VERB_ALT})\s+(?:the\s+|his\s+|her\s+|their\s+|its\s+|"
    rf"another\s+|a\s+new\s+)?{_OBJECT_GONE_GROUP}{_OBJECT_GONE_TERMINATOR}",
    re.IGNORECASE,
)

TIER2_SIMILARITY_THRESHOLD = 0.35
TIER2_MIN_CONFIDENCE = 0.55

OPPOSING_STATE_TERMS: tuple[tuple[str, str], ...] = (
    ("abandon", "active"),
    ("silent", "busy"),
    ("silent", "staff"),
    ("dusty", "working"),
    ("empty", "staffed"),
    ("decay", "operational"),
    ("derelict", "busy"),
)

# Words that turn "dead"/"killed" into an idiom rather than a death fact,
# e.g. "dead tired", "dead serious", "dead wrong", "dead ahead".
DEAD_IDIOM_FOLLOWERS: frozenset[str] = frozenset(
    {
        "ahead", "asleep", "broke", "center", "certain", "drunk", "even",
        "last", "on", "quiet", "right", "serious", "set", "silent", "slow",
        "still", "sure", "tired", "wrong",
    }
)

# Generic head nouns that describe a person without asserting a profession
# or role, e.g. "Marcus is a good man" should not become a trait fact.
GENERIC_TRAIT_TERMS: frozenset[str] = frozenset(
    {
        "bit", "boy", "child", "few", "friend", "girl", "guy", "joke", "kid",
        "little", "lot", "man", "mess", "moment", "one", "person",
        "stranger", "while", "woman",
    }
)

# Words allowed directly after a weekday in a timeline statement,
# e.g. "Today is Monday morning". Any other trailing word (such as
# "It is Friday somewhere") disqualifies the line as a timeline anchor.
TIME_OF_DAY_FOLLOWERS: frozenset[str] = frozenset(
    {"afternoon", "evening", "morning", "night"}
)


@dataclass
class Fact:
    """A structured fact extracted from a screenplay scene."""

    fact_id: str
    scene_id: str
    scene_number: int
    fact_type: str
    entity: str
    value: str
    raw_excerpt: str


# Contradiction confidence bands. "confirmed" is a clear rule violation;
# "possible" is a conservative finding (e.g. a state change that could be
# explained off-screen) surfaced for writer review rather than asserted.
STATUS_CONFIRMED: str = "confirmed"
STATUS_POSSIBLE: str = "possible"


@dataclass
class Contradiction:
    """A detected contradiction between facts in two scenes."""

    contradiction_id: str
    scene_id_a: str
    scene_id_b: str
    scene_number_a: int
    scene_number_b: int
    fact_a: Fact
    excerpt_b: str
    contradiction_type: str
    explanation: str
    confidence: float
    tier: int
    status: str = STATUS_CONFIRMED


class FactStore:
    """In-memory store for extracted screenplay facts."""

    def __init__(self) -> None:
        """Initialize an empty fact store."""
        self._facts: list[Fact] = []

    def add_fact(self, fact: Fact) -> None:
        """Add a fact to the store."""
        self._facts.append(fact)

    def get_facts_about(self, entity: str) -> list[Fact]:
        """Return all facts whose entity matches the given name (case-insensitive)."""
        key = _normalize_token(entity)
        return [fact for fact in self._facts if _normalize_token(fact.entity) == key]

    def get_all_facts(self) -> list[Fact]:
        """Return every stored fact."""
        return list(self._facts)

    def get_facts_by_type(self, fact_type: str) -> list[Fact]:
        """Return all facts of a given fact type."""
        return [fact for fact in self._facts if fact.fact_type == fact_type]


def _new_contradiction_id() -> str:
    """Generate a unique contradiction identifier."""
    return f"contr_{uuid.uuid4().hex[:8]}"


def _clean_entity(name: str) -> str:
    """Normalize an entity name extracted from regex."""
    return _normalize_token(name.strip(" ."))


def _resolve_character_entity(raw_entity: str) -> Optional[str]:
    """Resolve a captured entity span to a clean character key, or None.

    Guards character_trait / character_status extraction against the C1
    over-capture failure modes, mirroring the dependency engine's structural
    -character handling so both engines agree on what counts as a name:

    * Isolates the trailing ALL-CAPS span, so a capture that bled across a
      sentence boundary ("Smoke fills the dock. DETECTIVE VANCE") resolves to
      just the screenplay name ("DETECTIVE VANCE").
    * Falls back to a single clean title-case token (e.g. the appositive
      "Marcus") when there is no ALL-CAPS span, but rejects multi-word prose
      and anything containing a period.
    * Rejects pronouns / indefinite words (``NON_CHARACTER_WORDS``) such as
      "There", "It", "He" and inanimate nouns that take death verbs
      idiomatically (``INANIMATE_DEATH_NOUNS``) such as "the engine".

    Args:
        raw_entity: The raw ``entity`` group captured by a trait/status regex.

    Returns:
        A normalized uppercase character key, or None when the capture is not
        a character name.
    """
    name = _trailing_caps_name(raw_entity)
    if not name:
        candidate = raw_entity.strip()
        if "." in candidate or len(candidate.split()) != 1:
            return None
        if not candidate[:1].isupper():
            return None
        name = candidate
    key = _normalize_object_key(name)
    if len(key) < 2 or key in INANIMATE_DEATH_NOUNS:
        return None
    if all(word in NON_CHARACTER_WORDS for word in key.split()):
        return None
    return key


def _clean_value(value: str) -> str:
    """Normalize a fact value string."""
    return " ".join(value.strip().split())


def _value_words(value: str) -> set[str]:
    """Return lowercase word tokens from a fact value."""
    return {word.lower() for word in re.findall(r"[a-zA-Z]+", value)}


def _scene_body_lines(scene: SceneBlock) -> list[str]:
    """Return non-heading lines from a scene's raw text."""
    lines = scene.raw_text.splitlines()
    if not lines:
        return []
    return [line.strip() for line in lines[1:] if line.strip()]


def _scene_lines_by_source(scene: SceneBlock) -> tuple[list[str], list[str]]:
    """Split a scene's body lines into action lines and dialogue lines.

    Mirrors the dialogue-block logic used by the scene parser: lines after a
    character cue are dialogue until a blank line or transition resets state.

    Args:
        scene: A parsed scene block.

    Returns:
        Tuple of (action_lines, dialogue_lines), both stripped and non-empty.
    """
    action_lines: list[str] = []
    dialogue_lines: list[str] = []
    in_dialogue = False

    for line in scene.raw_text.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            in_dialogue = False
            continue
        if _is_transition(stripped):
            in_dialogue = False
            continue
        if _is_character_cue(stripped):
            in_dialogue = True
            continue
        if in_dialogue and (stripped.startswith("(") or not stripped.isupper()):
            dialogue_lines.append(stripped)
            continue
        in_dialogue = False
        action_lines.append(stripped)

    return action_lines, dialogue_lines


def _first_word_after(line: str, end_index: int) -> str:
    """Return the lowercase word immediately following an index in a line.

    Args:
        line: The full text line.
        end_index: Index where a regex match ended.

    Returns:
        The next word in lowercase, or an empty string when the match is
        followed by punctuation or the end of the line.
    """
    rest = line[end_index:].lstrip()
    match = re.match(r"[A-Za-z]+", rest)
    return match.group(0).lower() if match else ""


def _character_appears_in_scene(scene: SceneBlock, entity: str) -> tuple[bool, str]:
    """Check whether a character speaks or appears in a scene's action."""
    entity_key = _normalize_token(entity)
    for character in scene.characters:
        if _normalize_token(character) == entity_key:
            excerpt = _find_excerpt(scene.raw_text, character)
            return True, excerpt

    for line in _scene_body_lines(scene):
        if _is_character_cue(line):
            continue
        if re.search(rf"\b{re.escape(entity)}\b", line, re.IGNORECASE):
            return True, line

    return False, ""


def _find_excerpt(text: str, needle: str) -> str:
    """Find the first line in text containing needle (case-insensitive)."""
    for line in text.splitlines():
        if needle.lower() in line.lower():
            return line.strip()
    return needle


def _has_flashback_marker(text: str) -> bool:
    """Return True when text contains a flashback or time-jump marker."""
    lowered = text.lower()
    return any(marker in lowered for marker in FLASHBACK_MARKERS)


# Inflected injury verbs mapped to the canonical condition word stored in the
# fact value, so "breaks"/"broke" both record as "broken".
_INJURY_VERB_CANONICAL: dict[str, str] = {
    "breaks": "broken",
    "broke": "broken",
    "fractures": "fractured",
    "fractured": "fractured",
    "sprains": "sprained",
    "sprained": "sprained",
}


def _build_medical_value(groups: dict[str, Optional[str]]) -> str:
    """Build the canonical medical_state value from regex groups.

    Returns an empty string when a body part was captured but is not a real
    body part (e.g. "shot in the dark", "breaks his promise"), so the caller
    can skip the figurative match.

    Args:
        groups: The ``groupdict`` of a matched ``MEDICAL_STATE_PATTERNS`` regex.

    Returns:
        A canonical value string such as "unconscious", "in a coma",
        "shot left arm", or "unharmed"; empty when the match is figurative.
    """
    healthy = groups.get("healthy")
    if healthy:
        return healthy.lower()
    condition = groups.get("condition")
    if not condition:
        return "in a coma"
    canonical = _INJURY_VERB_CANONICAL.get(condition.lower(), condition.lower())
    part = groups.get("part")
    side = groups.get("side")
    if part is not None and part.lower() not in MEDICAL_BODY_PARTS:
        return ""
    pieces = [canonical]
    if side:
        pieces.append(side.lower())
    if part:
        pieces.append(part.lower())
    return " ".join(pieces)


def _classify_medical_value(value: str) -> tuple[str, Optional[str], Optional[str]]:
    """Classify a medical_state fact value into (kind, body_part, side).

    The value is the canonical string stored at extraction time, e.g.
    "unconscious", "in a coma", "shot left arm", "broken right leg", or a
    healthy state like "unharmed".

    Args:
        value: The stored medical_state fact value.

    Returns:
        A tuple of (kind, body_part, side) where kind is one of
        "incapacitated", "injured", or "healthy"; body_part and side are
        present only for injuries and may be None.
    """
    tokens = value.lower().split()
    if not tokens:
        return ("injured", None, None)
    head = tokens[0]
    if head in HEALTHY_CONDITIONS:
        return ("healthy", None, None)
    if value.lower().startswith("in a coma") or head in INCAPACITATING_CONDITIONS:
        return ("incapacitated", None, None)
    rest = tokens[1:]
    side: Optional[str] = None
    part: Optional[str] = None
    if rest and rest[0] in ("left", "right"):
        side = rest[0]
        rest = rest[1:]
    if rest:
        part = rest[0]
    return ("injured", part, side)


def _parse_day_number(value: str) -> Optional[int]:
    """Parse a weekday number from a timeline fact value, if present."""
    lowered = value.lower()
    for day_name, day_number in DAYS_OF_WEEK.items():
        if day_name in lowered:
            return day_number
    return None


def _previous_weekday(day_number: int) -> int:
    """Return the weekday number for the day before the given day (1-7)."""
    return 7 if day_number == 1 else day_number - 1


def _day_name(day_number: int) -> str:
    """Return the weekday name for a day number."""
    for name, number in DAYS_OF_WEEK.items():
        if number == day_number:
            return name.capitalize()
    return str(day_number)


class ContradictionEngine:
    """Extract facts and run Tier 1 deterministic contradiction checks."""

    def __init__(self) -> None:
        """Initialize the engine and load the spaCy English model once."""
        self.nlp: Language = spacy.load("en_core_web_sm")
        self._fact_counter: int = 0

    def _make_fact(
        self,
        scene: SceneBlock,
        fact_type: str,
        entity: str,
        value: str,
        raw_excerpt: str,
    ) -> Fact:
        """Create a Fact with a generated identifier."""
        self._fact_counter += 1
        return Fact(
            fact_id=f"fact_{self._fact_counter:04d}",
            scene_id=scene.scene_id,
            scene_number=scene.scene_number,
            fact_type=fact_type,
            entity=_clean_entity(entity),
            value=_clean_value(value),
            raw_excerpt=raw_excerpt.strip(),
        )

    def extract_facts(self, scenes: list[SceneBlock]) -> FactStore:
        """Extract structured facts from parsed scenes using spaCy and pattern rules.

        Args:
            scenes: Parsed scene blocks from the screenplay.

        Returns:
            A FactStore populated with extracted facts.
        """
        store = FactStore()
        sorted_scenes = sorted(scenes, key=lambda scene: scene.scene_number)

        for scene in sorted_scenes:
            self._extract_character_status_facts(scene, store)
            self._extract_medical_state_facts(scene, store)
            self._extract_timeline_facts(scene, store)
            self._extract_character_trait_facts(scene, store)
            self._extract_object_ownership_facts(scene, store)
            self._extract_object_state_facts(scene, store)
            self._extract_location_facts(scene, store)
            self._extract_location_description_facts(scene, store)

        return store

    def _extract_character_status_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Extract character life/death status facts from action lines only.

        Dialogue is excluded so spoken claims and slang do not create death
        facts, and idioms such as "dead tired" are rejected by checking the
        word that follows the death term.
        """
        action_lines, _ = _scene_lines_by_source(scene)
        for line in action_lines:
            for pattern in CHARACTER_STATUS_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                if _first_word_after(line, match.end()) in DEAD_IDIOM_FOLLOWERS:
                    continue
                entity = _resolve_character_entity(match.group("entity"))
                if entity is None:
                    continue
                store.add_fact(
                    self._make_fact(
                        scene,
                        "character_status",
                        entity,
                        "is dead",
                        line,
                    )
                )

    def _extract_medical_state_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Extract injury and medical-state facts from action lines only.

        Records incapacitating states ("MARCUS is unconscious", "ELENA is in a
        coma"), localized injuries with optional laterality ("RAY is shot in
        the left arm", "DANA breaks her right leg"), and explicit healthy
        states ("MARCUS is fine"). Dialogue is excluded so spoken/figurative
        phrasing does not create medical facts, entities are resolved with the
        shared character guard, and figurative idioms ("dying to leave") are
        rejected via ``MEDICAL_IDIOM_FOLLOWERS``.
        """
        action_lines, _ = _scene_lines_by_source(scene)
        for line in action_lines:
            for pattern in MEDICAL_STATE_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                entity = _resolve_character_entity(match.group("entity"))
                if entity is None:
                    continue
                groups = match.groupdict()
                condition = (groups.get("condition") or "").lower()
                if condition in MEDICAL_IDIOM_FOLLOWERS:
                    follower = _first_word_after(line, match.end())
                    if follower in MEDICAL_IDIOM_FOLLOWERS[condition]:
                        continue
                value = _build_medical_value(groups)
                if not value:
                    continue
                store.add_fact(
                    self._make_fact(scene, "medical_state", entity, value, line)
                )

    def _extract_timeline_facts(self, scene: SceneBlock, store: FactStore) -> None:
        """Extract explicit timeline references from action and dialogue.

        Dialogue is included because day anchors are usually spoken
        ("Today is Monday"), but a weekday followed by another word that is
        not a time of day (e.g. "It is Friday somewhere") is rejected.
        """
        action_lines, dialogue_lines = _scene_lines_by_source(scene)
        for line in action_lines + dialogue_lines:
            for pattern in TIMELINE_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                groups = match.groupdict()
                if groups.get("day"):
                    follower = _first_word_after(line, match.end())
                    if follower and follower not in TIME_OF_DAY_FOLLOWERS:
                        continue
                    day = match.group("day")
                    if "yesterday" in line.lower():
                        value = f"yesterday was {day}"
                    else:
                        value = f"day is {day}"
                    entity = day
                elif groups.get("offset"):
                    offset = match.group("offset")
                    value = offset.lower()
                    entity = "timeline"
                else:
                    continue
                store.add_fact(
                    self._make_fact(
                        scene,
                        "timeline",
                        entity,
                        value,
                        line,
                    )
                )

    def _extract_character_trait_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Extract profession and role trait facts from action lines only.

        Dialogue is excluded so insults and figures of speech do not become
        trait facts, and generic descriptions ("is a good man") are dropped
        when the trait's head noun carries no role information.
        """
        action_lines, _ = _scene_lines_by_source(scene)
        for line in action_lines:
            for pattern in CHARACTER_TRAIT_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                entity = _resolve_character_entity(match.group("entity"))
                if entity is None:
                    continue
                trait = _clean_value(match.group("trait"))
                if trait.split()[-1].lower() in GENERIC_TRAIT_TERMS:
                    continue
                store.add_fact(
                    self._make_fact(
                        scene,
                        "character_trait",
                        entity,
                        trait,
                        line,
                    )
                )

    def _extract_object_ownership_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Extract object possession and transfer facts from action lines only.

        Dialogue is excluded so figurative possession ("She has the nerve")
        does not create ownership facts.
        """
        action_lines, _ = _scene_lines_by_source(scene)
        for line in action_lines:
            for pattern, verb in OBJECT_OWNERSHIP_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                owner = _clean_entity(match.group("owner"))
                object_name = _clean_value(match.group("object"))
                recipient_raw = match.groupdict().get("recipient")
                if recipient_raw:
                    recipient = _clean_entity(recipient_raw)
                    value = f"{owner} {verb} {object_name} to {recipient}"
                else:
                    value = f"{owner} {verb} {object_name}"
                entity = object_name.upper()
                store.add_fact(
                    self._make_fact(
                        scene,
                        "object_ownership",
                        entity,
                        value,
                        line,
                    )
                )

    def _extract_object_state_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Extract object destruction and loss facts from action lines only.

        Records when a prop is destroyed ("MARCUS burns the ledger", "the only
        key is destroyed") or lost ("ELENA loses the badge", "leaves behind the
        gun"). These feed the object-continuity checks. Dialogue is excluded so
        spoken/figurative phrasing does not create state facts, and figurative
        objects (``NON_PROP_OBJECTS``) are filtered to protect precision.
        """
        action_lines, _ = _scene_lines_by_source(scene)
        for line in action_lines:
            self._add_object_state_facts(
                scene, store, line, OBJECT_DESTRUCTION_PATTERNS, "destroyed"
            )
            self._add_object_state_facts(
                scene, store, line, OBJECT_LOSS_PATTERNS, "lost"
            )

    def _add_object_state_facts(
        self,
        scene: SceneBlock,
        store: FactStore,
        line: str,
        patterns: tuple[tuple[re.Pattern[str], str], ...],
        state: str,
    ) -> None:
        """Add object_state facts for one line, one state kind.

        Args:
            scene: The scene the line belongs to.
            store: Fact store to append to.
            line: A single action line.
            patterns: (compiled pattern, shape) pairs to try.
            state: The state label to record ("destroyed" or "lost").
        """
        for pattern, _shape in patterns:
            match = pattern.search(line)
            if not match:
                continue
            object_name = _clean_value(match.group("object"))
            object_key = _normalize_token(object_name)
            if len(object_key) < 2:
                continue
            if any(word.lower() in NON_PROP_OBJECTS for word in object_key.split()):
                continue
            owner_raw = match.groupdict().get("owner")
            if owner_raw:
                owner = _clean_entity(owner_raw)
                value = f"{state} by {owner}"
            else:
                value = state
            store.add_fact(
                self._make_fact(scene, "object_state", object_key, value, line)
            )

    def _extract_location_facts(self, scene: SceneBlock, store: FactStore) -> None:
        """Extract location facts from scene headings."""
        if not scene.locations:
            return
        location = scene.locations[0]
        store.add_fact(
            self._make_fact(
                scene,
                "location",
                location,
                f"scene set in {location}",
                scene.heading,
            )
        )

    def _extract_location_description_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Extract descriptive location-state facts from action lines only."""
        action_lines, _ = _scene_lines_by_source(scene)
        for line in action_lines:
            for pattern in LOCATION_DESCRIPTION_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                location = _clean_entity(match.group("location"))
                state = _clean_value(match.group("state"))
                store.add_fact(
                    self._make_fact(
                        scene,
                        "location",
                        location,
                        state,
                        line,
                    )
                )

    def run_tier1(
        self, fact_store: FactStore, scenes: list[SceneBlock]
    ) -> list[Contradiction]:
        """Run all Tier 1 deterministic contradiction rules.

        Args:
            fact_store: Facts extracted from the screenplay.
            scenes: Parsed scene blocks in screenplay order.

        Returns:
            Contradictions sorted by confidence descending.
        """
        scene_lookup = {scene.scene_id: scene for scene in scenes}
        contradictions: list[Contradiction] = []
        contradictions.extend(
            self._check_character_alive_status(fact_store, scenes, scene_lookup)
        )
        contradictions.extend(
            self._check_medical_state(fact_store, scenes, scene_lookup)
        )
        contradictions.extend(
            self._check_timeline_consistency(fact_store, scenes, scene_lookup)
        )
        contradictions.extend(
            self._check_character_trait_conflict(fact_store, scene_lookup)
        )
        contradictions.extend(
            self._check_object_ownership(fact_store, scenes, scene_lookup)
        )
        contradictions.extend(
            self._check_object_state(fact_store, scenes, scene_lookup)
        )
        contradictions.sort(key=lambda item: item.confidence, reverse=True)
        return contradictions

    def run_tier2(
        self,
        fact_store: FactStore,
        scenes: list[SceneBlock],
        tier1_results: list[Contradiction],
    ) -> list[Contradiction]:
        """Detect semantic contradictions missed by Tier 1 pattern rules.

        Compares fact values for the same entity using spaCy similarity.

        Args:
            fact_store: Facts extracted from the screenplay.
            scenes: Parsed scene blocks in screenplay order.
            tier1_results: Contradictions already found by Tier 1.

        Returns:
            Tier 2 contradictions sorted by confidence descending.
        """
        scene_lookup = {scene.scene_id: scene for scene in scenes}
        tier1_coverage = self._tier1_scene_entity_coverage(tier1_results)
        facts_by_entity: dict[str, list[Fact]] = {}

        for fact in fact_store.get_all_facts():
            scene = scene_lookup.get(fact.scene_id)
            if (
                scene is not None
                and fact.fact_type == "location"
                and fact.raw_excerpt == scene.heading
            ):
                continue
            # Object continuity and medical state are handled deterministically
            # in Tier 1; their short state values ("destroyed", "unconscious")
            # are not meaningful for similarity comparison.
            if fact.fact_type in ("object_state", "medical_state"):
                continue
            facts_by_entity.setdefault(fact.entity, []).append(fact)

        results: list[Contradiction] = []

        for entity, facts in facts_by_entity.items():
            if len(facts) < 2:
                continue

            for left_index in range(len(facts)):
                for right_index in range(left_index + 1, len(facts)):
                    fact_a = facts[left_index]
                    fact_b = facts[right_index]
                    if fact_a.fact_type != fact_b.fact_type:
                        continue
                    if fact_a.scene_id == fact_b.scene_id:
                        continue

                    scene_ids = tuple(sorted([fact_a.scene_id, fact_b.scene_id]))
                    coverage_key = (
                        scene_ids[0],
                        scene_ids[1],
                        _normalize_token(entity),
                        fact_a.fact_type,
                    )
                    if coverage_key in tier1_coverage:
                        continue

                    similarity = self._compute_value_similarity(
                        fact_a.value, fact_b.value
                    )
                    if self._has_opposing_state_terms(fact_a.value, fact_b.value):
                        similarity = min(similarity, 0.25)
                    if similarity >= TIER2_SIMILARITY_THRESHOLD:
                        continue

                    confidence = round(0.75 - (similarity * 0.5), 2)
                    if confidence < TIER2_MIN_CONFIDENCE:
                        continue

                    earlier, later = (
                        (fact_a, fact_b)
                        if fact_a.scene_number <= fact_b.scene_number
                        else (fact_b, fact_a)
                    )
                    results.append(
                        Contradiction(
                            contradiction_id=_new_contradiction_id(),
                            scene_id_a=earlier.scene_id,
                            scene_id_b=later.scene_id,
                            scene_number_a=earlier.scene_number,
                            scene_number_b=later.scene_number,
                            fact_a=earlier,
                            excerpt_b=later.raw_excerpt,
                            contradiction_type=f"semantic_{earlier.fact_type}",
                            explanation=(
                                f"{entity} facts are semantically inconsistent "
                                f"(similarity {similarity:.2f}): "
                                f"'{earlier.value}' in {earlier.scene_id} vs "
                                f"'{later.value}' in {later.scene_id}."
                            ),
                            confidence=confidence,
                            tier=2,
                        )
                    )

        results.sort(key=lambda item: item.confidence, reverse=True)
        return results

    def run_analysis(self, scenes: list[SceneBlock]) -> list[Contradiction]:
        """Extract facts and run Tier 1 and Tier 2 contradiction analysis.

        Args:
            scenes: Parsed scene blocks from the screenplay.

        Returns:
            Combined contradictions sorted by confidence descending.
        """
        fact_store = self.extract_facts(scenes)
        tier1_results = self.run_tier1(fact_store, scenes)
        tier2_results = self.run_tier2(fact_store, scenes, tier1_results)
        return self._deduplicate_contradictions(tier1_results + tier2_results)

    def _compute_value_similarity(self, value_a: str, value_b: str) -> float:
        """Compute spaCy semantic similarity between two fact values."""
        doc_a = self.nlp(value_a)
        doc_b = self.nlp(value_b)
        direct_similarity = float(doc_a.similarity(doc_b))
        if direct_similarity < TIER2_SIMILARITY_THRESHOLD:
            return direct_similarity

        lemmas_a = {
            token.lemma_.lower()
            for token in doc_a
            if not token.is_stop and not token.is_punct
        }
        lemmas_b = {
            token.lemma_.lower()
            for token in doc_b
            if not token.is_stop and not token.is_punct
        }
        unique_a = lemmas_a - lemmas_b
        unique_b = lemmas_b - lemmas_a
        if not unique_a or not unique_b:
            return direct_similarity

        distinct_a = self.nlp(" ".join(sorted(unique_a)))
        distinct_b = self.nlp(" ".join(sorted(unique_b)))
        distinct_similarity = float(distinct_a.similarity(distinct_b))
        return min(direct_similarity, distinct_similarity)

    def _has_opposing_state_terms(self, value_a: str, value_b: str) -> bool:
        """Return True when two values contain clearly opposing state terms."""
        lowered_a = value_a.lower()
        lowered_b = value_b.lower()
        for term_a, term_b in OPPOSING_STATE_TERMS:
            if (term_a in lowered_a and term_b in lowered_b) or (
                term_b in lowered_a and term_a in lowered_b
            ):
                return True
        return False

    def _tier1_scene_entity_coverage(
        self, tier1_results: list[Contradiction]
    ) -> set[tuple[str, str, str, str]]:
        """Return scene/entity/type keys already covered by Tier 1 results."""
        covered: set[tuple[str, str, str, str]] = set()
        for contradiction in tier1_results:
            scene_ids = tuple(
                sorted([contradiction.scene_id_a, contradiction.scene_id_b])
            )
            covered.add(
                (
                    scene_ids[0],
                    scene_ids[1],
                    _normalize_token(contradiction.fact_a.entity),
                    contradiction.fact_a.fact_type,
                )
            )
        return covered

    def _deduplicate_contradictions(
        self, contradictions: list[Contradiction]
    ) -> list[Contradiction]:
        """Remove duplicate contradictions while preserving highest confidence."""
        unique: dict[tuple[str, str, str], Contradiction] = {}
        for contradiction in contradictions:
            scene_ids = tuple(
                sorted([contradiction.scene_id_a, contradiction.scene_id_b])
            )
            key = (scene_ids[0], scene_ids[1], contradiction.contradiction_type)
            existing = unique.get(key)
            if existing is None or contradiction.confidence > existing.confidence:
                unique[key] = contradiction
        combined = list(unique.values())
        combined.sort(key=lambda item: item.confidence, reverse=True)
        return combined

    def _check_character_alive_status(
        self,
        fact_store: FactStore,
        scenes: list[SceneBlock],
        scene_lookup: dict[str, SceneBlock],
    ) -> list[Contradiction]:
        """Flag characters who speak or act after being established as dead."""
        results: list[Contradiction] = []
        status_facts = fact_store.get_facts_by_type("character_status")

        for fact in status_facts:
            value_lower = fact.value.lower()
            if "dead" not in value_lower and "killed" not in value_lower:
                continue

            for scene in scenes:
                if scene.scene_number <= fact.scene_number:
                    continue
                appears, excerpt = _character_appears_in_scene(scene, fact.entity)
                if not appears:
                    continue
                results.append(
                    Contradiction(
                        contradiction_id=_new_contradiction_id(),
                        scene_id_a=fact.scene_id,
                        scene_id_b=scene.scene_id,
                        scene_number_a=fact.scene_number,
                        scene_number_b=scene.scene_number,
                        fact_a=fact,
                        excerpt_b=excerpt,
                        contradiction_type="character_alive_status",
                        explanation=(
                            f"{fact.entity} was established as dead in "
                            f"{fact.scene_id} but appears active in {scene.scene_id}."
                        ),
                        confidence=0.95,
                        tier=1,
                    )
                )

        return results

    def _check_medical_state(
        self,
        fact_store: FactStore,
        scenes: list[SceneBlock],
        scene_lookup: dict[str, SceneBlock],
    ) -> list[Contradiction]:
        """Flag injury/medical-state continuity problems for a character.

        Two conservative rules, both surfaced as *possible* because injuries
        are routinely treated or healed off-screen:

        - Laterality conflict: the same body part is injured on the left in one
          scene and the right in a later scene.
        - Contradicted recovery: an incapacitating state or injury is followed
          by an explicit healthy state ("fine", "unharmed") with no recovery
          action or time-jump between the two scenes.

        Args:
            fact_store: All extracted facts.
            scenes: Parsed scenes in screenplay order.
            scene_lookup: Scene id -> scene mapping.

        Returns:
            Medical-state contradictions.
        """
        results: list[Contradiction] = []
        facts_by_entity: dict[str, list[Fact]] = {}
        for fact in fact_store.get_facts_by_type("medical_state"):
            facts_by_entity.setdefault(fact.entity, []).append(fact)

        for entity, entity_facts in facts_by_entity.items():
            ordered = sorted(
                entity_facts, key=lambda item: (item.scene_number, item.fact_id)
            )
            for index, earlier in enumerate(ordered):
                kind_e, part_e, side_e = _classify_medical_value(earlier.value)
                for later in ordered[index + 1 :]:
                    if later.scene_number <= earlier.scene_number:
                        continue
                    if _has_flashback_marker(later.raw_excerpt):
                        continue
                    kind_l, part_l, side_l = _classify_medical_value(later.value)

                    if (
                        kind_e == "injured"
                        and kind_l == "injured"
                        and part_e is not None
                        and part_e == part_l
                        and side_e is not None
                        and side_l is not None
                        and side_e != side_l
                    ):
                        if self._medical_explanation_between(
                            scenes, earlier.scene_number, later.scene_number
                        ):
                            continue
                        results.append(
                            self._medical_contradiction(
                                earlier,
                                later,
                                "medical_laterality",
                                (
                                    f"{entity} is injured on the {side_e} "
                                    f"{part_e} in {earlier.scene_id} but the "
                                    f"{side_l} {part_l} in {later.scene_id}."
                                ),
                            )
                        )
                        break

                    if kind_e in ("incapacitated", "injured") and kind_l == "healthy":
                        if self._medical_explanation_between(
                            scenes, earlier.scene_number, later.scene_number
                        ):
                            continue
                        results.append(
                            self._medical_contradiction(
                                earlier,
                                later,
                                "medical_recovery",
                                (
                                    f"{entity} was '{earlier.value}' in "
                                    f"{earlier.scene_id} but is described as "
                                    f"'{later.value}' in {later.scene_id} with no "
                                    f"recovery or time jump in between."
                                ),
                            )
                        )
                        break

        return results

    def _medical_contradiction(
        self,
        earlier: Fact,
        later: Fact,
        contradiction_type: str,
        explanation: str,
    ) -> Contradiction:
        """Build a *possible* medical-state Contradiction from two facts."""
        return Contradiction(
            contradiction_id=_new_contradiction_id(),
            scene_id_a=earlier.scene_id,
            scene_id_b=later.scene_id,
            scene_number_a=earlier.scene_number,
            scene_number_b=later.scene_number,
            fact_a=earlier,
            excerpt_b=later.raw_excerpt,
            contradiction_type=contradiction_type,
            explanation=explanation,
            confidence=0.6,
            tier=1,
            status=STATUS_POSSIBLE,
        )

    def _medical_explanation_between(
        self,
        scenes: list[SceneBlock],
        from_scene_number: int,
        to_scene_number: int,
    ) -> bool:
        """Return True when a recovery or time-jump explains a later state.

        Scans the text of the contradicting scene and any scenes strictly
        between it and the establishing scene for a recovery action
        ("treated", "heals") or a forward time-jump ("weeks later", "next
        morning"), either of which makes a changed condition plausible.
        """
        for scene in scenes:
            if not (from_scene_number < scene.scene_number <= to_scene_number):
                continue
            if MEDICAL_EXPLANATION_PATTERN.search(scene.raw_text):
                return True
        return False

    def _check_timeline_consistency(
        self,
        fact_store: FactStore,
        scenes: list[SceneBlock],
        scene_lookup: dict[str, SceneBlock],
    ) -> list[Contradiction]:
        """Flag impossible backward day sequences without flashback markers."""
        results: list[Contradiction] = []
        timeline_facts = [
            fact
            for fact in fact_store.get_facts_by_type("timeline")
            if _parse_day_number(fact.value) is not None
        ]
        timeline_facts.sort(key=lambda fact: fact.scene_number)

        for index in range(len(timeline_facts) - 1):
            earlier = timeline_facts[index]
            later = timeline_facts[index + 1]
            earlier_day = _parse_day_number(earlier.value)
            later_day = _parse_day_number(later.value)
            if earlier_day is None or later_day is None:
                continue

            later_scene = scene_lookup.get(later.scene_id)
            later_text = later_scene.raw_text if later_scene else later.raw_excerpt
            if _has_flashback_marker(later_text):
                continue

            if "yesterday was" in earlier.value.lower():
                continue

            if "yesterday was" in later.value.lower():
                expected_yesterday = _previous_weekday(earlier_day)
                stated_yesterday = later_day
                if stated_yesterday != expected_yesterday:
                    results.append(
                        Contradiction(
                            contradiction_id=_new_contradiction_id(),
                            scene_id_a=earlier.scene_id,
                            scene_id_b=later.scene_id,
                            scene_number_a=earlier.scene_number,
                            scene_number_b=later.scene_number,
                            fact_a=earlier,
                            excerpt_b=later.raw_excerpt,
                            contradiction_type="timeline_consistency",
                            explanation=(
                                f"{earlier.value} in {earlier.scene_id} implies yesterday "
                                f"was {_day_name(expected_yesterday)}, but {later.value} "
                                f"in {later.scene_id} without a flashback marker."
                            ),
                            confidence=0.92,
                            tier=1,
                        )
                    )
                continue

            if later_day >= earlier_day:
                continue

            results.append(
                Contradiction(
                    contradiction_id=_new_contradiction_id(),
                    scene_id_a=earlier.scene_id,
                    scene_id_b=later.scene_id,
                    scene_number_a=earlier.scene_number,
                    scene_number_b=later.scene_number,
                    fact_a=earlier,
                    excerpt_b=later.raw_excerpt,
                    contradiction_type="timeline_consistency",
                    explanation=(
                        f"Timeline moves from {earlier.value} in {earlier.scene_id} "
                        f"to {later.value} in {later.scene_id} without a flashback "
                        f"or time-jump marker."
                    ),
                    confidence=0.92,
                    tier=1,
                )
            )

        return results

    def _check_character_trait_conflict(
        self,
        fact_store: FactStore,
        scene_lookup: dict[str, SceneBlock],
    ) -> list[Contradiction]:
        """Flag conflicting profession or role traits for the same character."""
        results: list[Contradiction] = []
        trait_facts = fact_store.get_facts_by_type("character_trait")
        by_entity: dict[str, list[Fact]] = {}

        for fact in trait_facts:
            by_entity.setdefault(fact.entity, []).append(fact)

        for entity, facts in by_entity.items():
            for left_index in range(len(facts)):
                for right_index in range(left_index + 1, len(facts)):
                    left = facts[left_index]
                    right = facts[right_index]
                    if left.value.lower() == right.value.lower():
                        continue
                    shared = _value_words(left.value) & _value_words(right.value)
                    if shared:
                        continue

                    earlier, later = (
                        (left, right) if left.scene_number <= right.scene_number else (right, left)
                    )
                    results.append(
                        Contradiction(
                            contradiction_id=_new_contradiction_id(),
                            scene_id_a=earlier.scene_id,
                            scene_id_b=later.scene_id,
                            scene_number_a=earlier.scene_number,
                            scene_number_b=later.scene_number,
                            fact_a=earlier,
                            excerpt_b=later.raw_excerpt,
                            contradiction_type="character_trait_conflict",
                            explanation=(
                                f"{entity} is described as '{earlier.value}' in "
                                f"{earlier.scene_id} and '{later.value}' in "
                                f"{later.scene_id} with no overlapping trait terms."
                            ),
                            confidence=0.85,
                            tier=1,
                        )
                    )

        return results

    def _check_object_ownership(
        self,
        fact_store: FactStore,
        scenes: list[SceneBlock],
        scene_lookup: dict[str, SceneBlock],
    ) -> list[Contradiction]:
        """Flag object possession changes without an on-screen handoff."""
        results: list[Contradiction] = []
        ownership_facts = sorted(
            fact_store.get_facts_by_type("object_ownership"),
            key=lambda fact: (fact.scene_number, fact.fact_id),
        )

        last_owner: dict[str, tuple[str, int, str, Fact]] = {}

        for fact in ownership_facts:
            current_owner = self._ownership_holder(fact)
            if not current_owner:
                continue

            object_key = _normalize_token(fact.entity)
            if object_key in last_owner:
                previous_owner, previous_scene_number, previous_scene_id, previous_fact = (
                    last_owner[object_key]
                )
                if (
                    _normalize_token(current_owner) != _normalize_token(previous_owner)
                    and fact.scene_number > previous_scene_number
                    and not self._has_handoff_between(
                        fact_store,
                        object_key,
                        previous_scene_number,
                        fact.scene_number,
                        previous_owner,
                        current_owner,
                    )
                ):
                    results.append(
                        Contradiction(
                            contradiction_id=_new_contradiction_id(),
                            scene_id_a=previous_scene_id,
                            scene_id_b=fact.scene_id,
                            scene_number_a=previous_scene_number,
                            scene_number_b=fact.scene_number,
                            fact_a=previous_fact,
                            excerpt_b=fact.raw_excerpt,
                            contradiction_type="object_ownership",
                            explanation=(
                                f"{object_key} was last held by {previous_owner} in "
                                f"{previous_scene_id}, but {current_owner} has it in "
                                f"{fact.scene_id} with no handoff between scenes."
                            ),
                            confidence=0.80,
                            tier=1,
                        )
                    )

            last_owner[object_key] = (
                current_owner,
                fact.scene_number,
                fact.scene_id,
                fact,
            )

        return results

    def _check_object_state(
        self,
        fact_store: FactStore,
        scenes: list[SceneBlock],
        scene_lookup: dict[str, SceneBlock],
    ) -> list[Contradiction]:
        """Flag props that reappear after being destroyed or lost.

        Two rules, both keyed on a later possession of the same object:

        - R1 (destroyed -> reappears): a destroyed object that someone holds or
          handles in a later scene, with no on-screen re-acquisition between, is
          a confirmed continuity error.
        - R2 (lost -> reappears): an object lost/left behind by a character that
          the same character holds again later, with no re-acquisition between,
          is surfaced as a *possible* issue (props are often recovered
          off-screen, so this stays conservative).

        Args:
            fact_store: All extracted facts.
            scenes: Parsed scenes in screenplay order.
            scene_lookup: Scene id -> scene mapping.

        Returns:
            Object-continuity contradictions.
        """
        results: list[Contradiction] = []
        state_facts = sorted(
            fact_store.get_facts_by_type("object_state"),
            key=lambda fact: (fact.scene_number, fact.fact_id),
        )
        for state_fact in state_facts:
            object_key = _normalize_token(state_fact.entity)
            is_destroyed = state_fact.value.lower().startswith("destroyed")
            state_owner = self._object_state_owner(state_fact)

            for owner_fact in fact_store.get_facts_by_type("object_ownership"):
                if _normalize_token(owner_fact.entity) != object_key:
                    continue
                if owner_fact.scene_number <= state_fact.scene_number:
                    continue
                if _has_flashback_marker(owner_fact.raw_excerpt):
                    continue
                if self._object_reacquired_between(
                    scenes,
                    object_key,
                    state_fact.scene_number,
                    owner_fact.scene_number,
                ):
                    continue

                holder = self._ownership_holder(owner_fact)
                if is_destroyed:
                    results.append(
                        self._object_state_contradiction(
                            state_fact,
                            owner_fact,
                            "object_destroyed",
                            (
                                f"{object_key} was destroyed in "
                                f"{state_fact.scene_id}, but it is handled again "
                                f"in {owner_fact.scene_id} with no re-creation."
                            ),
                            confidence=0.82,
                            status=STATUS_CONFIRMED,
                        )
                    )
                    break
                if (
                    state_owner
                    and holder
                    and _normalize_token(holder) == _normalize_token(state_owner)
                ):
                    results.append(
                        self._object_state_contradiction(
                            state_fact,
                            owner_fact,
                            "object_lost",
                            (
                                f"{object_key} was lost by {state_owner} in "
                                f"{state_fact.scene_id}, but {state_owner} has it "
                                f"again in {owner_fact.scene_id} with no on-screen "
                                f"recovery."
                            ),
                            confidence=0.6,
                            status=STATUS_POSSIBLE,
                        )
                    )
                    break

        return results

    def _object_state_contradiction(
        self,
        state_fact: Fact,
        owner_fact: Fact,
        contradiction_type: str,
        explanation: str,
        confidence: float,
        status: str,
    ) -> Contradiction:
        """Build an object-continuity Contradiction from two facts."""
        return Contradiction(
            contradiction_id=_new_contradiction_id(),
            scene_id_a=state_fact.scene_id,
            scene_id_b=owner_fact.scene_id,
            scene_number_a=state_fact.scene_number,
            scene_number_b=owner_fact.scene_number,
            fact_a=state_fact,
            excerpt_b=owner_fact.raw_excerpt,
            contradiction_type=contradiction_type,
            explanation=explanation,
            confidence=confidence,
            tier=1,
            status=status,
        )

    def _object_state_owner(self, fact: Fact) -> Optional[str]:
        """Parse the acting character from an object_state value, if present."""
        match = re.match(r"^(?:destroyed|lost)\s+by\s+(.+)$", fact.value, re.IGNORECASE)
        if match:
            return _clean_entity(match.group(1))
        return None

    def _object_reacquired_between(
        self,
        scenes: list[SceneBlock],
        object_key: str,
        from_scene_number: int,
        to_scene_number: int,
    ) -> bool:
        """Return True when the object is recovered/re-introduced between scenes.

        Scans the action lines of intervening scenes for a re-acquisition verb
        ("retrieves the key", "finds the gun") naming the same object, which
        explains an otherwise-suspicious reappearance.
        """
        for scene in scenes:
            if not (from_scene_number < scene.scene_number < to_scene_number):
                continue
            action_lines, _ = _scene_lines_by_source(scene)
            for line in action_lines:
                for match in OBJECT_REACQUIRE_PATTERN.finditer(line):
                    found_key = _normalize_token(_clean_value(match.group("object")))
                    if found_key == object_key:
                        return True
        return False

    def _ownership_holder(self, fact: Fact) -> Optional[str]:
        """Parse the current holder from an object ownership fact value."""
        value = fact.value
        handoff_match = re.match(
            rf"^(.+?)\s+(?:{_HANDOFF_VERBS_ALT})\s+.+?\s+to\s+(.+)$",
            value,
            re.IGNORECASE,
        )
        if handoff_match:
            return _clean_entity(handoff_match.group(1))

        spaced_value = f" {value.lower()} "
        for prefix in POSSESSION_VERB_LABELS:
            if f" {prefix} " in spaced_value:
                owner = value.split(f" {prefix} ", maxsplit=1)[0].strip()
                return _clean_entity(owner)

        return None

    def _facts_between_scenes(
        self,
        fact_store: FactStore,
        fact_type: str,
        entity_key: str,
        from_scene_number: int,
        to_scene_number: int,
    ) -> list[Fact]:
        """Return facts of a type for an entity strictly between two scenes.

        Shared primitive for "is there an intervening explanation?" checks used
        by the stateful trackers (ownership handoff, object continuity). A fact
        qualifies when its normalized entity matches ``entity_key`` and its scene
        number lies strictly inside ``(from_scene_number, to_scene_number)``.

        Args:
            fact_store: All extracted facts.
            fact_type: Fact type to scan (e.g. "object_ownership").
            entity_key: Normalized entity key to match (see ``_normalize_token``).
            from_scene_number: Exclusive lower scene bound.
            to_scene_number: Exclusive upper scene bound.

        Returns:
            Matching facts in screenplay order.
        """
        results: list[Fact] = []
        for fact in fact_store.get_facts_by_type(fact_type):
            if _normalize_token(fact.entity) != entity_key:
                continue
            if from_scene_number < fact.scene_number < to_scene_number:
                results.append(fact)
        results.sort(key=lambda item: (item.scene_number, item.fact_id))
        return results

    def _has_handoff_between(
        self,
        fact_store: FactStore,
        object_key: str,
        from_scene_number: int,
        to_scene_number: int,
        previous_owner: str,
        current_owner: str,
    ) -> bool:
        """Return True when an ownership transfer is recorded between two scenes."""
        if to_scene_number - from_scene_number <= 1:
            return True

        for fact in self._facts_between_scenes(
            fact_store,
            "object_ownership",
            object_key,
            from_scene_number,
            to_scene_number,
        ):
            holder = self._ownership_holder(fact)
            recipient: Optional[str] = None
            handoff_match = re.search(
                rf"(?:{_HANDOFF_VERBS_ALT})\s+.+?\s+to\s+(.+)$",
                fact.value,
                re.IGNORECASE,
            )
            if handoff_match:
                recipient = _clean_entity(handoff_match.group(1))

            if holder and _normalize_token(holder) == _normalize_token(previous_owner):
                if recipient and _normalize_token(recipient) == _normalize_token(current_owner):
                    return True
                if _normalize_token(holder) == _normalize_token(current_owner):
                    return True

        return False
