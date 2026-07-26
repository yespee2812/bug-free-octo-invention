"""Orphan and script detail routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from api.schemas import (
    OrphanGraphEdge,
    OrphanGraphNode,
    OrphanGraphResponse,
    OrphanGraphStats,
    OrphanListResponse,
    OrphanRecord,
    SceneDetailResponse,
    SceneSummary,
    ScriptDetailResponse,
)
from api.sessions import SessionStore
from orphan_graph_export import build_orphan_graph_view_payload

router = APIRouter(tags=["scripts"])


def _get_store(request: Request) -> SessionStore:
    """Return the shared session store from application state.

    Args:
        request: Current FastAPI request.

    Returns:
        Application-wide ``SessionStore`` instance.
    """
    return request.app.state.session_store


@router.get("/scripts/{script_id}", response_model=ScriptDetailResponse)
def get_script(script_id: str, request: Request) -> ScriptDetailResponse:
    """Return structure metadata for a stored script session.

    Args:
        script_id: Session identifier from upload.
        request: Current FastAPI request.

    Returns:
        Scene list, orphan count, and graph summary.

    Raises:
        HTTPException: When the session is missing or expired.
    """
    session = _get_store(request).get(script_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Script session not found or expired.")

    scenes = [SceneSummary(**scene) for scene in session.scenes]
    return ScriptDetailResponse(
        script_id=session.script_id,
        filename=session.filename,
        scene_count=len(session.scenes),
        orphan_count=session.orphan_count,
        structure_mode=session.structure_mode,  # type: ignore[arg-type]
        scenes=scenes,
        graph_summary=session.graph_summary,
    )


@router.get("/scripts/{script_id}/orphans", response_model=OrphanListResponse)
def get_orphans(script_id: str, request: Request) -> OrphanListResponse:
    """Return orphan scenes for a stored script session.

    Args:
        script_id: Session identifier from upload.
        request: Current FastAPI request.

    Returns:
        Orphan count and orphan scene summaries.

    Raises:
        HTTPException: When the session is missing or expired.
    """
    session = _get_store(request).get(script_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Script session not found or expired.")

    orphans = [OrphanRecord(**record) for record in session.orphans]
    return OrphanListResponse(
        script_id=session.script_id,
        orphan_count=session.orphan_count,
        orphans=orphans,
    )


@router.get(
    "/scripts/{script_id}/orphan-graph",
    response_model=OrphanGraphResponse,
)
def get_orphan_graph(script_id: str, request: Request) -> OrphanGraphResponse:
    """Return the OSD orphan graph for client-side visualization.

    Args:
        script_id: Session identifier from upload.
        request: Current FastAPI request.

    Returns:
        Scene nodes, weighted OSD edges, and summary stats.

    Raises:
        HTTPException: When the session is missing or expired.
    """
    session = _get_store(request).get(script_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Script session not found or expired.")

    payload = build_orphan_graph_view_payload(session.engine, session.orphans)
    return OrphanGraphResponse(
        script_id=session.script_id,
        nodes=[OrphanGraphNode(**node) for node in payload["nodes"]],
        edges=[OrphanGraphEdge(**edge) for edge in payload["edges"]],
        stats=OrphanGraphStats(**payload["stats"]),
    )


@router.get(
    "/scripts/{script_id}/scenes/{scene_id}",
    response_model=SceneDetailResponse,
)
def get_scene_detail(
    script_id: str,
    scene_id: str,
    request: Request,
) -> SceneDetailResponse:
    """Return the Fountain body for one scene in the script reader.

    Args:
        script_id: Session identifier from upload.
        scene_id: Scene identifier, e.g. ``scene_005``.
        request: Current FastAPI request.

    Returns:
        Scene heading and raw Fountain text for the reader.

    Raises:
        HTTPException: When the session or scene id is invalid.
    """
    session = _get_store(request).get(script_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Script session not found or expired.")

    scene = session.engine._scene_lookup.get(scene_id)
    if scene is None:
        raise HTTPException(status_code=422, detail=f"Unknown scene_id: {scene_id}")

    return SceneDetailResponse(
        script_id=session.script_id,
        scene_id=scene.scene_id,
        scene_number=scene.scene_number,
        heading=scene.heading,
        body=scene.raw_text,
    )
