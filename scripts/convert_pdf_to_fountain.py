"""CLI: convert screenplay PDFs to Fountain with automated noise reduction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pdf_to_fountain import ConversionStage, convert_pdf_to_fountain_file


def _parse_args() -> argparse.Namespace:
    """Parse command-line options for PDF-to-Fountain conversion."""
    parser = argparse.ArgumentParser(
        description=(
            "Convert screenplay PDFs to Fountain text with automated cleanup "
            "(reflow action, demote camera slugs)."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="+",
        help="One or more screenplay PDF files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (single input only). Default: stage-based suffix beside PDF.",
    )
    parser.add_argument(
        "--stage",
        choices=("raw", "clean", "refined"),
        default="clean",
        help=(
            "Conversion depth: raw extract only; clean (default) reflow + slug "
            "demotion; refined adds generic manual-pass rules."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Convert each input PDF to Fountain and print output paths."""
    args = _parse_args()
    inputs: list[Path] = [path.resolve() for path in args.input]
    stage: ConversionStage = args.stage

    if args.output is not None and len(inputs) != 1:
        raise SystemExit("--output requires exactly one input PDF.")

    for pdf_path in inputs:
        if not pdf_path.is_file():
            raise SystemExit(f"Input file not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise SystemExit(f"Expected a .pdf file: {pdf_path.name}")

        output_path = args.output if args.output is not None else None
        written = convert_pdf_to_fountain_file(
            pdf_path,
            output_path,
            stage=stage,
        )
        print(f"Wrote {stage} Fountain: {written}")


if __name__ == "__main__":
    main()
