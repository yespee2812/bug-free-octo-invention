"""State-of-the-art orphan scene graph builder (AR-OSD-2026).

Sprint 1: weighted C/L/P linkage matrix.
Sprint 2: meta-scene collapse, cinematic overrides, WCC subplot chains, findings.
Sprint 3: semantic E_ij embeddings (all-MiniLM-L6-v2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any, Literal

import networkx as nx

from osd_semantic import SceneSemanticCache, is_semantic_enabled, semantic_linkage
from scene_dependency import (
    CAPS_PROP_STOP_FIRST_WORDS,
    SceneBlock,
    WARDROBE_HEAD_NOUNS,
    _normalize_object_key,
    _normalize_token,
)

if TYPE_CHECKING:
    from scene_dependency import SceneDependencyEngine

OrphanType = Literal["hard", "subplot_chain"]

# AR-OSD-2026-SPEC Section 3 linkage weights (E_ij enabled in Sprint 3).
ALPHA_CHARACTER: float = 0.40
BETA_SPATIAL: float = 0.25
GAMMA_PROP: float = 0.20
DELTA_SEMANTIC: float = 0.15
LINK_THRESHOLD: float = 0.20

SUBPLOT_CHAIN_MAX_SIZE: int = 3
SUBPLOT_MIN_TOTAL_SCENES: int = 40
PROLOGUE_EXEMPT_SCENE_COUNT: int = 2

TEMPORAL_CONTINUITY_TOKENS: frozenset[str] = frozenset(
    {
        "CONTINUOUS", "LATER", "MOMENTS LATER", "SAME", "SAME TIME",
        "LATER THAT DAY", "LATER THAT NIGHT",
    }
)

MONTAGE_PATTERN = re.compile(r"\b(MONTAGE|SERIES OF SHOTS)\b", re.IGNORECASE)
INTERCUT_PATTERN = re.compile(r"\bINTERCUT\b", re.IGNORECASE)
PROLOGUE_PATTERN = re.compile(r"\bPROLOGUE\b", re.IGNORECASE)
FLASHBACK_PATTERN = re.compile(r"\bFLASHBACK\b", re.IGNORECASE)

COLLAPSIBLE_TAGS: frozenset[str] = frozenset({"montage", "intercut"})


@dataclass(frozen=True)
class LinkageComponents:
    """Per-pair linkage scores for the OSD weighted matrix."""

    character: float
    spatial: float
    prop: float
    semantic: float

    @property
    def total_weight(self) -> float:
        """Return the weighted sum W_ij from the OSD specification."""
        return (
            ALPHA_CHARACTER * self.character
            + BETA_SPATIAL * self.spatial
            + GAMMA_PROP * self.prop
            + DELTA_SEMANTIC * self.semantic
        )


@dataclass
class OsdUnit:
    """One OSD graph node, optionally representing a collapsed scene block."""

    unit_id: str
    member_scene_ids: list[str]
    merged_scene: SceneBlock
    cinematic_tag: str | None = None


@dataclass
class OrphanFinding:
    """Structured orphan classification for one scene."""

    scene_id: str
    scene_number: int
    heading: str
    orphan_type: OrphanType
    reasons: list[str] = field(default_factory=list)
    component_scenes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the finding to a JSON-serializable dictionary."""
        return {
            "scene_id": self.scene_id,
            "scene_number": self.scene_number,
            "heading": self.heading,
            "orphan_type": self.orphan_type,
            "reasons": self.reasons,
            "component_scenes": self.component_scenes,
        }


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    """Compute Jaccard similarity between two normalized entity sets."""
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def detect_cinematic_tag(scene: SceneBlock) -> str | None:
    """Detect prologue, flashback, montage, or intercut styling on a scene.

    Args:
        scene: Parsed scene block.

    Returns:
        Cinematic tag name, or ``None`` when no override tag applies.
    """
    text = f"{scene.heading}\n{scene.raw_text}"
    if PROLOGUE_PATTERN.search(text):
        return "prologue"
    if FLASHBACK_PATTERN.search(text):
        return "flashback"
    if MONTAGE_PATTERN.search(text):
        return "montage"
    if INTERCUT_PATTERN.search(scene.heading):
        return "intercut"
    return None


