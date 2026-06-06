"""Scene dependency analysis for Fountain-format screenplays."""

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import networkx as nx
import spacy
from spacy.language import Language

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


def _extract_objects_from_action(action_lines: list[str], nlp: Language) -> list[str]:
    """Extract noun phrases from action lines using spaCy noun chunks."""
    if not action_lines:
        return []

    text = " ".join(action_lines)
    doc = nlp(text)
    objects: list[str] = []
    seen: set[str] = set()

    for chunk in doc.noun_chunks:
        phrase = " ".join(token.text for token in chunk if not token.is_space)
        normalized = _normalize_object_key(phrase)
        if len(normalized) < 2 or normalized in seen:
            continue
        seen.add(normalized)
        objects.append(normalized)

    return objects


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

        Args:
            text: Raw Fountain screenplay text.

        Returns:
            A list of SceneBlock objects in screenplay order.
        """
        matches = list(SCENE_HEADING_PATTERN.finditer(text))
        scenes: list[SceneBlock] = []

        if not matches:
            return scenes

        for index, match in enumerate(matches, start=1):
            prefix = match.group(1).upper()
            location_tail = match.group(2).strip()
            heading = f"{prefix} {location_tail}".strip()
            start = match.start()
            end = matches[index].start() if index < len(matches) else len(text)
            raw_text = text[start:end].strip()
            body_lines = raw_text.splitlines()[1:]

            action_lines, character_lines = _split_action_and_dialogue(body_lines)
            characters = sorted(
                {_normalize_token(name) for name in character_lines},
                key=str.lower,
            )
            objects = _extract_objects_from_action(action_lines, self.nlp)
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
