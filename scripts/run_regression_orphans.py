"""Run orphan detection on scripts in ``scripts/regression testing``."""

from __future__ import annotations

from pathlib import Path

from scriptlens_structure import analyze_structure

FOLDER = Path(__file__).resolve().parent / "regression testing"
SUPPORTED = {".fountain", ".txt", ".fadein", ".md"}


def main() -> None:
    """Analyse every supported screenplay in the regression folder."""
    if not FOLDER.is_dir():
        raise SystemExit(f"Folder not found: {FOLDER}")

    files = sorted(
        (
            path
            for path in FOLDER.iterdir()
            if path.is_file()
            and (
                path.suffix.lower() in SUPPORTED
                or path.name.lower().endswith(".fountain.txt")
            )
        ),
        key=lambda path: path.name.lower(),
    )
    if not files:
        raise SystemExit(f"No Fountain/text scripts in {FOLDER}")

    summary_rows: list[tuple[str, int, int, list[str]]] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        results = analyze_structure(text)
        engine = results["engine"]
        orphans = results["structure"]["orphans"]
        scene_lookup = {scene.scene_id: scene for scene in engine.scenes}
        scene_count = int(results["script_summary"]["total_scenes"])
        mode = str(results["script_summary"]["structure_mode"])

        print("=" * 72)
        print(f"SCRIPT: {path.name}")
        print(f"scenes: {scene_count}  mode: {mode}  orphans: {len(orphans)}")
        if not orphans:
            print("  (none)")
        for record in orphans:
            scene_id = str(record["scene_id"])
            scene = scene_lookup.get(scene_id)
            heading = str(record.get("heading") or (scene.heading if scene else ""))
            orphan_type = str(record.get("orphan_type", ""))
            scene_number = record.get("scene_number", "?")
            print(f"  - {scene_id}  #{scene_number}  [{orphan_type}]  {heading}")
            reasons = record.get("reasons") or []
            if reasons:
                print(f"      reasons: {'; '.join(str(item) for item in reasons)}")

        summary_rows.append(
            (
                path.name,
                scene_count,
                len(orphans),
                [str(record["scene_id"]) for record in orphans],
            )
        )

    print()
    print("SUMMARY")
    print(f"{'script':<28} {'scenes':>6} {'orphans':>7}  orphan_ids")
    for name, scene_count, orphan_count, orphan_ids in summary_rows:
        print(f"{name:<28} {scene_count:>6} {orphan_count:>7}  {orphan_ids}")


if __name__ == "__main__":
    main()
