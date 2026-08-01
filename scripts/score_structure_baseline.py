"""Score the v3 structure corpus against ground-truth YAML checklists.

Evaluates orphans, simulate-cut impact, and simulate-edit edge floors for every
entry in ``tests/corpus/ground_truth/structure/manifest.yaml``. With ``--check``,
exits non-zero when metrics fall below the configured thresholds (CI gate).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scriptlens_structure import (
    analyze_structure,
    get_simulate_cut_impact,
    get_simulate_edit_impact,
)

DEFAULT_MANIFEST = (
    _REPO_ROOT / "tests" / "corpus" / "ground_truth" / "structure" / "manifest.yaml"
)
BASELINE_PATH = _REPO_ROOT / "tests" / "corpus" / "STRUCTURE_BASELINE_SCORE.md"


@dataclass
class CapabilityScore:
    """Precision/recall counters for one scored capability."""

    expected: int = 0
    matched: int = 0
    false_positives: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def recall(self) -> float:
        """Return matched / expected (1.0 when nothing was expected)."""
        if self.expected == 0:
            return 1.0
        return self.matched / self.expected

    @property
    def precision(self) -> float:
        """Return matched / (matched + false positives), or 1.0 when empty."""
        denom = self.matched + self.false_positives
        if denom == 0:
            return 1.0
        return self.matched / denom


@dataclass
class StructureBaseline:
    """Aggregate structure-corpus scores."""

    orphans: CapabilityScore = field(default_factory=CapabilityScore)
    simulate_cut: CapabilityScore = field(default_factory=CapabilityScore)
    simulate_edit: CapabilityScore = field(default_factory=CapabilityScore)
    scripts_scored: int = 0


def load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    """Load structure-corpus entries from a YAML manifest.

    Args:
        manifest_path: Path to ``structure/manifest.yaml``.

    Returns:
        List of script specification dictionaries.

    Raises:
        FileNotFoundError: When the manifest file is missing.
        ValueError: When the manifest shape is invalid.
    """
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Structure manifest not found: {manifest_path}")
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    scripts = payload.get("scripts", []) if isinstance(payload, dict) else None
    if not isinstance(scripts, list):
        raise ValueError(f"Invalid structure manifest format: {manifest_path}")
    return scripts


def _load_ground_truth(path: Path) -> dict[str, Any]:
    """Load a ground-truth YAML file.

    Args:
        path: Path to a structure ground-truth YAML.

    Returns:
        Parsed ground-truth dictionary.

    Raises:
        FileNotFoundError: When the YAML file is missing.
        ValueError: When the file does not parse to a mapping.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Ground truth not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Ground truth must be a mapping: {path}")
    return data


def _score_orphans(
    script_id: str,
    ground_truth: dict[str, Any],
    detected_orphans: set[str],
    score: CapabilityScore,
) -> None:
    """Update orphan precision/recall from one script.

    Args:
        script_id: Manifest script id (for failure messages).
        ground_truth: Loaded YAML checklist.
        detected_orphans: Orphan scene ids from the engine.
        score: Aggregate orphan counters to update.
    """
    expected = {str(item) for item in (ground_truth.get("expected_orphans") or [])}
    score.expected += len(expected)
    matched = expected & detected_orphans
    score.matched += len(matched)
    extras = detected_orphans - expected
    score.false_positives += len(extras)
    missing = expected - detected_orphans
    if missing:
        score.failures.append(
            f"{script_id}: orphan misses {sorted(missing)} (got {sorted(detected_orphans)})"
        )
    if extras:
        score.failures.append(
            f"{script_id}: orphan extras {sorted(extras)} (expected {sorted(expected)})"
        )


