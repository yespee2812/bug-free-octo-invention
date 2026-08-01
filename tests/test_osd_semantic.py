"""Tests for OSD Sprint 3 semantic embeddings."""

from __future__ import annotations

from pathlib import Path

import pytest
import numpy as np

from orphan_scene_detector import (
    attach_orphan_graph,
    compute_linkage_components,
)
from osd_semantic import (
    SceneSemanticCache,
    clear_embedding_cache,
    embedding_cache_size,
    semantic_linkage,
)
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


def test_precompute_reuses_shared_embedding_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second precompute of unchanged scenes does not re-encode them."""
    monkeypatch.delenv("OSD_DISABLE_SEMANTIC", raising=False)
    clear_embedding_cache()

    text = Path(
        "docs/demo_scripts/orphan_semantic_thread_demo.fountain",
    ).read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)

    first = SceneSemanticCache()
    first.precompute(scenes)
    assert embedding_cache_size() == len(first._vectors)
    assert first._vectors

    class _BoomModel:
        """Stand-in model that fails if encode is invoked unexpectedly."""

        def encode(self, *args: object, **kwargs: object) -> None:
            """Raise when the shared cache should have absorbed the work."""
            raise AssertionError("encode should not run on a full cache hit")

    monkeypatch.setattr(
        "osd_semantic._load_sentence_transformer",
        lambda: _BoomModel(),
    )

    second = SceneSemanticCache()
    second.precompute(scenes)
    assert set(second._vectors) == set(first._vectors)
    for scene_id, vector in first._vectors.items():
        assert np.allclose(second._vectors[scene_id], vector)


def test_precompute_encodes_only_changed_scenes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Editing one scene re-encodes only that scene's text."""
    monkeypatch.delenv("OSD_DISABLE_SEMANTIC", raising=False)
    clear_embedding_cache()

    text = Path(
        "docs/demo_scripts/orphan_semantic_thread_demo.fountain",
    ).read_text(encoding="utf-8")
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(text)

    warm = SceneSemanticCache()
    warm.precompute(scenes)
    warmed = embedding_cache_size()
    assert warmed >= 2

    encode_calls: list[int] = []
    real_loader = __import__(
        "osd_semantic",
        fromlist=["_load_sentence_transformer"],
    )._load_sentence_transformer
    real_model = real_loader()
    original_encode = real_model.encode

    def _counting_encode(texts: list[str], **kwargs: object) -> object:
        """Record batch sizes while delegating to the real encoder."""
        encode_calls.append(len(texts))
        return original_encode(texts, **kwargs)

    monkeypatch.setattr(real_model, "encode", _counting_encode)
    monkeypatch.setattr(
        "osd_semantic._load_sentence_transformer",
        lambda: real_model,
    )

    edited = list(scenes)
    changed = SceneBlock(
        scene_id=edited[0].scene_id,
        scene_number=edited[0].scene_number,
        heading=edited[0].heading,
        raw_text=edited[0].raw_text + "\nA brand new beat arrives.\n",
        characters=list(edited[0].characters),
        objects=list(edited[0].objects),
        locations=list(edited[0].locations),
        characters_speaking=list(edited[0].characters_speaking),
        characters_mentioned=list(edited[0].characters_mentioned),
        props_detected=list(edited[0].props_detected),
    )
    edited[0] = changed

    cool = SceneSemanticCache()
    cool.precompute(edited)
    assert encode_calls == [1]
    assert embedding_cache_size() == warmed + 1
    assert changed.scene_id in cool._vectors

