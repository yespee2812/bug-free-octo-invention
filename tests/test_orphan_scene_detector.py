"""Tests for the OSD Sprint 1 orphan scene detector."""

from __future__ import annotations

from pathlib import Path

import pytest

from orphan_scene_detector import (
    attach_orphan_graph,
    build_orphan_graph,
    build_osd_units,
    compute_link_weight,
    detect_cinematic_tag,
    jaccard_similarity,
    prop_linkage,
    spatial_linkage,
)
from scene_dependency import SceneBlock, SceneDependencyEngine

STATUE_DEMO = Path("docs/demo_scripts/orphan_statue_demo.fountain")
TEMPORAL_SCRIPT = """INT. HOUSE - KITCHEN - DAY

ELENA cooks breakfast.

INT. HOUSE - KITCHEN - CONTINUOUS

ELENA pours coffee.
"""


def _parse_script(script: str) -> list[SceneBlock]:
    """Parse Fountain text and attach an OSD orphan graph."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(script)
    engine.build_graph(scenes, include_fact_edges=False, include_causal_edges=False)
    attach_orphan_graph(engine, scenes)
    return scenes


def test_jaccard_similarity_basic() -> None:
    """Jaccard returns 1.0 for identical sets and 0.0 for disjoint sets."""
    assert jaccard_similarity({"A", "B"}, {"A", "B"}) == 1.0
    assert jaccard_similarity({"A"}, {"B"}) == 0.0
    assert jaccard_similarity(set(), set()) == 0.0


def test_scene_block_populates_speaking_and_mentioned() -> None:
    """Parser splits dialogue speakers from action-mentioned characters."""
    script = (
        "INT. ROOM - DAY\n\n"
        "MARCUS enters.\n\n"
        "MARCUS\n"
        "Hello.\n\n"
        "INT. HALL - DAY\n\n"
        "SOFIA waits.\n"
    )
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(script)
    assert "MARCUS" in scenes[0].characters_speaking
    assert scenes[0].characters_mentioned == []
    assert "SOFIA" in scenes[1].props_detected or "SOFIA" in scenes[1].characters


def test_temporal_continuous_links_immediate_prior() -> None:
    """CONTINUOUS sluglines link spatially to the immediately prior scene."""
    scenes = _parse_script(TEMPORAL_SCRIPT)
    assert scenes[1].time_of_day == "CONTINUOUS"
    weight = compute_link_weight(
        scenes[0],
        scenes[1],
        is_immediate_prior=True,
    )
    assert weight >= 0.20


def test_statue_demo_flags_scene_two_orphan() -> None:
    """The AR-OSD statue fixture marks scene_002 as an orphan."""
    text = STATUE_DEMO.read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    attach_orphan_graph(engine, scenes)
    orphans = engine.get_orphan_scenes()
    assert orphans == ["scene_002"]


def test_build_orphan_graph_adds_weighted_edges() -> None:
    """OSD graph edges store component scores and total weight."""
    text = STATUE_DEMO.read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    graph = build_orphan_graph(scenes)
    assert graph.has_edge("scene_001", "scene_003")
    edge = graph["scene_001"]["scene_003"]
    assert edge["edge_type"] == "osd"
    assert edge["weight"] >= 0.20
    assert edge["character"] > 0
    assert edge["prop"] > 0


def test_spatial_linkage_matches_shared_location_prefix() -> None:
    """Shared location hierarchy yields spatial linkage of 1.0."""
    scene_a = SceneBlock(
        scene_id="scene_001",
        scene_number=1,
        heading="INT. HOUSE - KITCHEN - DAY",
        locations=["HOUSE", "HOUSE KITCHEN"],
        time_of_day="DAY",
    )
    scene_b = SceneBlock(
        scene_id="scene_002",
        scene_number=2,
        heading="INT. HOUSE - BEDROOM - NIGHT",
        locations=["HOUSE", "HOUSE BEDROOM"],
        time_of_day="NIGHT",
    )
    assert spatial_linkage(scene_a, scene_b, is_immediate_prior=False) == 1.0


def test_prop_linkage_uses_detected_props() -> None:
    """Prop linkage reads props_detected and wardrobe_detected fields."""
    scene_a = SceneBlock(
        scene_id="scene_001",
        scene_number=1,
        heading="INT. A - DAY",
        props_detected=["LEDGER"],
    )
    scene_b = SceneBlock(
        scene_id="scene_002",
        scene_number=2,
        heading="INT. B - DAY",
        props_detected=["LEDGER"],
    )
    assert prop_linkage(scene_a, scene_b) == 1.0


@pytest.mark.parametrize(
    ("script_path", "expected_orphans"),
    [
        ("docs/demo_scripts/orphan_statue_demo.fountain", ["scene_002"]),
    ],
)
def test_orphan_spec_manifest_cases(script_path: str, expected_orphans: list[str]) -> None:
    """Golden orphan-spec fixtures match expected orphan scene ids."""
    text = Path(script_path).read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    attach_orphan_graph(engine, scenes)
    assert engine.get_orphan_scenes() == expected_orphans


def test_prologue_opening_scenes_are_exempt() -> None:
    """Prologue-tagged scripts exempt the opening scene pair from orphan flags."""
    text = Path("docs/demo_scripts/orphan_prologue_demo.fountain").read_text(
        encoding="utf-8",
    )
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    attach_orphan_graph(engine, scenes)
    assert engine.get_orphan_scenes() == []


def test_montage_block_is_exempt_from_orphans() -> None:
    """Montage sequences collapse into one node and are exempt from orphan flags."""
    text = Path("docs/demo_scripts/orphan_montage_demo.fountain").read_text(
        encoding="utf-8",
    )
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    attach_orphan_graph(engine, scenes)
    assert engine.get_orphan_scenes() == []


def test_flashback_with_shared_character_is_exempt() -> None:
    """Flashback scenes sharing a main-plot character are not flagged as orphans."""
    text = Path("docs/demo_scripts/orphan_flashback_demo.fountain").read_text(
        encoding="utf-8",
    )
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    attach_orphan_graph(engine, scenes)
    assert "scene_002" not in engine.get_orphan_scenes()


def test_montage_and_intercut_scenes_collapse_into_one_unit() -> None:
    """Montage headings collapse consecutive scenes into a single OSD unit."""
    text = Path("docs/demo_scripts/orphan_montage_demo.fountain").read_text(
        encoding="utf-8",
    )
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    units = build_osd_units(scenes)
    montage_units = [
        unit for unit in units if unit.cinematic_tag == "montage"
    ]
    assert len(montage_units) == 1
    assert len(montage_units[0].member_scene_ids) == 2


def _build_subplot_chain_script() -> str:
    """Build a 41-scene script with a two-scene disconnected island at the end."""
    chunks = ["INT. MAIN - DAY\n\nHERO enters.\n"]
    for beat in range(2, 40):
        chunks.append(f"\nINT. MAIN - DAY\n\nHERO continues beat {beat}.\n")
    chunks.append("\nINT. ISLAND A - DAY\n\nUNIQUE_A finds a NOTE.\n")
    chunks.append("\nINT. ISLAND B - DAY\n\nUNIQUE_A reads the NOTE.\n")
    return "".join(chunks)


def test_subplot_chain_flags_isolated_two_scene_thread() -> None:
    """Long scripts flag small disconnected components as orphan subplot chains."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(_build_subplot_chain_script())
    attach_orphan_graph(engine, scenes)
    orphan_ids = engine.get_orphan_scenes()
    assert orphan_ids == ["scene_040", "scene_041"]
    findings = {row["scene_id"]: row for row in engine.orphan_findings}
    assert findings["scene_040"]["orphan_type"] == "subplot_chain"
    assert findings["scene_041"]["orphan_type"] == "subplot_chain"
    assert len(findings["scene_040"]["component_scenes"]) == 2


def test_orphan_findings_include_reasons() -> None:
    """Hard orphan findings include human-readable reasons."""
    text = STATUE_DEMO.read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    attach_orphan_graph(engine, scenes)
    finding = engine.orphan_findings[0]
    assert finding["orphan_type"] == "hard"
    assert finding["reasons"]
    assert finding["scene_id"] == "scene_002"
