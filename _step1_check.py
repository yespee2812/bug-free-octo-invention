"""Temporary smoke check for lowercase props and cue-less titled characters."""

from scene_dependency import SceneDependencyEngine

SCRIPT = """
INT. SERVICE TUNNEL - NIGHT

ELENA picks up the blue ledger from a cracked tile.

ELENA
This changes everything.

INT. PRECINCT LOBBY - DAY

DETECTIVE MILLER watches the entrance. He never says a word.

INT. GETAWAY VAN - NIGHT

MARCUS has the blue ledger and counts cash bands.

INT. PRECINCT LOBBY - NIGHT

DETECTIVE MILLER files a report about the ledger.
"""


def main() -> None:
    """Print objects, characters, and edges for the step-1 smoke script."""
    engine = SceneDependencyEngine()
    scenes = engine.parse_fountain_text(SCRIPT)
    engine.build_graph(scenes)

    for scene in scenes:
        print(
            f"{scene.scene_id} chars={scene.characters} objects={scene.objects}"
        )

    print("\nEDGES:")
    for source, target, data in engine.graph.edges(data=True):
        print(f"  {source} -> {target} [{', '.join(data['edge_types'])}]")


if __name__ == "__main__":
    main()
