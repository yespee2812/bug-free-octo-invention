"""Scene dependency analysis for Fountain-format screenplays."""

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import networkx as nx
import spacy
from spacy.language import Language
from spacy.tokens import Doc

SCENE_HEADING_PATTERN = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s+(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
TRANSITION_PATTERN = re.compile(
    r"^(FADE IN\.?|FADE OUT\.?|FADE TO BLACK\.?|CUT TO:|DISSOLVE TO:|"
    r"MATCH CUT TO:|SMASH CUT TO:|TIME CUT:|INTERCUT:|END\.?)$",
    re.IGNORECASE,
)
CHARACTER_CUE_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9 .'\-@()]+$"
)
CAPS_SPAN_PATTERN = re.compile(
    r"\b[A-Z][A-Z0-9'\-]+(?:\s+[A-Z][A-Z0-9'\-]+)*\b"
)
# First words of all-caps spans that are camera/editorial directions or
# sound emphasis, not props (e.g. "CLOSE ON", "ANGLE ON", "BANG").
CAPS_PROP_STOP_FIRST_WORDS: frozenset[str] = frozenset(
    {
        "ANGLE", "BACK", "BANG", "BEAT", "BOOM", "CHYRON", "CLOSE",
        "CONTINUOUS", "CRASH", "END", "FLASHBACK", "INSERT", "INTERCUT",
        "LATER", "MONTAGE", "NOTE", "POV", "SERIES", "SLAM", "SUPER",
        "THUD", "TITLE",
    }
)
# Professional titles that mark a multi-word caps span as a character even
# when that character never receives a dialogue cue (e.g. "DETECTIVE MILLER").
PERSON_TITLE_WORDS: frozenset[str] = frozenset(
    {
        "AGENT", "CAPTAIN", "CHIEF", "COACH", "CORONER", "DEPUTY",
        "DETECTIVE", "DOCTOR", "DR", "JUDGE", "LIEUTENANT", "MAYOR",
        "MISS", "MR", "MRS", "MS", "NURSE", "OFFICER", "PROFESSOR",
        "SENATOR", "SERGEANT", "SHERIFF",
    }
)
# Constructions whose subject is a person by construction. They recover
# cue-less characters that NER misses on ALL-CAPS action text, mirroring the
# contradiction engine's character_status / character_trait facts (e.g.
# "MARCUS is a surgeon", "COLE is dead", "VANCE works as a fixer").
CHARACTER_FACT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?<![A-Za-z0-9])(?P<entity>[A-Za-z][A-Za-z0-9 .'\-]+?)\s+"
        r"(?:is|was)\s+(?:dead|killed)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<![A-Za-z0-9])(?P<entity>[A-Za-z][A-Za-z0-9 .'\-]+?)\s+"
        r"(?:has\s+)?died\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<![A-Za-z0-9])(?P<entity>[A-Za-z][A-Za-z0-9 .'\-]+?)\s+"
        r"works\s+as\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<![A-Za-z0-9])(?P<entity>[A-Za-z][A-Za-z0-9 .'\-]+?)\s+"
        r"is\s+(?:a|an)\s+(?P<role>[A-Za-z][A-Za-z\-]+)",
        re.IGNORECASE,
    ),
)
# Pronouns and indefinite words that can head a fact construction but never
# name a character.
NON_CHARACTER_WORDS: frozenset[str] = frozenset(
    {
        "ALL", "ANYONE", "BOTH", "EITHER", "EVERYBODY", "EVERYONE",
        "EVERYTHING", "HE", "HERE", "I", "IT", "NEITHER", "NOBODY",
        "NONE", "NOTHING", "ONE", "SHE", "SOMEONE", "SOMETHING", "THAT",
        "THERE", "THESE", "THEY", "THIS", "THOSE", "WE", "WHAT", "WHO",
        "YOU",
    }
)
# Inanimate nouns that "die"/"are dead" idiomatically (e.g. "the engine
# died"), so such a construction is never a character fact.
INANIMATE_DEATH_NOUNS: frozenset[str] = frozenset(
    {
        "BATTERY", "CAR", "CHATTER", "CONVERSATION", "CROWD", "ENGINE",
        "LIGHT", "LIGHTS", "LINE", "MOTOR", "MUSIC", "NOISE", "PARTY",
        "PHONE", "RADIO", "SIGNAL", "SOUND",
    }
)
# Generic head nouns for "X is a <role>" that describe anyone or anything
# rather than establishing a character role.
GENERIC_ROLE_TERMS: frozenset[str] = frozenset(
    {
        "beast", "bit", "blast", "boy", "child", "disaster", "dream",
        "few", "friend", "girl", "guy", "joke", "kid", "lot", "man",
        "mess", "moment", "one", "person", "stranger", "thing", "while",
        "woman", "wonder",
    }
)
# Possession and handoff phrasing. Shared with the contradiction engine's
# object-ownership facts; objects of these verbs are story props even when
# the writer never capitalizes them (e.g. "ELENA picks up the blue ledger").
OBJECT_OWNERSHIP_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?P<owner>[A-Z][A-Z0-9 .'\-]+?)\s+picks\s+up\s+(?:the\s+)?"
            r"(?P<object>[a-z][a-z0-9\s\-]+?)(?:\s+from|\s+on|\s+and|\.|$)",
            re.IGNORECASE,
        ),
        "picks up",
    ),
    (
        re.compile(
            r"(?P<owner>[A-Z][A-Z0-9 .'\-]+?)\s+has\s+(?:the\s+)?"
            r"(?P<object>[a-z][a-z0-9\s\-]+?)(?:\s+and|\s+on|\.|$)",
            re.IGNORECASE,
        ),
        "has",
    ),
    (
        re.compile(
            r"(?P<owner>[A-Z][A-Z0-9 .'\-]+?)\s+gives\s+(?:the\s+)?"
            r"(?P<object>[a-z][a-z0-9\s\-]+?)\s+to\s+"
            r"(?P<recipient>[A-Z][A-Z0-9 .'\-]+)",
            re.IGNORECASE,
        ),
        "gives to",
    ),
)
EDGE_WEIGHTS: dict[str, float] = {
    "character": 1.0,
    "object": 0.7,
    "location": 0.4,
    "fact": 0.5,
}


