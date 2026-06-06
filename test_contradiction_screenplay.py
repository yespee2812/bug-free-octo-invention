"""Fountain screenplay with deliberate Tier 1 and Tier 2 plot contradictions."""

CONTRADICTION_SCREENPLAY = """
FADE IN:

INT. CITY HOSPITAL - DAY

MARCUS is a surgeon at the city hospital. He scrubs in for morning rounds.

INT. WAREHOUSE DISTRICT - NIGHT

Gunfire echoes.

AGENT COLE is dead after the ambush.

INT. POLICE BRIEFING ROOM - DAY

DETECTIVE ROSS pins photos to the board.

DETECTIVE ROSS
Today is Monday. We move at dawn.

INT. SAFE HOUSE - DAY

ELENA picks up the silver key.

INT. WAREHOUSE - DAY

The warehouse was abandoned for decades, dusty and silent.

INT. APARTMENT - NIGHT

Rain on the glass. A calendar sits on the desk.

DETECTIVE ROSS
Yesterday was Wednesday. I still cannot explain it.

INT. ABANDONED MILL - NIGHT

MARCUS has the silver key.

INT. UNDERGROUND GARAGE - NIGHT

AGENT COLE steps from the shadows, very much alive.

AGENT COLE
Reports of my death were exaggerated.

He loads a fresh magazine.

INT. COURTHOUSE - DAY

Marcus, the city's best defence attorney, entered the court.

The gallery quiets. The judge waits.

INT. WAREHOUSE - DAY

The warehouse had been active for years, staff working around the clock.

INT. ROOFTOP - NIGHT

The skyline flickers. Wind rattles a loose antenna.

INT. STATION LOBBY - DAY

Officers pass paperwork. The shift change is uneventful.

FADE OUT.
"""

# Expected Tier 1 contradictions (type, establishing scene, contradicting scene).
EXPECTED_CONTRADICTIONS: list[tuple[str, str, str]] = [
    ("character_alive_status", "scene_002", "scene_008"),
    ("timeline_consistency", "scene_003", "scene_006"),
    ("character_trait_conflict", "scene_001", "scene_009"),
    ("object_ownership", "scene_004", "scene_007"),
]

# Expected Tier 2 contradictions (type, establishing scene, contradicting scene).
EXPECTED_TIER2_CONTRADICTIONS: list[tuple[str, str, str]] = [
    ("semantic_location", "scene_005", "scene_010"),
]

# Full ground truth for accuracy measurement (Tier 1 + Tier 2).
GROUND_TRUTH_CONTRADICTIONS: list[tuple[str, str, str]] = (
    EXPECTED_CONTRADICTIONS + EXPECTED_TIER2_CONTRADICTIONS
)

# Scenes that should not appear in any detected contradiction.
CLEAN_SCENES: list[str] = [
    "scene_011",
    "scene_012",
]
