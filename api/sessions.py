"""In-memory screenplay analysis sessions for the structure API."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from scene_dependency import SceneDependencyEngine
from scriptlens_structure import structure_state_from_draft

MAX_DRAFT_HISTORY: int = 50


def _utc_now() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        Timezone-aware UTC ``datetime``.
    """
    return datetime.now(timezone.utc)


def make_script_id(original_text: str) -> str:
    """Derive a stable session id from the imported screenplay text.

    Args:
        original_text: Immutable Fountain text from the first upload.

    Returns:
        First 16 hex characters of the SHA-256 digest.
    """
    digest = hashlib.sha256(original_text.encode("utf-8")).hexdigest()
    return digest[:16]


@dataclass
class AnalysisSession:
    """Server-side state for one analysed screenplay."""

    script_id: str
    filename: str
    original_text: str
    draft_text: str
    draft_revision: int
    input_format: str
    structure_mode: str
    scenes: list[dict[str, Any]]
    orphan_count: int
    orphans: list[dict[str, Any]]
    graph_summary: dict[str, Any]
    high_risk_scenes: list[dict[str, Any]]
    engine: SceneDependencyEngine
    draft_history: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utc_now)
    upload_hash: str | None = None


def refresh_session_structure(
    session: AnalysisSession,
    *,
    increment_revision: bool = False,
) -> AnalysisSession:
    """Re-analyze ``draft_text`` and refresh cached structure fields.

    Args:
        session: Session whose draft should be re-parsed.
        increment_revision: When True, bump ``draft_revision`` after rebuild.

    Returns:
        The same session instance with refreshed engine and metadata.
    """
    state = structure_state_from_draft(session.draft_text)
    session.engine = state["engine"]
    session.structure_mode = state["structure_mode"]
    session.scenes = state["scenes"]
    session.orphan_count = state["orphan_count"]
    session.orphans = state["orphans"]
    session.graph_summary = state["graph_summary"]
    session.high_risk_scenes = state["high_risk_scenes"]
    if increment_revision:
        session.draft_revision += 1
    return session


def record_draft_snapshot(session: AnalysisSession) -> None:
    """Push the current draft text onto the undo stack before a mutation.

    Args:
        session: Session whose working copy will be changed.
    """
    session.draft_history.append(session.draft_text)
    overflow = len(session.draft_history) - MAX_DRAFT_HISTORY
    if overflow > 0:
        del session.draft_history[:overflow]


def can_undo_draft(session: AnalysisSession) -> bool:
    """Return True when the session has at least one undo snapshot."""
    return bool(session.draft_history)


def undo_draft(session: AnalysisSession) -> AnalysisSession:
    """Restore the most recent draft snapshot and rebuild structure.

    Args:
        session: Session to roll back.

    Returns:
        The same session instance with restored draft text and metadata.

    Raises:
        ValueError: When there is nothing to undo.
    """
    if not session.draft_history:
        raise ValueError("Nothing to undo.")

    session.draft_text = session.draft_history.pop()
    session.draft_revision = max(0, session.draft_revision - 1)
    refresh_session_structure(session, increment_revision=False)
    return session


class SessionStore:
    """TTL-backed in-memory store for analysis sessions."""

    def __init__(self, ttl_hours: int = 24) -> None:
        """Initialize an empty session store.

        Args:
            ttl_hours: Hours before an untouched session expires.
        """
        self._sessions: dict[str, AnalysisSession] = {}
        self._upload_index: dict[str, str] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def purge_expired(self) -> int:
        """Remove sessions older than the configured TTL.

        Returns:
            Number of sessions removed.
        """
        cutoff = _utc_now() - self._ttl
        expired_ids = [
            script_id
            for script_id, session in self._sessions.items()
            if session.created_at < cutoff
        ]
        for script_id in expired_ids:
            session = self._sessions.pop(script_id, None)
            if session is not None and session.upload_hash:
                self._upload_index.pop(session.upload_hash, None)
        return len(expired_ids)

    def put(self, session: AnalysisSession) -> AnalysisSession:
        """Store or replace a session by ``script_id``.

        Args:
            session: Completed analysis session.

        Returns:
            The stored session.
        """
        self.purge_expired()
        previous = self._sessions.get(session.script_id)
        if (
            previous is not None
            and previous.upload_hash
            and previous.upload_hash != session.upload_hash
        ):
            self._upload_index.pop(previous.upload_hash, None)
        self._sessions[session.script_id] = session
        if session.upload_hash:
            self._upload_index[session.upload_hash] = session.script_id
        return session

    def get(self, script_id: str) -> AnalysisSession | None:
        """Return a session when present and not expired.

        Args:
            script_id: Session identifier from upload.

        Returns:
            The session, or ``None`` when missing or expired.
        """
        self.purge_expired()
        session = self._sessions.get(script_id)
        if session is None:
            return None
        if session.created_at < _utc_now() - self._ttl:
            del self._sessions[script_id]
            if session.upload_hash:
                self._upload_index.pop(session.upload_hash, None)
            return None
        return session

    def get_by_upload_hash(self, upload_hash: str) -> AnalysisSession | None:
        """Return a live session for a previously analysed upload digest.

        Args:
            upload_hash: SHA-256 hex digest of the raw upload bytes.

        Returns:
            Matching session, or ``None`` when missing or expired.
        """
        script_id = self._upload_index.get(upload_hash)
        if script_id is None:
            return None
        session = self.get(script_id)
        if session is None:
            self._upload_index.pop(upload_hash, None)
            return None
        if session.upload_hash != upload_hash:
            self._upload_index.pop(upload_hash, None)
            return None
        return session
