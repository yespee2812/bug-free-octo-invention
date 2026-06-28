"""Aggregate a corpus-wide baseline score for planted-error detection.

Reads the per-script engine output (``tests/corpus/reports/<stem>.json``) and the
planted ground truth (from :mod:`build_planted_ground_truth`), then computes
corpus-level recall / precision / F1 with order-insensitive scene matching.

Outputs ``tests/corpus/BASELINE_SCORE.md`` and prints a summary.

With ``--check``, exits non-zero when recall or false-positive counts regress
below configured thresholds (for CI).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.build_planted_ground_truth import ScriptErrors, build_dataset

REPORTS_DIR: Path = _REPO_ROOT / "tests" / "corpus" / "reports"
BASELINE_PATH: Path = _REPO_ROOT / "tests" / "corpus" / "BASELINE_SCORE.md"


def _detected_keys(stem: str) -> set[tuple[str, frozenset[int]]]:
    """Return order-insensitive (type, {scene_a, scene_b}) keys for a script."""
    json_path = REPORTS_DIR / f"{stem}.json"
    if not json_path.is_file():
        return set()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    items = data.get("contradictions", {}).get("items", [])
    keys: set[tuple[str, frozenset[int]]] = set()
    for item in items:
        scenes = item.get("scenes_involved", []) or []
        scene_ints = [int(scene) for scene in scenes[:2]]
        keys.add((str(item.get("contradiction_type", "")), frozenset(scene_ints)))
    return keys


def _planted_keys(script: ScriptErrors) -> set[tuple[str, frozenset[int]]]:
    """Return order-insensitive planted keys for a script."""
    return {
        (error.type, frozenset({error.establish_scene, error.contradict_scene}))
        for error in script.errors
    }


def _f1(precision: float, recall: float) -> float:
    """Return the harmonic mean of precision and recall (0 when both 0)."""
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _parse_args() -> argparse.Namespace:
    """Parse command-line options for baseline scoring."""
    parser = argparse.ArgumentParser(description="Score corpus planted-error detection.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 when metrics fall below threshold flags.",
    )
    parser.add_argument(
        "--min-recall",
        type=float,
        default=0.80,
        help="Minimum required recall when --check is set (default: 0.80).",
    )
    parser.add_argument(
        "--max-false-positives",
        type=int,
        default=4,
        help="Maximum allowed false positives when --check is set (default: 4).",
    )
    return parser.parse_args()


def main() -> None:
    """Compute and write the corpus baseline score."""
    args = _parse_args()
    dataset = build_dataset()

    total_planted = 0
    total_detected = 0
    true_positives = 0
    engine_subset_total = 0
    engine_subset_hits = 0
    missed_by_type: dict[str, int] = {}
    hit_by_type: dict[str, int] = {}
    per_script: list[tuple[str, int, int, int]] = []

    for script in dataset:
        planted = _planted_keys(script)
        detected = _detected_keys(script.script_id)
        matched = planted & detected

        total_planted += len(script.errors)
        total_detected += len(detected)
        true_positives += len(matched)

        for error in script.errors:
            key = (error.type, frozenset({error.establish_scene, error.contradict_scene}))
            bucket = hit_by_type if key in detected else missed_by_type
            bucket[error.type] = bucket.get(error.type, 0) + 1
            if error.engine_detectable:
                engine_subset_total += 1
                if key in detected:
                    engine_subset_hits += 1

        per_script.append(
            (script.script_id, len(script.errors), len(detected), len(matched))
        )

    recall = true_positives / total_planted if total_planted else 0.0
    precision = true_positives / total_detected if total_detected else 0.0
    false_positives = total_detected - true_positives
    subset_recall = (
        engine_subset_hits / engine_subset_total if engine_subset_total else 0.0
    )

    all_types = sorted(set(missed_by_type) | set(hit_by_type))

    lines: list[str] = [
        "# Baseline Score — Core Engine vs Planted Errors",
        "",
        f"Corpus: {len(dataset)} scripts, {total_planted} planted errors.",
        "Matching is order-insensitive on (contradiction_type, {scene_a, scene_b}).",
        "",
        "## Headline",
        "",
        f"- Planted errors (ground truth):        **{total_planted}**",
        f"- Detected by engine (any):             **{total_detected}**",
        f"- True positives (correct catches):     **{true_positives}**",
        f"- False positives:                      **{false_positives}**",
        f"- **Recall (overall): {recall:.1%}** ({true_positives}/{total_planted})",
        f"- Precision: {precision:.1%}"
        + (" (no detections emitted)" if total_detected == 0 else ""),
        f"- F1: {_f1(precision, recall):.1%}",
        "",
        "## On the engine's own supported categories",
        "",
        "Subset = planted errors whose type the engine claims to support "
        "(object_ownership, character_trait_conflict, medical_state).",
        "",
        f"- Supported-subset planted: **{engine_subset_total}**",
        f"- Supported-subset caught:  **{engine_subset_hits}**",
        f"- **Subset recall: {subset_recall:.1%}**",
        "",
        "## Recall by planted error type",
        "",
        "| Type | Planted | Caught | Recall |",
        "|------|---------|--------|--------|",
    ]
    for error_type in all_types:
        caught = hit_by_type.get(error_type, 0)
        missed = missed_by_type.get(error_type, 0)
        planted = caught + missed
        rate = caught / planted if planted else 0.0
        lines.append(f"| {error_type} | {planted} | {caught} | {rate:.0%} |")

    lines.extend(["", "## Per-script", "", "| Script | Planted | Detected | Matched |",
                  "|--------|---------|----------|---------|"])
    for script_id, planted, detected, matched in per_script:
        lines.append(f"| {script_id} | {planted} | {detected} | {matched} |")

    BASELINE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Planted: {total_planted}  Detected: {total_detected}  TP: {true_positives}")
    print(f"Recall: {recall:.1%}  Precision: {precision:.1%}  F1: {_f1(precision, recall):.1%}")
    print(f"Supported-subset recall: {subset_recall:.1%} "
          f"({engine_subset_hits}/{engine_subset_total})")
    print(f"Wrote: {BASELINE_PATH}")

    if args.check:
        failures: list[str] = []
        if recall < args.min_recall:
            failures.append(
                f"recall {recall:.1%} is below minimum {args.min_recall:.1%}"
            )
        if false_positives > args.max_false_positives:
            failures.append(
                f"false positives {false_positives} exceed maximum "
                f"{args.max_false_positives}"
            )
        if failures:
            for message in failures:
                print(f"BASELINE CHECK FAILED: {message}", file=sys.stderr)
            sys.exit(1)
        print(
            "Baseline check passed "
            f"(recall >= {args.min_recall:.1%}, "
            f"FP <= {args.max_false_positives})."
        )


if __name__ == "__main__":
    main()
