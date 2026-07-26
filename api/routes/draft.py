"""Draft mutation routes — delete scenes and apply edits to the working copy."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from api.deps import get_session_store, require_session
from api.draft_export import draft_export_filename
from api.schemas import (
    DraftApplyEditRequest,
    DraftDeleteRequest,
    DraftMutationResponse,
    SceneSummary,
)
from api.sessions import (
    AnalysisSession,
    can_undo_draft,
    record_draft_snapshot,
    refresh_session_structure,
    undo_draft,
)
from scriptlens_structure import (
    count_scene_headings,
    delete_scene_block,
    normalize_modified_scene_text,
    splice_scene_in_screenplay,
)

router = APIRouter(tags=["draft"])


def _mutation_response(
    session: AnalysisSession,
    *,
    previous_scene_count: int,
    affected_scene: dict[str, object] | None = None,
) -> DraftMutationResponse:
    """Build a draft mutation response from a refreshed session.

    Args:
        session: Analysis session after rebuild.
        previous_scene_count: Scene count before the mutation.
        affected_scene: Optional summary for the removed or edited scene.

    Returns:
        ``DraftMutationResponse`` for the API client.
    """
    scenes = [SceneSummary(**scene) for scene in session.scenes]
    affected = SceneSummary(**affected_scene) if affected_scene else None
    return DraftMutationResponse(
        script_id=session.script_id,
        draft_revision=session.draft_revision,
        scene_count=len(session.scenes),
        previous_scene_count=previous_scene_count,
        orphan_count=session.orphan_count,
        structure_mode=session.structure_mode,  # type: ignore[arg-type]
        scenes=scenes,
        graph_summary=session.graph_summary,
        affected_scene=affected,
        can_undo=can_undo_draft(session),
    )


@router.post(
    "/scripts/{script_id}/draft/delete",
    response_model=DraftMutationResponse,
)
def draft_delete_scene(
    script_id: str,
    body: DraftDeleteRequest,
    request: Request,
) -> DraftMutationResponse:
    """Remove one scene from the working draft and rebuild structure.

    Args:
        script_id: Session identifier from upload.
        body: Scene to delete from the draft.
        request: Current FastAPI request.

    Returns:
        Updated scene list, orphan count, and graph summary.

    Raises:
        HTTPException: When the session or scene id is invalid.
    """
    session = require_session(request, script_id)
    scene = session.engine._scene_lookup.get(body.scene_id)
    if scene is None:
        raise HTTPException(status_code=422, detail=f"Unknown scene_id: {body.scene_id}")

    previous_scene_count = count_scene_headings(session.draft_text)
    removed_summary = {
        "scene_id": scene.scene_id,
        "scene_number": scene.scene_number,
        "heading": scene.heading,
    }

    record_draft_snapshot(session)
    try:
        session.draft_text = delete_scene_block(session.draft_text, scene.scene_number)
    except ValueError as exc:
        session.draft_history.pop()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    refresh_session_structure(session, increment_revision=True)
    get_session_store(request).put(session)

    return _mutation_response(
        session,
        previous_scene_count=previous_scene_count,
        affected_scene=removed_summary,
    )


@router.post(
    "/scripts/{script_id}/draft/apply-edit",
    response_model=DraftMutationResponse,
)
def draft_apply_edit(
    script_id: str,
    body: DraftApplyEditRequest,
    request: Request,
) -> DraftMutationResponse:
    """Apply an edited scene block to the working draft and rebuild structure.

    Multi-slugline edits are allowed — they may split one scene into several.

    Args:
        script_id: Session identifier from upload.
        body: Scene id and replacement Fountain text.
        request: Current FastAPI request.

    Returns:
        Updated scene list, orphan count, and graph summary.

    Raises:
        HTTPException: When the session or scene id is invalid.
    """
    session = require_session(request, script_id)
    scene = session.engine._scene_lookup.get(body.scene_id)
    if scene is None:
        raise HTTPException(status_code=422, detail=f"Unknown scene_id: {body.scene_id}")

    previous_scene_count = count_scene_headings(session.draft_text)
    edited_summary = {
        "scene_id": scene.scene_id,
        "scene_number": scene.scene_number,
        "heading": scene.heading,
    }

    normalized_text = normalize_modified_scene_text(scene, body.modified_text)
    record_draft_snapshot(session)
    try:
        session.draft_text = splice_scene_in_screenplay(
            session.draft_text,
            scene.scene_number,
            normalized_text,
        )
    except ValueError as exc:
        session.draft_history.pop()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    refresh_session_structure(session, increment_revision=True)
    get_session_store(request).put(session)

    return _mutation_response(
        session,
        previous_scene_count=previous_scene_count,
        affected_scene=edited_summary,
    )


@router.post(
    "/scripts/{script_id}/draft/undo",
    response_model=DraftMutationResponse,
)
def draft_undo(
    script_id: str,
    request: Request,
) -> DraftMutationResponse:
    """Restore the previous working draft snapshot.

    Args:
        script_id: Session identifier from upload.
        request: Current FastAPI request.

    Returns:
        Updated scene list, orphan count, and graph summary.

    Raises:
        HTTPException: When the session has nothing to undo.
    """
    session = require_session(request, script_id)
    previous_scene_count = count_scene_headings(session.draft_text)

    try:
        undo_draft(session)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    get_session_store(request).put(session)
    return _mutation_response(
        session,
        previous_scene_count=previous_scene_count,
        affected_scene=None,
    )


@router.get("/scripts/{script_id}/draft/export")
def draft_export(
    script_id: str,
    request: Request,
) -> Response:
    """Download the current working draft as a Fountain file.

    Args:
        script_id: Session identifier from upload.
        request: Current FastAPI request.

    Returns:
        Plain-text Fountain download of ``draft_text``.

    Raises:
        HTTPException: When the session is missing.
    """
    session = require_session(request, script_id)
    download_name = draft_export_filename(session.filename, session.draft_revision)
    return Response(
        content=session.draft_text,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
        },
    )
