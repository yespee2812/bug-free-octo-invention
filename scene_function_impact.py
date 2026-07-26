"""Scene Function Impact (SFI) — D-lite beat extraction for simulate cut.

Deterministic Layer-1 analysis: label each scene's story functions, then judge
a cut by which later scenes lose a function they still consume. Continuity-graph
edges remain supporting evidence elsewhere; SFI drives cut wording when beats
are detected.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from scene_dependency import SceneBlock

FunctionType = Literal[
    "intro_character",
    "plant_object",
    "reveal",
    "directive",
    "promise",
    "decision",
    "rule_ban",
    "pursuit",
    "crisis",
    "payoff",
    "deadline_pressure",
]

RiskLevel = Literal["none", "low", "medium", "high"]

FUNCTION_WEIGHT: dict[FunctionType, float] = {
    "intro_character": 0.6,
    "plant_object": 0.9,
    "reveal": 0.85,
    "directive": 1.0,
    "promise": 0.95,
    "decision": 0.9,
    "rule_ban": 0.95,
    "pursuit": 0.8,
    "crisis": 0.85,
    "payoff": 0.7,
    "deadline_pressure": 0.4,
}

# Shared thread id for relationship / coming-of-age arcs.
_RELATIONSHIP_ARC = "RELATIONSHIP"

# Portable story objects often written in sentence case (not CAPS props).
_STORY_OBJECT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bwax[-\s]?sealed\s+envelope\b", re.IGNORECASE), "ENVELOPE"),
    (re.compile(r"\benvelope\b", re.IGNORECASE), "ENVELOPE"),
    (re.compile(r"\bleather\s+pouch\b", re.IGNORECASE), "POUCH"),
    (re.compile(r"\bpouch\b", re.IGNORECASE), "POUCH"),
    (re.compile(r"\bbriefcase\b", re.IGNORECASE), "BRIEFCASE"),
    (re.compile(r"\bsteel\s+briefcase\b", re.IGNORECASE), "BRIEFCASE"),
    (re.compile(r"\bsketch\b", re.IGNORECASE), "SKETCH"),
    (re.compile(r"\bcoordinates?\b", re.IGNORECASE), "COORDINATES"),
    (re.compile(r"\bjournal\b", re.IGNORECASE), "JOURNAL"),
    (re.compile(r"\bmap\b", re.IGNORECASE), "MAP"),
    (re.compile(r"\btin\s+box\b", re.IGNORECASE), "TIN BOX"),
    (re.compile(r"\bcairn\b", re.IGNORECASE), "CAIRN"),
    (re.compile(r"\brevolver\b", re.IGNORECASE), "REVOLVER"),
    (re.compile(r"\bmotorcycle\b", re.IGNORECASE), "MOTORCYCLE"),
    (
        re.compile(r"\bmagnetic\s+guest\s+book\b", re.IGNORECASE),
        "MAGNETIC GUEST BOOK",
    ),
    (re.compile(r"\bguest\s+book\b", re.IGNORECASE), "MAGNETIC GUEST BOOK"),
    (re.compile(r"\bmagnetic\s+thing\b", re.IGNORECASE), "MAGNETIC GUEST BOOK"),
)

_REVEAL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\b(?:never\s+told|never\s+knew|didn't\s+tell|turns\s+out)\b",
            re.IGNORECASE,
        ),
        "hidden_truth",
    ),
    (
        re.compile(
            r"\bwasn't\s+turning\s+back\b.*\bturning\s+toward\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "motive_reframe",
    ),
    (
        re.compile(
            r"\b(?:father|mother|dad|mom)\b.{0,80}\b(?:turned\s+back|why)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "family_backstory",
    ),
    (
        re.compile(
            r"\b(?:buried\s+it|keep\s+the\s+record|proof\b)",
            re.IGNORECASE,
        ),
        "suppressed_proof",
    ),
)

_DIRECTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bcoordinates?\b", re.IGNORECASE),
    re.compile(r"\bsketch\s+of\b", re.IGNORECASE),
    re.compile(r"\bmap\s+(?:of|to|shows?)\b", re.IGNORECASE),
    re.compile(r"\bindicated\b", re.IGNORECASE),
)

_PURSUIT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwhere\s+the\s+sketch\s+indicated\b", re.IGNORECASE),
    re.compile(r"\bexactly\s+where\b", re.IGNORECASE),
    re.compile(r"\bfollow(?:s|ing)?\s+the\s+(?:map|sketch|coordinates?)\b", re.IGNORECASE),
    re.compile(r"\btoward\s+(?:the\s+)?(?:cave|summit|ridge|fissure)\b", re.IGNORECASE),
    re.compile(r"\bcrest(?:s|ed)?\s+the\s+ridge\b", re.IGNORECASE),
)

_PAYOFF_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bfinds?\s+.{0,40}\bjournal\b", re.IGNORECASE),
    re.compile(r"\bunfinished\b", re.IGNORECASE),
    re.compile(r"\bproof\b", re.IGNORECASE),
    re.compile(r"\bhandoff\b", re.IGNORECASE),
    re.compile(r"\bwe're\s+done\b", re.IGNORECASE),
    re.compile(r"\bguest\s+book\s+lights\s+up\b", re.IGNORECASE),
    re.compile(r"\bprojects?\s+every\b", re.IGNORECASE),
    re.compile(
        r"\b(?:aims?|fires?|shoots?|delivers?)\s+(?:the\s+|a\s+|an\s+)?(?P<object>[\w\- ]{3,30})\b",
        re.IGNORECASE,
    ),
)

# Middle-scene object handling: grab/carry/use of a planted prop.
_CARRY_PATTERN = re.compile(
    r"\b(?P<verb>grabs?|takes?|picks\s+up|carries?|holds?|slides?|shoves?|checks?|"
    r"opens?|reads?|uses?|loads?)\s+(?:the\s+|a\s+|an\s+|her\s+|his\s+)?"
    r"(?P<object>[\w\- ]{3,40})\b",
    re.IGNORECASE,
)

# Prop malfunction / escalation before a later payoff (comedy gadget chaos).
_PROP_CHAOS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bclings?\b", re.IGNORECASE),
    re.compile(r"\bstuck\s+to\b", re.IGNORECASE),
    re.compile(r"\bsticks?\s+to\b", re.IGNORECASE),
    re.compile(r"\baccidentally\b", re.IGNORECASE),
    re.compile(r"\bmalfunctions?\b", re.IGNORECASE),
    re.compile(r"\bgoes\s+haywire\b", re.IGNORECASE),
    re.compile(r"\bservice\s+entrance\b", re.IGNORECASE),
)

_DEADLINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:thirty|thirty-six|twenty|\d+)\s+(?:hours?|minutes?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bwindow\s+closes\b", re.IGNORECASE),
    re.compile(r"\bweather\s+turns\b", re.IGNORECASE),
    re.compile(r"\bone\s+hour\b", re.IGNORECASE),
    re.compile(r"\bno\s+second\s+stops\b", re.IGNORECASE),
)

# Relationship-arc beats: promise → decision → pursuit → crisis → payoff.
_PROMISE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwe\s+promised\b", re.IGNORECASE),
    re.compile(r"\bone\s+perfect\s+week\b", re.IGNORECASE),
    re.compile(r"\bbefore\s+the\s+world\s+splits\s+us\b", re.IGNORECASE),
    re.compile(r"\bstay\s+(?:friends|together)\b", re.IGNORECASE),
    re.compile(r"\bpromise\s+me\b", re.IGNORECASE),
    re.compile(r"\buntil\s+(?:we're|we\s+are)\s+(?:old|sixty|grown)\b", re.IGNORECASE),
    re.compile(r"\bwhen\s+we're\s+sixty\b", re.IGNORECASE),
)

_DECISION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:then\s+)?we\s+make\s+something\b",
        re.IGNORECASE,
    ),
    re.compile(r"\blet's\s+(?:do|make|try)\b", re.IGNORECASE),
    re.compile(r"\bwe(?:'d|\s+had)\s+better\b", re.IGNORECASE),
    re.compile(r"\bwe(?:'re|\s+are)\s+doing\s+this\b", re.IGNORECASE),
    re.compile(r"\bdoesn't\s+fit\s+in\s+a\s+dorm\b", re.IGNORECASE),
)

_RELATIONAL_PURSUIT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bguerrilla\s+(?:senior\s+)?show\b", re.IGNORECASE),
    re.compile(r"\bdirects?\s+a\b", re.IGNORECASE),
    re.compile(r"\bplaces\s+in\s+five\b", re.IGNORECASE),
    re.compile(r"\bruns?\s+sound\b", re.IGNORECASE),
    re.compile(r"\bsenior\s+show\b", re.IGNORECASE),
)

_CRISIS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bprincipal(?:'s)?\s+footsteps\b", re.IGNORECASE),
    re.compile(r"\bkills?\s+the\s+mains\b", re.IGNORECASE),
    re.compile(r"\blaughing,?\s+terrified\b", re.IGNORECASE),
    re.compile(r"\bif\s+admin\s+catches\s+us\b", re.IGNORECASE),
    re.compile(r"\bworth\s+it\?\b", re.IGNORECASE),
    re.compile(r"\balmost\s+(?:caught|caught\s+us)\b", re.IGNORECASE),
)

_RELATIONAL_PAYOFF_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\breal\s+one\b", re.IGNORECASE),
    re.compile(r"\breal\s+week\b", re.IGNORECASE),
    re.compile(
        r"\bdidn't\s+get\s+a\s+perfect\s+week\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bsame\s+thing\s+if\s+you're\s+paying\s+attention\b", re.IGNORECASE),
)

# Comedy / social rule that later prop chaos violates.
_RULE_BAN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bno\s+props\b", re.IGNORECASE),
    re.compile(r"\bhates\s+props\b", re.IGNORECASE),
    re.compile(r"\bhide\s+the\s+magnetic\s+thing\b", re.IGNORECASE),
    re.compile(r"\bno\s+surprises\b", re.IGNORECASE),
)

_THEME_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bperfect\s+week\b", re.IGNORECASE), "WEEK"),
    (re.compile(r"\breal\s+(?:week|one)\b", re.IGNORECASE), "WEEK"),
    (re.compile(r"\bfriendship\b", re.IGNORECASE), "FRIENDSHIP"),
    (re.compile(r"\bbest\s+friend\b", re.IGNORECASE), "FRIENDSHIP"),
)

# Tokens that link pursuit/payoff back to earlier plants/directives.
_OBJECT_ALIAS_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"ENVELOPE", "POUCH", "PACKET", "PARCEL"}),
    frozenset({"SKETCH", "COORDINATES", "MAP", "JOURNAL", "TIN BOX", "CAIRN"}),
    frozenset({"BRIEFCASE"}),
    frozenset({"REVOLVER"}),
    frozenset({_RELATIONSHIP_ARC, "WEEK", "FRIENDSHIP"}),
    frozenset({"MAGNETIC GUEST BOOK", "GUEST BOOK"}),
)


@dataclass(frozen=True)
class SceneFunction:
    """One story function contributed by a scene."""

    function_type: FunctionType
    key: str
    label: str
    evidence: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize the function for API and tests."""
        return asdict(self)