def _person_like_keys_from_props(scene: SceneBlock) -> set[str]:
    """Return single-word caps props that are likely misclassified character names."""
    keys: set[str] = set()
    for prop in scene.props_detected or scene.objects:
        words = prop.split()
        if len(words) != 1:
            continue
        token = words[0]
        if token in WARDROBE_HEAD_NOUNS:
            continue
        if token in CAPS_PROP_STOP_FIRST_WORDS:
            continue
        if len(token) < 3:
            continue
        keys.add(_normalize_token(token))
    return keys


def _character_entity_set(scene: SceneBlock) -> set[str]:
    """Return normalized character keys for linkage and flashback overrides."""
    keys: set[str] = set()
    for name in scene.characters_speaking:
        keys.add(_normalize_token(name))
    for name in scene.characters_mentioned:
        keys.add(_normalize_token(name))
    for name in scene.characters:
        keys.add(_normalize_token(name))
    keys |= _person_like_keys_from_props(scene)
    keys.discard("")
    return keys


def _prop_entity_set(scene: SceneBlock) -> set[str]:
    """Return normalized prop and wardrobe keys for one scene."""
    keys: set[str] = set()
    for prop in scene.props_detected or scene.objects:
        keys.add(_normalize_object_key(prop))
    for item in scene.wardrobe_detected:
        keys.add(_normalize_object_key(item))
    keys.discard("")
    return keys


def _location_entity_set(scene: SceneBlock) -> set[str]:
    """Return normalized location keys extracted from a scene heading."""
    return {_normalize_token(location) for location in scene.locations if location}


def _primary_location(scene: SceneBlock) -> str:
    """Return the broadest location key for a scene."""
    if scene.locations:
        return _normalize_token(scene.locations[0])
    return ""


def _location_similarity(primary_a: str, primary_b: str) -> float:
    """Score primary-location overlap using sequence similarity."""
    if not primary_a or not primary_b:
        return 0.0
    if primary_a == primary_b:
        return 1.0
    ratio = SequenceMatcher(None, primary_a, primary_b).ratio()
    return 1.0 if ratio >= 0.85 else 0.0


def character_linkage(scene_a: SceneBlock, scene_b: SceneBlock) -> float:
    """Compute C_ij via Jaccard similarity of character entity sets."""
    return jaccard_similarity(_character_entity_set(scene_a), _character_entity_set(scene_b))


def spatial_linkage(
    scene_a: SceneBlock,
    scene_b: SceneBlock,
    *,
    is_immediate_prior: bool,
) -> float:
    """Compute L_ij using location overlap and temporal slugline overrides."""
    if is_immediate_prior and scene_b.time_of_day in TEMPORAL_CONTINUITY_TOKENS:
        return 1.0

    locations_a = _location_entity_set(scene_a)
    locations_b = _location_entity_set(scene_b)
    if locations_a & locations_b:
        return 1.0

    return _location_similarity(_primary_location(scene_a), _primary_location(scene_b))


def prop_linkage(scene_a: SceneBlock, scene_b: SceneBlock) -> float:
    """Compute P_ij via Jaccard similarity of prop and wardrobe sets."""
    return jaccard_similarity(_prop_entity_set(scene_a), _prop_entity_set(scene_b))


def compute_linkage_components(
    scene_a: SceneBlock,
    scene_b: SceneBlock,
    *,
    is_immediate_prior: bool,
    semantic_cache: SceneSemanticCache | None = None,
) -> LinkageComponents:
    """Compute all linkage components for an ordered scene pair."""
    return LinkageComponents(
        character=character_linkage(scene_a, scene_b),
        spatial=spatial_linkage(
            scene_a,
            scene_b,
            is_immediate_prior=is_immediate_prior,
        ),
        prop=prop_linkage(scene_a, scene_b),
        semantic=semantic_linkage(
            scene_a,
            scene_b,
            semantic_cache=semantic_cache,
        ),
    )


