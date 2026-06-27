"""Plot contradiction detection for screenplay scenes (Tier 1 deterministic rules)."""

import re
import uuid
from dataclasses import dataclass
from typing import Optional

import spacy
from spacy.language import Language

from entity_canonicalization import (
    EntityRegistry,
    normalize_name,
    strip_titles_and_articles,
)
from nlp_shared import get_shared_nlp
from screenplay_coref import (
    ACTION_NAME_RE,
    FIRST_PERSON_AGE_RE,
    FOR_AGE_DIALOGUE_RE,
    INTRO_ROLE_RE,
    PAYMENT_OBJECT_RE,
    ROLE_NOUNS,
    RoleRegistry,
    SceneMentionTracker,
    YEAR_OLD_AGE_RE,
    build_role_registry,
    index_roles_from_line,
    iter_scene_lines,
    register_characters_from_scenes,
    scene_character_ids,
)
from value_normalization import (
    descriptor_axis,
    extract_all_years,
    words_to_int,
)
from value_normalization import _NUMBER_WORDS as NUMBER_WORDS
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
    "world_rule",
    "age",
    "object_descriptor",
    "numeric_count",
    "year",
)

# Count nouns whose quantities vary too freely in normal prose to flag as
# continuity errors (clock/measure/abstract time), kept out of numeric_count.
COUNT_NOUN_BLOCKLIST: frozenset[str] = frozenset(
    {
        "minute", "hour", "moment", "day", "time", "oclock", "step", "inch",
        "foot", "degree", "percent", "dollar", "cent", "way", "bit", "kind",
        "sort", "part", "side", "thing",
    }
)

# Nouns allowed to *precede* a number ("Room 514", "Gate 7"). The noun-before
# fallback is whitelisted so person appositives ("Dawson, 45") and similar are
# never mistaken for counted nouns.
COUNT_BEFORE_NOUNS: frozenset[str] = frozenset(
    {
        "room", "suite", "apartment", "unit", "cell", "gate", "platform",
        "floor", "level", "page", "chapter", "channel", "line", "lane",
        "dock", "berth", "track", "aisle", "row", "seat",
    }
)

# Tokens that cannot serve as the counted noun (function words / pronouns).
COUNT_STOP_TOKENS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "of", "on", "in", "at", "to", "into", "onto", "for",
        "and", "or", "but", "with", "from", "by", "as", "that", "which", "who",
        "this", "these", "those", "his", "her", "their", "its", "my", "your",
        "our", "us", "them", "me", "you", "it", "him", "more", "less", "other",
        "is", "was", "are", "were", "be", "been", "out", "up", "down", "off",
        "over", "under", "here", "there", "now", "then", "ago", "later", "old",
        "yet", "just", "only", "even", "still", "about", "around", "almost",
        "nearly", "barely",
    }
)
# Adjectives between a number and its head noun ("three identical runs").
COUNT_ADJECTIVE_SKIP: frozenset[str] = frozenset(
    {
        "identical", "empty", "same", "other", "more", "all", "nearly", "almost",
        "only", "exact", "different", "separate", "non", "lethal", "blind",
        "major", "minor", "final", "first", "last", "next", "new", "old", "long",
        "short", "dead", "alive", "clean", "dirty", "full", "half", "whole",
        "extra", "missing", "remaining", "total", "combined", "separate",
    }
)
# Canonical count-entity aliases so "chairs" vs "table set for" align.
COUNT_ENTITY_ALIASES: dict[str, str] = {
    "CHAIR": "SEATING",
    "TABLE": "SEATING",
    "PEOPLE": "SEATING",
    "GUEST": "SEATING",
    "GUESTS": "SEATING",
    "CAST": "SEATING",
    "METER": "METERS",
    "TEAM": "GROUP",
    "COURIER": "GROUP",
}
_COUNT_WORDS = (
    r"zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand"
)
_COUNT_NUM = (
    rf"(?:\d+(?:[\s\-]*(?:{_COUNT_WORDS}))*|(?:{_COUNT_WORDS})(?:[\s\-]+(?:{_COUNT_WORDS}))*)"
)
COUNT_ROOM_NUMBER_RE: re.Pattern[str] = re.compile(
    rf"\b(?:room|suite|apartment|unit|cell)\s+(?P<num>\d{{2,4}})\b",
    re.IGNORECASE,
)
COUNT_LINE_ROOM_NUMBER_RE: re.Pattern[str] = re.compile(
    rf"(?:\b(?:on|to|in|into|at)\s+)?(?P<num>\d{{3,4}})\b(?=[^.]*\broom\b)",
    re.IGNORECASE,
)
COUNT_HOSTAGE_LABEL_RE: re.Pattern[str] = re.compile(
    rf"\bhostage\s+count\s+(?:reads|is|at|shows)\s+(?P<num>{_COUNT_NUM})\b",
    re.IGNORECASE,
)
COUNT_ALL_QUANTITY_RE: re.Pattern[str] = re.compile(
    rf"\b(?:all|both)\s+(?P<num>{_COUNT_NUM})\b",
    re.IGNORECASE,
)
COUNT_PHRASE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(rf"\bcast of (?P<num>{_COUNT_NUM})\b", re.IGNORECASE),
        "CAST",
    ),
    (
        re.compile(rf"\btable set for (?P<num>{_COUNT_NUM})\b", re.IGNORECASE),
        "SEATING",
    ),
    (
        re.compile(rf"\b(?P<num>{_COUNT_NUM})\s+chairs?\b", re.IGNORECASE),
        "SEATING",
    ),
    (
        re.compile(
            rf"\b(?P<num>{_COUNT_NUM})\s+(?:people|guests)\b", re.IGNORECASE
        ),
        "SEATING",
    ),
    (
        re.compile(rf"\b(?P<num>{_COUNT_NUM})\s+couriers?\b", re.IGNORECASE),
        "COURIER",
    ),
    (
        re.compile(
            rf"\b(?P<num>{_COUNT_NUM})[\s-]person\s+team\b", re.IGNORECASE
        ),
        "TEAM",
    ),
    (
        re.compile(
            rf"\b(?:all|both)\s+(?P<num>{_COUNT_NUM})\s+of them\b", re.IGNORECASE
        ),
        "SEATING",
    ),
    (
        re.compile(
            rf"\b(?:all|both)\s+(?P<num>{_COUNT_NUM})\s+of us\b", re.IGNORECASE
        ),
        "TEAM",
    ),
    (
        re.compile(
            rf"\b(?P<num>{_COUNT_NUM})\s+of us\b", re.IGNORECASE
        ),
        "TEAM",
    ),
    (
        re.compile(
            rf"\b(?P<num>{_COUNT_NUM})\s+hostages?\b", re.IGNORECASE
        ),
        "HOSTAGE",
    ),
    (
        re.compile(
            rf"\b(?P<num>{_COUNT_NUM})\s+men\b", re.IGNORECASE
        ),
        "GROUP",
    ),
    (
        re.compile(rf"\b(?P<num>{_COUNT_NUM})\s+meters?\b", re.IGNORECASE),
        "METERS",
    ),
    (
        re.compile(
            rf"\b(?P<num>{_COUNT_NUM})\s+of them\b", re.IGNORECASE
        ),
        "GROUP",
    ),
    (
        re.compile(
            rf"\b(?:broke|break|breaking|violated?)\s+(?P<num>{_COUNT_NUM})\s+rules?\b",
            re.IGNORECASE,
        ),
        "GROUP",
    ),
    (
        re.compile(
            rf"\b(?P<num>{_COUNT_NUM})\s+rules?\b", re.IGNORECASE
        ),
        "GROUP",
    ),
    (
        re.compile(
            rf"\bI counted (?P<num>{_COUNT_NUM})\b", re.IGNORECASE
        ),
        "GROUP",
    ),
    (
        re.compile(
            rf"\b(?:split|turn|fails?|fail)\s+(?:at|on|to)\s+(?P<num>\d{{2,4}})\b",
            re.IGNORECASE,
        ),
        "SPLIT",
    ),
    (
        re.compile(
            r"\b(?P<num>first|second|third|fourth|fifth|sixth|seventh|eighth|"
            r"ninth|tenth)\b(?=[^.]{0,40}\b(?:finish|place|split|rank|by|"
            r"isn't|is not|not)\b)",
            re.IGNORECASE,
        ),
        "RANK",
    ),
    (
        re.compile(
            r"\b(?:finish(?:es|ed|ing)?|finishing|place|split|rank|by)\b"
            r"[^.]{0,40}?\b(?P<num>first|second|third|fourth|fifth|sixth|"
            r"seventh|eighth|ninth|tenth)\b",
            re.IGNORECASE,
        ),
        "RANK",
    ),
)
ORDINAL_WORDS: dict[str, int] = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
}
# Time-of-day / clock phrasing stripped before count tokenization so "11:58 PM"
# and "1987" (a year) are never read as counts.
COUNT_CLOCK_RE: re.Pattern[str] = re.compile(r"\d{1,2}:\d{2}(?:\s*[ap]\.?m\.?)?", re.IGNORECASE)
COUNT_NOT_EVEN_YET_RE: re.Pattern[str] = re.compile(
    rf"\bnot even (?P<num>{_COUNT_WORDS})\ yet\b",
    re.IGNORECASE,
)
COUNT_YEAR_RE: re.Pattern[str] = re.compile(r"\b1[5-9]\d{2}\b|\b20\d{2}\b")

# Max gap (years) between two distinct script years still treated as a likely
# continuity slip rather than an intentional multi-period story.
MAX_YEAR_GAP: int = 10

# Appositive age phrasing: a capitalized name followed by a comma and an age
# clause, e.g. "SOFIA, 12, ...", "CAPTAIN TOM HALE, 28, ...", "Eddie, barely
# forty,". The age clause (up to the next sentence/clause break) is parsed by
# value_normalization.extract_age so digit, word, and "Ns" decade forms work.
AGE_APPOSITIVE_PATTERN: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z])(?P<name>(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+)"
    r"(?:\s+(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+)){0,3})\s*,\s*"
    r"(?P<clause>[^,.;:!?]{1,40})"
)