def _score_simulate_cut(
    script_id: str,
    ground_truth: dict[str, Any],
    engine: Any,
    score: CapabilityScore,
) -> None:
    """Update simulate-cut recall from labeled delete checks.

    Args:
        script_id: Manifest script id.
        ground_truth: Loaded YAML checklist.
        engine: Built ``SceneDependencyEngine`` for the script.
        score: Aggregate cut counters to update.
    """
    checks = list(ground_truth.get("expected_simulate_delete") or [])
    for check in checks:
        scene_id = str(check.get("scene_id", ""))
        expect = {str(item) for item in (check.get("expect_impacted") or [])}
        score.expected += 1
        impact = get_simulate_cut_impact(engine, scene_id, engine._scene_lookup)
        got = {str(row["scene_id"]) for row in impact.get("impacted_scenes", [])}
        risk = str(impact.get("risk_level", ""))
        risk_ok = True
        if "expect_risk_in" in check and check["expect_risk_in"]:
            allowed = {str(item) for item in check["expect_risk_in"]}
            risk_ok = risk in allowed
        elif check.get("expect_risk"):
            risk_ok = risk == str(check["expect_risk"])

        missing = expect - got
        if not missing and risk_ok:
            score.matched += 1
        else:
            detail = []
            if missing:
                detail.append(f"missing={sorted(missing)}")
            if not risk_ok:
                detail.append(f"risk={risk!r}")
            score.failures.append(
                f"{script_id}: cut {scene_id} failed ({', '.join(detail)}; got {sorted(got)})"
            )


def _score_simulate_edit(
    script_id: str,
    ground_truth: dict[str, Any],
    engine: Any,
    screenplay_text: str,
    score: CapabilityScore,
) -> None:
    """Update simulate-edit floor checks from labeled edit rows.

    An edit may *remove* edges (referent was the only link) or only *change*
    them (e.g. object weight drops while character continuity remains). Either
    floor may be asserted; when both are omitted the default is at least one
    removed **or** changed edge.

    Args:
        script_id: Manifest script id.
        ground_truth: Loaded YAML checklist.
        engine: Built ``SceneDependencyEngine`` for the script.
        screenplay_text: Canonical Fountain text.
        score: Aggregate edit counters to update.
    """
    checks = list(ground_truth.get("expected_simulate_edit") or [])
    for check in checks:
        scene_id = str(check.get("scene_id", ""))
        modified = str(check.get("modified_text", ""))
        has_removed_floor = "expect_edges_removed_min" in check
        has_changed_floor = "expect_edges_changed_min" in check
        min_removed = int(check.get("expect_edges_removed_min", 0))
        min_changed = int(check.get("expect_edges_changed_min", 0))
        score.expected += 1
        try:
            impact = get_simulate_edit_impact(
                engine,
                screenplay_text,
                scene_id,
                modified,
            )
        except ValueError as exc:
            score.failures.append(f"{script_id}: edit {scene_id} error: {exc}")
            continue

        edge_diff = impact.get("edge_diff", {})
        removed = len(edge_diff.get("removed", []))
        changed = len(edge_diff.get("changed", []))
        risk = str(impact.get("risk_level", ""))
        risk_ok = True
        if "expect_risk_in" in check and check["expect_risk_in"]:
            allowed = {str(item) for item in check["expect_risk_in"]}
            risk_ok = risk in allowed

        if has_removed_floor or has_changed_floor:
            floors_ok = removed >= min_removed and changed >= min_changed
        else:
            floors_ok = (removed + changed) >= 1

        if floors_ok and risk_ok:
            score.matched += 1
        else:
            score.failures.append(
                f"{script_id}: edit {scene_id} removed={removed} changed={changed} "
                f"(need removed>={min_removed}, changed>={min_changed}), risk={risk!r}"
            )


def evaluate_structure_corpus(manifest_path: Path) -> StructureBaseline:
    """Run every structure-corpus entry and aggregate capability scores.

    Args:
        manifest_path: Path to the structure manifest YAML.

    Returns:
        Aggregated baseline scores across orphans, cut, and edit.
    """
    baseline = StructureBaseline()
    for entry in load_manifest(manifest_path):
        script_id = str(entry["id"])
        script_path = _REPO_ROOT / str(entry["script"])
        gt_path = _REPO_ROOT / str(entry["ground_truth"])
        ground_truth = _load_ground_truth(gt_path)
        screenplay_text = script_path.read_text(encoding="utf-8")
        results = analyze_structure(screenplay_text)
        engine = results.pop("engine")
        detected = {
            str(record["scene_id"]) for record in results["structure"]["orphans"]
        }

        _score_orphans(script_id, ground_truth, detected, baseline.orphans)
        _score_simulate_cut(script_id, ground_truth, engine, baseline.simulate_cut)
        _score_simulate_edit(
            script_id,
            ground_truth,
            engine,
            screenplay_text,
            baseline.simulate_edit,
        )
        baseline.scripts_scored += 1
    return baseline


