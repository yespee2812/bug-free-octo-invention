"""Combined ScriptLens analysis: scene dependencies and plot contradictions."""

from pathlib import Path
from typing import Any

from legacy.plot_contradiction import (
    Contradiction,
    ContradictionEngine,
    INPUT_PROFILE_PDF_BENCHMARK,
    INPUT_PROFILE_STANDARD,
    InputProfile,
)
from pdf_to_fountain import ConversionStage
from pdf_ingest import ScreenplayLoadError, build_upload_ingest_warnings, ingest_pdf
from nlp_shared import get_shared_nlp
from scene_dependency import SceneBlock, SceneDependencyEngine

SUPPORTED_TEXT_SUFFIXES: frozenset[str] = frozenset(
    {".fountain", ".fadein", ".txt", ".md", ".screenplay"}
)
_PDF_DERIVED_STEM_MARKERS: tuple[str, ...] = ("_manual", "_refined", "_clean")


def _infer_input_profile(
    path: Path,
    input_format: str,
    explicit: InputProfile | None,
) -> InputProfile:
    """Choose standard vs pdf_benchmark when the caller did not specify a profile."""
    if explicit is not None:
        return explicit
    if input_format == "pdf":
        return INPUT_PROFILE_PDF_BENCHMARK
    stem = path.stem.lower()
    if any(marker in stem for marker in _PDF_DERIVED_STEM_MARKERS):
        return INPUT_PROFILE_PDF_BENCHMARK
    return INPUT_PROFILE_STANDARD


def analyze_screenplay(
    screenplay_text: str,
    *,
    input_profile: InputProfile = INPUT_PROFILE_STANDARD,
) -> dict[str, Any]:
    """Parse a Fountain screenplay and return a combined analysis report.

    Runs scene dependency graph construction and Tier 1 + Tier 2 contradiction
    detection, then assembles a structured result dictionary.

    Args:
        screenplay_text: Full screenplay in Fountain plain text.
        input_profile: ``standard`` for writer/CI scripts; ``pdf_benchmark``
            applies stricter numeric_count rules for PDF-extracted screenplays.

    Returns:
        Structured analysis with script summary, dependencies, contradictions,
        and an overall health score.
    """
    shared_nlp = get_shared_nlp()
    dependency_engine = SceneDependencyEngine(nlp=shared_nlp)
    scenes = dependency_engine.parse_fountain_text(screenplay_text)

    contradiction_engine = ContradictionEngine(
        nlp=shared_nlp,
        input_profile=input_profile,
    )
    fact_store = contradiction_engine.extract_facts(scenes)
    dependency_engine.build_graph(scenes, fact_store=fact_store)

    tier1_results = contradiction_engine.run_tier1(fact_store, scenes)
    tier2_results = contradiction_engine.run_tier2(
        fact_store, scenes, tier1_results
    )
    contradictions = contradiction_engine._deduplicate_contradictions(
        tier1_results + tier2_results
    )

    characters = sorted(
        {character for scene in scenes for character in scene.characters},
        key=str.casefold,
    )
    objects = sorted(
        {obj for scene in scenes for obj in scene.objects},
        key=str.casefold,
    )

    scene_lookup = {scene.scene_id: scene for scene in scenes}
    high_risk_scenes = _build_high_risk_scenes(dependency_engine, scene_lookup)

    contradiction_items = [_contradiction_to_dict(item) for item in contradictions]
    tier1_count = sum(1 for item in contradictions if item.tier == 1)
    tier2_count = sum(1 for item in contradictions if item.tier == 2)

    orphan_count = len(dependency_engine.get_orphan_scenes())
    health_score = max(0, 100 - (len(contradictions) * 8) - (orphan_count * 3))

    return {
        "script_summary": {
            "total_scenes": len(scenes),
            "total_characters": characters,
            "total_objects": objects,
        },
        "dependencies": {
            "graph_summary": dependency_engine.export_graph_summary(),
            "high_risk_scenes": high_risk_scenes,
        },
        "contradictions": {
            "total_found": len(contradictions),
            "by_tier": {"tier1": tier1_count, "tier2": tier2_count},
            "items": contradiction_items,
        },
        "health_score": health_score,
    }