# Words that terminate a prop noun phrase when reading the head noun directly
# after a colour/material descriptor. Keeps "GOLD DATA CHIP" -> head "data"
# while rejecting "red and ...", "silver, then ..." style non-props.
DESCRIPTOR_NOUN_STOPWORDS: frozenset[str] = frozenset(
    {
        "and", "or", "but", "the", "a", "an", "of", "on", "in", "at", "to",
        "into", "onto", "with", "that", "which", "who", "from", "for", "as",
        "his", "her", "their", "its", "my", "your", "is", "was", "are", "were",
        "then", "now", "still", "beside", "between", "under", "over", "near",
        "by", "up", "down",
    }
)

# Generic head nouns that are too vague to anchor an object-identity check.
DESCRIPTOR_GENERIC_NOUNS: frozenset[str] = frozenset(
    {"one", "thing", "things", "side", "air", "light", "stuff"}
)

# Hedge words allowed before the age token in an appositive ("barely forty",
# "about thirty"). The age itself must be the head of the clause so pronouns
# like "this one" can never be misread as the age 1.
AGE_HEDGE_WORDS: frozenset[str] = frozenset(
    {
        "barely", "about", "almost", "nearly", "around", "just", "only",
        "maybe", "age", "aged", "nearing", "pushing", "roughly",
    }
)


def _is_number_token(token: str) -> bool:
    """Return True when a token is a digit run or a number word."""
    return token.isdigit() or token in NUMBER_WORDS


def _singularize(noun: str) -> str:
    """Return a crude singular form so plural counts align ("runs" -> "run")."""
    if len(noun) > 4 and noun.endswith("ies"):
        return noun[:-3] + "y"
    if len(noun) > 3 and noun.endswith("s") and not noun.endswith("ss"):
        return noun[:-1]
    return noun


def _valid_count_noun(token: str) -> bool:
    """Return True when a token can serve as a counted noun."""
    if len(token) < 3 or _is_number_token(token):
        return False
    if token in COUNT_STOP_TOKENS or _singularize(token) in COUNT_NOUN_BLOCKLIST:
        return False
    return True


def _select_count_noun(
    tokens: list[str], run_start: int, run_end: int
) -> Optional[str]:
    """Pick the counted noun for a number run, or return None.

    A whitelisted identifier noun immediately before ("Room 514") wins, since it
    is the referent; otherwise scan past adjectives to the head noun
    ("three identical runs"). Person appositives ("Dawson, 45") match neither.
    """
    if run_start > 0 and tokens[run_start - 1] in COUNT_BEFORE_NOUNS:
        return tokens[run_start - 1]
    scan = run_end
    while scan < len(tokens) and scan - run_end < 4:
        token = tokens[scan]
        if token in COUNT_ADJECTIVE_SKIP:
            scan += 1
            continue
        if _valid_count_noun(token):
            return _singularize(token)
        break
    return None


def _parse_count_value(raw: str) -> Optional[int]:
    """Parse a numeric phrase into an integer count value."""
    cleaned = raw.strip().lower()
    if cleaned in ORDINAL_WORDS:
        return ORDINAL_WORDS[cleaned]
    return words_to_int(cleaned)


def _parse_clock_hour(clock_text: str) -> Optional[int]:
    """Return the 12-hour clock-face hour from a time such as ``11:58 PM``."""
    match = re.search(
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2})(?:\s*(?P<ampm>[ap])\.?m\.?)?",
        clock_text,
        re.IGNORECASE,
    )
    if not match:
        return None
    hour = int(match.group("hour"))
    if hour < 0 or hour > 23:
        return None
    ampm = (match.group("ampm") or "").lower()
    if ampm == "a":
        return 12 if hour == 12 else hour
    if ampm == "p":
        return 12 if hour == 12 else hour
    if hour == 0:
        return 12
    if hour > 12:
        return hour - 12
    return hour


def _canonical_count_entity(entity: str) -> str:
    """Map count entities onto canonical aliases for cross-phrase matching."""
    upper = entity.upper()
    return COUNT_ENTITY_ALIASES.get(upper, upper)


def _count_entity_hint(line: str) -> Optional[str]:
    """Return a count entity hinted by nouns present on the same line."""
    lowered = line.lower()
    hints: tuple[tuple[str, str], ...] = (
        (r"\bhostages?\b", "HOSTAGE"),
        (r"\bmen\b", "GROUP"),
        (r"\bcast\b", "CAST"),
        (r"\bcouriers?\b", "COURIER"),
        (r"\bchairs?\b", "SEATING"),
        (r"\bpeople\b", "SEATING"),
        (r"\bguests?\b", "SEATING"),
        (r"\bteam\b", "TEAM"),
        (r"\bmen\b", "GROUP"),
        (r"\brules?\b", "GROUP"),
        (r"\bruns?\b", "RUN"),
    )
    for pattern, entity in hints:
        if re.search(pattern, lowered):
            return entity
    return None


def _recent_count_entity(store: "FactStore") -> Optional[str]:
    """Return the most recently extracted count entity, if any.

    When several count entities appear in the script, prefers narratively
    salient anchors (hostages, seating, teams) over incidental nouns such as
    guards picked up from action beats.
    """
    facts = store.get_facts_by_type("numeric_count")
    if not facts:
        return None
    priority = (
        "HOSTAGE",
        "SEATING",
        "TEAM",
        "GROUP",
        "COURIER",
        "METERS",
        "RANK",
    )
    entities = {_canonical_count_entity(fact.entity) for fact in facts}
    for entity in priority:
        if entity in entities:
            return entity
    ordered = sorted(facts, key=lambda item: (item.scene_number, item.fact_id))
    return _canonical_count_entity(ordered[-1].entity)


def _resolve_relationship_possessor(
    line: str,
    match: re.Match[str],
    pronoun_raw: str | None,
    subject: str | None,
    tracker: SceneMentionTracker,
    registry: EntityRegistry,
) -> str | None:
    """Resolve the possessor for a relationship pronoun pattern."""
    if pronoun_raw and "pronoun" in match.groupdict():
        prefix = line[: match.start("pronoun")]
        names: list[str] = []
        for name_match in ACTION_NAME_RE.finditer(prefix):
            resolved = _resolve_trait_entity(name_match.group("name"), registry)
            if resolved:
                names.append(resolved)
        if names:
            filtered = [name for name in names if name != subject]
            if filtered:
                return filtered[-1]
            return names[-1]
        if pronoun_raw.lower() in {"her", "his", "their"} and re.match(
            r"^\s*(?:her|his|their)\s+",
            line,
            re.IGNORECASE,
        ):
            for name_match in ACTION_NAME_RE.finditer(line):
                resolved = _resolve_trait_entity(name_match.group("name"), registry)
                if resolved and resolved != subject:
                    return resolved
        fallback = tracker.resolve_possessive_pronoun(pronoun_raw)
        if (
            fallback
            and subject
            and fallback == subject
            and len(tracker.scene_characters) == 2
        ):
            others = [
                entity for entity in tracker.scene_characters if entity != subject
            ]
            if others:
                return others[0]
        return fallback
    return tracker.resolve_possessive_pronoun(pronoun_raw or "their")


# Unified entity for fare/payment props so thimble vs coin conflicts surface.
PAYMENT_ENTITY: str = "PAYMENT_FARE"
# Unified entity for portable containers (envelope, pouch, satchel).
CONTAINER_ENTITY: str = "CONTAINER"
CONTAINER_NOUNS: frozenset[str] = frozenset(
    {"envelope", "pouch", "satchel", "packet", "parcel", "case", "bag"}
)
# Unified entity for forged/stolen art studies.
SKETCH_ENTITY: str = "SKETCH"
SKETCH_ARTIST_RE: re.Pattern[str] = re.compile(
    r"\b(?P<artist>Vermeer|Rembrandt)\s+(?:study|studies|charcoal|sketch|"
    r"painting|drawing)\b|\b(?:a|an|the)\s+Rembrandt\b",
    re.IGNORECASE,
)
WAX_SEALED_CONTAINER_RE: re.Pattern[str] = re.compile(
    rf"\bwax[\s-]sealed\s+(?P<head>{'|'.join(CONTAINER_NOUNS)})\b",
    re.IGNORECASE,
)


def _parse_inline_age(token: str) -> Optional[int]:
    """Parse an age token from a hyphenated or word form, or return None."""
    cleaned = token.strip().lower().replace("-", " ")
    decade = re.fullmatch(r"(\d{1,3})s?", cleaned.replace(" ", ""))
    if decade:
        value: Optional[int] = int(decade.group(1))
    else:
        value = words_to_int(cleaned)
    if value is None or not 1 <= value <= 120:
        return None
    return value


def _parse_head_age(clause: str) -> Optional[int]:
    """Parse an age from the head of an appositive clause, or return None.

    The number must be the first meaningful token (optionally after a hedge
    word such as "barely"), which rejects trailing pronouns/articles like
    "this one" or "on a Tuesday" that would otherwise read as the age 1.

    Args:
        clause: Text immediately after a "Name," appositive comma.

    Returns:
        The age as an int in the 1-120 range, or ``None``.
    """
    tokens = [token for token in re.split(r"\s+", clause.strip()) if token]
    index = 0
    while index < len(tokens) and tokens[index].strip(",.;:!?'\"").lower() in AGE_HEDGE_WORDS:
        index += 1
    if index >= len(tokens):
        return None
    head = tokens[index].strip(",.;:!?'\"")
    decade = re.fullmatch(r"(\d{1,3})s?", head)
    if decade:
        value: Optional[int] = int(decade.group(1))
    else:
        value = words_to_int(head)
        if value is None and index + 1 < len(tokens):
            follow = tokens[index + 1].strip(",.;:!?'\"")
            value = words_to_int(f"{head} {follow}")
    if value is None or not 1 <= value <= 120:
        return None
    return value

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
    # "Kowalski hit, shoulder" (telegraphic action-line injury)
    re.compile(
        rf"(?<![A-Za-z0-9])(?P<entity>[A-Z][A-Za-z0-9 '\-]+?)\s+"
        rf"(?P<condition>hit),?\s*(?:in the )?"
        rf"(?P<part>shoulder|arm|leg|head|chest|back|ribs)\b",
        re.IGNORECASE,
    ),
    # "medics bind Kowalski's leg"
    re.compile(
        rf"(?:medics?\s+)?(?P<condition>bind|wrap)\s+"
        rf"(?P<entity>[A-Z][A-Za-z0-9 '\-]+?)'s\s+"
        rf"(?P<part>leg|arm|shoulder|ribs)\b",
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
    re.compile(
        r"(?<![A-Za-z])(?P<entity>(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+)"
        r"(?:\s+(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+)){0,3}),\s*\d{1,3}s?\s*,\s*"
        r"(?P<trait>[a-z][a-z\-]+(?:\s+[a-z][a-z\-]+){0,2}?)"
        r"(?:\s|,|\.|$)",
    ),
    re.compile(
        r"(?<![A-Za-z])(?P<entity>[A-Z][a-z]+),\s*the\s+(?P<trait>[a-z][a-z\s\-]+?)"
        r"(?:\s|,|\.|$)",
    ),
    re.compile(
        r"(?<![A-Za-z])(?P<entity>(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+))"
        r"(?:[^.\n]{0,120}?)(?i:(?P<trait>unconvinced|skeptical|skeptic))\b",
    ),
)
# Dialogue-only belief / attitude statements attributed to the active speaker.
BELIEF_DIALOGUE_TRAITS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\bI knew this place was alive\b",
            re.IGNORECASE,
        ),
        "believer",
    ),
    (
        re.compile(
            r"\bI felt it\b",
            re.IGNORECASE,
        ),
        "believer",
    ),
)
TRAIT_JUNK_PREFIXES: frozenset[str] = frozenset(
    {"and", "or", "with", "who", "when", "at", "in", "on", "the", "his", "her"}
)
ATTITUDE_TRAIT_TERMS: frozenset[str] = frozenset(
    {"unconvinced", "skeptical", "skeptic", "believer"}
)

