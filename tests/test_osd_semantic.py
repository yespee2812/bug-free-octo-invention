"""Tests for OSD Sprint 3 semantic embeddings."""

from __future__ import annotations

from pathlib import Path

import pytest
import numpy as np

from orphan_scene_detector import (
    attach_orphan_graph,
    compute_linkage_components,
)
from osd_semantic import SceneSemanticCache, semantic_linkage
from scene_dependency import SceneBlock, SceneDependencyEngine


def test_semantic_linkage_returns_zero_without_cache() -> None:
    """Semantic linkage is a no-op when no embedding cache is supplied."""
    scene_a = SceneBlock(
        scene_id="scene_001",
        scene_number=1,
        heading="INT. A - DAY",
        raw_text="Alpha text.",
    )
    scene_b = SceneBlock(
        scene_id="scene_002",
        scene_number=2,
        heading="INT. B - DAY",
        raw_text="Beta text.",
    )
    assert semantic_linkage(scene_a, scene_b) == 0.0


def test_compute_linkage_components_accepts_semantic_cache() -> None:
    """Linkage components include a semantic score from the cache."""
    scene_a = SceneBlock(
        scene_id="scene_001",
        scene_number=1,
        heading="INT. A - DAY",
        raw_text="Negotiator on rooftop.",
    )
    scene_b = SceneBlock(
        scene_id="scene_002",
        scene_number=2,
        heading="INT. B - DAY",
        raw_text="Negotiator on radio.",
    )
    cache = SceneSemanticCache()
    cache._vectors = {
        "scene_001": np.array([1.0, 0.0]),
        "scene_002": np.array([0.8, 0.6]),
    }

    components = compute_linkage_components(
        scene_a,
        scene_b,
        is_immediate_prior=True,
        semantic_cache=cache,
    )
    assert components.semantic == pytest.approx(0.8, abs=0.001)
    assert components.total_weight >= components.semantic * 0.15


def test_semantic_thread_demo_links_narrative_beats(monkeypatch: pytest.MonkeyPatch) -> None:
    """Similar narrative beats receive non-zero semantic linkage."""
    monkeypatch.delenv("OSD_DISABLE_SEMANTIC", raising=False)

    text = Path(
        "docs/demo_scripts/orphan_semantic_thread_demo.fountain",
    ).read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    cache = SceneSemanticCache()
    cache.precompute(scenes)

    components = compute_linkage_components(
        scenes[0],
        scenes[1],
        is_immediate_prior=True,
        semantic_cache=cache,
    )
    assert components.semantic > 0.35


def test_semantic_thread_demo_has_no_hard_orphans(monkeypatch: pytest.MonkeyPatch) -> None:
    """A threaded command-post script stays connected once E_ij is enabled."""
    monkeypatch.delenv("OSD_DISABLE_SEMANTIC", raising=False)

    text = Path(
        "docs/demo_scripts/orphan_semantic_thread_demo.fountain",
    ).read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)
    attach_orphan_graph(engine, scenes)
    assert engine.get_orphan_scenes() == []


def test_semantic_increases_link_weight_over_cpl_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E_ij adds extra weight beyond character, location, and prop overlap."""
    monkeypatch.delenv("OSD_DISABLE_SEMANTIC", raising=False)

    text = Path(
        "docs/demo_scripts/orphan_semantic_thread_demo.fountain",
    ).read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)

    without_semantic = compute_linkage_components(
        scenes[0],
        scenes[1],
        is_immediate_prior=True,
        semantic_cache=None,
    )
    cache = SceneSemanticCache()
    cache.precompute(scenes)
    with_semantic = compute_linkage_components(
        scenes[0],
        scenes[1],
        is_immediate_prior=True,
        semantic_cache=cache,
    )

    assert with_semantic.semantic > 0.0
    assert with_semantic.total_weight > without_semantic.total_weight