def load_screenplay_with_meta(
    input_path: str | Path,
    *,
    pdf_conversion: ConversionStage = "clean",
    source_filename: str | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """Load screenplay text and return ingest metadata for API responses.

    Args:
        input_path: Path to .pdf, .fountain, .txt, or similar.
        pdf_conversion: For PDFs only — ``raw``, ``clean``, or ``refined``.
        source_filename: Original upload filename used for PDF cleanup rules.

    Returns:
        Tuple of screenplay text, input format (``pdf`` or ``text``), and an
        ingest metadata dictionary.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the file type is not supported.
        ScreenplayLoadError: If a PDF cannot be converted.
    """
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        result = ingest_pdf(
            path,
            stage=pdf_conversion,
            source_filename=source_filename or path.name,
        )
        return (
            result.text,
            "pdf",
            {
                "pdf_conversion": pdf_conversion,
                "ingest_method": result.ingest_method,
                "slugline_count": result.slugline_count,
                "ingest_warnings": list(result.warnings),
            },
        )
    if suffix in SUPPORTED_TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8"), "text", {}

    raise ValueError(
        f"Unsupported file type '{suffix}' for {path.name}. "
        f"Use .pdf or one of: {', '.join(sorted(SUPPORTED_TEXT_SUFFIXES))}."
    )


def load_screenplay_text(
    input_path: str | Path,
    *,
    pdf_conversion: ConversionStage = "clean",
    source_filename: str | None = None,
) -> tuple[str, str]:
    """Load screenplay plain text from a PDF or text file.

    PDF inputs are converted to Fountain-style text before return. By default
    the ``clean`` stage reflows action and demotes camera slugs so analysis
    sees fewer false character names.

    Args:
        input_path: Path to .pdf, .fountain, .txt, or similar.
        pdf_conversion: For PDFs only — ``raw``, ``clean`` (default), or
            ``refined``. Ignored for Fountain/text files.
        source_filename: Original upload filename used for PDF cleanup rules.

    Returns:
        Tuple of (screenplay_text, input_format) where input_format is
        ``pdf`` or ``text``.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the file type is not supported.
        ScreenplayLoadError: If a PDF cannot be converted.
    """
    text, input_format, _meta = load_screenplay_with_meta(
        input_path,
        pdf_conversion=pdf_conversion,
        source_filename=source_filename,
    )
    return text, input_format


def analyze_from_path(
    input_path: str | Path,
    *,
    include_extracted_text: bool = False,
    input_profile: InputProfile | None = None,
    pdf_conversion: ConversionStage = "refined",
) -> dict[str, Any]:
    """Analyze a screenplay file (PDF or Fountain/text).

    Args:
        input_path: Path to the screenplay file.
        include_extracted_text: When True, include normalized text in the
            result (useful for debugging PDF extraction).
        input_profile: Engine input profile. Defaults to ``pdf_benchmark`` for
            PDF inputs and ``standard`` for Fountain/text files.
        pdf_conversion: For PDF inputs, conversion stage before analysis
            (``clean`` by default — see ``pdf_to_fountain``).

    Returns:
        Same structure as analyze_screenplay, plus an ``input`` metadata block.
    """
    path = Path(input_path).resolve()
    screenplay_text, input_format = load_screenplay_text(
        path,
        pdf_conversion=pdf_conversion,
    )
    profile = _infer_input_profile(path, input_format, input_profile)
    results = analyze_screenplay(screenplay_text, input_profile=profile)
    results["input"] = {
        "path": str(path),
        "filename": path.name,
        "format": input_format,
        "input_profile": profile,
    }
    if input_format == "pdf":
        results["input"]["pdf_conversion"] = pdf_conversion
    if include_extracted_text:
        results["input"]["extracted_text"] = screenplay_text
    return results


def _build_high_risk_scenes(
    engine: SceneDependencyEngine,
    scene_lookup: dict[str, SceneBlock],
) -> list[dict[str, Any]]:
    """Rank scenes by how many later scenes depend on them if cut."""
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
                "heading": heading,
                "would_break": len(impact),
                "impacted_scenes": [record["scene_id"] for record in impact],
            }
        )

    ranked.sort(key=lambda record: record["would_break"], reverse=True)
    return ranked


def _contradiction_to_dict(contradiction: Contradiction) -> dict[str, Any]:
    """Convert a Contradiction dataclass to the API result shape."""
    return {
        "scenes_involved": [
            contradiction.scene_number_a,
            contradiction.scene_number_b,
        ],
        "contradiction_type": contradiction.contradiction_type,
        "explanation": contradiction.explanation,
        "confidence": contradiction.confidence,
        "tier": contradiction.tier,
        "status": contradiction.status,
    }