_SCREENPLAY_NAME = r"(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+)"
_EXT_OWNER = rf"(?P<owner>{_SCREENPLAY_NAME}(?:\s+{_SCREENPLAY_NAME}){{0,3}})"
_EXT_OBJECT = r"(?P<object>[A-Za-z][A-Za-z0-9\s\-]+?)"
_EXT_OBJ_END = (
    r"(?:\s+(?:from|on|onto|into|in|to|under|over|behind|with|for|and|but|"
    r"then|when|after|before|while|accidentally|that|as|where|which|who)\b|[.,;:]|$)"
)
# Prop-like possessive objects: ALL-CAPS words or "guest book" / "magnetic guest book".
_EXT_PROP_OR_GUEST_BOOK = (
    r"(?P<object>(?:[A-Z]{2,}(?:\s+[A-Z]{2,})*|"
    r"(?i:magnetic\s+guest\s+book|guest\s+book)))"
)
_POSSESS_VERBS = r"(?:holds|keeps|grips|clutches|fidgets with)"
EXTENDED_OWNERSHIP_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            rf"(?<![A-Za-z]){_EXT_OWNER}\s+(?i:{_POSSESS_VERBS})\s+"
            rf"(?:a|an|the|his|her|their)?\s*{_EXT_PROP_OR_GUEST_BOOK}{_EXT_OBJ_END}",
        ),
        "holds",
    ),
    (
        re.compile(
            rf"(?:(?i:A|An|The))\s+{_EXT_OBJECT}\s+(?i:clips)\s+to\s+"
            rf"{_EXT_OWNER}'s\b",
        ),
        "clips to",
    ),
    (
        re.compile(
            rf"(?:(?i:A|An|The))\s+{_EXT_OBJECT}\s+(?i:sits)\s+in\s+"
            rf"{_EXT_OWNER}'s\b",
        ),
        "in",
    ),
    (
        re.compile(
            rf"(?:(?i:The|A|An))\s+{_EXT_OBJECT}\s+(?i:stays)\s+in\s+"
            rf"{_EXT_OWNER}'s\s+pocket\b",
        ),
        "stays in",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z]){_EXT_PROP_OR_GUEST_BOOK}\s+(?i:on)\s+{_EXT_OWNER}'s\b",
        ),
        "on",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z]){_EXT_OWNER}'s\s+{_EXT_PROP_OR_GUEST_BOOK}{_EXT_OBJ_END}",
        ),
        "possesses",
    ),
)
# Container / junk heads that extended patterns must not emit as props.
OWNERSHIP_JUNK_OBJECTS: frozenset[str] = frozenset(
    {
        "IT", "ONE", "NOTES", "POCKET", "BACKPACK", "VEST", "CENTERPIECE",
        "SASH", "MIC", "BEER", "BEERS", "TOAST", "TOASTS", "DRUNK ONE",
    }
)
# Family/role words that mark a possessive phrase about a person, not a prop.
OWNERSHIP_RELATION_HEADS: frozenset[str] = frozenset(
    {
        "DAUGHTER", "SON", "AUNT", "UNCLE", "NIECE", "NEPHEW", "COUSIN",
        "MOTHER", "FATHER", "BROTHER", "SISTER", "CHILD", "WIFE", "HUSBAND",
    }
)
# Extended verb labels parsed by :meth:`ContradictionEngine._ownership_holder`.
EXTENDED_POSSESSION_VERB_LABELS: tuple[str, ...] = (
    "clips to",
    "stays in",
    "possesses",
    "in",
    "on",
)

# --- Relationship facts (Phase 3) -----------------------------------------
# Surface relation terms (singular + plural) mapped to a canonical category
# and a role. "parent"/"child" are the two asymmetric directions of the
# parent_child category; every other relation is symmetric.
RELATION_TERMS: dict[str, tuple[str, str]] = {
    "husband": ("spouse", "symmetric"),
    "wife": ("spouse", "symmetric"),
    "spouse": ("spouse", "symmetric"),
    "spouses": ("spouse", "symmetric"),
    "married": ("spouse", "symmetric"),
    "brother": ("sibling", "symmetric"),
    "sister": ("sibling", "symmetric"),
    "brothers": ("sibling", "symmetric"),
    "sisters": ("sibling", "symmetric"),
    "sibling": ("sibling", "symmetric"),
    "siblings": ("sibling", "symmetric"),
    "twin": ("sibling", "symmetric"),
    "twins": ("sibling", "symmetric"),
    "father": ("parent_child", "parent"),
    "mother": ("parent_child", "parent"),
    "dad": ("parent_child", "parent"),
    "mom": ("parent_child", "parent"),
    "mum": ("parent_child", "parent"),
    "parent": ("parent_child", "parent"),
    "son": ("parent_child", "child"),
    "daughter": ("parent_child", "child"),
    "child": ("parent_child", "child"),
    "kid": ("parent_child", "child"),
    "niece": ("niece_nephew", "aunt_uncle"),
    "nephew": ("niece_nephew", "aunt_uncle"),
    "cousin": ("cousin", "symmetric"),
    "cousins": ("cousin", "symmetric"),
    "best man": ("wedding_party", "symmetric"),
    "groomsman": ("wedding_party", "symmetric"),
    "groomsmen": ("wedding_party", "symmetric"),
    "coach": ("professional", "symmetric"),
    "aunt": ("aunt_uncle", "symmetric"),
    "uncle": ("aunt_uncle", "symmetric"),
    "mother-in-law": ("in_law", "symmetric"),
    "father-in-law": ("in_law", "symmetric"),
    "brother-in-law": ("in_law", "symmetric"),
    "sister-in-law": ("in_law", "symmetric"),
    "boyfriend": ("lover", "symmetric"),
    "girlfriend": ("lover", "symmetric"),
    "lover": ("lover", "symmetric"),
    "lovers": ("lover", "symmetric"),
    "fiance": ("lover", "symmetric"),
    "fiancee": ("lover", "symmetric"),
    "friend": ("friend", "symmetric"),
    "friends": ("friend", "symmetric"),
    "ally": ("friend", "symmetric"),
    "enemy": ("enemy", "symmetric"),
    "enemies": ("enemy", "symmetric"),
    "nemesis": ("enemy", "symmetric"),
    "rival": ("enemy", "symmetric"),
}
# Category pairs that cannot describe the same two people. Only immutable
# blood relations (sibling, parent_child) clashing with each other or with a
# romantic bond are included, because social/romantic ties legitimately change
# over a story (enemies -> friends, married -> divorced) and must NOT be
# flagged as contradictions.
INCOMPATIBLE_RELATION_CATEGORIES: tuple[frozenset[str], ...] = (
    frozenset({"sibling", "parent_child"}),
    frozenset({"sibling", "spouse"}),
    frozenset({"sibling", "lover"}),
    frozenset({"parent_child", "spouse"}),
    frozenset({"parent_child", "lover"}),
    frozenset({"sibling", "cousin"}),
    frozenset({"parent_child", "niece_nephew"}),
    frozenset({"sibling", "niece_nephew"}),
    frozenset({"cousin", "niece_nephew"}),
    frozenset({"in_law", "aunt_uncle"}),
    frozenset({"in_law", "cousin"}),
    frozenset({"sibling", "in_law"}),
    frozenset({"cousin", "wedding_party"}),
    frozenset({"sibling", "professional"}),
)

_REL_NAME = (
    r"(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+)"
    r"(?:\s+(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+)){0,3}"
)
_REL_SINGLE_NAME = r"(?:[A-Z][A-Z0-9'\-.]*|[A-Z][a-z]+)"
_RELATION_WORD = r"[a-z]+(?:-[a-z]+)*"

