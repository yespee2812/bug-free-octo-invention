"""Run ScriptLens analysis on every screenplay in a corpus folder."""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scene_dependency import SceneDependencyEngine
from scriptlens_analyser import analyze_from_path, pretty_print_results

SUPPORTED_SUFFIXES: frozenset[str] = frozenset(
    {".fountain", ".fadein", ".txt", ".md", ".screenplay", ".pdf"}
)


def _capture_customer_report(results: dict[str, Any]) -> str:
    """Return the screenwriter-facing report text (same as CLI output)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        pretty_print_results(results)
    return buffer.getvalue()


def _load_ground_truth(path: Path) -> dict[str, Any] | None:
    """Load a ground-truth YAML file if it exists."""
    if not path.is_file():
        return None
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required for ground-truth comparison. "
            "Install with: pip install pyyaml"
        ) from exc
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else None


def _contradiction_key(item: dict[str, Any]) -> tuple[str, int, int]:
    """Build a comparable key from a contradiction result item."""
    scenes = item.get("scenes_involved", [0, 0])
    return (
        str(item.get("contradiction_type", "")),
        int(scenes[0]) if scenes else 0,
        int(scenes[1]) if len(scenes) > 1 else 0,
    )


def _yaml_contradiction_key(entry: dict[str, Any]) -> tuple[str, int, int]:
    """Build a comparable key from a ground-truth YAML entry."""
    return (
        str(entry.get("type", "")),
        int(entry.get("scene_number_a", entry.get("scene_a", 0))),
        int(entry.get("scene_number_b", entry.get("scene_b", 0))),
    )


def _evaluate_ground_truth(
    stem: str,
    results: dict[str, Any],
    ground_truth: dict[str, Any],
    screenplay_text: str,
) -> str:
    """Compare engine output to manual ground truth and return a text report."""
    lines: list[str] = [
        f"GROUND TRUTH EVALUATION: {stem}",
        "=" * 72,
        "",
    ]

    expected = list(ground_truth.get("expected_contradictions", []) or [])
    planted = list(ground_truth.get("planted_contradictions", []) or [])
    all_expected = expected + planted

    detected = results.get("contradictions", {}).get("items", [])
    detected_keys = {_contradiction_key(item) for item in detected}
    expected_keys = {_yaml_contradiction_key(entry) for entry in all_expected}

    matched = expected_keys & detected_keys
    missed = expected_keys - detected_keys
    extra = detected_keys - expected_keys

    lines.append("CONTRADICTIONS")
    lines.append(f"  Expected (manual + planted): {len(expected_keys)}")
    lines.append(f"  Detected by engine:          {len(detected_keys)}")
    lines.append(f"  Matched:                     {len(matched)}")
    lines.append(f"  Missed (false negatives):    {len(missed)}")
    lines.append(f"  Extra (false positives):     {len(extra)}")
    lines.append("")

    if missed:
        lines.append("  Missed:")
        for key in sorted(missed):
            lines.append(f"    - {key[0]}: scene {key[1]} vs scene {key[2]}")
        lines.append("")

    if extra:
        lines.append("  Extra (engine-only):")
        for key in sorted(extra):
            lines.append(f"    - {key[0]}: scene {key[1]} vs scene {key[2]}")
        lines.append("")

    delete_checks = ground_truth.get("expected_simulate_delete", []) or []
    if delete_checks:
        engine = SceneDependencyEngine()
        scenes = engine.parse_fountain_text(screenplay_text)
        engine.build_graph(scenes)
        lines.append("SIMULATE DELETE")
        for check in delete_checks:
            scene_id = str(check.get("scene_id", ""))
            expect = {str(item) for item in (check.get("expect_impacted") or [])}
            impact = engine.get_delete_impact(scene_id)
            got = {str(record["scene_id"]) for record in impact}
            missing = expect - got
            unexpected = got - expect
            status = "PASS" if not missing else "PARTIAL/FAIL"
            lines.append(f"  [{status}] delete {scene_id}")
            lines.append(f"    expected impacted: {sorted(expect)}")
            lines.append(f"    engine impacted:   {sorted(got)}")
            if missing:
                lines.append(f"    missing: {sorted(missing)}")
            if unexpected and not expect:
                lines.append(f"    (engine found extras: {len(unexpected)} scenes)")
        lines.append("")

    notes = ground_truth.get("notes")
    if notes:
        lines.append(f"Notes: {notes}")
        lines.append("")

    return "\n".join(lines)


def _discover_scripts(input_dir: Path) -> list[Path]:
    """Return supported screenplay files in input_dir sorted by name."""
    files = [
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    return sorted(files, key=lambda item: item.name.lower())


def run_batch(
    input_dir: Path,
    output_dir: Path,
    ground_truth_dir: Path | None,
    compare_ground_truth: bool,
) -> None:
    """Analyse all scripts in input_dir and write customer reports to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    scripts = _discover_scripts(input_dir)

    if not scripts:
        print(f"No scripts found in {input_dir}")
        print(f"Supported suffixes: {', '.join(sorted(SUPPORTED_SUFFIXES))}")
        return

    manifest_rows: list[dict[str, str | int]] = []

    for script_path in scripts:
        stem = script_path.stem
        print(f"Analysing: {script_path.name} ...")

        results = analyze_from_path(script_path)
        report_text = _capture_customer_report(results)

        header = (
            f"ScriptLens analysis\n"
            f"Input: {script_path.name}\n"
            f"Format: {results.get('input', {}).get('format', 'unknown')}\n"
            f"{'=' * 72}\n"
        )
        report_path = output_dir / f"{stem}_report.txt"
        report_path.write_text(header + report_text, encoding="utf-8")

        json_path = output_dir / f"{stem}.json"
        json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

        summary = results["script_summary"]
        graph = results["dependencies"]["graph_summary"]
        contra = results["contradictions"]
        manifest_rows.append(
            {
                "filename": script_path.name,
                "scenes": summary["total_scenes"],
                "edges": graph.get("total_edges", 0),
                "orphans": graph.get("orphan_count", 0),
                "contradictions": contra["total_found"],
                "tier1": contra["by_tier"]["tier1"],
                "tier2": contra["by_tier"]["tier2"],
                "health_score": results["health_score"],
                "report_file": report_path.name,
            }
        )

        if compare_ground_truth and ground_truth_dir is not None:
            truth_path = ground_truth_dir / f"{stem}.yaml"
            truth = _load_ground_truth(truth_path)
            if truth is not None:
                from scriptlens_analyser import load_screenplay_text

                text, _ = load_screenplay_text(script_path)
                eval_text = _evaluate_ground_truth(stem, results, truth, text)
                eval_path = output_dir / f"{stem}_evaluation.txt"
                eval_path.write_text(eval_text, encoding="utf-8")
                print(f"  -> evaluation: {eval_path.name}")

        print(f"  -> report: {report_path.name}")

    manifest_path = output_dir / "manifest.csv"
    if manifest_rows:
        with manifest_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0].keys()))
            writer.writeheader()
            writer.writerows(manifest_rows)
        print(f"\nWrote manifest: {manifest_path}")


def main() -> None:
    """CLI entry point for corpus batch analysis."""
    parser = argparse.ArgumentParser(
        description="Run ScriptLens on all screenplays in a folder and save customer reports."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=_REPO_ROOT / "tests" / "corpus" / "input",
        help="Folder containing .fountain / .txt / .pdf scripts.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_REPO_ROOT / "tests" / "corpus" / "reports",
        help="Folder for *_report.txt, *.json, manifest.csv.",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        default=_REPO_ROOT / "tests" / "corpus" / "ground_truth",
        help="Folder with <stem>.yaml ground truth files.",
    )
    parser.add_argument(
        "--compare-ground-truth",
        action="store_true",
        help="Write <stem>_evaluation.txt when matching YAML exists.",
    )
    args = parser.parse_args()

    run_batch(
        args.input_dir.resolve(),
        args.output_dir.resolve(),
        args.ground_truth_dir.resolve(),
        args.compare_ground_truth,
    )


if __name__ == "__main__":
    main()
