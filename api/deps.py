"""Shared FastAPI dependencies for structure routes."""

from __future__ import annotations

from fastapi import HTTPException, Request

from api.sessions import AnalysisSession, SessionStore


def get_session_store(request: Request) -> SessionStore:
    """Return the shared session store from application state.

    Args:
        request: Current FastAPI request.

    Returns:
        Application-wide ``SessionStore`` instance.
    """
    return request.app.state.session_store


def require_session(request: Request, script_id: str) -> AnalysisSession:
    """Load a script session or raise HTTP 404.

    Args:
        request: Current FastAPI request.
        script_id: Session identifier from upload.

    Returns:
        The active analysis session.

    Raises:
        HTTPException: When the session is missing or expired.
    """
    session = get_session_store(request).get(script_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Script session not found or expired.")
    return session