@dataclass
class SceneBlock:
    """A parsed scene from a Fountain screenplay."""

    scene_id: str
    scene_number: int
    heading: str
    characters: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class DependencyEdge:
    """A directed dependency between two scenes."""

    from_scene_id: str
    to_scene_id: str
    weight: float
    edge_type: str
    explanation: str


def _normalize_token(value: str) -> str:
    """Return a normalized uppercase key for matching characters and objects."""
    return " ".join(value.upper().split())


def _normalize_object_key(value: str) -> str:
    """Return a normalized object key with leading articles removed."""
    normalized = _normalize_token(value)
    for article in ("A ", "AN ", "THE ", "HIS ", "HER ", "THEIR ", "ITS "):
        if normalized.startswith(article):
            normalized = normalized[len(article) :].strip()
    return normalized


def _is_scene_heading(line: str) -> bool:
    """Return True when the line is a Fountain scene heading."""
    stripped = line.strip()
    return bool(
        re.match(r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s+", stripped, re.IGNORECASE)
    )


def _is_transition(line: str) -> bool:
    """Return True when the line is a screenplay transition."""
    stripped = line.strip()
    if TRANSITION_PATTERN.match(stripped):
        return True
    return stripped.endswith(":") and stripped == stripped.upper() and len(stripped) > 1


def _is_character_cue(line: str) -> bool:
    """Return True when the line is an all-caps character cue."""
    stripped = line.strip()
    if not stripped or _is_scene_heading(stripped) or _is_transition(stripped):
        return False
    if stripped.startswith("(") and stripped.endswith(")"):
        return False
    if not CHARACTER_CUE_PATTERN.match(stripped):
        return False
    letters = [char for char in stripped if char.isalpha()]
    if not letters:
        return False
    return all(char.isupper() for char in letters)


def _extract_location_from_heading(heading: str) -> str:
    """Extract the primary location name from a scene heading."""
    match = re.match(
        r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s+(.+)$",
        heading.strip(),
        re.IGNORECASE,
    )
    if not match:
        return ""
    location_part = match.group(2).strip()
    if " - " in location_part:
        location_part = location_part.split(" - ", maxsplit=1)[0].strip()
    if " – " in location_part:
        location_part = location_part.split(" – ", maxsplit=1)[0].strip()
    return location_part.upper()


def _split_action_and_dialogue(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split scene lines into action lines and character cue lines."""
    action_lines: list[str] = []
    character_lines: list[str] = []
    in_dialogue = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            in_dialogue = False
            continue
        if _is_transition(stripped):
            in_dialogue = False
            continue
        if _is_character_cue(stripped):
            character_lines.append(stripped)
            in_dialogue = True
            continue
        if in_dialogue and (stripped.startswith("(") or not stripped.isupper()):
            continue
        in_dialogue = False
        action_lines.append(stripped)

    return action_lines, character_lines


def _collect_character_aliases(text: str) -> dict[str, str]:
    """Map normalized character aliases to canonical cue names for a script.

    Aliases include the cue name itself (with parenthetical extensions
    removed) and its article-stripped form, so action mentions like
    "THE INFORMANT" or "INFORMANT" resolve to the same character.
    """
    aliases: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not _is_character_cue(stripped):
            continue
        name = _normalize_token(re.sub(r"\([^)]*\)", "", stripped))
        if not name:
            continue
        aliases.setdefault(name, name)
        aliases.setdefault(_normalize_object_key(name), name)
    return aliases


def _person_entity_keys(
    nlp: Language, action_text: str, doc: Optional[Doc]
) -> set[str]:
    """Return normalized keys for PERSON entities found in action text.

    NER results differ between ALL-CAPS and title-cased text, so persons are
    collected from both the raw doc and a copy where caps spans are
    title-cased (e.g. "MARCUS slumps" becomes "Marcus slumps"). The union
    maximizes recall of the person filter for cue-less characters.

    Args:
        nlp: Loaded spaCy pipeline.
        action_text: Joined action lines of one scene.
        doc: Already-parsed doc over action_text, or None when empty.

    Returns:
        Normalized keys (raw and article-stripped) for detected persons.
    """
    if not action_text:
        return set()

    docs: list[Doc] = [doc] if doc is not None else []
    transformed = CAPS_SPAN_PATTERN.sub(
        lambda span_match: span_match.group(0).title(), action_text
    )
    if transformed != action_text:
        docs.append(nlp(transformed))

    keys: set[str] = set()
    for parsed in docs:
        for ent in parsed.ents:
            if ent.label_ != "PERSON":
                continue
            keys.add(_normalize_token(ent.text))
            keys.add(_normalize_object_key(ent.text))
    return keys


def _trailing_caps_name(entity_text: str) -> str:
    """Return the last ALL-CAPS span in a captured entity, or empty string.

    Fact patterns can over-capture leading prose (e.g. "Smoke fills the dock.
    DETECTIVE VANCE"), so the trailing caps run isolates the actual name and,
    by requiring caps, keeps the signal to screenplay-style names rather than
    sentence-cased nouns like "The engine".

    Args:
        entity_text: Raw entity group captured by a character-fact pattern.

    Returns:
        The final ALL-CAPS word span, or an empty string when none is found.
    """
    spans = CAPS_SPAN_PATTERN.findall(entity_text)
    return spans[-1] if spans else ""


def _extract_structural_characters(
    action_lines: list[str], character_aliases: dict[str, str]
) -> set[str]:
    """Return character keys named in structural personhood constructions.

    The subject of "X is dead", "X died", "X works as ...", and "X is a
    <role>" is a person by construction, so these recover cue-less characters
    that NER misses on ALL-CAPS action text. Pronouns, inanimate nouns that
    die idiomatically, and generic role nouns are filtered for precision, and
    only ALL-CAPS names are promoted.

    Args:
        action_lines: Action (non-dialogue) lines of one scene.
        character_aliases: Normalized alias -> canonical cue name map.

    Returns:
        Normalized character keys detected from fact phrasing.
    """
    characters: set[str] = set()
    for line in action_lines:
        for pattern in CHARACTER_FACT_PATTERNS:
            for match in pattern.finditer(line):
                role = match.groupdict().get("role")
                if role and role.lower() in GENERIC_ROLE_TERMS:
                    continue
                name = _trailing_caps_name(match.group("entity"))
                key = _normalize_object_key(name)
                if len(key) < 2 or key in INANIMATE_DEATH_NOUNS:
                    continue
                if all(word in NON_CHARACTER_WORDS for word in key.split()):
                    continue
                characters.add(character_aliases.get(key, key))
    return characters


def _match_prop_by_suffix(key: str, known_props: set[str]) -> Optional[str]:
    """Resolve a key to an established prop key, exactly or by suffix.

    Args:
        key: Normalized object key for a mention (e.g. "BRIEFCASE").
        known_props: Caps prop keys established so far.

    Returns:
        The canonical prop key (e.g. "RED BRIEFCASE"), or None if unmatched.
    """
    if key in known_props:
        return key
    for prop in known_props:
        if prop.endswith(" " + key):
            return prop
    return None


def _extract_ownership_objects(
    action_lines: list[str],
    character_aliases: dict[str, str],
    known_props: set[str],
) -> list[str]:
    """Extract prop keys from possession and handoff verbs in action lines.

    Objects of verbs like "picks up", "has", and "gives ... to" are story
    props even when never capitalized, so this recovers props that the
    ALL-CAPS convention misses (e.g. "the blue ledger").

    Args:
        action_lines: Action (non-dialogue) lines of one scene.
        character_aliases: Normalized alias -> canonical cue name map.
        known_props: Established prop keys, used to canonicalize mentions.

    Returns:
        Ordered, deduplicated prop keys found via ownership phrasing.
    """
    objects: list[str] = []
    seen: set[str] = set()
    for line in action_lines:
        for pattern, _verb in OBJECT_OWNERSHIP_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            key = _normalize_object_key(match.group("object"))
            if len(key) < 2 or key in character_aliases:
                continue
            canonical = _match_prop_by_suffix(key, known_props) or key
            if canonical in seen:
                continue
            seen.add(canonical)
            objects.append(canonical)
    return objects


def _extract_caps_props_and_presences(
    action_lines: list[str],
    character_aliases: dict[str, str],
    person_keys: set[str],
) -> tuple[list[str], set[str]]:
    """Split all-caps action spans into prop names and character presences.

    Follows the screenwriting convention that important props are written in
    ALL CAPS in action lines. Spans matching known character cues count as
    that character being present in the scene rather than as objects, and
    multi-word spans starting with a professional title (e.g. "DETECTIVE
    MILLER") are treated as characters even without a dialogue cue.

    Args:
        action_lines: Action (non-dialogue) lines of one scene.
        character_aliases: Normalized alias -> canonical cue name map.
        person_keys: Normalized PERSON entity keys from spaCy NER.

    Returns:
        Tuple of (ordered caps prop keys, canonical character names present).
    """
    props: list[str] = []
    seen_props: set[str] = set()
    presences: set[str] = set()

    for line in action_lines:
        for span_match in CAPS_SPAN_PATTERN.finditer(line):
            span = span_match.group(0).strip("'- ")
            token_key = _normalize_token(span)
            object_key = _normalize_object_key(span)
            if len(object_key) < 2:
                continue
            canonical_character = character_aliases.get(
                token_key, character_aliases.get(object_key, "")
            )
            if canonical_character:
                presences.add(canonical_character)
                continue
            span_words = object_key.split()
            if (
                len(span_words) >= 2
                and span_words[0].rstrip(".") in PERSON_TITLE_WORDS
            ):
                presences.add(token_key)
                continue
            if span_words[0] in CAPS_PROP_STOP_FIRST_WORDS:
                continue
            if token_key in person_keys or object_key in person_keys:
                continue
            if object_key in seen_props:
                continue
            seen_props.add(object_key)
            props.append(object_key)

    return props, presences


def _match_known_prop_mentions(
    doc: Optional[Doc], known_props: set[str]
) -> list[str]:
    """Map noun-chunk mentions in action text to established caps props.

    A lowercase mention links to a prop when its normalized key equals the
    prop key or is a word-boundary suffix of it (e.g. "the briefcase"
    matches "RED BRIEFCASE"). Unmatched noun chunks are discarded, which
    keeps scenery and abstract nouns out of the object list.

    Args:
        doc: spaCy doc over the scene's action text, or None when empty.
        known_props: Caps prop keys established so far in screenplay order.

    Returns:
        Canonical prop keys mentioned in this scene's action text.
    """
    if doc is None or not known_props:
        return []

    mentions: list[str] = []
    seen: set[str] = set()
    for chunk in doc.noun_chunks:
        phrase = " ".join(token.text for token in chunk if not token.is_space)
        key = _normalize_object_key(phrase)
        if len(key) < 2:
            continue
        canonical = _match_prop_by_suffix(key, known_props)
        if canonical is not None and canonical not in seen:
            seen.add(canonical)
            mentions.append(canonical)

    return mentions


class SceneDependencyEngine:
    """Build and query a scene dependency graph from Fountain screenplay text."""

    def __init__(self) -> None:
        """Initialize the engine and load the spaCy English model once."""
        self.nlp: Language = spacy.load("en_core_web_sm")
        self.graph: nx.DiGraph = nx.DiGraph()
        self.scenes: list[SceneBlock] = []
        self._scene_lookup: dict[str, SceneBlock] = {}

    def parse_fountain_text(self, text: str) -> list[SceneBlock]:
        """Parse Fountain text into structured scene blocks.

        Splits the screenplay on scene headings (lines starting with INT. or EXT.),
        then extracts characters, objects, and locations for each scene.

        Characters include dialogue cues plus known characters named in
        ALL CAPS in action lines. Objects follow the screenwriting caps
        convention: a prop must be introduced in ALL CAPS in action; later
        lowercase mentions are linked back to the established prop.

        Args:
            text: Raw Fountain screenplay text.

        Returns:
            A list of SceneBlock objects in screenplay order.
        """
        matches = list(SCENE_HEADING_PATTERN.finditer(text))
        scenes: list[SceneBlock] = []

        if not matches:
            return scenes

        character_aliases = _collect_character_aliases(text)
        known_props: set[str] = set()

        for index, match in enumerate(matches, start=1):
            prefix = match.group(1).upper()
            location_tail = match.group(2).strip()
            heading = f"{prefix} {location_tail}".strip()
            start = match.start()
            end = matches[index].start() if index < len(matches) else len(text)
            raw_text = text[start:end].strip()
            body_lines = raw_text.splitlines()[1:]

            action_lines, character_lines = _split_action_and_dialogue(body_lines)
            cue_names = {_normalize_token(name) for name in character_lines}

            action_text = " ".join(action_lines)
            doc: Optional[Doc] = self.nlp(action_text) if action_text else None
            person_keys = _person_entity_keys(self.nlp, action_text, doc)
            structural_chars = _extract_structural_characters(
                action_lines, character_aliases
            )
            person_keys |= structural_chars

            caps_props, action_presences = _extract_caps_props_and_presences(
                action_lines, character_aliases, person_keys
            )
            ownership_props = _extract_ownership_objects(
                action_lines, character_aliases, known_props | set(caps_props)
            )
            known_props.update(caps_props)
            known_props.update(ownership_props)
            mention_props = _match_known_prop_mentions(doc, known_props)

            objects: list[str] = []
            for prop_name in caps_props + ownership_props + mention_props:
                if prop_name not in objects:
                    objects.append(prop_name)

            characters = sorted(
                cue_names | action_presences | structural_chars, key=str.lower
            )
            location = _extract_location_from_heading(heading)
            locations = [location] if location else []

            scene = SceneBlock(
                scene_id=f"scene_{index:03d}",
                scene_number=index,
                heading=heading.upper(),
                characters=characters,
                objects=objects,
                locations=locations,
                raw_text=raw_text,
            )
            scenes.append(scene)

        self.scenes = scenes
        self._scene_lookup = {scene.scene_id: scene for scene in scenes}
        return scenes

    def build_graph(self, scenes: list[SceneBlock]) -> None:
        """Build a directed dependency graph from parsed scenes.

        Adds one node per scene and creates edges from earlier scenes to later
        scenes when characters, objects, or locations first introduced in the
        earlier scene reappear downstream.

        Args:
            scenes: Parsed scene blocks.
        """
        self.scenes = sorted(scenes, key=lambda scene: scene.scene_number)
        self._scene_lookup = {scene.scene_id: scene for scene in self.scenes}
        self.graph = nx.DiGraph()

        for scene in self.scenes:
            self.graph.add_node(
                scene.scene_id,
                heading=scene.heading,
                scene_number=scene.scene_number,
            )

        first_seen_character: dict[str, str] = {}
        first_seen_object: dict[str, str] = {}
        first_seen_location: dict[str, str] = {}

        for scene in self.scenes:
            self._add_first_seen_edges(
                scene,
                scene.characters,
                first_seen_character,
                "character",
                "Character '{item}' first introduced",
            )
            self._add_first_seen_edges(
                scene,
                scene.objects,
                first_seen_object,
                "object",
                "Object '{item}' first mentioned",
            )
            self._add_first_seen_edges(
                scene,
                scene.locations,
                first_seen_location,
                "location",
                "Location '{item}' first established",
            )

    def _add_first_seen_edges(
        self,
        scene: SceneBlock,
        items: list[str],
        first_seen: dict[str, str],
        edge_type: str,
        explanation_template: str,
    ) -> None:
        """Add dependency edges based on first-seen tracking for a category."""
        weight = EDGE_WEIGHTS[edge_type]

        for item in items:
            key = (
                _normalize_token(item)
                if edge_type == "character"
                else _normalize_object_key(item)
                if edge_type == "object"
                else _normalize_token(item)
            )
            if not key:
                continue

            if key in first_seen:
                origin_scene_id = first_seen[key]
                if origin_scene_id != scene.scene_id:
                    explanation = (
                        f"{explanation_template.format(item=key)} in "
                        f"{origin_scene_id}, reused in {scene.scene_id}"
                    )
                    dependency_edge = DependencyEdge(
                        from_scene_id=origin_scene_id,
                        to_scene_id=scene.scene_id,
                        weight=weight,
                        edge_type=edge_type,
                        explanation=explanation,
                    )
                    self._upsert_edge(dependency_edge)
            else:
                first_seen[key] = scene.scene_id

    def _upsert_edge(self, dependency_edge: DependencyEdge) -> None:
        """Insert or merge a dependency edge into the graph."""
        source = dependency_edge.from_scene_id
        target = dependency_edge.to_scene_id

        if self.graph.has_edge(source, target):
            existing_weight = float(self.graph[source][target]["weight"])
            existing_explanation = str(self.graph[source][target]["explanation"])
            existing_types = list(self.graph[source][target]["edge_types"])

            merged_weight = existing_weight + dependency_edge.weight
            merged_explanation = (
                f"{existing_explanation}; {dependency_edge.explanation}"
            )
            if dependency_edge.edge_type not in existing_types:
                existing_types.append(dependency_edge.edge_type)

            self.graph[source][target]["weight"] = merged_weight
            self.graph[source][target]["explanation"] = merged_explanation
            self.graph[source][target]["edge_types"] = existing_types
            self.graph[source][target]["dependency_edges"].append(
                asdict(dependency_edge)
            )
            return

        self.graph.add_edge(
            source,
            target,
            weight=dependency_edge.weight,
            edge_type=dependency_edge.edge_type,
            edge_types=[dependency_edge.edge_type],
            explanation=dependency_edge.explanation,
            dependency_edges=[asdict(dependency_edge)],
        )

    def get_delete_impact(self, scene_id: str) -> list[dict[str, Any]]:
        """Return scenes that depend on the given scene, directly or transitively.

        Uses graph descendants to find downstream scenes that would be affected
        if the given scene were removed.

        Args:
            scene_id: The scene whose deletion impact should be evaluated.

        Returns:
            Impact records sorted by total dependency weight descending.
        """
        if scene_id not in self.graph:
            return []

        impacted: list[dict[str, Any]] = []
        for descendant_id in nx.descendants(self.graph, scene_id):
            scene = self._scene_lookup.get(descendant_id)
            if scene is None:
                continue

            try:
                path = nx.shortest_path(self.graph, scene_id, descendant_id)
            except nx.NetworkXNoPath:
                continue

            total_weight = self._path_weight(path)
            impacted.append(
                {
                    "scene_id": descendant_id,
                    "scene_number": scene.scene_number,
                    "heading": scene.heading,
                    "dependency_path": path,
                    "total_weight": total_weight,
                }
            )

        impacted.sort(key=lambda record: record["total_weight"], reverse=True)
        return impacted

    def get_scene_dependencies(self, scene_id: str) -> list[dict[str, Any]]:
        """Return all scenes that the given scene depends on.

        Uses graph ancestors to find upstream scenes that the given scene relies on.

        Args:
            scene_id: The scene whose upstream dependencies should be returned.

        Returns:
            Dependency records sorted by total dependency weight descending.
        """
        if scene_id not in self.graph:
            return []

        dependencies: list[dict[str, Any]] = []
        for ancestor_id in nx.ancestors(self.graph, scene_id):
            scene = self._scene_lookup.get(ancestor_id)
            if scene is None:
                continue

            try:
                path = nx.shortest_path(self.graph, ancestor_id, scene_id)
            except nx.NetworkXNoPath:
                continue

            total_weight = self._path_weight(path)
            dependencies.append(
                {
                    "scene_id": ancestor_id,
                    "scene_number": scene.scene_number,
                    "heading": scene.heading,
                    "dependency_path": path,
                    "total_weight": total_weight,
                }
            )

        dependencies.sort(key=lambda record: record["total_weight"], reverse=True)
        return dependencies

    def get_orphan_scenes(self) -> list[str]:
        """Return scene IDs with no incoming edges, excluding the first scene.

        Orphan scenes are not depended upon by any other scene and may be
        candidates for cutting.

        Returns:
            Scene IDs with zero in-degree, excluding scene_001.
        """
        orphans: list[str] = []
        for scene_id in self.graph.nodes:
            if scene_id == "scene_001":
                continue
            if self.graph.in_degree(scene_id) == 0:
                orphans.append(scene_id)
        return sorted(orphans)

    def export_graph_summary(self) -> dict[str, Any]:
        """Return high-level statistics about the dependency graph.

        Returns:
            Summary metrics including scene count, edge count, the most depended-on
            scene, orphan count, and average upstream dependencies per scene.
        """
        total_scenes = self.graph.number_of_nodes()
        total_edges = self.graph.number_of_edges()
        orphan_count = len(self.get_orphan_scenes())

        most_depended_on_scene: Optional[str] = None
        if total_scenes > 0:
            most_depended_on_scene = max(
                self.graph.nodes,
                key=lambda node_id: self.graph.in_degree(node_id),
            )
            if self.graph.in_degree(most_depended_on_scene) == 0:
                most_depended_on_scene = None

        dependency_counts = [
            len(nx.ancestors(self.graph, scene_id))
            for scene_id in self.graph.nodes
        ]
        avg_dependencies = (
            sum(dependency_counts) / total_scenes if total_scenes else 0.0
        )

        return {
            "total_scenes": total_scenes,
            "total_edges": total_edges,
            "most_depended_on_scene": most_depended_on_scene,
            "orphan_count": orphan_count,
            "avg_dependencies_per_scene": round(avg_dependencies, 2),
        }

    def _path_weight(self, path: list[str]) -> float:
        """Calculate the total edge weight along a dependency path."""
        total = 0.0
        for index in range(len(path) - 1):
            source = path[index]
            target = path[index + 1]
            if self.graph.has_edge(source, target):
                total += float(self.graph[source][target]["weight"])
        return round(total, 2)
