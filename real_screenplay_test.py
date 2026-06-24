"""Realistic thriller screenplay for end-to-end ScriptLens testing."""

from scriptlens_analyser import analyze_screenplay, pretty_print_results

# ---------------------------------------------------------------------------
# Planted contradictions (for manual verification):
#   1. character_alive_status — scene ~5: DETECTIVE VANCE is dead;
#      scene ~18: DETECTIVE VANCE appears alive again.
#   2. object_ownership — scene ~9: ELENA picks up the blue ledger;
#      scene ~16: MARCUS has the blue ledger (no handoff).
# Note: the script still contains "Today is Monday" / "Yesterday was
# Wednesday", but timeline_consistency detection is disabled by design, so it
# is no longer a planted/expected contradiction.
# ---------------------------------------------------------------------------

REAL_SCREENPLAY = """
FADE IN:

INT. FEDERAL ARCHIVES - DAY

MARCUS spreads blueprints across a table. A RED BRIEFCASE sits locked nearby.

MARCUS
The vault sits behind three inches of steel.

INT. DETECTIVE BUREAU - DAY

DETECTIVE ROSS pins surveillance stills to the board. DETECTIVE VANCE studies the timeline.

DETECTIVE VANCE
The crew met twice this week. We stay on MARCUS.

INT. HARBOR WAREHOUSE - NIGHT

Gunfire echoes. Smoke fills the dock.

DETECTIVE VANCE is dead after the shootout.

INT. SAFE APARTMENT - DAY

ELENA pours coffee. MARCUS checks the RED BRIEFCASE latches.

ELENA
Jordan still thinks we are only scouting.

MARCUS
He drives when we move. Nothing else.

INT. BANK VAULT ANTEROOM - NIGHT

MARCUS tests a SILVER KEY against the inner door. The RED BRIEFCASE waits on a dolly.

INT. ROOFTOP GARDEN - NIGHT

City lights below. Subplot: ELENA and MARCUS argue in whispers.

ELENA
You promised my sister would never hear about this.

MARCUS
She won't. Not from me.

INT. POLICE WAR ROOM - DAY

DETECTIVE ROSS addresses the squad. Maps cover the wall.

DETECTIVE ROSS
Today is Monday. We hit the harbor unit at dawn.

INT. HARBOR CAFE - DAY

THEO, the informant, slides a napkin across the table. MARCUS reads the address.

THEO
Vance's team is watching the docks again.

INT. SERVICE TUNNEL - NIGHT

ELENA picks up the blue ledger from a cracked tile.

She photographs two pages before the lights flicker.

INT. POLICE EVIDENCE ROOM - DAY

DETECTIVE ROSS catalogs items from the harbor raid. A photo of the RED BRIEFCASE dominates the board.

INT. PARKING GARAGE - NIGHT

JORDAN revs the engine. MARCUS loads tools into the trunk.

JORDAN
Tell me we are not walking into a trap.

MARCUS
We move tonight or we lose the window.

INT. MARCUS WORKSHOP - DAY

Files on vault sensors. The SILVER KEY hangs on a peg.

CAPTAIN REED
Internal affairs wants your logs by five.

INT. COURTHOUSE PLAZA - DAY

Reporters crowd the steps. Lawyers hurry inside with folders.

INT. ELENA'S APARTMENT - NIGHT

Rain on the window. DETECTIVE ROSS sits across from a cold cup of tea.

DETECTIVE ROSS
Yesterday was Wednesday. I still cannot square the harbor report.

INT. UNDERGROUND VAULT - NIGHT

MARCUS and ELENA breach the inner door. Alarms strobe red.

ELENA
Sixty seconds until the grid resets.

INT. GETAWAY VAN - NIGHT

Tires screech on wet asphalt.

MARCUS has the blue ledger and counts cash bands.

MARCUS
Ross will connect the tunnel to the workshop.

INT. CITY NEWSROOM - DAY

Subplot: a producer pitches a segment on the harbor shootout. THEO watches from the edit bay.

INT. RIVERFRONT STREET - DAY

DETECTIVE VANCE steps from the patrol car, very much alive.

DETECTIVE VANCE
Reports of my death were a ruse to flush the crew.

INT. TRAUMA WARD - DAY

JORDAN lies bandaged. ELENA signs the visitor log.

INT. INTERROGATION ROOM - DAY

DETECTIVE ROSS sets the RED BRIEFCASE photo in front of MARCUS.

DETECTIVE ROSS
Start with the ledger. Then the key.

MARCUS
Ask Vance why he played dead.

INT. ABANDONED FACTORY - NIGHT

The crew splits stacks from the RED BRIEFCASE. JORDAN counts in silence.

INT. AIRPORT ROAD - NIGHT

ELENA boards a shuttle with one bag. MARCUS watches from the fence line.

FADE OUT.
"""

PLANTED_CONTRADICTION_TYPES: tuple[str, ...] = (
    "character_alive_status",
    "object_ownership",
)


def verify_results(results: dict) -> list[str]:
    """Return a list of verification failure messages (empty if all pass)."""
    failures: list[str] = []
    summary = results["script_summary"]
    graph = results["dependencies"]["graph_summary"]
    contradictions = results["contradictions"]
    health = results["health_score"]

    scene_count = summary["total_scenes"]
    if scene_count < 20:
        failures.append(f"Expected at least 20 scenes, parsed {scene_count}.")

    edge_count = graph.get("total_edges", 0)
    if edge_count < 1:
        failures.append(f"Expected dependency edges, found {edge_count}.")

    detected_types = {item["contradiction_type"] for item in contradictions["items"]}
    matched_planted = sum(
        1 for planted in PLANTED_CONTRADICTION_TYPES if planted in detected_types
    )
    if matched_planted < 2:
        failures.append(
            "Expected at least 2 of 3 planted contradiction types detected; "
            f"got {matched_planted} ({sorted(detected_types)})."
        )

    if health < 40 or health > 85:
        failures.append(
            f"Health score {health} outside target range 40-85."
        )

    return failures


def main() -> None:
    """Run ScriptLens on the real screenplay and print verification plus report."""
    results = analyze_screenplay(REAL_SCREENPLAY)
    failures = verify_results(results)

    print()
    print("=" * 72)
    print("REAL SCREENPLAY TEST - VERIFICATION")
    print("=" * 72)
    print(f"  Scenes parsed:        {results['script_summary']['total_scenes']}")
    print(f"  Dependency edges:     {results['dependencies']['graph_summary']['total_edges']}")
    print(f"  Contradictions found: {results['contradictions']['total_found']}")
    print(f"  Health score:         {results['health_score']}")
    if failures:
        print()
        print("  FAILURES:")
        for message in failures:
            print(f"    - {message}")
    else:
        print()
        print("  All checks passed.")

    pretty_print_results(results)

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
