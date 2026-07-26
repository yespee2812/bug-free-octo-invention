"""CLI entry point for ScriptLens screenplay analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from legacy.scriptlens_analyser import analyze_from_path, pretty_print_results
from scriptlens_structure import (
    analyze_structure_from_path,
    get_simulate_cut_impact,
    pretty_print_structure_results,
)
from scene_dependency import SceneDependencyEngine


def _print_simulate_cut(results: dict[str, object], scene_id: str) -> None:
    """Print simulate-cut impact for a structure analysis session.

    Args:
        results: Structure analysis results with an attached engine.
        scene_id: Scene identifier to evaluate, e.g. ``scene_005``.

    Raises:
        SystemExit: When the engine or scene id is missing.
    """
    engine = results.get("engine")
    if not isinstance(engine, SceneDependencyEngine):
        print(
            "Simulate cut requires a built engine. Re-run with --structure-only "
            "and --simulate-cut together.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    impact = get_simulate_cut_impact(engine, scene_id, engine._scene_lookup)
    removed = impact["removed_scene"]
    if removed is None:
        print(f"Unknown scene id: {scene_id}", file=sys.stderr)
        raise SystemExit(1)

    print()
    print("=" * 72)
    print("SIMULATE CUT")
    print("=" * 72)
    print(
        f"Removing scene {removed['scene_number']}: {removed['heading']} "
        f"({removed['scene_id']})"
    )
    print(f"  {impact['summary']}")
    print(f"  Risk level: {impact['risk_level']}")
    impacted = impact["impacted_scenes"]
    if not impacted:
        print("  No downstream scenes depend on this scene.")
        return

    print(f"  Would affect {len(impacted)} later scene(s):")
    for record in impacted[:10]:
        path = " -> ".join(record["dependency_path"])
        reason = record.get("impact_reason") or record.get("explanation", "")
        print(
            f"    Scene {record['scene_number']}: {record['heading']} "
            f"(path: {path})"
        )
        if reason:
            print(f"      {reason}")
    if len(impacted) > 10:
        print(f"    ... and {len(impacted) - 10} more.")
    print()


def build_parser() -> argparse.ArgumentParser:
    """Build the ScriptLens CLI argument parser.

    Returns:
        Configured argument parser for ``run_scriptlens.py``.
    """
    parser = argparse.ArgumentParser(
        description="Analyse a screenplay with ScriptLens.",
    )
    parser.add_argument(
        "screenplay",
        type=Path,
        help="Path to .fountain, .pdf, or other supported screenplay file.",
    )
    parser.add_argument(
        "--structure-only",
        action="store_true",
        help="Structure-only mode: orphans and scene graph (no contradictions).",
    )
    parser.add_argument(
        "--simulate-cut",
        metavar="SCENE_ID",
        help="With --structure-only, preview delete impact for SCENE_ID.",
    )
    return parser


def main() -> None:
    """Analyse a screenplay file and print the selected report."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.screenplay.is_file():
        print(f"File not found: {args.screenplay}", file=sys.stderr)
        raise SystemExit(1)

    if args.structure_only:
        results = analyze_structure_from_path(
            args.screenplay,
            include_engine=bool(args.simulate_cut),
        )
        pretty_print_structure_results(results)
        if args.simulate_cut:
            _print_simulate_cut(results, args.simulate_cut)
        return

    if args.simulate_cut:
        print(
            "--simulate-cut requires --structure-only.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    results = analyze_from_path(args.screenplay)
    pretty_print_results(results)


if __name__ == "__main__":
    main()