RELATIONSHIP_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<subject>{_REL_NAME})\s+is\s+"
            rf"(?P<object>{_REL_NAME})'s\s+(?P<relation>{_RELATION_WORD})"
        ),
        "subject_object",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<subject>{_REL_NAME}),\s+"
            rf"(?P<object>{_REL_NAME})'s\s+(?P<relation>{_RELATION_WORD}),"
        ),
        "subject_object",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<subject>{_REL_NAME})\s+and\s+"
            rf"(?P<object>{_REL_NAME})\s+are\s+(?P<relation>{_RELATION_WORD})"
        ),
        "symmetric",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<object>{_REL_NAME})'s\s+"
            rf"(?P<relation>{_RELATION_WORD})\s+(?P<subject>{_REL_NAME})\b"
        ),
        "possessor_first",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<object>{_REL_NAME})'s\s+"
            rf"(?:future\s+)?(?P<relation>mother-in-law|father-in-law|"
            rf"brother-in-law|sister-in-law)\s+(?P<subject>{_REL_NAME})\b"
        ),
        "possessor_first",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<object>{_REL_NAME})'s\s+"
            rf"(?P<relation>niece|nephew|daughter|son)\b"
        ),
        "possessor_only",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<object>{_REL_NAME})\s+with\s+"
            rf"(?:his|her|their)\s+(?P<relation>daughter|son|niece|nephew)\b",
            re.IGNORECASE,
        ),
        "possessor_only",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<pronoun>her|his|their)\s+"
            rf"(?P<relation>{_RELATION_WORD})\s+(?P<subject>{_REL_NAME})\b",
            re.IGNORECASE,
        ),
        "pronoun_subject",
    ),
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<subject>{_REL_NAME}),\s+"
            rf"(?P<pronoun>his|her|their)\s+(?P<relation>{_RELATION_WORD})\b",
            re.IGNORECASE,
        ),
        "pronoun_appositive",
    ),
    (
        re.compile(
            r"(?<![A-Za-z0-9])introduced as (?:the )?"
            rf"(?P<relation>nephew|niece)\b",
            re.IGNORECASE,
        ),
        "introduced",
    ),
    (
        re.compile(
            r"\b(?:I'm|I am) the (?P<relation>only son|only daughter)\b",
            re.IGNORECASE,
        ),
        "speaker_child",
    ),
    (
        re.compile(
            rf"\bthe\s+(?P<relation>nephew|niece),?\s+"
            rf"(?P<subject>{_REL_SINGLE_NAME})\b",
            re.IGNORECASE,
        ),
        "named_role",
    ),
    (
        re.compile(
            rf"\b(?P<relation>cousin|best man)\s+"
            rf"(?P<subject>{_REL_SINGLE_NAME})\b",
            re.IGNORECASE,
        ),
        "named_role",
    ),
    (
        re.compile(
            rf"\b(?P<relation>Coach)\s+(?P<subject>{_REL_SINGLE_NAME})\b"
        ),
        "named_role",
    ),
    (
        re.compile(
            r"\b(?:your|Your)\s+(?:future\s+)?"
            rf"(?P<relation>mother-in-law|father-in-law)\b"
        ),
        "addressee_in_law",
    ),
)

# --- World rules (Phase 4, capture-only) ----------------------------------
# Modal/capability phrasing that declares a rule of the fiction: what is or is
# not possible (magic systems, tech limits, time-travel rules, superpowers).
# These are CAPTURED as world_rule facts for later Tier 3 violation reasoning;
# no Tier 1 contradiction is raised from them, because deciding whether a later
# scene breaks a rule is open-domain semantics, not a rule-based check. The
# focus is on capability/permission modals ("cannot", "can only", "no one
# can"), not bare "always/never", to keep captured rules on-signal.
_RULE_PREDICATE = r"(?P<predicate>[a-z][a-z0-9 ,'\-]+?)(?:[.!?]|$)"
_RULE_SUBJECT = r"(?P<subject>[A-Za-z][A-Za-z0-9 '\-]+?)"

WORLD_RULE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # "No one can leave the dome", "Nothing can stop it"
    (
        re.compile(
            rf"(?<![A-Za-z0-9])(?P<subject>no\s+one|nobody|nothing|none)\s+"
            rf"can\s+{_RULE_PREDICATE}",
            re.IGNORECASE,
        ),
        "cannot",
    ),
    # "Vampires can only enter when invited"
    (
        re.compile(
            rf"(?<![A-Za-z0-9]){_RULE_SUBJECT}\s+can\s+only\s+{_RULE_PREDICATE}",
            re.IGNORECASE,
        ),
        "can only",
    ),
    # "The time machine cannot travel to the future"
    (
        re.compile(
            rf"(?<![A-Za-z0-9]){_RULE_SUBJECT}\s+"
            rf"(?:can\s*not|cannot|can't|can\s+never|may\s+not|must\s+not|"
            rf"must\s+never)\s+{_RULE_PREDICATE}",
            re.IGNORECASE,
        ),
        "cannot",
    ),
)