def pretty_print_results(results: dict[str, Any]) -> None:
    """Print analysis results in plain language for screenwriters."""
    summary = results["script_summary"]
    dependencies = results["dependencies"]
    graph = dependencies["graph_summary"]
    contradictions = results["contradictions"]
    health = results["health_score"]

    print()
    print("=" * 72)
    print("SCRIPTLENS STORY REPORT")
    print("=" * 72)

    print()
    print("YOUR SCRIPT AT A GLANCE")
    print("-" * 72)
    print(f"  Scenes:     {summary['total_scenes']}")
    character_list = summary["total_characters"]
    if character_list:
        print(f"  Characters: {', '.join(character_list)}")
    else:
        print("  Characters: (none detected)")
    object_list = summary["total_objects"]
    if object_list:
        print(f"  Props:      {', '.join(object_list)}")
    else:
        print("  Props:      (none detected)")

    print()
    print("HOW YOUR SCENES CONNECT")
    print("-" * 72)
    print(
        f"  Your story has {graph['total_scenes']} scenes linked by "
        f"{graph['total_edges']} story connections."
    )
    if graph.get("most_depended_on_scene"):
        print(
            f"  The scene other scenes rely on most: "
            f"{graph['most_depended_on_scene']}."
        )
    print(
        f"  On average, each scene builds on about "
        f"{graph['avg_dependencies_per_scene']} earlier scenes."
    )
    orphan_count = graph.get("orphan_count", 0)
    if orphan_count:
        print(
            f"  {orphan_count} scene(s) sit loosely in the story - nothing later "
            "depends on them, so they may be easy to cut or need stronger ties."
        )
    else:
        print("  Every scene after the opening is referenced by a later scene.")

    high_risk = dependencies["high_risk_scenes"]
    print()
    print("SCENES YOU SHOULD NOT CUT LIGHTLY")
    print("-" * 72)
    if not high_risk:
        print("  No scene removals would knock out later story beats.")
    else:
        for index, record in enumerate(high_risk[:5], start=1):
            print(
                f"  {index}. {record['scene_id']} - {record['heading']}"
            )
            print(
                f"     Removing this would weaken {record['would_break']} "
                "later scene(s): "
                f"{', '.join(record['impacted_scenes'])}."
            )
        if len(high_risk) > 5:
            print(f"  ... and {len(high_risk) - 5} more scene(s) with downstream ties.")

    print()
    print("STORY CONSISTENCY ISSUES")
    print("-" * 72)
    total = contradictions["total_found"]
    if total == 0:
        print("  No contradictions found - facts and timeline look consistent.")
    else:
        by_tier = contradictions["by_tier"]
        print(
            f"  Found {total} possible inconsistency(ies): "
            f"{by_tier['tier1']} clear conflict(s), "
            f"{by_tier['tier2']} subtler mismatch(es)."
        )
        for index, item in enumerate(contradictions["items"], start=1):
            scene_a, scene_b = item["scenes_involved"]
            label = _plain_contradiction_label(item["contradiction_type"])
            confidence_pct = int(round(item["confidence"] * 100))
            prefix = "Possible issue" if item.get("status") == "possible" else "Issue"
            print()
            print(f"  {prefix} {index}: {label}")
            print(f"    Between scene {scene_a} and scene {scene_b}")
            print(f"    {item['explanation']}")
            print(f"    Confidence: about {confidence_pct}%")

    print()
    print("OVERALL SCRIPT HEALTH")
    print("-" * 72)
    print(f"  Score: {health} / 100")
    if health >= 85:
        print("  Your draft is in strong shape - few structural or logic concerns.")
    elif health >= 70:
        print(
            "  Solid draft with room to tighten loose scenes or fix a few "
            "story beats."
        )
    elif health >= 50:
        print(
            "  Worth a revision pass: address contradictions and scenes that "
            "feel disconnected."
        )
    else:
        print(
            "  Several story logic or structure issues - prioritize "
            "contradictions and scene links before polishing dialogue."
        )
    print()


def _plain_contradiction_label(contradiction_type: str) -> str:
    """Map internal contradiction types to screenwriter-friendly labels."""
    labels = {
        "character_alive_status": "A character is dead in one scene but alive in another",
        "timeline_consistency": "The timeline or day of the week does not line up",
        "character_trait_conflict": "A character's job or role contradicts an earlier scene",
        "object_ownership": "An important object changes hands with no explanation",
        "object_destroyed": "An object is destroyed but appears again later",
        "object_lost": "An object is lost or left behind but turns up again",
        "medical_laterality": "An injury switches sides of the body between scenes",
        "medical_recovery": "A serious injury or condition vanishes with no recovery",
        "relationship_conflict": "Two characters' relationship contradicts an earlier scene",
        "relationship_role_inversion": "A family role is reversed between two characters",
        "semantic_location": "A place is described differently in two scenes",
    }
    return labels.get(
        contradiction_type,
        contradiction_type.replace("_", " ").title(),
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        report = analyze_from_path(sys.argv[1])
    else:
        from legacy.test_contradiction_screenplay import CONTRADICTION_SCREENPLAY

        report = analyze_screenplay(CONTRADICTION_SCREENPLAY)
    pretty_print_results(report)