def _write_baseline_markdown(baseline: StructureBaseline, path: Path) -> None:
    """Write a human-readable structure baseline summary.

    Args:
        baseline: Aggregated scores.
        path: Destination markdown path.
    """
    lines = [
        "# Structure corpus baseline",
        "",
        f"Scripts scored: **{baseline.scripts_scored}**",
        "",
        "| Capability | Expected | Matched | FP | Recall | Precision |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| Orphans | {baseline.orphans.expected} | {baseline.orphans.matched} | "
            f"{baseline.orphans.false_positives} | {baseline.orphans.recall:.3f} | "
            f"{baseline.orphans.precision:.3f} |"
        ),
        (
            f"| Simulate cut | {baseline.simulate_cut.expected} | "
            f"{baseline.simulate_cut.matched} | {baseline.simulate_cut.false_positives} | "
            f"{baseline.simulate_cut.recall:.3f} | {baseline.simulate_cut.precision:.3f} |"
        ),
        (
            f"| Simulate edit | {baseline.simulate_edit.expected} | "
            f"{baseline.simulate_edit.matched} | {baseline.simulate_edit.false_positives} | "
            f"{baseline.simulate_edit.recall:.3f} | {baseline.simulate_edit.precision:.3f} |"
        ),
        "",
    ]
    failures = (
        baseline.orphans.failures
        + baseline.simulate_cut.failures
        + baseline.simulate_edit.failures
    )
    if failures:
        lines.append("## Failures")
        lines.append("")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    """Parse CLI options for structure baseline scoring."""
    parser = argparse.ArgumentParser(
        description="Score the v3 structure corpus (orphans, cut, edit).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to structure/manifest.yaml",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when metrics fall below threshold flags.",
    )
    parser.add_argument(
        "--min-orphan-recall",
        type=float,
        default=1.0,
        help="Minimum orphan recall when --check is set (default: 1.0).",
    )
    parser.add_argument(
        "--min-orphan-precision",
        type=float,
        default=0.9,
        help="Minimum orphan precision when --check is set (default: 0.9).",
    )
    parser.add_argument(
        "--min-cut-recall",
        type=float,
        default=1.0,
        help="Minimum simulate-cut recall when --check is set (default: 1.0).",
    )
    parser.add_argument(
        "--min-edit-recall",
        type=float,
        default=1.0,
        help="Minimum simulate-edit recall when --check is set (default: 1.0).",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point for structure corpus scoring."""
    args = _parse_args()
    manifest_path = args.manifest.resolve()
    baseline = evaluate_structure_corpus(manifest_path)
    _write_baseline_markdown(baseline, BASELINE_PATH)

    print(f"Scripts scored: {baseline.scripts_scored}")
    print(
        f"Orphans   recall={baseline.orphans.recall:.3f} "
        f"precision={baseline.orphans.precision:.3f} "
        f"(matched {baseline.orphans.matched}/{baseline.orphans.expected}, "
        f"fp={baseline.orphans.false_positives})"
    )
    print(
        f"Cut       recall={baseline.simulate_cut.recall:.3f} "
        f"(matched {baseline.simulate_cut.matched}/{baseline.simulate_cut.expected})"
    )
    print(
        f"Edit      recall={baseline.simulate_edit.recall:.3f} "
        f"(matched {baseline.simulate_edit.matched}/{baseline.simulate_edit.expected})"
    )
    print(f"Wrote {BASELINE_PATH.relative_to(_REPO_ROOT)}")

    failures = (
        baseline.orphans.failures
        + baseline.simulate_cut.failures
        + baseline.simulate_edit.failures
    )
    for item in failures:
        print(f"FAIL  {item}")

    if not args.check:
        raise SystemExit(1 if failures else 0)

    ok = (
        baseline.orphans.recall >= args.min_orphan_recall
        and baseline.orphans.precision >= args.min_orphan_precision
        and baseline.simulate_cut.recall >= args.min_cut_recall
        and baseline.simulate_edit.recall >= args.min_edit_recall
    )
    if not ok:
        print("Structure baseline thresholds not met.")
        raise SystemExit(1)
    print("Structure baseline thresholds OK.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
