"""Health check route for the ScriptLens structure API."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return API liveness for deploy and monitoring checks.

    Returns:
        Static health payload with ``ok: true``.
    """
    return HealthResponse()