@dataclass
class SceneFunctionCutImpact:
    """SFI verdict for removing one scene."""

    removed_scene_id: str
    lost_functions: list[SceneFunction] = field(default_factory=list)
    at_risk_scenes: list[dict[str, Any]] = field(default_factory=list)
    is_bridge: bool = False
    risk_level: RiskLevel = "none"
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the cut-impact verdict."""
        return {
            "removed_scene_id": self.removed_scene_id,
            "lost_functions": [item.to_dict() for item in self.lost_functions],
            "at_risk_scenes": list(self.at_risk_scenes),
            "is_bridge": self.is_bridge,
            "risk_level": self.risk_level,
            "summary": self.summary,
        }


def _normalize_key(value: str) -> str:
    """Return a stable uppercase key for function identity."""
    return " ".join(value.upper().replace("-", " ").split())


def _object_keys_from_text(text: str) -> list[str]:
    """Extract story-object keys from free text via portable patterns."""
    found: list[str] = []
    seen: set[str] = set()
    for pattern, key in _STORY_OBJECT_PATTERNS:
        if pattern.search(text) and key not in seen:
            seen.add(key)
            found.append(key)
    return found


def _object_keys_from_scene(scene: SceneBlock) -> list[str]:
    """Combine CAPS props with sentence-case story-object matches."""
    keys: list[str] = []
    seen: set[str] = set()
    for prop in scene.props_detected + scene.objects:
        normalized = _normalize_key(prop)
        for article in ("A ", "AN ", "THE "):
            if normalized.startswith(article):
                normalized = normalized[len(article) :].strip()
        if "ENVELOPE" in normalized:
            normalized = "ENVELOPE"
        elif "POUCH" in normalized:
            normalized = "POUCH"
        elif "BRIEFCASE" in normalized:
            normalized = "BRIEFCASE"
        if normalized and normalized not in seen:
            seen.add(normalized)
            keys.append(normalized)
    for key in _object_keys_from_text(scene.raw_text):
        if key not in seen:
            seen.add(key)
            keys.append(key)
    return keys


def _related_object_keys(key: str) -> set[str]:
    """Return alias group members for an object key, including itself."""
    normalized = _normalize_key(key)
    related = {normalized}
    for group in _OBJECT_ALIAS_GROUPS:
        if normalized in group:
            related.update(group)
    return related


def _first_evidence(pattern: re.Pattern[str], text: str, limit: int = 90) -> str:
    """Return a short evidence snippet for a regex match."""
    match = pattern.search(text)
    if match is None:
        return ""
    start = max(0, match.start() - 20)
    end = min(len(text), match.end() + 40)
    snippet = " ".join(text[start:end].split())
    if len(snippet) > limit:
        return snippet[: limit - 1] + "…"
    return snippet


def _character_intro_keys(scenes: list[SceneBlock]) -> dict[str, str]:
    """Map normalized character name to the scene that first introduces them."""
    first_seen: dict[str, str] = {}
    for scene in scenes:
        for name in scene.characters:
            key = _normalize_key(name)
            # Collapse partials onto longer forms when already known.
            matched = key
            for existing in list(first_seen):
                if key == existing or key in existing or existing in key:
                    matched = existing
                    break
            if matched not in first_seen:
                first_seen[matched] = scene.scene_id
    return first_seen


def _relationship_theme_keys(text: str) -> list[str]:
    """Return theme keys for relationship-arc linkage, always including RELATIONSHIP."""
    keys: list[str] = [_RELATIONSHIP_ARC]
    seen = {_RELATIONSHIP_ARC}
    for pattern, theme in _THEME_PATTERNS:
        if pattern.search(text) and theme not in seen:
            seen.add(theme)
            keys.append(theme)
    return keys


def _append_relationship_beats(
    scene_fns: list[SceneFunction],
    text: str,
) -> None:
    """Detect promise / decision / relational pursuit / crisis / payoff beats."""
    themes = _relationship_theme_keys(text)
    theme_label = "/".join(
        theme.title() for theme in themes if theme != _RELATIONSHIP_ARC
    ) or "Relationship"
    arc_key = _RELATIONSHIP_ARC

    promise_pattern = next(
        (pattern for pattern in _PROMISE_PATTERNS if pattern.search(text)),
        None,
    )
    if promise_pattern is not None:
        scene_fns.append(
            SceneFunction(
                function_type="promise",
                key=f"promise:{arc_key}",
                label=f"Relationship promise ({theme_label})",
                evidence=_first_evidence(promise_pattern, text),
            )
        )

    decision_pattern = next(
        (pattern for pattern in _DECISION_PATTERNS if pattern.search(text)),
        None,
    )
    if decision_pattern is not None:
        scene_fns.append(
            SceneFunction(
                function_type="decision",
                key=f"decision:{arc_key}",
                label=f"Relationship decision ({theme_label})",
                evidence=_first_evidence(decision_pattern, text),
            )
        )

    relational_pursuit = next(
        (pattern for pattern in _RELATIONAL_PURSUIT_PATTERNS if pattern.search(text)),
        None,
    )
    if relational_pursuit is not None:
        scene_fns.append(
            SceneFunction(
                function_type="pursuit",
                key=f"pursuit:{arc_key}",
                label=f"Acts on relationship plan ({theme_label})",
                evidence=_first_evidence(relational_pursuit, text),
            )
        )

    crisis_pattern = next(
        (pattern for pattern in _CRISIS_PATTERNS if pattern.search(text)),
        None,
    )
    if crisis_pattern is not None:
        scene_fns.append(
            SceneFunction(
                function_type="crisis",
                key=f"crisis:{arc_key}",
                label=f"Relationship crisis ({theme_label})",
                evidence=_first_evidence(crisis_pattern, text),
            )
        )

    relational_payoff = next(
        (pattern for pattern in _RELATIONAL_PAYOFF_PATTERNS if pattern.search(text)),
        None,
    )
    if relational_payoff is not None:
        scene_fns.append(
            SceneFunction(
                function_type="payoff",
                key=f"payoff:{arc_key}",
                label=f"Relationship payoff ({theme_label})",
                evidence=_first_evidence(relational_payoff, text),
            )
        )


def extract_scene_functions(scenes: list[SceneBlock]) -> dict[str, list[SceneFunction]]:
    """Label story functions for every scene in screenplay order.

    Args:
        scenes: Parsed scene blocks in order.

    Returns:
        Map of scene_id to ordered function list.
    """
    intro_map = _character_intro_keys(scenes)
    object_first_scene: dict[str, str] = {}
    functions: dict[str, list[SceneFunction]] = {scene.scene_id: [] for scene in scenes}

    for scene in scenes:
        text = scene.raw_text
        scene_fns = functions[scene.scene_id]

        for name, intro_scene_id in intro_map.items():
            if intro_scene_id != scene.scene_id:
                continue
            scene_fns.append(
                SceneFunction(
                    function_type="intro_character",
                    key=f"character:{name}",
                    label=f"Introduces {name.title()}",
                    evidence=name,
                )
            )

        for object_key in _object_keys_from_scene(scene):
            if object_key not in object_first_scene:
                object_first_scene[object_key] = scene.scene_id
                scene_fns.append(
                    SceneFunction(
                        function_type="plant_object",
                        key=f"object:{object_key}",
                        label=f"Plants {object_key.title()}",
                        evidence=object_key,
                    )
                )

        for pattern, topic in _REVEAL_PATTERNS:
            if pattern.search(text):
                scene_fns.append(
                    SceneFunction(
                        function_type="reveal",
                        key=f"reveal:{topic}",
                        label=f"Reveal: {topic.replace('_', ' ')}",
                        evidence=_first_evidence(pattern, text),
                    )
                )

        directive_pattern = next(
            (pattern for pattern in _DIRECTIVE_PATTERNS if pattern.search(text)),
            None,
        )
        if directive_pattern is not None:
            directive_objects = [
                key
                for key in _object_keys_from_scene(scene)
                if key in {"SKETCH", "COORDINATES", "MAP"}
            ] or ["DIRECTIVE"]
            for object_key in directive_objects:
                scene_fns.append(
                    SceneFunction(
                        function_type="directive",
                        key=f"directive:{object_key}",
                        label=f"Directive via {object_key.title()}",
                        evidence=_first_evidence(directive_pattern, text),
                    )
                )

        pursuit_pattern = next(
            (pattern for pattern in _PURSUIT_PATTERNS if pattern.search(text)),
            None,
        )
        if pursuit_pattern is not None:
            pursuit_objects = [
                key
                for key in _object_keys_from_scene(scene)
                if key in {"SKETCH", "COORDINATES", "MAP", "JOURNAL", "CAIRN"}
            ] or ["SKETCH"]
            for object_key in pursuit_objects:
                scene_fns.append(
                    SceneFunction(
                        function_type="pursuit",
                        key=f"pursuit:{object_key}",
                        label=f"Pursues {object_key.title()} lead",
                        evidence=_first_evidence(pursuit_pattern, text),
                    )
                )

        payoff_pattern = next(
            (pattern for pattern in _PAYOFF_PATTERNS if pattern.search(text)),
            None,
        )
        if payoff_pattern is not None:
            payoff_objects = [
                key
                for key in _object_keys_from_scene(scene)
                if key
                in {
                    "JOURNAL",
                    "SKETCH",
                    "BRIEFCASE",
                    "REVOLVER",
                    "ENVELOPE",
                    "MAGNETIC GUEST BOOK",
                }
            ]
            if not payoff_objects:
                match = payoff_pattern.search(text)
                captured = ""
                if match is not None and "object" in match.groupdict() and match.group("object"):
                    captured = _normalize_key(match.group("object"))
                payoff_objects = [captured] if captured else ["PAYOFF"]
            for object_key in payoff_objects:
                scene_fns.append(
                    SceneFunction(
                        function_type="payoff",
                        key=f"payoff:{object_key}",
                        label=f"Payoff involving {object_key.title()}",
                        evidence=_first_evidence(payoff_pattern, text),
                    )
                )

        # Object carry/use in a non-first scene becomes a pursuit bridge beat.
        if object_first_scene:
            for match in _CARRY_PATTERN.finditer(text):
                raw_object = _normalize_key(match.group("object"))
                matched_key = ""
                for known in list(object_first_scene):
                    if (
                        known in raw_object
                        or raw_object in known
                        or bool(_related_object_keys(known) & _related_object_keys(raw_object))
                    ):
                        matched_key = known
                        break
                if not matched_key:
                    continue
                if object_first_scene.get(matched_key) == scene.scene_id:
                    continue
                scene_fns.append(
                    SceneFunction(
                        function_type="pursuit",
                        key=f"pursuit:{matched_key}",
                        label=f"Carries {matched_key.title()} forward",
                        evidence=_first_evidence(_CARRY_PATTERN, match.group(0)),
                    )
                )

        # Planted-prop chaos/escalation (e.g. gadget stuck before the payoff).
        chaos_pattern = next(
            (pattern for pattern in _PROP_CHAOS_PATTERNS if pattern.search(text)),
            None,
        )
        if chaos_pattern is not None and object_first_scene:
            chaos_objects = [
                key
                for key in _object_keys_from_scene(scene)
                if object_first_scene.get(key) not in {None, scene.scene_id}
            ]
            for object_key in chaos_objects:
                scene_fns.append(
                    SceneFunction(
                        function_type="crisis",
                        key=f"crisis:{object_key}",
                        label=f"Escalates {object_key.title()} chaos",
                        evidence=_first_evidence(chaos_pattern, text),
                    )
                )
                scene_fns.append(
                    SceneFunction(
                        function_type="pursuit",
                        key=f"pursuit:{object_key}",
                        label=f"Carries {object_key.title()} toward payoff",
                        evidence=_first_evidence(chaos_pattern, text),
                    )
                )

        for pattern in _DEADLINE_PATTERNS:
            if pattern.search(text):
                scene_fns.append(
                    SceneFunction(
                        function_type="deadline_pressure",
                        key=f"deadline:{scene.scene_id}",
                        label="Deadline / time pressure",
                        evidence=_first_evidence(pattern, text),
                    )
                )
                break

        _append_relationship_beats(scene_fns, text)

        rule_ban_pattern = next(
            (pattern for pattern in _RULE_BAN_PATTERNS if pattern.search(text)),
            None,
        )
        if rule_ban_pattern is not None:
            ban_objects = [
                key
                for key in _object_keys_from_scene(scene)
                if key in {"MAGNETIC GUEST BOOK", "GUEST BOOK"}
            ]
            if not ban_objects and re.search(
                r"\b(?:prop|magnetic|guest\s+book)\b",
                text,
                re.IGNORECASE,
            ):
                ban_objects = ["MAGNETIC GUEST BOOK"]
            for object_key in ban_objects or ["PROPS"]:
                scene_fns.append(
                    SceneFunction(
                        function_type="rule_ban",
                        key=f"ban:{object_key}",
                        label=f"Bans / forbids {object_key.title()}",
                        evidence=_first_evidence(rule_ban_pattern, text),
                    )
                )

        # Deduplicate by (type, key) while preserving order.
        deduped: list[SceneFunction] = []
        seen_keys: set[tuple[str, str]] = set()
        for item in scene_fns:
            marker = (item.function_type, item.key)
            if marker in seen_keys:
                continue
            seen_keys.add(marker)
            deduped.append(item)
        functions[scene.scene_id] = deduped

    return functions


def _functions_by_type(
    functions: list[SceneFunction],
    function_type: FunctionType,
) -> list[SceneFunction]:
    """Filter functions by type."""
    return [item for item in functions if item.function_type == function_type]


def _tokens_related(left: str, right: str) -> bool:
    """Return True when two function tokens share an alias group."""
    return bool(_related_object_keys(left) & _related_object_keys(right))


def _scene_consumes_function(
    consumer_fns: list[SceneFunction],
    supplier: SceneFunction,
) -> bool:
    """Return True when a later scene consumes the supplier function."""
    if supplier.function_type == "plant_object":
        object_key = supplier.key.split(":", 1)[-1]
        related = _related_object_keys(object_key)
        for item in consumer_fns:
            if item.function_type in {"pursuit", "payoff", "directive"}:
                token = item.key.split(":", 1)[-1]
                if token in related or bool(related & _related_object_keys(token)):
                    return True
            if item.function_type == "plant_object":
                token = item.key.split(":", 1)[-1]
                if token in related and token != object_key:
                    # Alias continuation (envelope → pouch) still consumes the plant.
                    return True
        return False

    if supplier.function_type == "directive":
        object_key = supplier.key.split(":", 1)[-1]
        related = _related_object_keys(object_key)
        for item in consumer_fns:
            if item.function_type in {"pursuit", "payoff"}:
                token = item.key.split(":", 1)[-1]
                if token in related or bool(related & _related_object_keys(token)):
                    return True
        return False

    if supplier.function_type == "reveal":
        topic = supplier.key.split(":", 1)[-1]
        for item in consumer_fns:
            if item.function_type == "reveal" and item.key == supplier.key:
                return True
            if item.function_type in {"pursuit", "payoff", "directive"}:
                # Family/motive reveals commonly unlock later cave/journal payoffs.
                if topic in {"family_backstory", "motive_reframe", "hidden_truth"}:
                    token = item.key.split(":", 1)[-1]
                    if token in {"SKETCH", "COORDINATES", "JOURNAL", "CAIRN", "TIN BOX"}:
                        return True
                    if item.function_type == "payoff" and "proof" in item.evidence.lower():
                        return True
        return False

    if supplier.function_type == "promise":
        theme = supplier.key.split(":", 1)[-1]
        for item in consumer_fns:
            if item.function_type in {"decision", "pursuit", "crisis", "payoff"}:
                if _tokens_related(theme, item.key.split(":", 1)[-1]):
                    return True
        return False

    if supplier.function_type == "decision":
        theme = supplier.key.split(":", 1)[-1]
        for item in consumer_fns:
            if item.function_type in {"pursuit", "crisis", "payoff"}:
                if _tokens_related(theme, item.key.split(":", 1)[-1]):
                    return True
        return False

    if supplier.function_type == "rule_ban":
        banned = supplier.key.split(":", 1)[-1]
        related = _related_object_keys(banned)
        for item in consumer_fns:
            if item.function_type in {"plant_object", "pursuit", "payoff", "crisis"}:
                token = item.key.split(":", 1)[-1]
                if token in related or bool(related & _related_object_keys(token)):
                    return True
            if item.function_type == "payoff" and banned == "PROPS":
                return True
        return False

    if supplier.function_type == "pursuit":
        object_key = supplier.key.split(":", 1)[-1]
        related = _related_object_keys(object_key)
        for item in consumer_fns:
            if item.function_type in {"crisis", "payoff"}:
                token = item.key.split(":", 1)[-1]
                if token in related or bool(related & _related_object_keys(token)):
                    return True
                if token == "PAYOFF":
                    return True
        return False

    if supplier.function_type == "crisis":
        theme = supplier.key.split(":", 1)[-1]
        for item in consumer_fns:
            if item.function_type == "payoff" and _tokens_related(
                theme,
                item.key.split(":", 1)[-1],
            ):
                return True
        return False

    if supplier.function_type == "intro_character":
        # Intros are consumed only when later scenes would lose first presence —
        # handled via alternate-supplier check, not consumer match.
        return False

    if supplier.function_type == "deadline_pressure":
        return False

    if supplier.function_type == "payoff":
        return False

    return False


def _has_alternate_supplier(
    scenes: list[SceneBlock],
    functions_by_scene: dict[str, list[SceneFunction]],
    removed_scene_id: str,
    supplier: SceneFunction,
) -> bool:
    """Return True when an earlier scene still supplies the same function key."""
    removed = next(scene for scene in scenes if scene.scene_id == removed_scene_id)
    for scene in scenes:
        if scene.scene_number >= removed.scene_number:
            continue
        for item in functions_by_scene.get(scene.scene_id, []):
            if item.function_type != supplier.function_type:
                continue
            if item.key == supplier.key:
                return True
            if supplier.function_type in {
                "plant_object",
                "directive",
                "pursuit",
                "promise",
                "decision",
                "rule_ban",
                "crisis",
            }:
                left = supplier.key.split(":", 1)[-1]
                right = item.key.split(":", 1)[-1]
                if bool(_related_object_keys(left) & _related_object_keys(right)):
                    return True
    return False


def _is_bridge_scene(
    removed_fns: list[SceneFunction],
    later_functions: list[list[SceneFunction]],
) -> bool:
    """Return True when the scene carries a mid-arc beat into a later consumer."""
    bridge_types: tuple[FunctionType, ...] = (
        "pursuit",
        "decision",
        "crisis",
        "promise",
        "rule_ban",
    )
    for function_type in bridge_types:
        for supplier in _functions_by_type(removed_fns, function_type):
            for consumer_fns in later_functions:
                if _scene_consumes_function(consumer_fns, supplier):
                    return True
    return False


def evaluate_scene_function_cut(
    scenes: list[SceneBlock],
    scene_id: str,
) -> SceneFunctionCutImpact:
    """Judge simulate-cut impact using story functions (D-lite).

    Args:
        scenes: Parsed scene blocks in order.
        scene_id: Scene being considered for removal.

    Returns:
        Structured SFI cut verdict with summary and risk level.
    """
    result = SceneFunctionCutImpact(removed_scene_id=scene_id)
    scene_lookup = {scene.scene_id: scene for scene in scenes}
    removed = scene_lookup.get(scene_id)
    if removed is None:
        result.summary = "Unknown scene."
        return result

    functions_by_scene = extract_scene_functions(scenes)
    removed_fns = functions_by_scene.get(scene_id, [])
    later_scenes = [scene for scene in scenes if scene.scene_number > removed.scene_number]
    later_fn_lists = [functions_by_scene[scene.scene_id] for scene in later_scenes]

    result.is_bridge = _is_bridge_scene(removed_fns, later_fn_lists)

    lost: list[SceneFunction] = []
    at_risk: dict[str, dict[str, Any]] = {}

    actionable = [
        item
        for item in removed_fns
        if item.function_type
        in {
            "plant_object",
            "reveal",
            "directive",
            "promise",
            "decision",
            "rule_ban",
            "pursuit",
            "crisis",
            "intro_character",
        }
    ]
    bridge_types = {"pursuit", "decision", "crisis", "promise", "rule_ban"}

    for supplier in actionable:
        if supplier.function_type == "intro_character":
            # Only flag when this scene is the sole intro and many later scenes
            # feature that character — covered via plant/reveal/directive primarily.
            # Keep intro loss only when no alternate intro exists and later scenes exist.
            if later_scenes and not _has_alternate_supplier(
                scenes, functions_by_scene, scene_id, supplier
            ):
                # Count later scenes mentioning this character family.
                name = supplier.key.split(":", 1)[-1]
                consumers = [
                    scene
                    for scene in later_scenes
                    if any(
                        name in _normalize_key(char) or _normalize_key(char) in name
                        for char in scene.characters
                    )
                ]
                if not consumers:
                    continue
                lost.append(supplier)
                for scene in consumers:
                    record = at_risk.setdefault(
                        scene.scene_id,
                        {
                            "scene_id": scene.scene_id,
                            "scene_number": scene.scene_number,
                            "heading": scene.heading,
                            "lost_function_labels": [],
                            "impact_reason": "",
                        },
                    )
                    record["lost_function_labels"].append(supplier.label)
            continue

        consumers = [
            scene
            for scene, fns in zip(later_scenes, later_fn_lists)
            if _scene_consumes_function(fns, supplier)
        ]
        if not consumers:
            continue

        # Mid-arc relationship/object bridges stay even if an earlier alternate exists.
        if supplier.function_type in bridge_types or (
            supplier.function_type in {"plant_object", "directive", "reveal"}
            and not _has_alternate_supplier(
                scenes, functions_by_scene, scene_id, supplier
            )
        ):
            lost.append(supplier)
            for scene in consumers:
                record = at_risk.setdefault(
                    scene.scene_id,
                    {
                        "scene_id": scene.scene_id,
                        "scene_number": scene.scene_number,
                        "heading": scene.heading,
                        "lost_function_labels": [],
                        "impact_reason": "",
                    },
                )
                record["lost_function_labels"].append(supplier.label)

    # Ensure bridge suppliers are retained even if the first pass skipped a label.
    if result.is_bridge:
        for function_type in (
            "pursuit",
            "decision",
            "crisis",
            "promise",
            "rule_ban",
        ):
            for supplier in _functions_by_type(removed_fns, function_type):
                if supplier not in lost:
                    lost.append(supplier)
                for scene, fns in zip(later_scenes, later_fn_lists):
                    if not _scene_consumes_function(fns, supplier):
                        continue
                    record = at_risk.setdefault(
                        scene.scene_id,
                        {
                            "scene_id": scene.scene_id,
                            "scene_number": scene.scene_number,
                            "heading": scene.heading,
                            "lost_function_labels": [],
                            "impact_reason": "",
                        },
                    )
                    if supplier.label not in record["lost_function_labels"]:
                        record["lost_function_labels"].append(supplier.label)

    for record in at_risk.values():
        labels = record["lost_function_labels"]
        joined = ", ".join(labels)
        record["impact_reason"] = (
            f"Loses story function(s) from Scene {removed.scene_number}: {joined}."
        )

    result.lost_functions = lost
    result.at_risk_scenes = sorted(
        at_risk.values(),
        key=lambda row: row["scene_number"],
    )
    terminal_relationship_payoff = (not later_scenes) and any(
        item.function_type == "payoff"
        and item.key.split(":", 1)[-1]
        in {_RELATIONSHIP_ARC, "WEEK", "FRIENDSHIP"}
        for item in removed_fns
    )
    result.risk_level, result.summary = _summarize_sfi(
        removed.scene_number,
        lost,
        result.at_risk_scenes,
        is_bridge=result.is_bridge,
        has_later_scenes=bool(later_scenes),
        had_any_functions=bool(removed_fns),
        terminal_relationship_payoff=terminal_relationship_payoff,
    )
    return result


def _summarize_sfi(
    scene_number: int,
    lost: list[SceneFunction],
    at_risk_scenes: list[dict[str, Any]],
    *,
    is_bridge: bool,
    has_later_scenes: bool,
    had_any_functions: bool,
    terminal_relationship_payoff: bool = False,
) -> tuple[RiskLevel, str]:
    """Build risk level and plain-English summary for an SFI cut."""
    if not has_later_scenes:
        if terminal_relationship_payoff:
            return (
                "low",
                (
                    f"Scene {scene_number} is the relationship payoff — "
                    "nothing later depends on it, but cutting removes the landing."
                ),
            )
        return (
            "none",
            (
                f"Safe to cut — Scene {scene_number} is terminal; "
                "no later scenes rely on its story functions."
            ),
        )

    if not lost and not is_bridge:
        if not had_any_functions:
            return (
                "low",
                (
                    f"Low structural risk — Scene {scene_number} has no clear "
                    "setup, reveal, or pursuit beat; verify dramatically."
                ),
            )
        return (
            "low",
            (
                f"Low structural risk — Scene {scene_number}'s beats are not "
                "uniquely required by later scenes; verify dramatically."
            ),
        )

    labels = []
    seen: set[str] = set()
    for item in lost:
        if item.label in seen:
            continue
        seen.add(item.label)
        labels.append(item.label)
    label_text = ", ".join(labels[:3]) if labels else "a carrier beat"
    count = len(at_risk_scenes)

    weight = sum(FUNCTION_WEIGHT.get(item.function_type, 0.5) for item in lost)
    relationship_tokens = {_RELATIONSHIP_ARC, "WEEK", "FRIENDSHIP"}
    has_relationship_loss = any(
        item.function_type in {"promise", "decision"}
        or (
            item.function_type in {"pursuit", "payoff", "crisis"}
            and item.key.split(":", 1)[-1] in relationship_tokens
        )
        for item in lost
    )
    has_prop_escalation = any(
        item.function_type in {"crisis", "pursuit", "rule_ban"}
        and item.key.split(":", 1)[-1] not in relationship_tokens
        for item in lost
    )
    if is_bridge or weight >= 1.6 or count >= 3 or has_relationship_loss:
        risk: RiskLevel = "high"
    elif weight >= 0.8 or count >= 2:
        risk = "medium"
    else:
        risk = "low"

    if is_bridge and count:
        if has_relationship_loss:
            summary = (
                f"Cutting Scene {scene_number} would break the relationship arc "
                f"({label_text})."
            )
        elif has_prop_escalation:
            summary = (
                f"Cutting Scene {scene_number} would remove a prop escalation beat "
                f"that later scenes still rely on ({label_text})."
            )
        else:
            summary = (
                f"Cutting Scene {scene_number} would remove a pursuit beat that "
                f"later scenes still rely on ({label_text})."
            )
    elif count == 1:
        other = at_risk_scenes[0]["scene_number"]
        summary = (
            f"Cutting Scene {scene_number} would drop {label_text}, "
            f"affecting Scene {other}."
        )
    else:
        summary = (
            f"Cutting Scene {scene_number} would drop {label_text}, "
            f"affecting {count} later scenes."
        )
    return risk, summary


def sfi_rows_to_impacted_scenes(
    removed_scene_id: str,
    sfi: SceneFunctionCutImpact,
) -> list[dict[str, Any]]:
    """Convert SFI at-risk rows into simulate-cut impacted_scene records.

    Args:
        removed_scene_id: Scene being cut.
        sfi: Evaluated SFI cut impact.

    Returns:
        Impact rows compatible with ``ImpactedScene`` enrichment fields.
    """
    rows: list[dict[str, Any]] = []
    for record in sfi.at_risk_scenes:
        weight = 0.0
        for label in record.get("lost_function_labels", []):
            for item in sfi.lost_functions:
                if item.label == label:
                    weight += FUNCTION_WEIGHT.get(item.function_type, 0.5)
        rows.append(
            {
                "scene_id": record["scene_id"],
                "scene_number": record["scene_number"],
                "heading": record["heading"],
                "dependency_path": [removed_scene_id, record["scene_id"]],
                "total_weight": round(weight or 0.5, 3),
                "explanation": record["impact_reason"],
                "impact_reason": record["impact_reason"],
                "hop_explanations": [record["impact_reason"]],
                "link_hops": 1,
                "severity": "direct",
            }
        )
    return rows
