"""Generate ground-truth YAML files and a human-readable log for planted errors.

This module is the single source of truth for the errors intentionally injected
into the genre starter scripts under ``tests/corpus/input/``. Running it writes:

* one ``<script>.yaml`` per script into ``tests/corpus/ground_truth/`` so the
  corpus batch can score detection with ``--compare-ground-truth``;
* a consolidated ``tests/corpus/PLANTED_ERROR_LOG.md`` for human review.

Each 5-scene script carries 2 planted errors and each 10-scene script carries 3.
Scene numbers are 1-indexed by the order of INT./EXT. headings in the file,
matching the "scene N" numbering used in the customer report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

CORPUS_ROOT: Path = Path(__file__).resolve().parent.parent / "tests" / "corpus"
INPUT_DIR: Path = CORPUS_ROOT / "input"
GROUND_TRUTH_DIR: Path = CORPUS_ROOT / "ground_truth"
LOG_PATH: Path = CORPUS_ROOT / "PLANTED_ERROR_LOG.md"


@dataclass(frozen=True)
class PlantedError:
    """A single intentional contradiction planted into a script."""

    type: str
    establish_scene: int
    contradict_scene: int
    characters: tuple[str, ...]
    objects: tuple[str, ...]
    engine_detectable: bool
    note: str


@dataclass(frozen=True)
class ScriptErrors:
    """All planted errors for one screenplay file."""

    script_id: str
    filename: str
    errors: list[PlantedError] = field(default_factory=list)


def _e(
    type: str,
    a: int,
    b: int,
    characters: tuple[str, ...],
    objects: tuple[str, ...],
    engine: bool,
    note: str,
) -> PlantedError:
    """Build a :class:`PlantedError` with positional brevity."""
    return PlantedError(type, a, b, characters, objects, engine, note)


def build_dataset() -> list[ScriptErrors]:
    """Return the full catalogue of planted errors for all 40 scripts."""
    data: list[ScriptErrors] = [
        ScriptErrors(
            "action_5scene_errors",
            "action_5scene_errors.fountain",
            [
                _e("object_ownership", 2, 5, ("SANTOS", "VEGA"), ("RED FLARE CANISTER",), True,
                   "Flare clips to Vega's vest (sc2); Santos pulls his own flare (sc5)."),
                _e("numeric_count", 1, 5, (), ("HOSTAGES",), False,
                   "Hostage count reads 3 (sc1, sc3) vs 'All four' (sc5)."),
            ],
        ),
        ScriptErrors(
            "action_10scene_errors",
            "action_10scene_errors.fountain",
            [
                _e("numeric_count", 1, 10, (), ("HOSTAGES",), False,
                   "Three hostages circled (sc1) vs 'All four' (sc10)."),
                _e("object_ownership", 3, 9, ("VEGA", "PARK"), ("RED FLARE CANISTER",), True,
                   "Flare on Vega's vest (sc3); Park fires the flare (sc9)."),
                _e("name_consistency", 3, 7, ("OSEI",), (), False,
                   "Operative named Osei (sc3, sc4) vs 'Oshea' (sc7)."),
            ],
        ),
        ScriptErrors(
            "crime_5scene_errors",
            "crime_5scene_errors.fountain",
            [
                _e("numeric_count", 3, 5, ("EDDIE", "PELL"), (), False,
                   "'Three runs this month' (sc3) vs 'Four runs this month' (sc5)."),
                _e("character_age", 1, 4, ("EDDIE MORAN",), (), False,
                   "Eddie introduced as 50s (sc1) vs 'barely forty' (sc4)."),
            ],
        ),
        ScriptErrors(
            "crime_10scene_errors",
            "crime_10scene_errors.fountain",
            [
                _e("character_knowledge", 8, 4, ("PELL",), ("yellow slicker buyer",), False,
                   "Pell names the yellow-slicker buyer (sc4) before discovering them (sc8)."),
                _e("relationship_fact", 5, 7, ("EDDIE",), (), False,
                   "Eddie's daughter (sc5) vs Eddie's niece (sc7)."),
                _e("numeric_count", 4, 6, ("PELL",), (), False,
                   "'three identical runs' (sc4) vs 'Four runs in a month' (sc6)."),
            ],
        ),
        ScriptErrors(
            "romance_5scene_errors",
            "romance_5scene_errors.fountain",
            [
                _e("object_identity", 1, 5, ("JAMES",), ("SATCHEL",), False,
                   "Leather satchel (sc1) vs canvas satchel (sc5)."),
                _e("character_trait_conflict", 1, 4, ("CLAIRE HART",), (), True,
                   "Claire is a novelist (sc1) vs 'the poet' (sc4)."),
            ],
        ),
        ScriptErrors(
            "romance_10scene_errors",
            "romance_10scene_errors.fountain",
            [
                _e("object_identity", 2, 8, ("JAMES",), ("SATCHEL",), False,
                   "Leather satchel (sc2) vs canvas satchel (sc8)."),
                _e("object_identity", 5, 10, ("JAMES", "CLAIRE"), ("PHOTO",), False,
                   "Photo of the two of them (sc5) vs photo of her parents (sc10)."),
                _e("numeric_count", 7, 10, (), (), False,
                   "'Six years of silence' (sc7) vs 'eight years' (sc10)."),
            ],
        ),
        ScriptErrors(
            "scifi_5scene_errors",
            "scifi_5scene_errors.fountain",
            [
                _e("object_identity", 1, 3, ("KARA",), ("DATA CHIP",), False,
                   "Gold data chip (sc1) vs silver data chip (sc3)."),
                _e("character_knowledge", 5, 2, ("NOLAN",), ("signal",), False,
                   "Nolan says the signal is 'meant for me' (sc2) before the reveal (sc5)."),
            ],
        ),
        ScriptErrors(
            "scifi_10scene_errors",
            "scifi_10scene_errors.fountain",
            [
                _e("object_identity", 1, 3, ("KARA",), ("DATA CHIP",), False,
                   "Gold data chip (sc1) vs silver data chip (sc3)."),
                _e("date_year", 2, 6, ("HALE",), ("Meridian",), False,
                   "Meridian missing in 2014 (sc2) vs lost in 2009 (sc6)."),
                _e("numeric_count", 4, 7, (), (), False,
                   "'four-person team' (sc4) vs 'All six of us' (sc7)."),
            ],
        ),
        ScriptErrors(
            "horror_5scene_errors",
            "horror_5scene_errors.fountain",
            [
                _e("date_year", 2, 3, ("LEAH",), ("VHS tape",), False,
                   "Tape labeled CHRISTMAS '94 (sc2) vs '93 (sc3)."),
                _e("character_knowledge", 4, 5, ("LEAH",), ("trapdoor",), False,
                   "Trapdoor 'stepped over a thousand times' (sc4) vs 'never noticed' (sc5)."),
            ],
        ),
        ScriptErrors(
            "horror_10scene_errors",
            "horror_10scene_errors.fountain",
            [
                _e("numeric_count", 1, 9, ("LEAH",), (), False,
                   "'One week to empty it' (sc1) vs 'Three weeks in this house' (sc9)."),
                _e("date_year", 3, 5, ("LEAH",), ("VHS tape",), False,
                   "CHRISTMAS '94 (sc3) vs '93 (sc5)."),
                _e("character_age", 7, 10, ("LEAH",), (), False,
                   "'when I was twelve' (sc7) vs 'Not since I was eight' (sc10)."),
            ],
        ),
        ScriptErrors(
            "adventure_5scene_errors",
            "adventure_5scene_errors.fountain",
            [
                _e("date_year", 2, 5, ("M. OKAFOR",), ("expedition",), False,
                   "Tin box 'M. OKAFOR, 1987' (sc2) vs 'British expedition, 1985' (sc5)."),
                _e("object_identity", 1, 3, ("JUNE",), ("ENVELOPE",), False,
                   "Wax-sealed envelope (sc1) vs 'leather pouch' (sc3)."),
            ],
        ),
        ScriptErrors(
            "adventure_10scene_errors",
            "adventure_10scene_errors.fountain",
            [
                _e("numeric_count", 8, 10, ("JUNE",), (), False,
                   "'measured the peak wrong by sixty meters' (sc8) vs 'forty meters higher' (sc10)."),
                _e("date_year", 4, 8, ("M. OKAFOR",), ("expedition",), False,
                   "Tin box 1987 (sc4) vs '1985 British labels' (sc8)."),
                _e("name_consistency", 2, 9, ("TENZIN",), (), False,
                   "Guide Tenzin (sc2) vs 'Tensing' (sc9)."),
            ],
        ),
        ScriptErrors(
            "comedy_5scene_errors",
            "comedy_5scene_errors.fountain",
            [
                _e("object_ownership", 2, 4, ("DAVE", "TOM"), ("MAGNETIC GUEST BOOK",), True,
                   "Guest book in Dave's backpack (sc2) vs 'Tom's MAGNETIC GUEST BOOK' (sc4)."),
                _e("relationship_fact", 3, 4, ("DIANE", "DAVE"), (), False,
                   "Dave's future mother-in-law Diane (sc3) vs 'Dave's aunt Diane' (sc4)."),
            ],
        ),
        ScriptErrors(
            "comedy_10scene_errors",
            "comedy_10scene_errors.fountain",
            [
                _e("object_ownership", 3, 6, ("DAVE", "TOM"), ("MAGNETIC GUEST BOOK",), True,
                   "Dave reveals the guest book (sc3) vs 'Tom's guest book' (sc6)."),
                _e("relationship_fact", 4, 9, ("DIANE", "MAYA"), (), False,
                   "Diane is the mother-in-law (sc4) vs 'Maya's sister Diane' (sc9)."),
                _e("relationship_fact", 1, 6, ("PETE", "TOM"), (), False,
                   "Cousin Pete / best man Tom (sc1) vs 'best man Pete' (sc6)."),
            ],
        ),
        ScriptErrors(
            "coming_of_age_5scene_errors",
            "coming_of_age_5scene_errors.fountain",
            [
                _e("numeric_count", 3, 5, (), ("cast",), False,
                   "'cast of twelve' (sc3) vs 'all fifteen of them' (sc5)."),
                _e("character_fact", 2, 5, ("JORDAN",), (), False,
                   "Jordan bound for state school (sc2) vs 'Coast school for me' (sc5)."),
            ],
        ),
        ScriptErrors(
            "coming_of_age_10scene_errors",
            "coming_of_age_10scene_errors.fountain",
            [
                _e("character_fact", 3, 10, ("MAYA",), (), False,
                   "Maya's coast school confirmed (sc3) vs 'State school' (sc10)."),
                _e("numeric_count", 9, 9, ("PRINCIPAL", "JORDAN"), (), False,
                   "Principal 'You broke three rules' vs Jordan 'Five rules' (both sc9)."),
                _e("date_year", 1, 6, (), ("class banner",), False,
                   "Banner CLASS OF 2026 (sc1) vs CLASS OF 2025 (sc6)."),
            ],
        ),
        ScriptErrors(
            "drama_5scene_errors",
            "drama_5scene_errors.fountain",
            [
                _e("object_ownership", 1, 5, ("RICHARD", "ELENA"), ("SILVER WEDDING BAND",), True,
                   "Richard holds the band (sc1) vs 'stays in Elena's pocket' (sc5)."),
                _e("character_age", 2, 3, ("SOFIA",), (), False,
                   "Sofia, 12 (sc2) vs 'fastest ten-year-old' (sc3)."),
            ],
        ),
        ScriptErrors(
            "drama_10scene_errors",
            "drama_10scene_errors.fountain",
            [
                _e("object_ownership", 1, 10, ("RICHARD", "ELENA"), ("SILVER WEDDING BAND",), True,
                   "Richard holds the band (sc1) vs 'Elena keeps the SILVER BAND' (sc10)."),
                _e("character_age", 2, 3, ("SOFIA",), (), False,
                   "Sofia, 12 (sc2) vs 'For eleven' (sc3)."),
                _e("relationship_fact", 3, 8, ("ALMA", "RICHARD"), (), False,
                   "Coach Alma (sc3) vs 'Alma, his sister' (sc8)."),
            ],
        ),
        ScriptErrors(
            "family_5scene_errors",
            "family_5scene_errors.fountain",
            [
                _e("numeric_count", 1, 3, ("MARIA",), (), False,
                   "'Twenty people at six' (sc1) vs 'a table set for eighteen' (sc3)."),
                _e("numeric_count", 2, 4, ("RAUL",), (), False,
                   "Father 'absent twenty years' (sc2) vs 'Fifteen years' (sc4)."),
            ],
        ),
        ScriptErrors(
            "family_10scene_errors",
            "family_10scene_errors.fountain",
            [
                _e("numeric_count", 1, 9, ("RAUL",), (), False,
                   "'reunion twenty years in the making' (sc1) vs 'Twenty-five years of silence' (sc9)."),
                _e("numeric_count", 5, 10, ("MARIA",), (), False,
                   "'Twenty chairs' (sc5) vs 'a table set for eighteen' (sc10)."),
                _e("relationship_fact", 3, 8, ("DIANA", "ANTONIO"), (), False,
                   "Antonio's sister Diana (sc3) vs 'Antonio's cousin Diana' (sc8)."),
            ],
        ),
        ScriptErrors(
            "fantasy_5scene_errors",
            "fantasy_5scene_errors.fountain",
            [
                _e("object_identity", 1, 5, ("MIRA",), ("COMPASS",), False,
                   "Brass compass (sc1) vs 'iron compass' (sc5)."),
                _e("object_identity", 2, 4, ("STRANGER",), ("payment",), False,
                   "Stranger pays with a silver thimble (sc2) vs 'paid with a brass coin' (sc4)."),
            ],
        ),
        ScriptErrors(
            "fantasy_10scene_errors",
            "fantasy_10scene_errors.fountain",
            [
                _e("object_identity", 1, 5, ("MIRA",), ("COMPASS",), False,
                   "Brass compass (sc1) vs 'iron compass' (sc5)."),
                _e("character_age", 2, 6, ("ELI",), (), False,
                   "Eli, 10 (sc2) vs 'barely seven' (sc6)."),
                _e("object_identity", 3, 5, ("STRANGER",), ("payment",), False,
                   "Stranger offers a silver thimble (sc3) vs 'paid with a brass coin' (sc5)."),
            ],
        ),
        ScriptErrors(
            "heist_5scene_errors",
            "heist_5scene_errors.fountain",
            [
                _e("object_identity", 3, 5, ("MARCUS",), ("sketch",), False,
                   "Vermeer study (sc3) vs 'Rembrandt charcoal' (sc5)."),
                _e("character_knowledge", 5, 2, ("SLOANE",), (), False,
                   "Sloane says 'somebody already knows' (sc2) before the THEY KNOW text (sc5)."),
            ],
        ),
        ScriptErrors(
            "heist_10scene_errors",
            "heist_10scene_errors.fountain",
            [
                _e("object_identity", 6, 10, ("MARCUS",), ("sketch",), False,
                   "Vermeer study (sc6) vs 'a Rembrandt' (sc10)."),
                _e("character_knowledge", 9, 3, ("SLOANE",), (), False,
                   "Sloane 'they know we're coming' (sc3) before the THEY KNOW text (sc9)."),
                _e("numeric_count", 4, 6, ("PAK", "MARCUS"), (), False,
                   "'Twelve-second holes' (sc4) vs 'Twenty-second holes' (sc6)."),
            ],
        ),
        ScriptErrors(
            "historical_fiction_5scene_errors",
            "historical_fiction_5scene_errors.fountain",
            [
                _e("relationship_fact", 1, 4, ("LUC", "MARIE"), (), False,
                   "'Her brother Luc' (sc1) vs 'Luc, her cousin' (sc4)."),
                _e("date_year", 1, 4, (), (), False,
                   "Slug dated 1943 (sc1) vs 'the autumn of 1942' (sc4)."),
            ],
        ),
        ScriptErrors(
            "historical_fiction_10scene_errors",
            "historical_fiction_10scene_errors.fountain",
            [
                _e("date_year", 1, 5, (), (), False,
                   "Slug dated 1943 (sc1) vs 'this one of 1941' (sc5)."),
                _e("numeric_count", 5, 8, ("MARIE",), ("couriers",), False,
                   "'blesses three couriers' (sc5) vs 'Four of us left that church' (sc8)."),
                _e("relationship_fact", 1, 4, ("LUC", "MARIE"), (), False,
                   "'Her brother Luc' (sc1) vs 'Luc, her cousin' (sc4)."),
            ],
        ),
        ScriptErrors(
            "mystery_5scene_errors",
            "mystery_5scene_errors.fountain",
            [
                _e("character_age", 2, 5, ("TOMAS",), (), False,
                   "Tomas, 22 (sc2) vs 'A nineteen-year-old gardener' (sc5)."),
                _e("character_knowledge", 1, 3, ("MAYA",), ("GLASS KEY",), False,
                   "Key 'here at midnight' (sc1) vs 'gone since last week, not midnight' (sc3)."),
            ],
        ),
        ScriptErrors(
            "mystery_10scene_errors",
            "mystery_10scene_errors.fountain",
            [
                _e("character_age", 4, 10, ("TOMAS",), (), False,
                   "Tomas, 22 (sc4) vs 'a nineteen-year-old gardener' (sc10)."),
                _e("relationship_fact", 3, 9, ("CALEB",), (), False,
                   "Caleb introduced as the nephew (sc3) vs 'I'm the only son' (sc9)."),
                _e("fact_consistency", 5, 10, ("TOMAS",), ("footprint",), False,
                   "Print 'smaller than Tomas's boot' (sc5) vs 'matched Tomas exactly' (sc10)."),
            ],
        ),
        ScriptErrors(
            "noir_5scene_errors",
            "noir_5scene_errors.fountain",
            [
                _e("numeric_count", 2, 3, (), ("hotel room",), False,
                   "Room 514 (sc2) vs room 415 (sc3)."),
                _e("object_identity", 2, 4, (), ("RED HAT",), False,
                   "Woman in a red hat (sc2) vs 'green hat' (sc4)."),
            ],
        ),
        ScriptErrors(
            "noir_10scene_errors",
            "noir_10scene_errors.fountain",
            [
                _e("numeric_count", 3, 5, (), ("hotel room",), False,
                   "Room 514 (sc3) vs room 415 (sc5)."),
                _e("object_identity", 3, 6, (), ("RED HAT",), False,
                   "Woman in a red hat (sc3) vs 'Green hat' (sc6)."),
                _e("character_knowledge", 10, 2, ("FRANK", "CLIENT"), (), False,
                   "Frank states the client is the partner (sc2) before the final reveal (sc10)."),
            ],
        ),
        ScriptErrors(
            "sports_5scene_errors",
            "sports_5scene_errors.fountain",
            [
                _e("numeric_count", 2, 4, ("NINA",), (), False,
                   "Nationals finish 'fourth' (sc2) vs 'Third by a fingernail' (sc4)."),
                _e("character_age", 1, 5, ("NINA",), (), False,
                   "Nina Vasquez, 22 (sc1) vs 'Nina, twenty' (sc5)."),
            ],
        ),
        ScriptErrors(
            "sports_10scene_errors",
            "sports_10scene_errors.fountain",
            [
                _e("numeric_count", 3, 8, ("NINA", "ALMA"), (), False,
                   "'Nina fourth by a hundredth' (sc3) vs 'Third isn't a sentence' (sc8)."),
                _e("numeric_count", 7, 10, ("NINA",), (), False,
                   "Split fails at 150 (sc7) vs 'Turn at 175' (sc10)."),
                _e("character_age", 2, 6, ("NINA",), (), False,
                   "Nina Vasquez, 22 (sc2) vs 'Twenty years old' (sc6)."),
            ],
        ),
        ScriptErrors(
            "supernatural_5scene_errors",
            "supernatural_5scene_errors.fountain",
            [
                _e("numeric_count", 1, 5, ("ELISE",), (), False,
                   "'Three families left' (sc1) vs 'Four families' (sc5)."),
                _e("location_continuity", 2, 5, ("ELISE",), ("haunted bedroom",), False,
                   "East bedroom (sc2, sc3) vs WEST BEDROOM (sc5)."),
            ],
        ),
        ScriptErrors(
            "supernatural_10scene_errors",
            "supernatural_10scene_errors.fountain",
            [
                _e("numeric_count", 2, 8, ("ELISE", "DAN"), (), False,
                   "'Three families' (sc2) vs 'Four families' (sc8)."),
                _e("location_continuity", 4, 7, ("ELISE",), ("haunted bedroom",), False,
                   "East bedroom (sc4) vs WEST BEDROOM (sc7)."),
                _e("character_trait_conflict", 2, 6, ("DAN",), (), True,
                   "Dan the skeptic, 'unconvinced' (sc2) vs 'I knew this place was alive' (sc6)."),
            ],
        ),
        ScriptErrors(
            "thriller_5scene_errors",
            "thriller_5scene_errors.fountain",
            [
                _e("object_identity", 1, 4, ("LENA",), ("DUFFEL",), False,
                   "Black duffel (sc1) vs 'gray duffel' (sc4)."),
                _e("numeric_count", 1, 3, ("LENA",), (), False,
                   "Watch reads 11:58 PM (sc1) vs 'not even eleven yet' (sc3)."),
            ],
        ),
        ScriptErrors(
            "thriller_10scene_errors",
            "thriller_10scene_errors.fountain",
            [
                _e("object_identity", 2, 6, ("LENA",), ("DUFFEL",), False,
                   "Black duffel (sc2) vs 'gray duffel' (sc6)."),
                _e("numeric_count", 1, 5, ("LENA",), (), False,
                   "'three exchange points' (sc1) vs 'Four exchange points' (sc5)."),
                _e("numeric_count", 7, 9, ("DMITRI", "LENA"), (), False,
                   "'Five of them, I counted five' (sc7) vs 'Three men exit the sedan' (sc9)."),
            ],
        ),
        ScriptErrors(
            "war_5scene_errors",
            "war_5scene_errors.fountain",
            [
                _e("numeric_count", 2, 5, ("HALE",), ("listening post",), False,
                   "Listening post '200 meters out' (sc2) vs 'Three hundred meters' (sc5)."),
                _e("character_age", 1, 3, ("TOM HALE",), (), False,
                   "Sergeant Tom Hale, 28 (sc1) vs 'thirty-one' (sc3)."),
            ],
        ),
        ScriptErrors(
            "war_10scene_errors",
            "war_10scene_errors.fountain",
            [
                _e("character_age", 1, 8, ("TOM HALE",), (), False,
                   "Sergeant Tom Hale, 28 (sc1) vs 'thirty-one' (sc8)."),
                _e("medical_state", 8, 9, ("KOWALSKI",), (), True,
                   "Kowalski hit in the shoulder (sc8) vs medics 'bind Kowalski's leg' (sc9)."),
                _e("numeric_count", 2, 10, ("HALE",), ("listening post",), False,
                   "Listening post '200 meters out' (sc2) vs 'Three hundred meters out' (sc10)."),
            ],
        ),
        ScriptErrors(
            "western_5scene_errors",
            "western_5scene_errors.fountain",
            [
                _e("location_continuity", 2, 3, ("DAWSON",), ("pasture",), False,
                   "Diverts flow to 'his south pasture' (sc2) vs 'My north pasture finally drinks' (sc3)."),
                _e("character_age", 2, 4, ("JESSE",), (), False,
                   "Foreman Jesse, 30s (sc2) vs 'barely twenty-five' (sc4)."),
            ],
        ),
        ScriptErrors(
            "western_10scene_errors",
            "western_10scene_errors.fountain",
            [
                _e("location_continuity", 3, 4, ("DAWSON",), ("pasture",), False,
                   "'his south pasture' (sc3) vs 'My north fields finally drink' (sc4)."),
                _e("character_knowledge", 8, 3, ("JESSE",), ("railroad plot",), False,
                   "Jesse names the railroad feud (sc3) before Dawson reveals it (sc8)."),
                _e("character_age", 4, 8, ("WILL DAWSON",), (), False,
                   "Will Dawson, 45 (sc4) vs 'Dawson, fifty now' (sc8)."),
            ],
        ),
    ]
    return data


def _yaml_list(values: tuple[str, ...]) -> str:
    """Render a tuple of strings as an inline YAML list."""
    if not values:
        return "[]"
    quoted = ", ".join(f'"{value}"' for value in values)
    return f"[{quoted}]"


def write_ground_truth(script: ScriptErrors) -> Path:
    """Write one ground-truth YAML file and return its path."""
    lines: list[str] = [
        f"script_id: {script.script_id}",
        f"filename: {script.filename}",
        "",
        "planted_contradictions:",
    ]
    for error in script.errors:
        lines.extend(
            [
                f"  - type: {error.type}",
                f"    scene_number_a: {error.establish_scene}",
                f"    scene_number_b: {error.contradict_scene}",
                f"    characters: {_yaml_list(error.characters)}",
                f"    objects: {_yaml_list(error.objects)}",
                f"    engine_detectable: {str(error.engine_detectable).lower()}",
                f'    note: "{error.note}"',
            ]
        )
    out_path = GROUND_TRUTH_DIR / f"{script.script_id}.yaml"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def write_log(dataset: list[ScriptErrors]) -> Path:
    """Write the consolidated human-readable markdown log and return its path."""
    total_errors = sum(len(script.errors) for script in dataset)
    engine_errors = sum(
        1 for script in dataset for error in script.errors if error.engine_detectable
    )
    lines: list[str] = [
        "# Planted Error Log — Genre Starter Scripts",
        "",
        "Errors injected into the genre starter scripts for engine testing.",
        "Scene numbers are 1-indexed by INT./EXT. heading order (matches the",
        '"scene N" numbering in the customer report).',
        "",
        f"- Scripts: **{len(dataset)}** (20 genres x 5-scene + 10-scene)",
        "- 5-scene scripts: 2 planted errors each; 10-scene scripts: 3 each",
        f"- Total planted errors: **{total_errors}**",
        f"- Currently engine-detectable (Tier 1/2): **{engine_errors}** "
        "(ownership / trait / medical-state types)",
        "",
        "Inputs live in `tests/corpus/input/`; ground truth in "
        "`tests/corpus/ground_truth/`.",
        "",
        "| Script | # | Type | Establish | Contradict | Characters | Objects | Engine? | Description |",
        "|--------|---|------|-----------|------------|------------|---------|---------|-------------|",
    ]
    for script in dataset:
        for index, error in enumerate(script.errors, start=1):
            characters = ", ".join(error.characters) or "—"
            objects = ", ".join(error.objects) or "—"
            engine = "yes" if error.engine_detectable else "no"
            lines.append(
                f"| {script.script_id} | {index} | {error.type} | "
                f"sc{error.establish_scene} | sc{error.contradict_scene} | "
                f"{characters} | {objects} | {engine} | {error.note} |"
            )
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return LOG_PATH


def main() -> None:
    """Generate all ground-truth YAML files and the consolidated log."""
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset()
    missing = [s.filename for s in dataset if not (INPUT_DIR / s.filename).exists()]
    if missing:
        raise FileNotFoundError(f"Missing input scripts: {missing}")
    for script in dataset:
        write_ground_truth(script)
    write_log(dataset)
    total = sum(len(s.errors) for s in dataset)
    print(f"Wrote {len(dataset)} ground-truth files and {total} planted errors.")
    print(f"Log: {LOG_PATH}")


if __name__ == "__main__":
    main()