def compute_link_weight(
    scene_a: SceneBlock,
    scene_b: SceneBlock,
    *,
    is_immediate_prior: bool,
    semantic_cache: SceneSemanticCache | None = None,
) -> float:
    """Return W_ij for an ordered scene pair using OSD weights."""
    return compute_linkage_components(
        scene_a,
        scene_b,
        is_immediate_prior=is_immediate_prior,
        semantic_cache=semantic_cache,
    ).total_weight


def _link_explanation(components: LinkageComponents) -> str:
    """Build a human-readable explanation for a weighted orphan-graph edge."""
    parts: list[str] = []
    if components.character > 0:
        parts.append(f"character={components.character:.2f}")
    if components.spatial > 0:
        parts.append(f"spatial={components.spatial:.2f}")
    if components.prop > 0:
        parts.append(f"prop={components.prop:.2f}")
    if components.semantic > 0:
        parts.append(f"semantic={components.semantic:.2f}")
    return "; ".join(parts) if parts else "osd_weighted_link"


def _merge_scene_blocks(members: list[SceneBlock], unit_id: str) -> SceneBlock:
    """Merge multiple scenes into one synthetic block for external linkage.

    Args:
        members: Scene blocks represented by one OSD unit.
        unit_id: Synthetic scene id for the merged block.

    Returns:
        Combined ``SceneBlock`` with unioned entity fields.
    """
    first = members[0]

    def _union(field: str) -> list[str]:
        seen: set[str] = set()
        merged: list[str] = []
        for scene in members:
            for value in getattr(scene, field):
                key = _normalize_token(value)
                if key and key not in seen:
                    seen.add(key)
                    merged.append(value)
        return merged

    return SceneBlock(
        scene_id=unit_id,
        scene_number=first.scene_number,
        heading=first.heading,
        characters=_union("characters"),
        objects=_union("objects"),
        locations=_union("locations"),
        raw_text="\n\n".join(scene.raw_text for scene in members),
        characters_speaking=_union("characters_speaking"),
        characters_mentioned=_union("characters_mentioned"),
        props_detected=_union("props_detected"),
        wardrobe_detected=_union("wardrobe_detected"),
        time_of_day=first.time_of_day,
    )


def build_osd_units(scenes: list[SceneBlock]) -> list[OsdUnit]:
    """Collapse montage and intercut sequences into unified OSD units.

    Args:
        scenes: Parsed scene blocks in screenplay order.

    Returns:
        Ordered OSD units, one per scene or collapsed block.
    """
    ordered = sorted(scenes, key=lambda scene: scene.scene_number)
    units: list[OsdUnit] = []
    index = 0
    unit_counter = 1

    while index < len(ordered):
        scene = ordered[index]
        tag = detect_cinematic_tag(scene)
        if tag in COLLAPSIBLE_TAGS:
            members = [scene]
            cursor = index + 1
            while cursor < len(ordered):
                next_tag = detect_cinematic_tag(ordered[cursor])
                if next_tag == tag or (
                    tag == "intercut" and next_tag == "intercut"
                ):
                    members.append(ordered[cursor])
                    cursor += 1
                    continue
                break
            unit_id = f"unit_{unit_counter:03d}"
            unit_counter += 1
            units.append(
                OsdUnit(
                    unit_id=unit_id,
                    member_scene_ids=[member.scene_id for member in members],
                    merged_scene=_merge_scene_blocks(members, unit_id),
                    cinematic_tag=tag,
                )
            )
            index = cursor
            continue

        unit_id = f"unit_{unit_counter:03d}"
        unit_counter += 1
        units.append(
            OsdUnit(
                unit_id=unit_id,
                member_scene_ids=[scene.scene_id],
                merged_scene=scene,
                cinematic_tag=tag,
            )
        )
        index += 1

    return units


