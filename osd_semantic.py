"""Semantic embeddings for OSD E_ij linkage (Sprint 3).

Uses ``all-MiniLM-L6-v2`` via ``sentence-transformers`` when enabled. Set
``OSD_DISABLE_SEMANTIC=1`` to skip model loading (tests, CI without model cache).

Phase C (dialogue-as-structure): embeddings use heading + action +
structure-bearing dialogue only, not full slang-heavy spoken walls.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scene_dependency import SceneBlock

SEMANTIC_MODEL_NAME = "all-MiniLM-L6-v2"
# Cap spoken text in the embed blob so dialect chatter cannot dominate E_ij.
SEMANTIC_DIALOGUE_CHAR_CAP: int = 400
# When no structure-bearing lines exist, keep a short dialogue sample.
SEMANTIC_FALLBACK_DIALOGUE_LINES: int = 3

_PARENTHETICAL_ONLY = re.compile(r"^\([^)]*\)$")
_ADDRESSEE_PAREN = re.compile(r"\(to\s+[^)]+\)", re.IGNORECASE)


def is_semantic_enabled() -> bool:
    """Return True when semantic linkage should run."""
    return os.environ.get("OSD_DISABLE_SEMANTIC", "").lower() not in (
        "1",
        "true",
        "yes",
    )


def _scene_known_props(scene: SceneBlock) -> set[str]:
    """Return planted prop keys available for soft/alias matching.

    Args:
        scene: Parsed scene block.

    Returns:
        Prop keys from ``props_detected`` or ``objects``.
    """
    props = scene.props_detected or scene.objects or []
    return {prop for prop in props if prop}


def _scene_known_characters(scene: SceneBlock) -> set[str]:
    """Return character names established on this scene for mention checks.

    Args:
        scene: Parsed scene block.

    Returns:
        Cue, mentioned, and presence names for the scene.
    """
    names: set[str] = set()
    for bucket in (
        scene.characters_speaking,
        scene.characters_mentioned,
        scene.characters,
    ):
        for name in bucket or []:
            if name:
                names.add(name)
    return names


def _is_structure_bearing_dialogue_line(line: str, scene: SceneBlock) -> bool:
    """Return True when a spoken line carries structural cargo for E_ij.

    Structure-bearing means causal callback phrasing, a known character
    mention, a planted prop soft/alias hit, or a known location token.

    Args:
        line: One stripped dialogue or parenthetical line.
        scene: Scene that owns the line (provides known entities).

    Returns:
        True when the line should be included in the semantic blob.
    """
    from scene_dependency import (
        CAUSAL_DIALOGUE_PATTERNS,
        _match_known_character_mentions,
        _match_prop_soft_mentions,
    )

    stripped = line.strip()
    if not stripped:
        return False

    if _PARENTHETICAL_ONLY.match(stripped) and not _ADDRESSEE_PAREN.search(stripped):
        return False

    if any(pattern.search(stripped) for pattern in CAUSAL_DIALOGUE_PATTERNS):
        return True

    known_props = _scene_known_props(scene)
    if known_props and _match_prop_soft_mentions(stripped, known_props):
        return True

    aliases: dict[str, str] = {}
    for name in _scene_known_characters(scene):
        aliases[name.upper()] = name
        first = name.split()[0]
        if first:
            aliases[first.upper()] = name
    if aliases and _match_known_character_mentions(stripped, aliases):
        return True

    for location in scene.locations or []:
        loc = location.strip()
        if len(loc) < 4:
            continue
        if re.search(rf"\b{re.escape(loc)}\b", stripped, re.IGNORECASE):
            return True

    return False


def _select_structure_dialogue(scene: SceneBlock, dialogue_lines: list[str]) -> list[str]:
    """Pick structure-bearing dialogue, with a short fallback sample.

    Args:
        scene: Scene providing entity context.
        dialogue_lines: Spoken lines in screenplay order.

    Returns:
        Ordered dialogue lines to embed, before the character-cap trim.
    """
    bearing = [
        line
        for line in dialogue_lines
        if _is_structure_bearing_dialogue_line(line, scene)
    ]
    if bearing:
        return bearing

    fallback: list[str] = []
    for line in dialogue_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _PARENTHETICAL_ONLY.match(stripped) and not _ADDRESSEE_PAREN.search(
            stripped
        ):
            continue
        fallback.append(line)
        if len(fallback) >= SEMANTIC_FALLBACK_DIALOGUE_LINES:
            break
    return fallback


def _cap_dialogue_chars(lines: list[str], max_chars: int) -> str:
    """Join dialogue lines until the character budget is exhausted.

    Args:
        lines: Dialogue lines to include.
        max_chars: Maximum characters of spoken text.

    Returns:
        Joined dialogue string within the budget.
    """
    if max_chars <= 0 or not lines:
        return ""

    parts: list[str] = []
    used = 0
    for line in lines:
        candidate = line.strip()
        if not candidate:
            continue
        extra = len(candidate) + (1 if parts else 0)
        if used + extra > max_chars:
            remaining = max_chars - used - (1 if parts else 0)
            if remaining > 20:
                parts.append(candidate[:remaining].rstrip())
            break
        parts.append(candidate)
        used += extra
    return "\n".join(parts)


def scene_semantic_text(scene: SceneBlock) -> str:
    """Build the text blob embedded for one scene.

    Uses heading + action + structure-bearing dialogue (capped). Full
    slang-only dialogue walls are not embedded.

    Args:
        scene: Parsed scene block.

    Returns:
        Text used for the MiniLM embedding.
    """
    from scene_dependency import _extract_dialogue_lines, _split_action_and_dialogue

    heading = scene.heading.strip()
    raw_lines = scene.raw_text.splitlines()
    body_lines = raw_lines[1:] if raw_lines else []
    action_lines, _character_cues = _split_action_and_dialogue(body_lines)
    dialogue_lines = _extract_dialogue_lines(scene.raw_text)

    parts: list[str] = []
    if heading:
        parts.append(heading)

    action_text = "\n".join(line for line in action_lines if line.strip()).strip()
    if action_text:
        parts.append(action_text)

    selected = _select_structure_dialogue(scene, dialogue_lines)
    dialogue_text = _cap_dialogue_chars(selected, SEMANTIC_DIALOGUE_CHAR_CAP)
    if dialogue_text:
        parts.append(dialogue_text)

    if parts:
        return "\n".join(parts)
    return heading or scene.raw_text.strip()


@lru_cache(maxsize=1)
def _load_sentence_transformer() -> Any:
    """Load and cache the MiniLM sentence-transformer model.

    Returns:
        Loaded ``SentenceTransformer`` instance.

    Raises:
        ImportError: When ``sentence-transformers`` is not installed.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(SEMANTIC_MODEL_NAME)


