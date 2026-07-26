"""Run ScriptLens on the clean produced-script benchmark (no ground truth).

Analyses every screenplay in ``tests/corpus/benchmark/clean_produced/`` (or a
custom ``--input-dir``) and writes customer reports to
``tests/corpus/benchmark/reports/``. Does not compare to planted ground truth.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from legacy.plot_contradiction import INPUT_PROFILE_PDF_BENCHMARK
from scripts.run_corpus_batch import run_batch

_DEFAULT_INPUT = _REPO_ROOT / "tests" / "corpus" / "benchmark" / "clean_produced"
_DEFAULT_OUTPUT = _REPO_ROOT / "tests" / "corpus" / "benchmark" / "reports"


def _parse_args() -> argparse.Namespace:
    """Parse command-line options for the clean benchmark batch."""
    parser = argparse.ArgumentParser(
        description=(
            "Analyse clean produced scripts for false-positive benchmarking "
            "(no ground-truth comparison)."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=_DEFAULT_INPUT,
        help="Folder containing benchmark screenplays (.fountain, .pdf, etc.).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help="Folder for generated *_report.txt and *.json files.",
    )
    return parser.parse_args()


def main() -> None:
    """Run batch analysis on the clean produced-script benchmark."""
    args = _parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not input_dir.is_dir():
        print(f"Input folder not found: {input_dir}")
        print("Create it or pass --input-dir to your script folder.")
        sys.exit(1)

    print(f"Clean benchmark input:  {input_dir}")
    print(f"Clean benchmark output: {output_dir}")
    print("(No ground-truth comparison — measuring false positives only.)\n")

    run_batch(
        input_dir,
        output_dir,
        ground_truth_dir=None,
        compare_ground_truth=False,
        input_profile=INPUT_PROFILE_PDF_BENCHMARK,
        pdf_conversion="refined",
    )


if __name__ == "__main__":
    main()
