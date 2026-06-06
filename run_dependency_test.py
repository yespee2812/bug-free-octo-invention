"""Run the scene dependency pipeline against the sample screenplay."""

from scene_dependency import SceneDependencyEngine
from test_screenplay import SAMPLE_SCREENPLAY


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_delete_impact(engine: SceneDependencyEngine, scene_id: str) -> None:
    """Print downstream impact for a deleted scene."""
    print_section(f"DELETE IMPACT: {scene_id}")
    impact = engine.get_delete_impact(scene_id)
    if not impact:
        print("No downstream scenes depend on this scene.")
        return

    impacted_ids = [record["scene_id"] for record in impact]
    print(f"Scenes affected ({len(impact)}): {', '.join(impacted_ids)}")
    print()
    for record in impact:
        path = " -> ".join(record["dependency_path"])
        print(
            f"  {record['scene_id']} (#{record['scene_number']}): "
            f"{record['heading']}"
        )
        print(f"    Path: {path}")
        print(f"    Total weight: {record['total_weight']}")


def main() -> None:
    """Parse the sample screenplay and print a dependency analysis report."""
    print_section("SCRIPTLENS SCENE DEPENDENCY TEST")
    print("Running pipeline: parse -> build_graph -> query")

    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(SAMPLE_SCREENPLAY)
    engine.build_graph(scenes)

    print_section("PARSE RESULTS")
    print(f"Scenes parsed: {len(scenes)}")
    for scene in scenes:
        print(f"  {scene.scene_id} (#{scene.scene_number}): {scene.heading}")
        print(f"    Characters: {', '.join(scene.characters) or '(none)'}")
        print(f"    Objects: {', '.join(scene.objects) or '(none)'}")
        print(f"    Locations: {', '.join(scene.locations) or '(none)'}")

    print_section("SCENE DEPENDENCIES (upstream)")
    for scene in scenes:
        dependencies = engine.get_scene_dependencies(scene.scene_id)
        print(f"\n{scene.scene_id} (#{scene.scene_number}): {scene.heading}")
        if not dependencies:
            print("  Depends on: (none)")
            continue
        upstream_ids = [record["scene_id"] for record in dependencies]
        print(f"  Depends on: {', '.join(upstream_ids)}")
        for record in dependencies:
            path = " -> ".join(record["dependency_path"])
            print(
                f"    <- {record['scene_id']} (#{record['scene_number']}): "
                f"{record['heading']} [weight: {record['total_weight']}, path: {path}]"
            )

    print_delete_impact(engine, "scene_005")
    print("  (Expected affected scenes: scene_011, scene_012)")

    print_delete_impact(engine, "scene_001")
    print("  (Expected: many downstream scenes - briefcase and Marcus ripple forward)")

    print_section("ORPHAN SCENES")
    orphans = engine.get_orphan_scenes()
    if orphans:
        print(f"Orphan count: {len(orphans)}")
        print("  (Expected orphans: scene_002, scene_004 - nothing depends on them)")
        for scene_id in orphans:
            scene = engine._scene_lookup[scene_id]
            print(
                f"  {scene_id} (#{scene.scene_number}): {scene.heading}"
            )
    else:
        print("No orphan scenes found.")

    print_section("GRAPH SUMMARY")
    summary = engine.export_graph_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print()
    print("Test run complete.")


if __name__ == "__main__":
    main()
