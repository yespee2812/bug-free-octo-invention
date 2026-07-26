"""Compare a writer error-injection log to ScriptLens analysis output."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from legacy.plot_contradiction import INPUT_PROFILE_STANDARD
from legacy.scriptlens_analyser import analyze_from_path
from legacy.writer_log_eval import compare_writer_log_to_results, format_comparison_report


def _load_yaml(path: Path) -> dict:
    """Load a YAML file and return a dict.

    Args:
        path: Path to a ``.yaml`` file.

    Returns:
        Parsed YAML mapping.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImportError: If PyYAML is not installed.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Log file not found: {path}")
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required. Install with: pip install pyyaml"
        ) from exc
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return data


def _parse_args() -> argparse.Namespace:
    """Parse command-line options for writer-log comparison."""
    parser = argparse.ArgumentParser(
        description=(
            "Run ScriptLens on a writer script and compare results to their "
            "error-injection log (answer sheet)."
        )
    )
    parser.add_argument(
        "script",
        type=Path,
        help="Screenplay file (.fountain, .pdf, etc.).",
    )
    parser.add_argument(
        "log",
        type=Path,
        help="Writer ERROR_LOG.yaml answer sheet.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Save comparison report to this .txt path.",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        default=None,
        help="Also save full ScriptLens JSON results to this path.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point: analyse script and compare to writer log."""
    args = _parse_args()
    script_path = args.script.resolve()
    log_path = args.log.resolve()

    log_data = _load_yaml(log_path)
    results = analyze_from_path(
        script_path,
        input_profile=INPUT_PROFILE_STANDARD,
    )
    comparison = compare_writer_log_to_results(log_data, results)
    report = format_comparison_report(script_path.name, log_data, comparison)

    print(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"\nWrote comparison report: {args.output.resolve()}")

    if args.json_report is not None:
        import json

        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Wrote engine JSON: {args.json_report.resolve()}")


if __name__ == "__main__":
    main()