def build_orphan_graph_from_units(
    units: list[OsdUnit],
    *,
    threshold: float = LINK_THRESHOLD,
    semantic_cache: SceneSemanticCache | None = None,
) -> nx.DiGraph:
    """Build the weighted OSD graph on collapsed units.

    Args:
        units: Ordered OSD units.
        threshold: Minimum W_ij required to add an edge.

    Returns:
        Directed graph whose nodes are unit ids.
    """
    graph = nx.DiGraph()
    for unit in units:
        graph.add_node(
            unit.unit_id,
            heading=unit.merged_scene.heading,
            member_scene_ids=unit.member_scene_ids,
            cinematic_tag=unit.cinematic_tag,
        )

    for later_index, unit_b in enumerate(units):
        for earlier_index in range(later_index):
            unit_a = units[earlier_index]
            components = compute_linkage_components(
                unit_a.merged_scene,
                unit_b.merged_scene,
                is_immediate_prior=(later_index - earlier_index == 1),
                semantic_cache=semantic_cache,
            )
            weight = components.total_weight
            if weight < threshold:
                continue
            graph.add_edge(
                unit_a.unit_id,
                unit_b.unit_id,
                weight=round(weight, 4),
                edge_type="osd",
                explanation=_link_explanation(components),
                character=round(components.character, 4),
                spatial=round(components.spatial, 4),
                prop=round(components.prop, 4),
                semantic=round(components.semantic, 4),
            )

    return graph


def expand_unit_graph_to_scene_graph(
    unit_graph: nx.DiGraph,
    units: list[OsdUnit],
    scenes: list[SceneBlock],
) -> nx.DiGraph:
    """Project a unit-level OSD graph onto original scene ids.

    Args:
        unit_graph: Weighted graph built on OSD units.
        units: Ordered unit list used to build the graph.
        scenes: Original parsed scene blocks.

    Returns:
        Scene-level directed graph preserving screenplay order.
    """
    scene_lookup = {scene.scene_id: scene for scene in scenes}
    unit_lookup = {unit.unit_id: unit for unit in units}
    graph = nx.DiGraph()

    for scene in scenes:
        graph.add_node(
            scene.scene_id,
            heading=scene.heading,
            scene_number=scene.scene_number,
        )

    for source_unit, target_unit, data in unit_graph.edges(data=True):
        source_members = unit_lookup[source_unit].member_scene_ids
        target_members = unit_lookup[target_unit].member_scene_ids
        for source_id in source_members:
            for target_id in target_members:
                source_scene = scene_lookup.get(source_id)
                target_scene = scene_lookup.get(target_id)
                if source_scene is None or target_scene is None:
                    continue
                if source_scene.scene_number >= target_scene.scene_number:
                    continue
                graph.add_edge(source_id, target_id, **data)

    return graph


def _script_has_prologue(scenes: list[SceneBlock]) -> bool:
    """Return True when one of the opening scenes is tagged as prologue."""
    for scene in scenes[:PROLOGUE_EXEMPT_SCENE_COUNT]:
        if detect_cinematic_tag(scene) == "prologue":
            return True
    return False


def _scene_to_unit_map(units: list[OsdUnit]) -> dict[str, str]:
    """Map each scene id to its OSD unit id."""
    mapping: dict[str, str] = {}
    for unit in units:
        for scene_id in unit.member_scene_ids:
            mapping[scene_id] = unit.unit_id
    return mapping


def _main_component_scene_ids(
    unit_graph: nx.DiGraph,
    units: list[OsdUnit],
) -> set[str]:
    """Return scene ids belonging to the largest weakly connected unit component."""
    if unit_graph.number_of_nodes() == 0:
        return set()

    undirected = unit_graph.to_undirected()
    components = list(nx.connected_components(undirected))
    if not components:
        return set()

    main_units = max(components, key=len)
    scene_ids: set[str] = set()
    unit_lookup = {unit.unit_id: unit for unit in units}
    for unit_id in main_units:
        scene_ids.update(unit_lookup[unit_id].member_scene_ids)
    return scene_ids


def _main_component_characters(
    main_scene_ids: set[str],
    scene_lookup: dict[str, SceneBlock],
) -> set[str]:
    """Return character keys appearing anywhere in the main story component."""
    keys: set[str] = set()
    for scene_id in main_scene_ids:
        scene = scene_lookup.get(scene_id)
        if scene is None:
            continue
        keys |= _character_entity_set(scene)
    return keys


