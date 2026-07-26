"""Convert a planted-error screenplay, analyse it, and compare to ground truth.

Use this for one-off writer scripts or custom planted PDFs/Word docs (not the
Hollywood clean benchmark). Converts PDF → refined Fountain or Word → Fountain,
runs the engine with the ``standard`` profile (same as the planted CI corpus),
and writes reports.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from docx_to_fountain import convert_docx_to_fountain_file
from pdf_to_fountain import convert_pdf_to_fountain_file
from legacy.plot_contradiction import INPUT_PROFILE_STANDARD
from legacy.scriptlens_analyser import analyze_from_path, pretty_print_results

from scripts.run_corpus_batch import _capture_customer_report, _evaluate_ground_truth, _load_ground_truth

_DEFAULT_INPUT_DIR = _REPO_ROOT / "tests" / "corpus" / "input"
_DEFAULT_GT_DIR = _REPO_ROOT / "tests" / "corpus" / "ground_truth"
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "tests" / "corpus" / "reports"


def _parse_args() -> argparse.Namespace:
    """Parse command-line options for planted PDF evaluation."""
    parser = argparse.ArgumentParser(
        description=(
            "Convert a planted-error screenplay (PDF or Word) to Fountain, "
            "analyse with the standard engine profile, and optionally compare "
            "to ground truth."
        )
    )
    parser.add_argument(
        "script",
        type=Path,
        help="Path to the planted-error screenplay (.pdf or .docx).",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=None,
        help="Ground-truth YAML (default: tests/corpus/ground_truth/<stem>.yaml).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUTPUT_DIR,
        help="Folder for report JSON/txt (default: tests/corpus/reports/).",
    )
    parser.add_argument(
        "--fountain-out",
        type=Path,
        default=None,
        help="Where to save Fountain (default: beside input as <stem>_refined.fountain).",
    )
    return parser.parse_args()


def _convert_planted_script(
    script_path: Path,
    fountain_out: Path | None,
) -> tuple[Path, str]:
    """Convert a planted-error PDF or Word document to Fountain.

    Args:
        script_path: Source screenplay path.
        fountain_out: Optional Fountain output path.

    Returns:
        Tuple of (fountain path, source format label).
    """
    stem = script_path.stem
    fountain_path = fountain_out or script_path.with_name(f"{stem}_refined.fountain")
    suffix = script_path.suffix.lower()

    if suffix == ".pdf":
        written = convert_pdf_to_fountain_file(
            script_path,
            fountain_path,
            stage="refined",
        )
        return written, "pdf"
    if suffix == ".docx":
        written = convert_docx_to_fountain_file(script_path, fountain_path)
        return written, "docx"

    raise ValueError(
        f"Expected a .pdf or .docx file, got: {script_path.name}"
    )


def run_planted_pdf_eval(
    script_path: Path,
    *,
    ground_truth_path: Path | None = None,
    output_dir: Path = _DEFAULT_OUTPUT_DIR,
    fountain_out: Path | None = None,
) -> dict[str, Any]:
    """Convert, analyse, and optionally score one planted-error screenplay.

    Args:
        script_path: Source screenplay PDF or Word document.
        ground_truth_path: Optional YAML with planted/expected contradictions.
        output_dir: Destination for customer report and JSON.
        fountain_out: Optional Fountain output path.

    Returns:
        Analysis results dictionary from ``analyze_from_path``.
    """
    script_path = script_path.resolve()
    if not script_path.is_file():
        raise FileNotFoundError(f"Script not found: {script_path}")

    stem = script_path.stem
    fountain_path, source_format = _convert_planted_script(script_path, fountain_out)

    results = analyze_from_path(
        fountain_path,
        input_profile=INPUT_PROFILE_STANDARD,
        include_extracted_text=False,
    )
    results["input"]["source_script"] = str(script_path)
    results["input"]["source_format"] = source_format
    results["input"]["refined_fountain"] = str(fountain_path)

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    report_text = _capture_customer_report(results)
    header = (
        f"ScriptLens analysis\n"
        f"Input script: {script_path.name} ({source_format})\n"
        f"Fountain: {fountain_path.name}\n"
        f"Profile: {INPUT_PROFILE_STANDARD}\n"
        f"{'=' * 72}\n"
    )
    report_path = output_dir / f"{stem}_report.txt"
    report_path.write_text(header + report_text, encoding="utf-8")

    json_path = output_dir / f"{stem}.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    gt_path = ground_truth_path or (_DEFAULT_GT_DIR / f"{stem}.yaml")
    if gt_path.is_file():
        ground_truth = _load_ground_truth(gt_path)
        if ground_truth is not None:
            fountain_text = fountain_path.read_text(encoding="utf-8")
            eval_text = _evaluate_ground_truth(stem, results, ground_truth, fountain_text)
            eval_path = output_dir / f"{stem}_evaluation.txt"
            eval_path.write_text(eval_text, encoding="utf-8")
            print(f"Wrote evaluation: {eval_path}")

    print(f"Wrote refined Fountain: {fountain_path}")
    print(f"Wrote report:         {report_path}")
    print(f"Wrote JSON:           {json_path}")
    print()
    with contextlib.redirect_stdout(sys.stdout):
        pretty_print_results(results)

    return results


def main() -> None:
    """CLI entry point for planted screenplay evaluation."""
    args = _parse_args()
    run_planted_pdf_eval(
        args.script,
        ground_truth_path=args.ground_truth,
        output_dir=args.output_dir,
        fountain_out=args.fountain_out,
    )


if __name__ == "__main__":
    main()