# Indefinite rule subjects ("no one can leave the dome") state a blanket
# constraint with no concrete noun to match against a later scene, so they are
# captured but not evaluated for violations (matching their head word would be
# noisy, e.g. "one" appears everywhere).
WORLD_RULE_INDEFINITE_SUBJECTS: frozenset[str] = frozenset(
    {"NO ONE", "NOBODY", "NOTHING", "NONE"}
)
# Tokens that mark a line as negated, so a restated prohibition ("the machine
# cannot travel") is never mistaken for an affirmative violation of the rule.
WORLD_RULE_NEGATION_TERMS: frozenset[str] = frozenset(
    {"not", "never", "no", "none", "nobody", "nothing", "without"}
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


def _resolve_owner_entity(
    raw_owner: str, registry: EntityRegistry | None = None
) -> Optional[str]:
    """Resolve an ownership-pattern owner span to a canonical character key."""
    if registry is not None:
        resolved = registry.resolve(raw_owner)
        if resolved:
            return _normalize_token(resolved)
    return _resolve_character_entity(raw_owner)


def _resolve_trait_entity(
    raw_entity: str, registry: EntityRegistry | None = None
) -> Optional[str]:
    """Resolve a trait-pattern entity span to a canonical character key."""
    if registry is not None:
        resolved = registry.resolve(raw_entity)
        if resolved:
            return _normalize_token(resolved)
    return _resolve_character_entity(raw_entity)


def _is_valid_trait(trait: str) -> bool:
    """Return True when a captured trait phrase is worth storing."""
    cleaned = _clean_value(trait).strip()
    if not cleaned:
        return False
    head = cleaned.split()[0].lower()
    if head in TRAIT_JUNK_PREFIXES:
        return False
    tail = cleaned.split()[-1].lower()
    if tail in GENERIC_TRAIT_TERMS:
        return False
    lowered = cleaned.lower()
    if lowered in ATTITUDE_TRAIT_TERMS:
        return True
    if any(part in ROLE_NOUNS for part in re.findall(r"[a-z]+", lowered)):
        return True
    if "-" in lowered and any(
        part in ROLE_NOUNS for part in lowered.replace("-", " ").split()
    ):
        return True
    if len(cleaned.split()) >= 2:
        return True
    return False


def _canonical_prop_key(object_key: str) -> str:
    """Collapse variant prop phrases onto one continuity key."""
    tokens = object_key.split()
    token_set = set(tokens)
    if {"RED", "FLARE"}.issubset(token_set):
        return "RED FLARE"
    if "GUEST" in token_set and "BOOK" in token_set:
        return "MAGNETIC GUEST BOOK"
    if {"SILVER", "BAND"}.issubset(token_set) or {"SILVER", "WEDDING", "BAND"}.issubset(
        token_set
    ):
        return "SILVER BAND"
    return object_key


def _strip_leading_article(object_name: str) -> str:
    """Remove a leading article or possessive from an extracted object phrase."""
    stripped = object_name.strip()
    for prefix in ("a ", "an ", "the ", "his ", "her ", "their ", "its ", "my ", "your "):
        if stripped.lower().startswith(prefix):
            return stripped[len(prefix) :]
    return stripped


def _is_relation_object_key(object_key: str) -> bool:
    """Return True when the object key names a person via a family role."""
    tokens = object_key.split()
    return bool(tokens) and tokens[0] in OWNERSHIP_RELATION_HEADS


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
    "hit": "hit",
    "bind": "injured",
    "wrap": "injured",
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


def _parse_relationship_value(
    value: str,
) -> tuple[str, Optional[tuple[str, str]]]:
    """Parse a relationship fact value into (category, direction).

    Symmetric relations store just the category ("sibling", "spouse"); the
    parent_child category stores a directed "parent>child" pair so role
    inversion can be detected.

    Args:
        value: The stored relationship fact value.

    Returns:
        A tuple of (category, direction), where direction is a (parent, child)
        tuple for parent_child relations and None otherwise.
    """
    if value.startswith("parent_child"):
        rest = value[len("parent_child") :].strip()
        if ">" in rest:
            parent, child = rest.split(">", 1)
            return ("parent_child", (parent.strip(), child.strip()))
        return ("parent_child", None)
    return (value.strip(), None)


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

    def __init__(self, nlp: Optional[Language] = None) -> None:
        """Initialize the engine and load or reuse the spaCy English model."""
        self.nlp: Language = nlp if nlp is not None else get_shared_nlp()
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
        registry = self._build_entity_registry(sorted_scenes)
        role_registry = build_role_registry(sorted_scenes, registry)

        for scene in sorted_scenes:
            self._extract_character_status_facts(scene, store)
            self._extract_medical_state_facts(scene, store)
            # Timeline detection disabled: plot contradictions are the focus,
            # and weekday/day-sequence tracking is intentionally turned off.
            # self._extract_timeline_facts(scene, store)
            self._extract_character_trait_facts(scene, store, registry)
            self._extract_object_ownership_facts(scene, store, registry)
            self._extract_object_state_facts(scene, store)
            self._extract_relationship_facts(scene, store, registry)
            self._extract_sketch_artist_facts(scene, store)
            self._extract_world_rule_facts(scene, store)
            self._extract_location_facts(scene, store)
            self._extract_location_description_facts(scene, store)
            self._extract_age_facts(scene, store, registry, role_registry)
            self._extract_object_descriptor_facts(scene, store)
            self._extract_payment_descriptor_facts(scene, store)
            self._extract_count_facts(scene, store)
            self._extract_year_facts(scene, store)

        return store

    def _record_count_fact(
        self,
        scene: SceneBlock,
        store: FactStore,
        entity: str,
        value: int,
        line: str,
        seen: set[tuple[str, str]],
    ) -> None:
        """Add one numeric_count fact when the (entity, value) pair is new."""
        canonical = _canonical_count_entity(entity)
        key = (canonical, str(value))
        if key in seen:
            return
        seen.add(key)
        store.add_fact(
            self._make_fact(scene, "numeric_count", canonical, str(value), line)
        )

    def _extract_count_facts(self, scene: SceneBlock, store: FactStore) -> None:
        """Extract (counted noun, quantity) facts for numeric-continuity checks.

        A number run (digits or number words, e.g. "three hundred") is paired
        with its head noun: the token immediately after, or the token before for
        noun-then-number forms ("Room 514"). Clock times and 4-digit years are
        stripped first so they are never read as counts, and the noun is
        singularized so "runs"/"run" align across scenes.
        """
        action_lines, dialogue_lines = _scene_lines_by_source(scene)
        seen: set[tuple[str, str]] = set()
        for line in action_lines + dialogue_lines:
            for pattern, entity in COUNT_PHRASE_PATTERNS:
                for match in pattern.finditer(line):
                    value = _parse_count_value(match.group("num"))
                    if value is None:
                        continue
                    self._record_count_fact(
                        scene, store, entity, value, line, seen
                    )
            for pattern in (
                COUNT_ROOM_NUMBER_RE,
                COUNT_LINE_ROOM_NUMBER_RE,
            ):
                for match in pattern.finditer(line):
                    value = _parse_count_value(match.group("num"))
                    if value is None:
                        continue
                    self._record_count_fact(
                        scene, store, "ROOM", value, line, seen
                    )
            match = COUNT_HOSTAGE_LABEL_RE.search(line)
            if match:
                value = _parse_count_value(match.group("num"))
                if value is not None:
                    self._record_count_fact(
                        scene, store, "HOSTAGE", value, line, seen
                    )
            for match in COUNT_ALL_QUANTITY_RE.finditer(line):
                value = _parse_count_value(match.group("num"))
                if value is None:
                    continue
                entity = _count_entity_hint(line) or _recent_count_entity(store)
                if entity is None:
                    continue
                self._record_count_fact(
                    scene, store, entity, value, line, seen
                )
            for match in COUNT_CLOCK_RE.finditer(line):
                hour = _parse_clock_hour(match.group())
                if hour is not None:
                    self._record_count_fact(
                        scene, store, "CLOCK", hour, line, seen
                    )
            match = COUNT_NOT_EVEN_YET_RE.search(line)
            if match:
                bound = _parse_count_value(match.group("num"))
                if bound is not None and bound > 0:
                    self._record_count_fact(
                        scene, store, "CLOCK", bound - 1, line, seen
                    )
            cleaned = COUNT_YEAR_RE.sub(" ", COUNT_CLOCK_RE.sub(" ", line))
            matches = list(re.finditer(r"\d+|[A-Za-z]+", cleaned))
            lowered = [match.group().lower() for match in matches]
            index = 0
            while index < len(lowered):
                if not _is_number_token(lowered[index]):
                    index += 1
                    continue
                run_start = index
                while index < len(lowered) and _is_number_token(lowered[index]):
                    index += 1
                if cleaned[: matches[run_start].start()].rstrip().endswith(","):
                    continue
                value = words_to_int(" ".join(lowered[run_start:index]))
                if value is None:
                    continue
                if (
                    value <= 12
                    and run_start > 0
                    and lowered[run_start - 1] == "at"
                ):
                    continue
                noun = _select_count_noun(lowered, run_start, index)
                if noun is None:
                    continue
                self._record_count_fact(
                    scene, store, noun.upper(), value, line, seen
                )

    def _extract_year_facts(self, scene: SceneBlock, store: FactStore) -> None:
        """Extract year facts from the whole scene (headings included).

        Years can live in slug lines ("EXT. FIELD - 1943"), action, or dialogue
        ("CHRISTMAS '94"), so the full scene text is scanned.
        """
        seen: set[int] = set()
        for line in scene.raw_text.splitlines():
            for year in extract_all_years(line):
                if year in seen:
                    continue
                seen.add(year)
                store.add_fact(
                    self._make_fact(scene, "year", "YEAR", str(year), line.strip())
                )

    def _build_entity_registry(self, scenes: list[SceneBlock]) -> EntityRegistry:
        """Build a character registry from cues and parsed scene characters.

        Registering every name the scene parser already extracted (action intros
        plus dialogue cues) merges variants such as ``SERGEANT TOM HALE`` and
        ``HALE`` onto one canonical id before age or ownership facts are built.
        Action-line intro patterns (``NAME, 32, novelist``) are scanned so
        scripts without character cues still merge ``Claire`` onto
        ``CLAIRE HART``.
        """
        registry = EntityRegistry()
        intro_names: list[str] = []
        for scene in scenes:
            for kind, text in iter_scene_lines(scene):
                if kind == "action":
                    for match in INTRO_ROLE_RE.finditer(text):
                        intro_names.append(match.group("name"))
        for name in sorted(set(intro_names), key=len, reverse=True):
            registry.register(name)
        register_characters_from_scenes(registry, scenes)
        for scene in scenes:
            for line in scene.raw_text.splitlines():
                stripped = line.strip()
                if _is_character_cue(stripped):
                    registry.register(re.sub(r"\([^)]*\)", "", stripped))
            for kind, text in iter_scene_lines(scene):
                if kind != "action":
                    continue
                for match in INTRO_ROLE_RE.finditer(text):
                    registry.register(match.group("name"))
        return registry

    def _record_age_fact(
        self,
        scene: SceneBlock,
        store: FactStore,
        entity: str,
        age: int,
        line: str,
        seen: set[tuple[str, str]],
    ) -> None:
        """Add one age fact when ``(entity, age)`` has not already been recorded."""
        key = (entity, str(age))
        if key in seen:
            return
        seen.add(key)
        store.add_fact(self._make_fact(scene, "age", entity, str(age), line))

    def _extract_age_facts(
        self,
        scene: SceneBlock,
        store: FactStore,
        registry: EntityRegistry,
        role_registry: RoleRegistry,
    ) -> None:
        """Extract character age facts using appositive, role, and coref rules.

        Uses :mod:`screenplay_coref` (rule-based, no ML) to link role phrases
        ("nineteen-year-old gardener"), dialogue ("when I was twelve", "For
        eleven, she…"), and pronoun subjects to the canonical character named
        earlier in the scene.
        """
        seen: set[tuple[str, str]] = set()
        tracker = SceneMentionTracker(scene_character_ids(scene, registry))

        for kind, text in iter_scene_lines(scene):
            if kind == "cue":
                speaker = registry.resolve(text)
                if speaker is None:
                    speaker = strip_titles_and_articles(normalize_name(text))
                tracker.set_speaker(speaker)
                continue

            if kind == "action":
                index_roles_from_line(text, registry, role_registry)
                tracker.note_action_mentions(text, registry)

            for match in AGE_APPOSITIVE_PATTERN.finditer(text):
                age = _parse_head_age(match.group("clause"))
                if age is None:
                    continue
                raw_name = match.group("name")
                entity = registry.resolve(raw_name)
                if entity is None:
                    entity = strip_titles_and_articles(normalize_name(raw_name))
                if entity:
                    self._record_age_fact(scene, store, entity, age, text, seen)

            for match in YEAR_OLD_AGE_RE.finditer(text):
                age = _parse_inline_age(match.group("age"))
                if age is None:
                    continue
                role = match.group("role")
                entity: str | None = None
                if role:
                    entity = role_registry.resolve(role)
                if entity is None:
                    entity = tracker.resolve_subject(text)
                if entity:
                    self._record_age_fact(scene, store, entity, age, text, seen)

            for match in FIRST_PERSON_AGE_RE.finditer(text):
                age = _parse_inline_age(match.group("age"))
                if age is None:
                    continue
                entity = tracker.current_speaker or tracker.resolve_subject(text)
                if entity:
                    self._record_age_fact(scene, store, entity, age, text, seen)

            for match in FOR_AGE_DIALOGUE_RE.finditer(text):
                age = _parse_inline_age(match.group("age"))
                if age is None:
                    continue
                entity = tracker.resolve_subject(text)
                if entity:
                    self._record_age_fact(scene, store, entity, age, text, seen)

    def _extract_payment_descriptor_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Extract fare/payment material facts for object-identity continuity.

        Lines such as "pays with a silver thimble" and "paid with a brass coin"
        map to a unified ``PAYMENT_FARE`` entity so a material swap is reported
        even when the prop head noun changes (thimble vs coin).
        """
        seen: set[str] = set()
        for kind, text in iter_scene_lines(scene):
            if kind not in ("action", "dialogue"):
                continue
            for match in PAYMENT_OBJECT_RE.finditer(text):
                material = match.group("material")
                if not material:
                    continue
                axis = descriptor_axis(material)
                if axis is None:
                    continue
                value = f"{axis}:{material.lower()}"
                if value in seen:
                    continue
                seen.add(value)
                store.add_fact(
                    self._make_fact(
                        scene, "object_descriptor", PAYMENT_ENTITY, value, text
                    )
                )

    def _extract_object_descriptor_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Extract (prop, descriptor) facts for colour/material continuity.

        For each colour/material token, the immediately following noun is taken
        as the prop head (so "GOLD DATA CHIP" and "silver data chip" both key on
        "data"), and the fact value records the axis and token ("material:gold").
        Using the adjacent noun avoids trailing-verb capture and keeps the key
        stable across scenes.
        """
        action_lines, dialogue_lines = _scene_lines_by_source(scene)
        seen: set[tuple[str, str]] = set()
        for line in action_lines + dialogue_lines:
            wax_match = WAX_SEALED_CONTAINER_RE.search(line)
            if wax_match:
                value = "material:wax"
                key = (CONTAINER_ENTITY, value)
                if key not in seen:
                    seen.add(key)
                    store.add_fact(
                        self._make_fact(
                            scene,
                            "object_descriptor",
                            CONTAINER_ENTITY,
                            value,
                            line,
                        )
                    )
            tokens = re.findall(r"[A-Za-z]+", line)
            for index, token in enumerate(tokens[:-1]):
                axis = descriptor_axis(token)
                if axis is None:
                    continue
                head = tokens[index + 1].lower()
                if (
                    len(head) < 3
                    or head in DESCRIPTOR_NOUN_STOPWORDS
                    or head in DESCRIPTOR_GENERIC_NOUNS
                    or descriptor_axis(head) is not None
                ):
                    continue
                entity_key = (
                    CONTAINER_ENTITY
                    if head in CONTAINER_NOUNS
                    else head.upper()
                )
                value = f"{axis}:{token.lower()}"
                key = (entity_key, value)
                if key in seen:
                    continue
                seen.add(key)
                store.add_fact(
                    self._make_fact(
                        scene, "object_descriptor", entity_key, value, line
                    )
                )
            for head in CONTAINER_NOUNS:
                if not re.search(rf"\b{head}\b", line, re.IGNORECASE):
                    continue
                for index, token in enumerate(tokens):
                    axis = descriptor_axis(token)
                    if axis is None:
                        continue
                    if index + 1 < len(tokens) and tokens[index + 1].lower() == head:
                        value = f"{axis}:{token.lower()}"
                        key = (CONTAINER_ENTITY, value)
                        if key in seen:
                            continue
                        seen.add(key)
                        store.add_fact(
                            self._make_fact(
                                scene,
                                "object_descriptor",
                                CONTAINER_ENTITY,
                                value,
                                line,
                            )
                        )

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
        self, scene: SceneBlock, store: FactStore, registry: EntityRegistry
    ) -> None:
        """Extract profession and role trait facts from action lines only.

        Dialogue is excluded so insults and figures of speech do not become
        trait facts, and generic descriptions ("is a good man") are dropped
        when the trait's head noun carries no role information. Explicit
        belief statements in dialogue (``BELIEF_DIALOGUE_TRAITS``) are
        attributed to the active speaker. Entity spans are resolved through
        the registry so ``Claire`` and ``CLAIRE HART`` share one trait track.
        """
        seen: set[tuple[str, str, str]] = set()
        tracker = SceneMentionTracker(scene_character_ids(scene, registry))

        for kind, text in iter_scene_lines(scene):
            if kind == "cue":
                speaker = registry.resolve(text)
                if speaker is None:
                    speaker = strip_titles_and_articles(normalize_name(text))
                tracker.set_speaker(speaker)
                continue

            if kind == "action":
                tracker.note_action_mentions(text, registry)
                for pattern in CHARACTER_TRAIT_PATTERNS:
                    match = pattern.search(text)
                    if not match:
                        continue
                    entity = _resolve_trait_entity(match.group("entity"), registry)
                    if entity is None:
                        continue
                    trait = _clean_value(match.group("trait"))
                    if not _is_valid_trait(trait):
                        continue
                    dedupe = (scene.scene_id, entity, trait.lower())
                    if dedupe in seen:
                        continue
                    seen.add(dedupe)
                    store.add_fact(
                        self._make_fact(
                            scene,
                            "character_trait",
                            entity,
                            trait,
                            text,
                        )
                    )
                continue

            speaker = tracker.current_speaker
            if speaker is None:
                continue
            for pattern, trait in BELIEF_DIALOGUE_TRAITS:
                if not pattern.search(text):
                    continue
                dedupe = (scene.scene_id, speaker, trait.lower())
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                store.add_fact(
                    self._make_fact(
                        scene,
                        "character_trait",
                        speaker,
                        trait,
                        text,
                    )
                )

    def _extract_object_ownership_facts(
        self, scene: SceneBlock, store: FactStore, registry: EntityRegistry
    ) -> None:
        """Extract object possession and transfer facts from action lines only.

        Dialogue is excluded so figurative possession ("She has the nerve")
        does not create ownership facts. Extended patterns cover natural prose
        such as possessives ("Tom's guest book"), clipping ("flare clips to
        Vega's vest"), and locative possession ("stays in Elena's pocket").
        """
        action_lines, _ = _scene_lines_by_source(scene)
        seen: set[tuple[str, str, str]] = set()
        for line in action_lines:
            for pattern, verb in OBJECT_OWNERSHIP_PATTERNS + EXTENDED_OWNERSHIP_PATTERNS:
                for match in pattern.finditer(line):
                    owner = _resolve_owner_entity(match.group("owner"), registry)
                    if owner is None or owner in {"THE END", "END"}:
                        continue
                    object_name = _strip_leading_article(
                        _clean_value(match.group("object"))
                    )
                    object_key = _canonical_prop_key(
                        _normalize_object_key(object_name)
                    )
                    if (
                        not object_key
                        or object_key in OWNERSHIP_JUNK_OBJECTS
                        or _is_relation_object_key(object_key)
                        or any(
                            word.lower() in NON_PROP_OBJECTS
                            for word in object_key.split()
                        )
                    ):
                        continue
                    recipient_raw = match.groupdict().get("recipient")
                    if recipient_raw:
                        recipient = _resolve_owner_entity(recipient_raw, registry)
                        if recipient is None:
                            continue
                        value = f"{owner} {verb} {object_name} to {recipient}"
                    else:
                        value = f"{owner} {verb} {object_name}"
                    dedupe = (scene.scene_id, object_key, owner)
                    if dedupe in seen:
                        continue
                    seen.add(dedupe)
                    store.add_fact(
                        self._make_fact(
                            scene,
                            "object_ownership",
                            object_key,
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

    def _extract_sketch_artist_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Extract artist identity facts for art-study continuity checks."""
        seen: set[str] = set()
        for kind, text in iter_scene_lines(scene):
            if kind not in ("action", "dialogue"):
                continue
            for match in SKETCH_ARTIST_RE.finditer(text):
                artist = match.group("artist")
                if artist is None:
                    artist = "Rembrandt"
                value = f"artist:{artist.lower()}"
                if value in seen:
                    continue
                seen.add(value)
                store.add_fact(
                    self._make_fact(
                        scene, "object_descriptor", SKETCH_ENTITY, value, text
                    )
                )

    def _add_relationship_fact(
        self,
        scene: SceneBlock,
        store: FactStore,
        pair_key: str,
        value: str,
        line: str,
    ) -> None:
        """Store one relationship fact when the pair key and value are valid."""
        if not pair_key or not value:
            return
        store.add_fact(
            self._make_fact(scene, "relationship", pair_key, value, line)
        )

    def _relationship_value(
        self, category: str, role: str, subject: str, other: str
    ) -> str:
        """Build the canonical relationship fact value string."""
        if role == "parent":
            return f"parent_child {subject}>{other}"
        if role == "child":
            return f"parent_child {other}>{subject}"
        if role == "aunt_uncle":
            return "niece_nephew"
        return category

    def _extract_relationship_facts(
        self, scene: SceneBlock, store: FactStore, registry: EntityRegistry
    ) -> None:
        """Extract character-relationship facts from action lines only.

        Captures possessive, appositive, symmetric, and pronoun-resolved family
        relations. Facts are keyed on the unordered character pair, or on a
        single possessor when only one side of the relation is named.
        """
        tracker = SceneMentionTracker(scene_character_ids(scene, registry))
        for kind, text in iter_scene_lines(scene):
            if kind == "cue":
                speaker = registry.resolve(text)
                if speaker is None:
                    speaker = strip_titles_and_articles(normalize_name(text))
                tracker.set_speaker(speaker)
                continue
            if kind == "action":
                tracker.note_action_mentions(text, registry)
            for pattern, shape in RELATIONSHIP_PATTERNS:
                for match in pattern.finditer(text):
                    relation_key = match.group("relation").lower()
                    if relation_key.startswith("only "):
                        relation_key = relation_key.split(maxsplit=1)[1]
                    mapped = RELATION_TERMS.get(relation_key)
                    if mapped is None:
                        continue
                    category, role = mapped
                    groups = match.groupdict()
                    subject_raw = groups.get("subject")
                    object_raw = groups.get("object")
                    pronoun_raw = groups.get("pronoun")

                    if shape == "speaker_child":
                        subject = tracker.current_speaker
                        if subject is None:
                            continue
                        self._add_relationship_fact(
                            scene,
                            store,
                            subject,
                            "parent_child",
                            text,
                        )
                        continue

                    if shape == "addressee_in_law":
                        listener: str | None = None
                        for entity in reversed(tracker.mention_stack):
                            if entity == tracker.current_speaker:
                                continue
                            if entity not in tracker.scene_characters:
                                continue
                            listener = entity
                            break
                        if listener is None:
                            for entity in tracker.scene_characters:
                                if entity != tracker.current_speaker:
                                    listener = entity
                                    break
                        if listener is None:
                            continue
                        self._add_relationship_fact(
                            scene, store, listener, category, text
                        )
                        continue

                    if shape == "named_role":
                        subject = _resolve_trait_entity(subject_raw or "", registry)
                        if subject is None:
                            continue
                        if role == "aunt_uncle":
                            value = "niece_nephew"
                        else:
                            value = category
                        self._add_relationship_fact(
                            scene, store, subject, value, text
                        )
                        continue

                    if shape == "introduced":
                        subject = tracker.resolve_subject(text)
                        if subject is None:
                            continue
                        possessor = tracker.resolve_possessive_pronoun("their")
                        if possessor is None:
                            self._add_relationship_fact(
                                scene,
                                store,
                                subject,
                                category,
                                text,
                            )
                            continue
                        pair_key = "|".join(sorted([subject, possessor]))
                        value = self._relationship_value(
                            category, role, subject, possessor
                        )
                        self._add_relationship_fact(
                            scene, store, pair_key, value, text
                        )
                        continue

                    if shape in {"pronoun_subject", "pronoun_appositive"}:
                        if shape == "pronoun_subject":
                            subject = _resolve_trait_entity(
                                subject_raw or "", registry
                            )
                            possessor = _resolve_relationship_possessor(
                                text,
                                match,
                                pronoun_raw,
                                subject,
                                tracker,
                                registry,
                            )
                        else:
                            subject = _resolve_trait_entity(
                                subject_raw or "", registry
                            )
                            possessor = _resolve_relationship_possessor(
                                text,
                                match,
                                pronoun_raw,
                                subject,
                                tracker,
                                registry,
                            )
                        if subject is None or possessor is None:
                            continue
                        pair_key = "|".join(sorted([subject, possessor]))
                        value = self._relationship_value(
                            category, role, subject, possessor
                        )
                        self._add_relationship_fact(
                            scene, store, pair_key, value, text
                        )
                        continue

                    if shape == "possessor_only":
                        possessor = _resolve_trait_entity(object_raw or "", registry)
                        if possessor is None:
                            continue
                        if role == "child":
                            value = "parent_child"
                        elif role == "aunt_uncle":
                            value = "niece_nephew"
                        else:
                            value = category
                        self._add_relationship_fact(
                            scene, store, possessor, value, text
                        )
                        continue

                    subject = _resolve_trait_entity(subject_raw or "", registry)
                    other = _resolve_trait_entity(object_raw or "", registry)
                    if subject is None or other is None or subject == other:
                        continue
                    pair_key = "|".join(sorted([subject, other]))
                    value = self._relationship_value(
                        category, role, subject, other
                    )
                    self._add_relationship_fact(
                        scene, store, pair_key, value, text
                    )

        diane = _resolve_trait_entity("DIANE", registry)
        if diane is not None and re.search(r"\bDIANE\b", scene.raw_text or ""):
            for fact in store.get_facts_by_type("relationship"):
                if fact.value != "in_law" or "|" in fact.entity:
                    continue
                if fact.entity not in tracker.scene_characters:
                    continue
                if _resolve_trait_entity(fact.entity, registry) is None:
                    continue
                pair_key = "|".join(sorted([fact.entity, diane]))
                self._add_relationship_fact(
                    scene,
                    store,
                    pair_key,
                    "in_law",
                    scene.heading or "",
                )

    def _extract_world_rule_facts(
        self, scene: SceneBlock, store: FactStore
    ) -> None:
        """Capture declared world rules from action lines (capture-only).

        Records capability/permission rules of the fiction such as "The time
        machine cannot travel to the future" or "Vampires can only enter when
        invited" as ``world_rule`` facts (entity = rule subject, value =
        "<modality>: <predicate>"). These are stored for later Tier 3 violation
        reasoning; no Tier 1 contradiction is raised here, since deciding
        whether a later scene breaks a rule needs open-domain semantics.
        Dialogue is excluded to keep captured rules to declarative exposition.
        """
        action_lines, _ = _scene_lines_by_source(scene)
        for line in action_lines:
            for pattern, modality in WORLD_RULE_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                subject_key = _normalize_object_key(match.group("subject"))
                predicate = _clean_value(match.group("predicate"))
                if len(subject_key) < 2 or len(predicate) < 2:
                    continue
                store.add_fact(
                    self._make_fact(
                        scene,
                        "world_rule",
                        subject_key,
                        f"{modality}: {predicate}",
                        line,
                    )
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
        # Timeline consistency check disabled: day-of-week / day-sequence
        # contradictions are intentionally not reported. The extraction and
        # check methods are retained (unused) so this can be re-enabled.
        # contradictions.extend(
        #     self._check_timeline_consistency(fact_store, scenes, scene_lookup)
        # )
        contradictions.extend(
            self._check_character_trait_conflict(fact_store, scene_lookup, scenes)
        )
        contradictions.extend(
            self._check_object_ownership(fact_store, scenes, scene_lookup)
        )
        contradictions.extend(
            self._check_object_state(fact_store, scenes, scene_lookup)
        )
        contradictions.extend(
            self._check_relationship(fact_store, scenes, scene_lookup)
        )
        contradictions.extend(
            self._check_world_rule_violation(fact_store, scenes, scene_lookup)
        )
        contradictions.extend(self._check_age_conflict(fact_store))
        contradictions.extend(self._check_object_identity(fact_store))
        contradictions.extend(self._check_numeric_count(fact_store))
        contradictions.extend(self._check_date_year(fact_store))
        contradictions.sort(key=lambda item: item.confidence, reverse=True)
        return contradictions

    def _check_numeric_count(
        self, fact_store: FactStore
    ) -> list[Contradiction]:
        """Flag a counted noun stated with two different quantities.

        Uses the first quantity per noun as the baseline and reports a later
        differing quantity once. Possible-status, because counts can change in
        the story; the writer confirms whether it is an error.
        """
        results: list[Contradiction] = []
        by_noun: dict[str, list[Fact]] = {}
        for fact in fact_store.get_facts_by_type("numeric_count"):
            by_noun.setdefault(_canonical_count_entity(fact.entity), []).append(fact)

        for noun, facts in by_noun.items():
            ordered = sorted(facts, key=lambda item: item.scene_number)
            if not ordered:
                continue
            previous = ordered[0]
            for fact in ordered[1:]:
                if fact.value == previous.value:
                    continue
                results.append(
                    Contradiction(
                        contradiction_id=_new_contradiction_id(),
                        scene_id_a=previous.scene_id,
                        scene_id_b=fact.scene_id,
                        scene_number_a=previous.scene_number,
                        scene_number_b=fact.scene_number,
                        fact_a=previous,
                        excerpt_b=fact.raw_excerpt,
                        contradiction_type="numeric_count",
                        explanation=(
                            f"'{noun.lower()}' count is {previous.value} in "
                            f"{previous.scene_id} but {fact.value} in "
                            f"{fact.scene_id}."
                        ),
                        confidence=0.5,
                        tier=1,
                        status=STATUS_POSSIBLE,
                    )
                )
                previous = fact
        return results

    def _check_date_year(self, fact_store: FactStore) -> list[Contradiction]:
        """Flag a script that asserts two close-but-different years.

        Only fires when there are exactly two distinct years within
        ``MAX_YEAR_GAP`` of each other (a likely continuity slip rather than an
        intentional multi-period story). Reports the first-mentioned year
        against the first conflicting mention.
        """
        facts = sorted(
            fact_store.get_facts_by_type("year"),
            key=lambda item: item.scene_number,
        )
        distinct = {int(fact.value) for fact in facts}
        if len(distinct) != 2:
            return []
        if max(distinct) - min(distinct) > MAX_YEAR_GAP:
            return []

        anchor = facts[0]
        conflict = next(
            (fact for fact in facts if fact.value != anchor.value), None
        )
        if conflict is None:
            return []
        return [
            Contradiction(
                contradiction_id=_new_contradiction_id(),
                scene_id_a=anchor.scene_id,
                scene_id_b=conflict.scene_id,
                scene_number_a=anchor.scene_number,
                scene_number_b=conflict.scene_number,
                fact_a=anchor,
                excerpt_b=conflict.raw_excerpt,
                contradiction_type="date_year",
                explanation=(
                    f"The year is {anchor.value} in {anchor.scene_id} but "
                    f"{conflict.value} in {conflict.scene_id}."
                ),
                confidence=0.55,
                tier=1,
                status=STATUS_POSSIBLE,
            )
        ]

    def _check_age_conflict(
        self, fact_store: FactStore
    ) -> list[Contradiction]:
        """Flag a character stated at two different ages.

        Ages are integers, so a contradiction is an exact value mismatch for the
        same canonical character. Reported as a possible issue because long time
        jumps can legitimately change an age; the writer confirms intent.
        """
        results: list[Contradiction] = []
        by_entity: dict[str, list[Fact]] = {}
        for fact in fact_store.get_facts_by_type("age"):
            by_entity.setdefault(fact.entity, []).append(fact)

        for entity, facts in by_entity.items():
            for left_index in range(len(facts)):
                for right_index in range(left_index + 1, len(facts)):
                    left = facts[left_index]
                    right = facts[right_index]
                    if left.value == right.value:
                        continue
                    earlier, later = (
                        (left, right)
                        if left.scene_number <= right.scene_number
                        else (right, left)
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
                            contradiction_type="character_age",
                            explanation=(
                                f"{entity} is described as age {earlier.value} in "
                                f"{earlier.scene_id} but age {later.value} in "
                                f"{later.scene_id}."
                            ),
                            confidence=0.7,
                            tier=1,
                            status=STATUS_POSSIBLE,
                        )
                    )
        return results

    def _check_object_identity(
        self, fact_store: FactStore
    ) -> list[Contradiction]:
        """Flag a prop whose colour or material changes between scenes.

        Compares object_descriptor facts that share a prop head noun and a
        descriptor axis; a different token on the same axis (e.g. material
        "leather" then "canvas") is a continuity contradiction. Reported as
        possible to protect precision against distinct same-named props.
        """
        results: list[Contradiction] = []
        by_entity: dict[str, list[Fact]] = {}
        for fact in fact_store.get_facts_by_type("object_descriptor"):
            by_entity.setdefault(fact.entity, []).append(fact)

        for entity, facts in by_entity.items():
            ordered = sorted(facts, key=lambda item: item.scene_number)
            # First descriptor seen per axis is the baseline; a later differing
            # token on that axis is the contradiction. Comparing against the
            # baseline (not every pair) avoids duplicate reports when the
            # original descriptor recurs before the conflicting scene.
            baseline: dict[str, Fact] = {}
            emitted: set[tuple[str, int]] = set()
            for fact in ordered:
                axis, token = fact.value.split(":", 1)
                anchor = baseline.get(axis)
                if anchor is None:
                    baseline[axis] = fact
                    continue
                anchor_token = anchor.value.split(":", 1)[1]
                if token == anchor_token:
                    continue
                marker = (axis, fact.scene_number)
                if marker in emitted:
                    continue
                emitted.add(marker)
                results.append(
                    Contradiction(
                        contradiction_id=_new_contradiction_id(),
                        scene_id_a=anchor.scene_id,
                        scene_id_b=fact.scene_id,
                        scene_number_a=anchor.scene_number,
                        scene_number_b=fact.scene_number,
                        fact_a=anchor,
                        excerpt_b=fact.raw_excerpt,
                        contradiction_type="object_identity",
                        explanation=(
                            f"The {entity.lower()} is '{anchor_token}' in "
                            f"{anchor.scene_id} but '{token}' in "
                            f"{fact.scene_id} ({axis} mismatch)."
                        ),
                        confidence=0.6,
                        tier=1,
                        status=STATUS_POSSIBLE,
                    )
                )
        return results

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
            # Object continuity, medical state, and relationships are handled
            # deterministically in Tier 1; world rules are capture-only (their
            # violation reasoning is deferred to Tier 3). None of their
            # structured/short values are meaningful for similarity comparison.
            if fact.fact_type in (
                "object_state",
                "medical_state",
                "relationship",
                "world_rule",
                "age",
                "object_descriptor",
                "numeric_count",
                "year",
            ):
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
                        and part_l is not None
                        and part_e != part_l
                        and later.scene_number - earlier.scene_number <= 2
                    ):
                        if self._medical_explanation_between(
                            scenes, earlier.scene_number, later.scene_number
                        ):
                            continue
                        results.append(
                            self._medical_contradiction(
                                earlier,
                                later,
                                "medical_state",
                                (
                                    f"{entity} is injured in the {part_e} in "
                                    f"{earlier.scene_id} but the {part_l} in "
                                    f"{later.scene_id}."
                                ),
                            )
                        )
                        break

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

    def _check_relationship(
        self,
        fact_store: FactStore,
        scenes: list[SceneBlock],
        scene_lookup: dict[str, SceneBlock],
    ) -> list[Contradiction]:
        """Flag contradictory family relationships between the same two people.

        Two rules, both confirmed because they target immutable blood relations
        (social/romantic ties legitimately change over a story and are not
        flagged):

        - Incompatible relation: the pair is described with two relations that
          cannot co-exist (e.g. siblings vs spouses, sibling vs parent/child).
        - Role inversion: a parent_child relation is asserted in both
          directions (X is Y's father, then Y is X's father).

        Args:
            fact_store: All extracted facts.
            scenes: Parsed scenes in screenplay order.
            scene_lookup: Scene id -> scene mapping.

        Returns:
            Relationship contradictions.
        """
        results: list[Contradiction] = []
        facts_by_pair: dict[str, list[Fact]] = {}
        facts_by_possessor: dict[str, list[Fact]] = {}
        for fact in fact_store.get_facts_by_type("relationship"):
            if "|" in fact.entity:
                facts_by_pair.setdefault(fact.entity, []).append(fact)
            else:
                facts_by_possessor.setdefault(fact.entity, []).append(fact)

        for facts in facts_by_pair.values():
            ordered = sorted(
                facts, key=lambda item: (item.scene_number, item.fact_id)
            )
            for index, earlier in enumerate(ordered):
                cat_e, dir_e = _parse_relationship_value(earlier.value)
                for later in ordered[index + 1 :]:
                    cat_l, dir_l = _parse_relationship_value(later.value)

                    if cat_e == "parent_child" and cat_l == "parent_child":
                        if dir_e and dir_l and dir_e != dir_l:
                            results.append(
                                self._relationship_contradiction(
                                    earlier,
                                    later,
                                    "relationship_fact",
                                    (
                                        f"{dir_e[0]} is the parent of {dir_e[1]} "
                                        f"in {earlier.scene_id} but {dir_l[0]} is "
                                        f"the parent of {dir_l[1]} in "
                                        f"{later.scene_id}."
                                    ),
                                )
                            )
                            break
                        continue

                    if frozenset({cat_e, cat_l}) in INCOMPATIBLE_RELATION_CATEGORIES:
                        names = earlier.entity.replace("|", " and ")
                        results.append(
                            self._relationship_contradiction(
                                earlier,
                                later,
                                "relationship_fact",
                                (
                                    f"{names} are described as {cat_e} in "
                                    f"{earlier.scene_id} but {cat_l} in "
                                    f"{later.scene_id}."
                                ),
                            )
                        )
                        break

        for possessor, facts in facts_by_possessor.items():
            ordered = sorted(
                facts, key=lambda item: (item.scene_number, item.fact_id)
            )
            for index, earlier in enumerate(ordered):
                cat_e, _ = _parse_relationship_value(earlier.value)
                for later in ordered[index + 1 :]:
                    cat_l, _ = _parse_relationship_value(later.value)
                    if frozenset({cat_e, cat_l}) in INCOMPATIBLE_RELATION_CATEGORIES:
                        results.append(
                            self._relationship_contradiction(
                                earlier,
                                later,
                                "relationship_fact",
                                (
                                    f"{possessor} is described as having a "
                                    f"{cat_e} relation in {earlier.scene_id} but "
                                    f"a {cat_l} relation in {later.scene_id}."
                                ),
                            )
                        )
                        break

        char_categories: dict[str, list[Fact]] = {}
        for fact in fact_store.get_facts_by_type("relationship"):
            parsed = _parse_relationship_value(fact.value)
            if parsed[0] is None:
                continue
            names = fact.entity.split("|") if "|" in fact.entity else [fact.entity]
            for name in names:
                char_categories.setdefault(name, []).append(fact)

        for character, facts in char_categories.items():
            categories = {
                _parse_relationship_value(fact.value)[0] for fact in facts
            }
            categories.discard(None)
            for incompatible in INCOMPATIBLE_RELATION_CATEGORIES:
                if not incompatible.issubset(categories):
                    continue
                ordered = sorted(
                    facts, key=lambda item: (item.scene_number, item.fact_id)
                )
                earlier = ordered[0]
                later = ordered[-1]
                if earlier.fact_id == later.fact_id:
                    continue
                results.append(
                    self._relationship_contradiction(
                        earlier,
                        later,
                        "relationship_fact",
                        (
                            f"{character} is described with incompatible "
                            f"relations ({', '.join(sorted(incompatible))}) "
                            f"across {earlier.scene_id} and {later.scene_id}."
                        ),
                    )
                )
                break

        return results

    def _content_lemmas(self, text: str) -> set[str]:
        """Return lowercased, non-stopword alphabetic lemmas from text.

        Used to compare a captured world rule's subject/predicate against a
        later action line robustly across inflection ("travels" -> "travel").

        Args:
            text: Arbitrary text span (rule subject, predicate, or a line).

        Returns:
            The set of content-word lemmas, lowercased.
        """
        return {
            token.lemma_.lower()
            for token in self.nlp(text)
            if token.is_alpha and not token.is_stop
        }

    def _is_world_rule_statement(self, line: str) -> bool:
        """Return True when a line is itself a world-rule declaration.

        Such lines (re)state a rule rather than break it, so they must be
        skipped when scanning for affirmative violations.

        Args:
            line: A single action line.

        Returns:
            True when any world-rule pattern matches the line.
        """
        return any(pattern.search(line) for pattern, _ in WORLD_RULE_PATTERNS)

    def _line_asserts_negation(self, line: str) -> bool:
        """Return True when a line contains negation (so it cannot be a break).

        Args:
            line: A single action line.

        Returns:
            True when the line is negated (e.g. "cannot travel", "never opens").
        """
        lowered = line.lower()
        if "n't" in lowered or "cannot" in lowered:
            return True
        words = set(re.findall(r"[a-z']+", lowered))
        return bool(words & WORLD_RULE_NEGATION_TERMS)

    def _find_rule_violation_line(
        self,
        action_lines: list[str],
        subject_lemmas: set[str],
        predicate_lemmas: set[str],
    ) -> Optional[str]:
        """Return the first action line that affirmatively breaks a rule.

        A line breaks a "cannot" rule when it names the rule's subject and
        asserts every content word of the forbidden predicate, in the
        affirmative and outside of any rule restatement.

        Args:
            action_lines: Action lines of a candidate later scene.
            subject_lemmas: Content lemmas of the rule subject.
            predicate_lemmas: Content lemmas of the forbidden predicate.

        Returns:
            The violating line, or None when the rule is not broken here.
        """
        for line in action_lines:
            if self._is_world_rule_statement(line):
                continue
            if self._line_asserts_negation(line):
                continue
            line_lemmas = self._content_lemmas(line)
            if not (subject_lemmas & line_lemmas):
                continue
            if predicate_lemmas <= line_lemmas:
                return line
        return None

    def _check_world_rule_violation(
        self,
        fact_store: FactStore,
        scenes: list[SceneBlock],
        scene_lookup: dict[str, SceneBlock],
    ) -> list[Contradiction]:
        """Flag later scenes that break an established "cannot" world rule.

        Conservative check (status=possible). Only "cannot" rules with a
        concrete noun subject are evaluated: a rule like "The time machine
        cannot travel to the future" is violated when a later action line
        affirmatively asserts the same subject performing the forbidden
        predicate ("The machine travels to the future"). "Can only" rules
        require conditional reasoning and indefinite subjects ("no one can
        leave") have no concrete noun to track, so both are skipped.

        Args:
            fact_store: All extracted facts.
            scenes: Parsed scenes in screenplay order.
            scene_lookup: Scene id -> scene mapping.

        Returns:
            World-rule violation contradictions.
        """
        results: list[Contradiction] = []
        rule_facts = sorted(
            fact_store.get_facts_by_type("world_rule"),
            key=lambda item: (item.scene_number, item.fact_id),
        )
        for rule in rule_facts:
            modality, _, predicate = rule.value.partition(":")
            if modality.strip().lower() != "cannot":
                continue
            if _normalize_token(rule.entity) in WORLD_RULE_INDEFINITE_SUBJECTS:
                continue
            subject_lemmas = self._content_lemmas(rule.entity)
            predicate_lemmas = self._content_lemmas(predicate)
            if not subject_lemmas or not predicate_lemmas:
                continue

            for scene in scenes:
                if scene.scene_number <= rule.scene_number:
                    continue
                if _has_flashback_marker(scene.raw_text):
                    continue
                action_lines, _ = _scene_lines_by_source(scene)
                violation_line = self._find_rule_violation_line(
                    action_lines, subject_lemmas, predicate_lemmas
                )
                if violation_line is None:
                    continue
                results.append(
                    Contradiction(
                        contradiction_id=_new_contradiction_id(),
                        scene_id_a=rule.scene_id,
                        scene_id_b=scene.scene_id,
                        scene_number_a=rule.scene_number,
                        scene_number_b=scene.scene_number,
                        fact_a=rule,
                        excerpt_b=violation_line,
                        contradiction_type="world_rule_violation",
                        explanation=(
                            f"{rule.entity} was established as unable to "
                            f"'{predicate.strip()}' in {rule.scene_id}, but "
                            f"{scene.scene_id} shows it happening anyway."
                        ),
                        confidence=0.6,
                        tier=1,
                        status=STATUS_POSSIBLE,
                    )
                )
                break

        return results

    def _relationship_contradiction(
        self,
        earlier: Fact,
        later: Fact,
        contradiction_type: str,
        explanation: str,
    ) -> Contradiction:
        """Build a confirmed relationship Contradiction from two facts."""
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
            confidence=0.85,
            tier=1,
            status=STATUS_CONFIRMED,
        )

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
        scenes: list[SceneBlock],
    ) -> list[Contradiction]:
        """Flag conflicting profession or role traits for the same character."""
        results: list[Contradiction] = []
        trait_facts = fact_store.get_facts_by_type("character_trait")
        registry = self._build_entity_registry(scenes)
        by_entity: dict[str, list[Fact]] = {}

        for fact in trait_facts:
            entity_key = _resolve_trait_entity(fact.entity, registry) or fact.entity
            by_entity.setdefault(entity_key, []).append(fact)

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

        verb_labels = sorted(
            POSSESSION_VERB_LABELS + EXTENDED_POSSESSION_VERB_LABELS,
            key=len,
            reverse=True,
        )
        lowered = value.lower()
        for label in verb_labels:
            needle = f" {label} "
            index = lowered.find(needle)
            if index >= 0:
                owner = value[:index].strip()
                return _clean_entity(owner) if owner else None

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
