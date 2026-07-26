"""Structure-only ScriptLens analysis: orphans, scene graph, simulate-cut prep.

This module is the v3 product path. It does not run plot contradiction detection.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any, Literal

from nlp_shared import get_shared_nlp
from pdf_to_fountain import ConversionStage
from scene_dependency import SCENE_HEADING_PATTERN, SceneBlock, SceneDependencyEngine

from orphan_scene_detector import attach_orphan_graph, orphan_records_from_engine
from scene_function_impact import (
    evaluate_scene_function_cut,
    sfi_rows_to_impacted_scenes,
)
from simulate_impact_summary import (
    build_downstream_at_risk_records,
    enrich_cut_impact_scenes,
    format_orphan_delta_message,
    merge_cut_impact_rows,
    summarize_cut_impact,
    summarize_edit_impact,
)
from screenplay_io import SUPPORTED_TEXT_SUFFIXES, load_screenplay_with_meta
from pdf_ingest import PdfIngestResult, ScreenplayLoadError, build_upload_ingest_warnings

StructureMode = Literal["full", "limited"]

_SLUGLINE_DETECT_PATTERN = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)\s+",
    re.IGNORECASE,
)


def detect_structure_mode(scenes: list[SceneBlock]) -> StructureMode:
    """Return full when sluglines are detected, else limited.

    Args:
        scenes: Parsed scene blocks from the screenplay.

    Returns:
        ``full`` if at least one scene heading looks like INT/EXT; otherwise
        ``limited`` (typical for image-only PDF exports).
    """
    if not scenes:
        return "limited"
    for scene in scenes:
        if _SLUGLINE_DETECT_PATTERN.match(scene.heading.strip()):
            return "full"
    return "limited"


def _build_high_risk_scenes(
    engine: SceneDependencyEngine,
    scene_lookup: dict[str, SceneBlock],
) -> list[dict[str, Any]]:
    """Rank scenes by how many later scenes depend on them if cut.

    Args:
        engine: Built dependency engine with a populated graph.
        scene_lookup: Map of scene_id to parsed scene blocks.

    Returns:
        Records sorted by downstream breakage count descending.
    """
    ranked: list[dict[str, Any]] = []
    for scene_id in engine.graph.nodes:
        impact = engine.get_delete_impact(scene_id)
        if not impact:
            continue
        scene = scene_lookup.get(scene_id)
        heading = scene.heading if scene else scene_id
        ranked.append(
            {
                "scene_id": scene_id,
                "scene_number": scene.scene_number if scene else 0,
                "heading": heading,
                "would_break": len(impact),
                "impacted_scenes": [record["scene_id"] for record in impact],
            }
        )

    ranked.sort(key=lambda record: record["would_break"], reverse=True)
    return ranked


def _scene_to_summary(scene: SceneBlock) -> dict[str, Any]:
    """Convert a scene block to a lightweight API/CLI summary.

    Args:
        scene: Parsed scene block.

    Returns:
        Summary dict with id, number, and heading.
    """
    return {
        "scene_id": scene.scene_id,
        "scene_number": scene.scene_number,
        "heading": scene.heading,
    }


def _orphan_records(
    engine: SceneDependencyEngine,
    scene_lookup: dict[str, SceneBlock],
) -> list[dict[str, Any]]:
    """Build orphan scene summaries from the dependency engine.

    Args:
        engine: Built dependency engine.
        scene_lookup: Map of scene_id to parsed scene blocks.

    Returns:
        Orphan records with type and reasons, sorted by scene number.
    """
    return orphan_records_from_engine(engine, scene_lookup)


def analyze_structure(screenplay_text: str) -> dict[str, Any]:
    """Parse a screenplay and return structure-only analysis.

    Builds the scene dependency graph using continuity edges and causal
    dialogue callbacks. Plot contradiction and fact-store extraction are not
    used.

    Args:
        screenplay_text: Full screenplay in Fountain plain text.

    Returns:
        Structure report with scenes, orphans, graph summary, and high-risk
        scenes. No ``contradictions`` key is included.
    """
    shared_nlp = get_shared_nlp()
    engine = SceneDependencyEngine(nlp=shared_nlp)
    scenes = engine.parse_fountain_text(screenplay_text)
    engine.build_graph(
        scenes,
        include_fact_edges=False,
        include_causal_edges=True,
    )
    attach_orphan_graph(engine, scenes)

    scene_lookup = {scene.scene_id: scene for scene in scenes}
    orphan_records = _orphan_records(engine, scene_lookup)
    graph_summary = engine.export_graph_summary()

    return {
        "script_summary": {
            "total_scenes": len(scenes),
            "structure_mode": detect_structure_mode(scenes),
        },
        "scenes": [_scene_to_summary(scene) for scene in scenes],
        "structure": {
            "orphan_count": len(orphan_records),
            "orphans": orphan_records,
            "graph_summary": graph_summary,
            "high_risk_scenes": _build_high_risk_scenes(engine, scene_lookup),
        },
        "engine": engine,
    }


def analyze_structure_from_path(
    input_path: str | Path,
    *,
    include_engine: bool = False,
    pdf_conversion: ConversionStage = "refined",
) -> dict[str, Any]:
    """Analyze a screenplay file using the structure-only path.

    Args:
        input_path: Path to PDF or Fountain/text screenplay.
        include_engine: When True, keep the ``SceneDependencyEngine`` on the
            result for simulate-cut calls in the same process. API layers should
            store the engine in a session instead of serializing this field.
        pdf_conversion: PDF conversion stage passed to ``load_screenplay_text``.

    Returns:
        Structure report plus an ``input`` metadata block. The ``engine`` key is
        omitted unless ``include_engine`` is True.

    Raises:
        FileNotFoundError: If the input path does not exist.
        ValueError: If the file type is unsupported.
    """
    path = Path(input_path).resolve()
    screenplay_text, input_format, ingest_meta = load_screenplay_with_meta(
        path,
        pdf_conversion=pdf_conversion,
        source_filename=path.name,
    )
    results = analyze_structure(screenplay_text)
    engine = results.pop("engine")

    results["input"] = {
        "path": str(path),
        "filename": path.name,
        "format": input_format,
        **ingest_meta,
    }
    if input_format == "pdf":
        ingest = PdfIngestResult(
            text=screenplay_text,
            conversion_stage=pdf_conversion,
            ingest_method=ingest_meta.get("ingest_method", "slugline_extract"),
            slugline_count=int(ingest_meta.get("slugline_count", 0)),
            warnings=list(ingest_meta.get("ingest_warnings", [])),
        )
        results["input"]["ingest_warnings"] = build_upload_ingest_warnings(
            ingest,
            structure_mode=results["script_summary"]["structure_mode"],
            scene_count=results["script_summary"]["total_scenes"],
        )

    if include_engine:
        results["engine"] = engine

    return results


def analyze_structure_from_bytes(
    content: bytes,
    filename: str,
    *,
    pdf_conversion: ConversionStage = "refined",
) -> tuple[dict[str, Any], SceneDependencyEngine, str]:
    """Analyze uploaded screenplay bytes using the structure-only path.

    Writes content to a temporary file so ``load_screenplay_text`` can reuse the
    existing PDF and Fountain loaders.

    Args:
        content: Raw uploaded file bytes.
        filename: Original filename (used for suffix detection).
        pdf_conversion: PDF conversion stage when the upload is a PDF.

    Returns:
        Tuple of structure report (without ``engine`` key), the built
        ``SceneDependencyEngine``, and canonical screenplay text for session
        storage.

    Raises:
        ValueError: If the filename suffix is unsupported or content is empty.
    """
    if not content:
        raise ValueError("Uploaded file is empty.")

    suffix = Path(filename).suffix.lower()
    if suffix != ".pdf" and suffix not in SUPPORTED_TEXT_SUFFIXES:
        allowed = ", ".join(sorted({".pdf", *SUPPORTED_TEXT_SUFFIXES}))
        raise ValueError(
            f"Unsupported file type '{suffix}'. Use one of: {allowed}."
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        temp_path = Path(handle.name)
        handle.write(content)

    try:
        screenplay_text, input_format, ingest_meta = load_screenplay_with_meta(
            temp_path,
            pdf_conversion=pdf_conversion,
            source_filename=filename,
        )
    finally:
        temp_path.unlink(missing_ok=True)

    results = analyze_structure(screenplay_text)
    engine = results.pop("engine")
    results["input"] = {
        "filename": filename,
        "format": input_format,
        **ingest_meta,
    }
    if input_format == "pdf":
        ingest = PdfIngestResult(
            text=screenplay_text,
            conversion_stage=pdf_conversion,
            ingest_method=ingest_meta.get("ingest_method", "slugline_extract"),
            slugline_count=int(ingest_meta.get("slugline_count", 0)),
            warnings=list(ingest_meta.get("ingest_warnings", [])),
        )
        results["input"]["ingest_warnings"] = build_upload_ingest_warnings(
            ingest,
            structure_mode=results["script_summary"]["structure_mode"],
            scene_count=results["script_summary"]["total_scenes"],
        )

    return results, engine, screenplay_text


def _path_explanation(engine: SceneDependencyEngine, path: list[str]) -> str:
    """Return a human-readable label for the first hop on a dependency path.

    Args:
        engine: Built dependency engine.
        path: Ordered scene ids from removed scene to impacted scene.

    Returns:
        Edge explanation string, or empty when no hop exists.
    """
    if len(path) < 2:
        return ""
    edge_data = engine.graph.get_edge_data(path[0], path[1]) or {}
    explanation = edge_data.get("explanation", "")
    return str(explanation) if explanation else ""


def get_simulate_cut_impact(
    engine: SceneDependencyEngine,
    scene_id: str,
    scene_lookup: dict[str, SceneBlock],
) -> dict[str, Any]:
    """Return simulate-cut impact for a scene using a built engine.

    Combines continuity-graph delete impact with Scene Function Impact (SFI
    D-lite). Story-function losses drive the headline verdict; graph paths
    remain as supporting downstream rows.

    Args:
        engine: Dependency engine with a populated graph.
        scene_id: Scene to evaluate for deletion impact.
        scene_lookup: Map of scene_id to parsed scene blocks.

    Returns:
        Removed scene metadata and impacted downstream scenes with paths.
    """
    scene = scene_lookup.get(scene_id)
    if scene is None:
        return {
            "removed_scene": None,
            "impacted_scenes": [],
        }

    graph_impacted = enrich_cut_impact_scenes(
        engine,
        [
            {
                **record,
                "explanation": _path_explanation(engine, record["dependency_path"]),
            }
            for record in engine.get_delete_impact(scene_id)
        ],
    )
    sfi = evaluate_scene_function_cut(engine.scenes, scene_id)
    sfi_impacted = sfi_rows_to_impacted_scenes(scene_id, sfi)
    impacted = merge_cut_impact_rows(graph_impacted, sfi_impacted)
    removed_summary = _scene_to_summary(scene)
    headline = summarize_cut_impact(
        removed_summary,
        impacted,
        sfi_summary=sfi.summary,
        sfi_risk_level=sfi.risk_level,
        sfi_lost_count=len(sfi.lost_functions),
        sfi_is_bridge=sfi.is_bridge,
    )

    return {
        "removed_scene": removed_summary,
        "impacted_scenes": impacted,
        "summary": headline["summary"],
        "risk_level": headline["risk_level"],
        "lost_functions": [item.to_dict() for item in sfi.lost_functions],
        "verdict_basis": "scene_functions"
        if sfi.lost_functions or sfi.is_bridge
        else "continuity_graph",
    }


def normalize_modified_scene_text(
    original_scene: SceneBlock,
    modified_text: str,
) -> str:
    """Ensure edited scene text includes a slugline before re-parsing.

    Args:
        original_scene: Scene block being edited.
        modified_text: User-supplied Fountain text for the scene.

    Returns:
        Normalized scene text with a leading slugline.
    """
    text = modified_text.strip()
    if not text:
        return original_scene.raw_text

    first_line = text.splitlines()[0].strip()
    if _SLUGLINE_DETECT_PATTERN.match(first_line):
        return text

    return f"{original_scene.heading}\n\n{text}"


def count_scene_headings(screenplay_text: str) -> int:
    """Return how many INT./EXT. sluglines appear in screenplay text.

    Args:
        screenplay_text: Full Fountain screenplay text.

    Returns:
        Number of scene-heading matches in document order.
    """
    return len(list(SCENE_HEADING_PATTERN.finditer(screenplay_text)))


def delete_scene_block(screenplay_text: str, scene_number: int) -> str:
    """Remove one scene block from screenplay text.

    Deletes from the selected slugline through the character before the next
    slugline (or end of file).

    Args:
        screenplay_text: Full Fountain screenplay text.
        scene_number: One-based scene index matching parser order.

    Returns:
        Updated screenplay text with the scene block removed.

    Raises:
        ValueError: When the scene number is out of range.
    """
    matches = list(SCENE_HEADING_PATTERN.finditer(screenplay_text))
    if scene_number < 1 or scene_number > len(matches):
        raise ValueError(f"Invalid scene_number: {scene_number}")

    index = scene_number - 1
    start = matches[index].start()
    end = matches[index + 1].start() if index + 1 < len(matches) else len(screenplay_text)
    updated = screenplay_text[:start] + screenplay_text[end:]
    return updated.strip() + "\n"


def structure_state_from_draft(draft_text: str) -> dict[str, Any]:
    """Build engine and structure metadata from draft Fountain text.

    Args:
        draft_text: Current working-copy screenplay text.

    Returns:
        Engine plus structure fields used to refresh an analysis session.
    """
    results = analyze_structure(draft_text)
    engine = results.pop("engine")
    structure = results["structure"]
    return {
        "engine": engine,
        "structure_mode": results["script_summary"]["structure_mode"],
        "scenes": results["scenes"],
        "orphan_count": structure["orphan_count"],
        "orphans": structure["orphans"],
        "graph_summary": structure["graph_summary"],
        "high_risk_scenes": structure["high_risk_scenes"],
    }


def splice_scene_in_screenplay(
    screenplay_text: str,
    scene_number: int,
    modified_scene_text: str,
) -> str:
    """Replace one scene's Fountain block inside a full screenplay.

    Args:
        screenplay_text: Full screenplay text.
        scene_number: One-based scene index matching parser order.
        modified_scene_text: Replacement Fountain text for that scene.

    Returns:
        Updated screenplay text with the scene body swapped in.

    Raises:
        ValueError: When the scene number is out of range.
    """
    matches = list(SCENE_HEADING_PATTERN.finditer(screenplay_text))
    if scene_number < 1 or scene_number > len(matches):
        raise ValueError(f"Invalid scene_number: {scene_number}")

    index = scene_number - 1
    start = matches[index].start()
    end = matches[index + 1].start() if index + 1 < len(matches) else len(screenplay_text)
    middle = modified_scene_text.strip()
    if middle and not middle.endswith("\n"):
        middle += "\n\n"
    return screenplay_text[:start] + middle + screenplay_text[end:].lstrip("\n")


def _snapshot_graph_edges(
    engine: SceneDependencyEngine,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Capture a comparable view of all dependency edges in a graph.

    Args:
        engine: Built dependency engine.

    Returns:
        Map of ``(from_scene_id, to_scene_id)`` to edge metadata.
    """
    snapshot: dict[tuple[str, str], dict[str, Any]] = {}
    for source, target, data in engine.graph.edges(data=True):
        snapshot[(source, target)] = {
            "from_scene_id": source,
            "to_scene_id": target,
            "weight": round(float(data.get("weight", 0.0)), 4),
            "edge_type": str(data.get("edge_type", "")),
            "explanation": str(data.get("explanation", "")),
        }
    return snapshot


