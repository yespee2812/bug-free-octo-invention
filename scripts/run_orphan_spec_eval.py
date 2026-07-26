"""Evaluate orphan detection against AR-OSD golden fixtures."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from orphan_scene_detector import attach_orphan_graph
from scene_dependency import SceneDependencyEngine

DEFAULT_MANIFEST = (
    _REPO_ROOT / "tests/corpus/ground_truth/orphan_spec/manifest.yaml"
)


def load_manifest(manifest_path: Path) -> list[dict[str, object]]:
    """Load orphan-spec golden entries from a YAML manifest.

    Args:
        manifest_path: Path to ``manifest.yaml``.

    Returns:
        List of script specification dictionaries.

    Raises:
        FileNotFoundError: When the manifest file is missing.
    """
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    scripts = payload.get("scripts", [])
    if not isinstance(scripts, list):
        raise ValueError(f"Invalid manifest format: {manifest_path}")
    return scripts


def evaluate_orphan_spec(manifest_path: Path) -> int:
    """Run orphan detection for every manifest entry and report mismatches.

    Args:
        manifest_path: Path to the orphan-spec manifest YAML file.

    Returns:
        Process exit code (0 when all entries pass).
    """
    failures = 0
    for entry in load_manifest(manifest_path):
        script_id = str(entry["id"])
        script_path = _REPO_ROOT / str(entry["path"])
        expected = sorted(str(scene_id) for scene_id in entry["orphans"])
        requires_semantic = bool(entry.get("requires_semantic"))

        if requires_semantic and os.environ.get("OSD_DISABLE_SEMANTIC", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            print(f"SKIP  {script_id}: requires semantic embeddings (OSD_DISABLE_SEMANTIC set)")
            continue

        text = script_path.read_text(encoding="utf-8")
        engine = SceneDependencyEngine()
        scenes = engine.parse_fountain_text(text)
        attach_orphan_graph(engine, scenes)
        actual = engine.get_orphan_scenes()

        if actual == expected:
            print(f"PASS  {script_id}: orphans={actual}")
            continue

        print(f"FAIL  {script_id}: expected={expected} actual={actual}")
        failures += 1

    if failures:
        print(f"\n{failures} orphan-spec fixture(s) failed.")
        return 1

    print("\nAll orphan-spec fixtures passed.")
    return 0


def main() -> None:
    """CLI entry point for orphan-spec evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate OSD orphan detection against golden fixtures.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to orphan_spec manifest.yaml",
    )
    args = parser.parse_args()
    raise SystemExit(evaluate_orphan_spec(args.manifest.resolve()))


if __name__ == "__main__":
    main()
