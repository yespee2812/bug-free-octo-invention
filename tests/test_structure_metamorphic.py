"""Metamorphic and synthetic tests for the v3 structure engine.

Implements the two highest-ROI unconventional methods from
``docs/SCRIPTLENS_TESTING_PROCESS.pdf``:

- Entity-swap isomorphism (consistent renames must preserve structure)
- Synthetic Chekhov's-gun generator (plant → filler → payoff across variants)

Rename maps and Chekhov patterns are loaded from
``tests/corpus/ground_truth/structure/rename_and_chekhov_patterns.yaml``
so owners can extend them without editing this file.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from orphan_scene_detector import attach_orphan_graph
from scene_dependency import SceneDependencyEngine
from scriptlens_structure import analyze_structure, get_simulate_cut_impact

PATTERNS_PATH = Path(
    "tests/corpus/ground_truth/structure/rename_and_chekhov_patterns.yaml"
)


def _load_patterns() -> dict[str, object]:
    """Load owner-editable rename maps and Chekhov patterns.

    Returns:
        Parsed YAML mapping.
    """
    payload = yaml.safe_load(PATTERNS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid patterns file: {PATTERNS_PATH}")
    return payload


def _rename_pairs(entry_key: str) -> tuple[Path, list[tuple[str, str]]]:
    """Return script path and rename pairs for a patterns entry.

    Args:
        entry_key: Top-level key in the patterns YAML.

    Returns:
        Tuple of script path and ``(from, to)`` rename pairs.
    """
    payload = _load_patterns()
    entry = payload[entry_key]
    assert isinstance(entry, dict)
    script = Path(str(entry["script"]))
    renames = [
        (str(item["from"]), str(item["to"]))
        for item in entry.get("renames", [])
    ]
    return script, renames


def _chekhov_variants() -> list[tuple[str, str, str]]:
    """Return Chekhov (plant, mid, payoff) wording triples.

    Returns:
        List of plant/mid/payoff strings from the patterns YAML.
    """
    payload = _load_patterns()
    rows = payload.get("chekhov_patterns", [])
    assert isinstance(rows, list)
    return [
        (str(row["plant"]), str(row["mid"]), str(row["payoff"]))
        for row in rows
    ]


def _structure_signature(screenplay_text: str) -> dict[str, object]:
    """Return a comparable structure fingerprint for metamorphic checks.

    Args:
        screenplay_text: Fountain screenplay text.

    Returns:
        Dict with orphan ids, directed edge pairs, and scene count.
    """
    results = analyze_structure(screenplay_text)
    engine = results["engine"]
    orphans = tuple(sorted(engine.get_orphan_scenes()))
    edges = tuple(
        sorted(
            (str(source), str(target))
            for source, target in engine.graph.edges()
        )
    )
    return {
        "scene_count": results["script_summary"]["total_scenes"],
        "orphans": orphans,
        "edges": edges,
    }


def _apply_rename_map(text: str, rename_map: list[tuple[str, str]]) -> str:
    """Apply entity renames longest-first so multi-word names win.

    Args:
        text: Original screenplay text.
        rename_map: Ordered (from, to) pairs; longer ``from`` values preferred.

    Returns:
        Text with all mapped entities replaced.
    """
    updated = text
    for source, target in sorted(rename_map, key=lambda pair: len(pair[0]), reverse=True):
        pattern = re.compile(re.escape(source), flags=re.IGNORECASE)
        updated = pattern.sub(target, updated)
    return updated


def test_entity_swap_isomorphism_revolver_seed() -> None:
    """Renaming Marcus/revolver must preserve orphans and edge pairs."""
    script_path, rename_map = _rename_pairs("revolver_chain_demo")
    original = script_path.read_text(encoding="utf-8")
    renamed = _apply_rename_map(original, rename_map)
    assert _structure_signature(original) == _structure_signature(renamed)


def test_entity_swap_isomorphism_action_seed() -> None:
    """Action-demo renames keep orphan set and dependency topology stable."""
    script_path, rename_map = _rename_pairs("action_5scene_simulate_demo")
    original = script_path.read_text(encoding="utf-8")
    renamed = _apply_rename_map(original, rename_map)
    before = _structure_signature(original)
    after = _structure_signature(renamed)
    assert before["scene_count"] == after["scene_count"]
    assert before["orphans"] == after["orphans"]
    assert before["edges"] == after["edges"]


def test_entity_swap_isomorphism_birth_locket_demo() -> None:
    """Birth-locket renames keep orphan set and dependency topology stable."""
    script_path, rename_map = _rename_pairs("birth_locket_2scene_demo")
    original = script_path.read_text(encoding="utf-8")
    renamed = _apply_rename_map(original, rename_map)
    before = _structure_signature(original)
    after = _structure_signature(renamed)
    assert before["scene_count"] == after["scene_count"]
    assert before["orphans"] == after["orphans"]
    assert before["edges"] == after["edges"]


def _chekhov_script(plant: str, mid_ref: str, payoff_ref: str) -> str:
    """Build a three-scene plant → filler → payoff Fountain micro-script.

    Args:
        plant: Object phrase planted in scene 1.
        mid_ref: How scene 2 refers to the object.
        payoff_ref: How scene 3 refers to the object.

    Returns:
        Fountain text for the synthetic script.
    """
    planted = plant[0].upper() + plant[1:] if plant else plant
    return (
        "INT. ROOM ONE - DAY\n\n"
        f"A table. {planted} rests in plain sight.\n\n"
        "INT. ROOM TWO - DAY\n\n"
        f"ALEX picks up {mid_ref}.\n\n"
        "INT. ROOM THREE - NIGHT\n\n"
        f"ALEX uses {payoff_ref}.\n"
    )


@pytest.mark.parametrize(("plant", "mid_ref", "payoff_ref"), _chekhov_variants())
def test_chekhov_generator_links_plant_to_payoff(
    plant: str,
    mid_ref: str,
    payoff_ref: str,
) -> None:
    """Every wording variant must create plant→payoff continuity and no orphans."""
    script = _chekhov_script(plant, mid_ref, payoff_ref)
    results = analyze_structure(script)
    engine = results["engine"]
    assert results["script_summary"]["total_scenes"] == 3
    assert engine.get_orphan_scenes() == []

    edge_pairs = {(str(source), str(target)) for source, target in engine.graph.edges()}
    assert ("scene_001", "scene_002") in edge_pairs
    assert ("scene_001", "scene_003") in edge_pairs or ("scene_002", "scene_003") in edge_pairs

    impact = get_simulate_cut_impact(engine, "scene_001", engine._scene_lookup)
    impacted = {row["scene_id"] for row in impact["impacted_scenes"]}
    assert "scene_002" in impacted or "scene_003" in impacted


def test_scene_permutation_locality_independent_pair() -> None:
    """Swapping two entity-disjoint adjacent scenes keeps other edges stable."""
    script = (
        "INT. LAB - DAY\n\n"
        "DR. MAYA plants a VIAL on the bench.\n\n"
        "INT. ALLEY - NIGHT\n\n"
        "A stray CAT watches the rain.\n\n"
        "INT. ROOFTOP - DAY\n\n"
        "A lone PIGEON lands on the ledge.\n\n"
        "INT. LAB - NIGHT\n\n"
        "DR. MAYA opens the vial.\n"
    )
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(script)
    assert len(scenes) == 4

    body_two = scenes[1].raw_text
    body_three = scenes[2].raw_text
    permuted = (
        script.replace(body_two, "__TMP__", 1)
        .replace(body_three, body_two, 1)
        .replace("__TMP__", body_three, 1)
    )

    before = _structure_signature(script)
    after = _structure_signature(permuted)
    assert before["scene_count"] == after["scene_count"]
    assert set(before["orphans"]) == {"scene_002", "scene_003"}
    assert set(after["orphans"]) == {"scene_002", "scene_003"}
    assert ("scene_001", "scene_004") in set(before["edges"])
    assert ("scene_001", "scene_004") in set(after["edges"])


def test_attach_orphan_graph_still_runs_after_rename() -> None:
    """OSD attach path tolerates fully renamed entities."""
    script_path, rename_map = _rename_pairs("revolver_chain_demo")
    original = script_path.read_text(encoding="utf-8")
    renamed = _apply_rename_map(original, rename_map)
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(renamed)
    engine.build_graph(scenes, include_fact_edges=False, include_causal_edges=True)
    attach_orphan_graph(engine, scenes)
    assert engine.get_orphan_scenes() == []