def _diff_graph_edges(
    before: dict[tuple[str, str], dict[str, Any]],
    after: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Compare edge snapshots and return added, removed, and changed edges.

    Args:
        before: Edge snapshot from the original graph.
        after: Edge snapshot from the edited graph.

    Returns:
        Dictionary with ``added``, ``removed``, and ``changed`` edge lists.
    """
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []

    for key, record in after.items():
        if key not in before:
            added.append(record)
            continue
        prior = before[key]
        if (
            prior["weight"] != record["weight"]
            or prior["edge_type"] != record["edge_type"]
            or prior["explanation"] != record["explanation"]
        ):
            changed.append(
                {
                    "from_scene_id": record["from_scene_id"],
                    "to_scene_id": record["to_scene_id"],
                    "before": prior,
                    "after": record,
                }
            )

    for key, record in before.items():
        if key not in after:
            removed.append(record)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def get_simulate_edit_impact(
    engine: SceneDependencyEngine,
    screenplay_text: str,
    scene_id: str,
    modified_text: str,
) -> dict[str, Any]:
    """Preview dependency edge changes after rewriting one scene.

    Re-parses the full screenplay with the edited scene spliced in, rebuilds the
    graph using continuity edges only, and diffs against the current session
    graph.

    Args:
        engine: Current session dependency engine.
        screenplay_text: Canonical screenplay text for the session.
        scene_id: Scene being edited.
        modified_text: Replacement Fountain text for that scene.

    Returns:
        Edge diff, orphan delta, and downstream scene ids at risk.

    Raises:
        ValueError: When the scene id is unknown or the splice fails.
    """
    scene = engine._scene_lookup.get(scene_id)
    if scene is None:
        raise ValueError(f"Unknown scene_id: {scene_id}")

    normalized_text = normalize_modified_scene_text(scene, modified_text)
    updated_screenplay = splice_scene_in_screenplay(
        screenplay_text,
        scene.scene_number,
        normalized_text,
    )

    before_edges = _snapshot_graph_edges(engine)
    orphans_before = len(engine.get_orphan_scenes())
    scene_count_before = engine.graph.number_of_nodes()

    after_results = analyze_structure(updated_screenplay)
    after_engine = after_results.pop("engine")
    after_edges = _snapshot_graph_edges(after_engine)
    orphans_after = len(after_engine.get_orphan_scenes())
    scene_count_after = after_engine.graph.number_of_nodes()

    edge_diff = _diff_graph_edges(before_edges, after_edges)
    downstream_at_risk = build_downstream_at_risk_records(
        scene_id,
        edge_diff,
        engine._scene_lookup,
    )
    orphan_delta = {
        "before": orphans_before,
        "after": orphans_after,
        "message": format_orphan_delta_message(orphans_before, orphans_after),
    }
    headline = summarize_edit_impact(edge_diff, orphan_delta, downstream_at_risk)

    return {
        "scene_id": scene_id,
        "edited_scene": _scene_to_summary(scene),
        "edge_diff": edge_diff,
        "orphan_delta": orphan_delta,
        "scene_count_before": scene_count_before,
        "scene_count_after": scene_count_after,
        "downstream_at_risk": downstream_at_risk,
        "summary": headline["summary"],
        "risk_level": headline["risk_level"],
    }


def pretty_print_structure_results(results: dict[str, Any]) -> None:
    """Print structure-only results in plain language for screenwriters.

    Args:
        results: Output from ``analyze_structure`` or ``analyze_structure_from_path``.
    """
    summary = results["script_summary"]
    structure = results["structure"]
    graph = structure["graph_summary"]
    orphans = structure["orphans"]
    high_risk = structure["high_risk_scenes"]
    mode = summary.get("structure_mode", "full")

    print()
    print("=" * 72)
    print("SCRIPTLENS STRUCTURE REPORT")
    print("=" * 72)

    print()
    print("YOUR SCRIPT AT A GLANCE")
    print("-" * 72)
    print(f"  Scenes:          {summary['total_scenes']}")
    print(f"  Structure mode:  {mode}")
    if mode == "limited":
        print(
            "  Note: Scene breaks were not detected. Upload Fountain or a "
            "text-based PDF for full structure analysis."
        )

    print()
    print("LOOSELY CONNECTED SCENES (ORPHANS)")
    print("-" * 72)
    orphan_count = structure["orphan_count"]
    if orphan_count == 0:
        print("  No orphan scenes detected after the opening.")
    else:
        print(
            f"  {orphan_count} scene(s) sit loosely in the story — nothing "
            "later depends on them:"
        )
        for record in orphans:
            print(
                f"    Scene {record['scene_number']}: {record['heading']} "
                f"({record['scene_id']})"
            )

    print()
    print("HOW YOUR SCENES CONNECT")
    print("-" * 72)
    print(
        f"  {graph['total_scenes']} scenes linked by "
        f"{graph['total_edges']} story connections."
    )
    if graph.get("most_depended_on_scene"):
        print(
            f"  Most depended-on scene: {graph['most_depended_on_scene']}."
        )
    print(
        f"  Average upstream dependencies per scene: "
        f"{graph['avg_dependencies_per_scene']}."
    )

    print()
    print("SCENES YOU SHOULD NOT CUT LIGHTLY")
    print("-" * 72)
    if not high_risk:
        print("  No scene removals would knock out later story beats.")
    else:
        for index, record in enumerate(high_risk[:5], start=1):
            print(
                f"  {index}. Scene {record['scene_number']} - {record['heading']}"
            )
            print(
                f"     Removing this would weaken {record['would_break']} "
                "later scene(s): "
                f"{', '.join(record['impacted_scenes'])}."
            )
        if len(high_risk) > 5:
            print(f"  ... and {len(high_risk) - 5} more scene(s) with downstream ties.")

    print()
    print("NEXT: Simulate cut a scene with:")
    print("  python run_scriptlens.py <script> --structure-only --simulate-cut scene_005")
    print()