class SceneSemanticCache:
    """Cache scene embeddings for pairwise semantic linkage."""

    def __init__(self) -> None:
        """Initialize an empty embedding cache."""
        self._vectors: dict[str, Any] = {}
        self._model: Any | None = None

    def precompute(self, scenes: list[SceneBlock]) -> None:
        """Encode all scenes in one batch for efficient reuse.

        Args:
            scenes: Scene blocks whose semantic text will be embedded.
        """
        if not is_semantic_enabled() or not scenes:
            return

        try:
            model = _load_sentence_transformer()
        except ImportError:
            return

        texts: list[str] = []
        scene_ids: list[str] = []
        for scene in scenes:
            text = scene_semantic_text(scene)
            if not text.strip():
                continue
            texts.append(text)
            scene_ids.append(scene.scene_id)

        if not texts:
            return

        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        self._model = model
        for scene_id, vector in zip(scene_ids, embeddings, strict=True):
            self._vectors[scene_id] = vector

    def similarity(self, scene_a: SceneBlock, scene_b: SceneBlock) -> float:
        """Compute cosine similarity between two scene embeddings.

        Args:
            scene_a: Earlier scene in screenplay order.
            scene_b: Later scene in screenplay order.

        Returns:
            Similarity score in ``[0.0, 1.0]``, or ``0.0`` when unavailable.
        """
        vector_a = self._vectors.get(scene_a.scene_id)
        vector_b = self._vectors.get(scene_b.scene_id)
        if vector_a is None or vector_b is None:
            return 0.0

        dot = float((vector_a * vector_b).sum())
        return max(0.0, min(1.0, dot))


def semantic_linkage(
    scene_a: SceneBlock,
    scene_b: SceneBlock,
    *,
    semantic_cache: SceneSemanticCache | None = None,
) -> float:
    """Compute E_ij semantic overlap between two scenes.

    Args:
        scene_a: Earlier scene block.
        scene_b: Later scene block.
        semantic_cache: Optional precomputed embedding cache.

    Returns:
        Semantic similarity score used in the OSD weighted matrix.
    """
    if semantic_cache is None:
        return 0.0
    return semantic_cache.similarity(scene_a, scene_b)