def _is_exempt_scene(
    scene: SceneBlock,
    unit: OsdUnit,
    *,
    has_prologue: bool,
    main_characters: set[str],
) -> tuple[bool, list[str]]:
    """Apply AR-OSD cinematic false-positive overrides for one scene.

    Returns:
        Tuple of exemption flag and human-readable override reasons.
    """
    reasons: list[str] = []
    if scene.scene_id == "scene_001":
        return True, ["Opening scene is always excluded from orphan detection."]

    if has_prologue and scene.scene_number <= PROLOGUE_EXEMPT_SCENE_COUNT:
        return True, ["Prologue override: opening scenes are exempt."]

    if unit.cinematic_tag == "montage":
        return True, ["Montage block treated as a unified narrative node (exempt)."]

    if unit.cinematic_tag == "flashback":
        scene_keys = _character_entity_set(scene)
        for main_key in main_characters:
            if main_key in scene_keys:
                return True, [
                    f"Flashback override: shares characters with main plot ({main_key})."
                ]
            for scene_key in scene_keys:
                if main_key in scene_key or scene_key in main_key:
                    return True, [
                        (
                            "Flashback override: shares characters with main plot "
                            f"({main_key})."
                        )
                    ]

    return False, reasons


def detect_orphan_findings(
    scenes: list[SceneBlock],
    units: list[OsdUnit],
    unit_graph: nx.DiGraph,
    scene_graph: nx.DiGraph,
) -> list[OrphanFinding]:
    """Classify hard orphans and orphan subplot chains per AR-OSD Section 4.

    Args:
        scenes: Original parsed scene blocks.
        units: Collapsed OSD units.
        unit_graph: Weighted graph on units.
        scene_graph: Scene-level projection of the unit graph.

    Returns:
        Orphan findings sorted by scene number.
    """
    scene_lookup = {scene.scene_id: scene for scene in scenes}
    unit_lookup = {unit.unit_id: unit for unit in units}
    scene_to_unit = _scene_to_unit_map(units)
    has_prologue = _script_has_prologue(scenes)
    main_scene_ids = _main_component_scene_ids(unit_graph, units)
    main_characters = _main_component_characters(main_scene_ids, scene_lookup)

    unit_in_degree = {
        unit_id: unit_graph.in_degree(unit_id) for unit_id in unit_graph.nodes
    }

    undirected = unit_graph.to_undirected()
    components = [set(component) for component in nx.connected_components(undirected)]
    main_units = max(components, key=len) if components else set()

    subplot_unit_ids: set[str] = set()
    if len(scenes) >= SUBPLOT_MIN_TOTAL_SCENES:
        for component in components:
            if component == main_units:
                continue
            if 1 <= len(component) <= SUBPLOT_CHAIN_MAX_SIZE:
                subplot_unit_ids.update(component)

    findings: list[OrphanFinding] = []

    for scene in sorted(scenes, key=lambda item: item.scene_number):
        unit_id = scene_to_unit[scene.scene_id]
        unit = unit_lookup[unit_id]
        exempt, exempt_reasons = _is_exempt_scene(
            scene,
            unit,
            has_prologue=has_prologue,
            main_characters=main_characters,
        )
        if exempt:
            continue

        component_scene_ids: list[str] = []
        for component in components:
            if unit_id not in component:
                continue
            for member_unit_id in component:
                component_scene_ids.extend(unit_lookup[member_unit_id].member_scene_ids)
            component_scene_ids = sorted(set(component_scene_ids))
            break

        if unit_id in subplot_unit_ids:
            findings.append(
                OrphanFinding(
                    scene_id=scene.scene_id,
                    scene_number=scene.scene_number,
                    heading=scene.heading,
                    orphan_type="subplot_chain",
                    reasons=[
                        (
                            "Part of a small scene thread disconnected from the "
                            f"main story graph ({len(component_scene_ids)} scene(s))."
                        )
                    ],
                    component_scenes=component_scene_ids,
                )
            )
            continue

        if unit_in_degree.get(unit_id, 0) == 0:
            outgoing = list(scene_graph.out_edges(scene.scene_id, data=True))
            if outgoing:
                # Scenes that link forward into the story are not cuttable floaters
                # even when no earlier scene links back (e.g. expedition mid-thread).
                continue
            reasons = [
                "Hard orphan: no incoming or outgoing OSD links to the story graph.",
            ]
            findings.append(
                OrphanFinding(
                    scene_id=scene.scene_id,
                    scene_number=scene.scene_number,
                    heading=scene.heading,
                    orphan_type="hard",
                    reasons=reasons,
                    component_scenes=[scene.scene_id],
                )
            )

    findings.sort(key=lambda item: item.scene_number)
    return findings


