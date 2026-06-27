"""Feature tests for the object-continuity (possessions) contradiction checks.

These are unit-level regression tests for Phase 1. They are complementary to
the corpus-graded precision/recall harness that grades the whole engine; here
each rule ships with a positive case (must flag) and a negative case (must not
flag, covering the legitimate off-screen-explanation paths).
"""

from plot_contradiction import (
    STATUS_CONFIRMED,
    STATUS_POSSIBLE,
    Contradiction,
    ContradictionEngine,
)
from scene_dependency import SceneDependencyEngine

_dependency_engine = SceneDependencyEngine()
_contradiction_engine = ContradictionEngine()


def _analyze(script: str) -> list[Contradiction]:
    """Parse a Fountain script and run full contradiction analysis."""
    scenes = _dependency_engine.parse_fountain_text(script)
    return _contradiction_engine.run_analysis(scenes)


def _of_type(
    contradictions: list[Contradiction], contradiction_type: str
) -> list[Contradiction]:
    """Filter contradictions to a single type."""
    return [c for c in contradictions if c.contradiction_type == contradiction_type]


DESTROYED_THEN_REAPPEARS = """INT. OFFICE - NIGHT

MARCUS burns the ledger in the trash can.

INT. SAFEHOUSE - LATER

ELENA has the ledger.
"""

DESTROYED_NO_REAPPEARANCE = """INT. OFFICE - NIGHT

MARCUS burns the ledger in the trash can.

INT. STREET - DAY

ELENA walks home alone.
"""

LOST_THEN_REAPPEARS = """INT. DOCK - NIGHT

ELENA loses the silver key in the water.

INT. CAR - LATER

ELENA has the silver key.
"""

LOST_THEN_REACQUIRED = """INT. DOCK - NIGHT

ELENA loses the silver key in the water.

INT. DOCK - LATER

ELENA retrieves the silver key from the mud.

INT. CAR - NIGHT

ELENA has the silver key.
"""

FIGURATIVE_NON_PROPS = """INT. ROOM - NIGHT

ELENA loses her patience with him.

The blast shatters the silence.

INT. ROOM - LATER

ELENA has a plan.
"""

GUEST_BOOK_OWNERSHIP_CONFLICT = """INT. REHEARSAL DINNER - NIGHT

DAVE reveals the MAGNETIC GUEST BOOK to the wedding party.

INT. HALLWAY - DAY

Guests mingle. No one touches the guest book.

INT. RECEPTION - NIGHT

The best man Pete chases Tom's guest book as it sticks to a rolling cart.
"""

OWNERSHIP_NO_FALSE_POSITIVE = """INT. BLEACHERS - DAY

Sofia between her parents on the bleachers. Elena keeps the SILVER BAND in her pocket.
"""

BAND_OWNERSHIP_CONFLICT = """INT. COURTHOUSE - DAY

RICHARD holds a SILVER WEDDING BAND on a chain.

INT. APARTMENT - NIGHT

Elena stares at unpaid bills. The band stays in a drawer.

INT. KITCHEN - NIGHT

Sofia between her parents on the bleachers. Elena keeps the SILVER BAND in her pocket.
"""


def test_destroyed_object_reappears_is_confirmed() -> None:
    """A destroyed object handled later is a confirmed continuity error."""
    found = _of_type(_analyze(DESTROYED_THEN_REAPPEARS), "object_destroyed")
    assert len(found) == 1
    assert found[0].status == STATUS_CONFIRMED


def test_destroyed_object_not_reappearing_is_clean() -> None:
    """A destroyed object that is never seen again must not flag."""
    assert _of_type(_analyze(DESTROYED_NO_REAPPEARANCE), "object_destroyed") == []


def test_lost_object_reappears_is_possible() -> None:
    """An object lost then held again by its loser is a possible issue."""
    found = _of_type(_analyze(LOST_THEN_REAPPEARS), "object_lost")
    assert len(found) == 1
    assert found[0].status == STATUS_POSSIBLE


def test_lost_object_reacquired_between_is_clean() -> None:
    """On-screen recovery between scenes explains the reappearance."""
    assert _of_type(_analyze(LOST_THEN_REACQUIRED), "object_lost") == []


def test_figurative_phrases_do_not_flag() -> None:
    """Figurative loss/destruction ('loses patience', 'shatters the silence') is ignored."""
    contradictions = _analyze(FIGURATIVE_NON_PROPS)
    assert _of_type(contradictions, "object_lost") == []
    assert _of_type(contradictions, "object_destroyed") == []


def test_guest_book_ownership_conflict_is_confirmed() -> None:
    """Lowercase possessive 'Tom's guest book' maps to the same prop as ALL-CAPS."""
    found = _of_type(_analyze(GUEST_BOOK_OWNERSHIP_CONFLICT), "object_ownership")
    assert len(found) == 1
    assert found[0].status == STATUS_CONFIRMED


def test_ownership_no_false_positive_on_relation_phrase() -> None:
    """'Sofia between her parents' must not swallow Elena as a junk owner."""
    found = _of_type(_analyze(OWNERSHIP_NO_FALSE_POSITIVE), "object_ownership")
    assert len(found) == 0


def test_silver_band_ownership_conflict_is_confirmed() -> None:
    """Richard holds the band; Elena keeps it later with no handoff."""
    found = _of_type(_analyze(BAND_OWNERSHIP_CONFLICT), "object_ownership")
    assert len(found) == 1
    assert found[0].status == STATUS_CONFIRMED
