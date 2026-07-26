"""Draft export filename helpers."""

from __future__ import annotations

from pathlib import Path


def draft_export_filename(filename: str, draft_revision: int) -> str:
    """Build a download filename for the current working draft.

    Args:
        filename: Original uploaded filename.
        draft_revision: Number of draft mutations applied so far.

    Returns:
        Suggested ``.fountain`` download name.
    """
    stem = Path(filename).stem or "screenplay"
    if draft_revision > 0:
        return f"{stem}_draft_rev{draft_revision}.fountain"
    return f"{stem}_working.fountain"
