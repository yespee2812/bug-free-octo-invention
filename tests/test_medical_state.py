"""Feature tests for the injuries & medical-state contradiction checks (Phase 2).

Each rule ships with a positive case (must flag) and the matching negative
case that covers a legitimate off-screen explanation (recovery action or a
time jump), since injuries are routinely treated or healed between scenes.
"""

from plot_contradiction import (
    STATUS_POSSIBLE,
    Contradiction,
    ContradictionEngine,
    Fact,
    _build_medical_value,
    _classify_medical_value,
)
from scene_dependency import SceneDependencyEngine

_dependency_engine = SceneDependencyEngine()
_contradiction_engine = ContradictionEngine()


def _analyze(script: str) -> list[Contradiction]:
    """Parse a Fountain script and run full contradiction analysis."""
    scenes = _dependency_engine.parse_fountain_text(script)
    return _contradiction_engine.run_analysis(scenes)


def _facts(script: str) -> list[Fact]:
    """Parse a Fountain script and return medical_state facts."""
    scenes = _dependency_engine.parse_fountain_text(script)
    store = _contradiction_engine.extract_facts(scenes)
    return store.get_facts_by_type("medical_state")


def _of_type(
    contradictions: list[Contradiction], contradiction_type: str
) -> list[Contradiction]:
    """Filter contradictions to a single type."""
    return [c for c in contradictions if c.contradiction_type == contradiction_type]


def test_classify_and_build_value_round_trip() -> None:
    """Value building and classification agree on kind/part/side."""
    assert _build_medical_value({"condition": "shot", "side": "left", "part": "arm"}) == (
        "shot left arm"
    )
    assert _build_medical_value({"condition": "breaks", "part": "leg"}) == "broken leg"
    assert _build_medical_value({"condition": "shot", "part": "dark"}) == ""
    assert _classify_medical_value("unconscious") == ("incapacitated", None, None)
    assert _classify_medical_value("shot left arm") == ("injured", "arm", "left")
    assert _classify_medical_value("unharmed") == ("healthy", None, None)


LATERALITY_CONFLICT = """INT. ALLEY - NIGHT

MARCUS is shot in the left arm.

INT. CLINIC - CONTINUOUS

MARCUS clutches his wound as the bullet is dug out of the right arm.
"""

LATERALITY_CONFLICT_DIRECT = """INT. ALLEY - NIGHT

MARCUS is wounded in the left shoulder.

INT. CAR - NIGHT

MARCUS is wounded in the right shoulder.
"""

BODY_PART_CONFLICT = """INT. TRENCH - NIGHT

KOWALSKI hit, shoulder. Hale hauls him up.

INT. AID STATION - NIGHT

Medics bind Kowalski's leg.
"""

RECOVERY_CONFLICT = """INT. WAREHOUSE - NIGHT

ELENA is unconscious on the floor.

INT. STREET - NIGHT

ELENA is fine.
"""

RECOVERY_EXPLAINED = """INT. WAREHOUSE - NIGHT

ELENA is unconscious on the floor.

INT. HOSPITAL - DAY

A medic treated her through the night.

INT. STREET - WEEKS LATER

ELENA is fine.
"""

FIGURATIVE_MEDICAL = """INT. OFFICE - DAY

MARCUS is dying to leave the meeting.

ELENA has blind faith in the plan.

RAY is paralyzed with fear.

DANA is blind to the truth.

NOAH is deaf to reason.
"""


def test_laterality_conflict_is_flagged_possible() -> None:
    """The same injury switching body sides is a possible continuity issue."""
    found = _of_type(_analyze(LATERALITY_CONFLICT_DIRECT), "medical_laterality")
    assert len(found) == 1
    assert found[0].status == STATUS_POSSIBLE


def test_body_part_conflict_is_flagged_possible() -> None:
    """An adjacent-scene injury that jumps body parts is a possible issue."""
    found = _of_type(_analyze(BODY_PART_CONFLICT), "medical_state")
    assert len(found) == 1
    assert found[0].status == STATUS_POSSIBLE


def test_recovery_conflict_is_flagged_possible() -> None:
    """Incapacitation then 'fine' with no recovery is a possible issue."""
    found = _of_type(_analyze(RECOVERY_CONFLICT), "medical_recovery")
    assert len(found) == 1
    assert found[0].status == STATUS_POSSIBLE


def test_recovery_with_treatment_and_time_gap_is_clean() -> None:
    """Treatment plus a time jump explains a later healthy state."""
    assert _of_type(_analyze(RECOVERY_EXPLAINED), "medical_recovery") == []


def test_figurative_medical_phrases_create_no_facts() -> None:
    """'dying to leave' and 'blind faith' must not become medical facts."""
    assert _facts(FIGURATIVE_MEDICAL) == []