def build_orphan_graph(
    scenes: list[SceneBlock],
    *,
    threshold: float = LINK_THRESHOLD,
    semantic_cache: SceneSemanticCache | None = None,
) -> nx.DiGraph:
    """Build the scene-level OSD graph used for orphan detection.

    Args:
        scenes: Parsed scene blocks in screenplay order.
        threshold: Minimum W_ij required to add an edge.

    Returns:
        Directed graph with weighted ``osd`` edges between scene ids.
    """
    units = build_osd_units(scenes)
    unit_graph = build_orphan_graph_from_units(
        units,
        threshold=threshold,
        semantic_cache=semantic_cache,
    )
    return expand_unit_graph_to_scene_graph(unit_graph, units, scenes)


def _build_semantic_cache(units: list[OsdUnit]) -> SceneSemanticCache | None:
    """Precompute semantic embeddings for all OSD unit scenes when enabled."""
    if not is_semantic_enabled():
        return None
    cache = SceneSemanticCache()
    cache.precompute([unit.merged_scene for unit in units])
    return cache


def attach_orphan_graph(
    engine: SceneDependencyEngine,
    scenes: list[SceneBlock],
    *,
    threshold: float = LINK_THRESHOLD,
) -> nx.DiGraph:
    """Build OSD graphs, classify orphans, and store results on the engine.

    Args:
        engine: Engine whose orphan fields will be populated.
        scenes: Parsed scene blocks in screenplay order.
        threshold: Minimum W_ij required to add an edge.

    Returns:
        The scene-level orphan graph instance.
    """
    units = build_osd_units(scenes)
    semantic_cache = _build_semantic_cache(units)
    unit_graph = build_orphan_graph_from_units(
        units,
        threshold=threshold,
        semantic_cache=semantic_cache,
    )
    scene_graph = expand_unit_graph_to_scene_graph(unit_graph, units, scenes)
    findings = detect_orphan_findings(scenes, units, unit_graph, scene_graph)

    engine.orphan_graph = scene_graph
    engine.orphan_unit_graph = unit_graph
    engine.orphan_findings = [finding.to_dict() for finding in findings]
    return engine.orphan_graph


def orphan_records_from_engine(
    engine: SceneDependencyEngine,
    scene_lookup: dict[str, SceneBlock],
) -> list[dict[str, Any]]:
    """Build API-ready orphan records from stored OSD findings.

    Args:
        engine: Engine with ``orphan_findings`` populated.
        scene_lookup: Map of scene id to parsed scene block.

    Returns:
        Orphan record dictionaries sorted by scene number.
    """
    if engine.orphan_findings is not None:
        return sorted(engine.orphan_findings, key=lambda item: item["scene_number"])

    records: list[dict[str, Any]] = []
    for scene_id in engine.get_orphan_scenes():
        scene = scene_lookup.get(scene_id)
        if scene is None:
            continue
        records.append(
            {
                "scene_id": scene.scene_id,
                "scene_number": scene.scene_number,
                "heading": scene.heading,
                "orphan_type": "hard",
                "reasons": ["Hard orphan: no incoming OSD links from earlier scenes."],
                "component_scenes": [scene.scene_id],
            }
        )
    return records
