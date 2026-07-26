"""Map writer error-injection logs to engine types and compare to analysis results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Substrings matched case-insensitively against the writer log ``category`` field.
# Order matters: first match wins.
WRITER_CATEGORY_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("dead", "alive", "death", "killed", "kia"), "character_alive_status"),
    (("timeline", "calendar", "day of the week", "yesterday", "clock"), "timeline_consistency"),
    (("profession", "role clash", "job", "surgeon", "lawyer", "trait"), "character_trait_conflict"),
    (("wrong owner", "ownership", "changes hands", "never with"), "object_ownership"),
    (("destroyed", "burned", "shredded"), "object_destroyed"),
    (("lost", "left behind", "misplaced"), "object_lost"),
    (("laterality", "wrong side", "left arm", "right arm"), "medical_laterality"),
    (("recovery", "vanish", "injury", "medical", "unconscious"), "medical_recovery"),
    (("parent", "child reversed", "role inversion"), "relationship_fact"),
    (("relationship", "sibling", "spouse", "brother", "sister", "wife", "husband"), "relationship_fact"),
    (("location", "warehouse", "description clash"), "location_continuity"),
    (("semantic location", "same place"), "semantic_location"),
    (("numeric", "count", "hostage", "room number", "runs this month"), "numeric_count"),
    (("year", "date year", "expedition"), "date_year"),
    (("age", "years old", "fifty", "forty"), "character_age"),
    (("name", "spelling", "typo"), "name_consistency"),
    (("knowledge", "should not know", "deduction", "awareness"), "character_knowledge"),
    (("identity", "object identity", "payment", "photo"), "object_identity"),
    (("world rule",), ""),
)

# When the mapped type differs from what the engine emits, accept these aliases.
ENGINE_TYPE_ALIASES: dict[str, frozenset[str]] = {
    "relationship_conflict": frozenset({"relationship_fact"}),
    "relationship_role_inversion": frozenset({"relationship_fact"}),
    "location_continuity": frozenset({"location_continuity", "semantic_location"}),
    "semantic_location": frozenset({"semantic_location", "location_continuity"}),
    "object_destroyed": frozenset({"object_destroyed", "object_state"}),
    "object_lost": frozenset({"object_lost", "object_state"}),
}


@dataclass(frozen=True)
class ExpectedError:
    """One planted error from a writer log, mapped for engine comparison."""

    error_number: int
    writer_category: str
    engine_type: str
    scene_a: int
    scene_b: int
    note: str
    mappable: bool


@dataclass(frozen=True)
class ComparisonResult:
    """Outcome of comparing a writer log to engine contradictions."""

    expected: list[ExpectedError]
    matched: list[tuple[ExpectedError, dict[str, Any]]]
    missed: list[ExpectedError]
    unmapped: list[ExpectedError]
    extra: list[dict[str, Any]]
    detected_count: int


def map_writer_category(category: str) -> tuple[str, bool]:
    """Map a plain-English writer category to an engine contradiction type.

    Args:
        category: Value of ``category`` in the writer error log.

    Returns:
        Tuple of (engine_type, mappable). Empty engine_type means not auto-mapped.
    """
    lowered = category.strip().lower()
    if not lowered:
        return "", False
    for keywords, engine_type in WRITER_CATEGORY_RULES:
        if any(keyword in lowered for keyword in keywords):
            return engine_type, bool(engine_type)
    return lowered.replace(" ", "_"), True


def _scene_pair_key(engine_type: str, scene_a: int, scene_b: int) -> tuple[str, int, int]:
    """Normalize a contradiction key so scene order does not matter."""
    first, second = sorted((int(scene_a), int(scene_b)))
    return engine_type, first, second


def _accepted_engine_types(engine_type: str) -> frozenset[str]:
    """Return engine types that satisfy a mapped writer category."""
    aliases = ENGINE_TYPE_ALIASES.get(engine_type, frozenset())
    return frozenset({engine_type, *aliases})


def parse_writer_log(log_data: dict[str, Any]) -> list[ExpectedError]:
    """Convert a writer error-injection log dict into expected engine errors.

    Args:
        log_data: Parsed YAML from ``ERROR_INJECTION_LOG_TEMPLATE.yaml``.

    Returns:
        Expected errors with mapped engine types and scene numbers.
    """
    planted = list(log_data.get("planted_errors") or [])
    expected: list[ExpectedError] = []
    for index, entry in enumerate(planted, start=1):
        if not isinstance(entry, dict):
            continue
        category = str(entry.get("category") or "").strip()
        engine_type, mappable = map_writer_category(category)
        scene_a = int(entry.get("establishing_scene") or 0)
        scene_b = int(entry.get("contradicting_scene") or 0)
        note_parts = [
            str(entry.get("establishing_moment") or "").strip(),
            str(entry.get("contradicting_moment") or "").strip(),
            str(entry.get("how_a_reader_notices") or "").strip(),
        ]
        note = " | ".join(part for part in note_parts if part)
        expected.append(
            ExpectedError(
                error_number=int(entry.get("error_number") or index),
                writer_category=category,
                engine_type=engine_type,
                scene_a=scene_a,
                scene_b=scene_b,
                note=note[:240],
                mappable=mappable and scene_a > 0 and scene_b > 0,
            )
        )
    return expected


def compare_writer_log_to_results(
    log_data: dict[str, Any],
    results: dict[str, Any],
) -> ComparisonResult:
    """Compare a writer log to ScriptLens analysis results.

    Args:
        log_data: Parsed writer error-injection YAML.
        results: Output dict from ``analyze_from_path`` / ``analyze_screenplay``.

    Returns:
        Structured match, miss, unmapped, and extra-flag breakdown.
    """
    expected = parse_writer_log(log_data)
    detected = list(results.get("contradictions", {}).get("items", []))

    detected_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    for item in detected:
        scenes = item.get("scenes_involved") or [0, 0]
        scene_a = int(scenes[0]) if scenes else 0
        scene_b = int(scenes[1]) if len(scenes) > 1 else scene_a
        key = _scene_pair_key(str(item.get("contradiction_type", "")), scene_a, scene_b)
        detected_by_key.setdefault(key, item)

    matched: list[tuple[ExpectedError, dict[str, Any]]] = []
    missed: list[ExpectedError] = []
    unmapped: list[ExpectedError] = []
    used_keys: set[tuple[str, int, int]] = set()

    for error in expected:
        if not error.mappable:
            unmapped.append(error)
            continue
        accepted = _accepted_engine_types(error.engine_type)
        key = _scene_pair_key(error.engine_type, error.scene_a, error.scene_b)
        hit = None
        for candidate_type in accepted:
            candidate_key = _scene_pair_key(candidate_type, error.scene_a, error.scene_b)
            if candidate_key in detected_by_key:
                hit = detected_by_key[candidate_key]
                used_keys.add(candidate_key)
                break
        if hit is not None:
            matched.append((error, hit))
        else:
            missed.append(error)

    extra = [
        item
        for key, item in detected_by_key.items()
        if key not in used_keys
    ]
    return ComparisonResult(
        expected=expected,
        matched=matched,
        missed=missed,
        unmapped=unmapped,
        extra=extra,
        detected_count=len(detected),
    )


def format_comparison_report(
    script_name: str,
    log_data: dict[str, Any],
    comparison: ComparisonResult,
) -> str:
    """Render a human-readable writer-log vs engine comparison report.

    Args:
        script_name: Screenplay filename or stem for the report header.
        log_data: Parsed writer log (for metadata).
        comparison: Result from ``compare_writer_log_to_results``.

    Returns:
        Plain-text report suitable for saving or printing.
    """
    writer = str(log_data.get("writer_name") or "").strip()
    title = str(log_data.get("script_title") or script_name).strip()
    mappable = [error for error in comparison.expected if error.mappable]
    lines: list[str] = [
        f"WRITER LOG EVALUATION: {title}",
        f"Script file: {script_name}",
        "=" * 72,
        "",
    ]
    if writer:
        lines.append(f"Writer: {writer}")
        lines.append("")

    lines.extend(
        [
            "SUMMARY",
            f"  Planted errors in log:     {len(comparison.expected)}",
            f"  Auto-mappable:             {len(mappable)}",
            f"  Matched by engine:         {len(comparison.matched)}",
            f"  Missed (false negatives):  {len(comparison.missed)}",
            f"  Unmapped (manual review):  {len(comparison.unmapped)}",
            f"  Extra engine flags:        {len(comparison.extra)}",
            f"  Total engine detections:   {comparison.detected_count}",
            "",
        ]
    )
    if mappable:
        recall = len(comparison.matched) / len(mappable)
        lines.append(f"  Recall (auto-mapped only): {recall:.0%}")
        lines.append("")

    if comparison.matched:
        lines.append("MATCHED")
        for error, hit in comparison.matched:
            lines.append(
                f"  [{error.error_number}] {error.writer_category} -> "
                f"{hit.get('contradiction_type')} "
                f"(scene {error.scene_a} vs {error.scene_b})"
            )
        lines.append("")

    if comparison.missed:
        lines.append("MISSED — review manually (engine may have used different scenes/type)")
        for error in comparison.missed:
            lines.append(
                f"  [{error.error_number}] {error.writer_category} -> "
                f"expected {error.engine_type} "
                f"(scene {error.scene_a} vs {error.scene_b})"
            )
            if error.note:
                lines.append(f"      {error.note}")
        lines.append("")

    if comparison.unmapped:
        lines.append("UNMAPPED — category not linked to engine or missing scene numbers")
        for error in comparison.unmapped:
            lines.append(
                f"  [{error.error_number}] {error.writer_category or '(no category)'} "
                f"(scene {error.scene_a} vs {error.scene_b})"
            )
        lines.append("")

    if comparison.extra:
        lines.append("EXTRA ENGINE FLAGS (possible false positives)")
        for item in comparison.extra:
            scenes = item.get("scenes_involved") or [0, 0]
            lines.append(
                f"  - {item.get('contradiction_type')}: "
                f"scene {scenes[0]} vs {scenes[1] if len(scenes) > 1 else scenes[0]}"
            )
            explanation = str(item.get("explanation") or "")
            if explanation:
                lines.append(f"      {explanation[:120]}")
        lines.append("")

    notes = str(log_data.get("notes") or "").strip()
    if notes:
        lines.append(f"Writer notes: {notes}")
        lines.append("")

    lines.append(
        "Tip: A miss does not always mean failure — the engine may have caught "
        "the issue under a different type or scene pair. Check the full report."
    )
    return "\n".join(lines)
