"""Simulate-cut route for structure analysis sessions."""



from __future__ import annotations



from fastapi import APIRouter, HTTPException, Request



from api.deps import require_session

from api.schemas import (

    EdgeChangeRecord,

    EdgeDiffRecord,

    EdgeDiffResponse,

    ImpactedScene,

    OrphanDelta,

    DownstreamAtRiskScene,

    SceneSummary,

    SimulateCutRequest,

    SimulateCutResponse,

    SimulateEditRequest,

    SimulateEditResponse,

)

from scriptlens_structure import get_simulate_cut_impact, get_simulate_edit_impact



router = APIRouter(tags=["simulate"])





@router.post(

    "/scripts/{script_id}/simulate/cut",

    response_model=SimulateCutResponse,

)

def simulate_cut(

    script_id: str,

    body: SimulateCutRequest,

    request: Request,

) -> SimulateCutResponse:

    """Preview downstream impact of removing one scene.



    Uses the current working draft graph. Does not modify the draft.



    Args:

        script_id: Session identifier from upload.

        body: Scene to simulate removing.

        request: Current FastAPI request.



    Returns:

        Removed scene metadata and impacted downstream scenes with paths.



    Raises:

        HTTPException: When the session or scene id is invalid.

    """

    session = require_session(request, script_id)

    impact = get_simulate_cut_impact(

        session.engine,

        body.scene_id,

        session.engine._scene_lookup,

    )



    removed = impact["removed_scene"]

    if removed is None:

        raise HTTPException(

            status_code=422,

            detail=f"Unknown scene_id: {body.scene_id}",

        )



    impacted_scenes = [

        ImpactedScene(**record) for record in impact["impacted_scenes"]

    ]

    return SimulateCutResponse(

        script_id=script_id,

        removed_scene=SceneSummary(**removed),

        impacted_scenes=impacted_scenes,

        impacted_count=len(impacted_scenes),

        summary=str(impact["summary"]),

        risk_level=impact["risk_level"],

    )





def _edge_diff_to_response(edge_diff: dict[str, object]) -> EdgeDiffResponse:

    """Convert a raw edge diff dict into API response models.



    Args:

        edge_diff: Output from ``get_simulate_edit_impact``.



    Returns:

        Pydantic ``EdgeDiffResponse`` instance.

    """

    added = [EdgeDiffRecord(**record) for record in edge_diff.get("added", [])]

    removed = [EdgeDiffRecord(**record) for record in edge_diff.get("removed", [])]

    changed: list[EdgeChangeRecord] = []

    for record in edge_diff.get("changed", []):

        changed.append(

            EdgeChangeRecord(

                from_scene_id=record["from_scene_id"],

                to_scene_id=record["to_scene_id"],

                before=EdgeDiffRecord(**record["before"]),

                after=EdgeDiffRecord(**record["after"]),

            )

        )

    return EdgeDiffResponse(added=added, removed=removed, changed=changed)





@router.post(

    "/scripts/{script_id}/simulate/edit",

    response_model=SimulateEditResponse,

)

def simulate_edit(

    script_id: str,

    body: SimulateEditRequest,

    request: Request,

) -> SimulateEditResponse:

    """Preview dependency edge changes after rewriting one scene.



    Diffs against the current working draft. Does not modify the draft unless

    the client calls ``POST /draft/apply-edit``.



    Args:

        script_id: Session identifier from upload.

        body: Scene id and replacement Fountain text.

        request: Current FastAPI request.



    Returns:

        Edge diff, orphan delta, scene-count delta, and downstream scenes at risk.



    Raises:

        HTTPException: When the session or scene id is invalid.

    """

    session = require_session(request, script_id)



    try:

        impact = get_simulate_edit_impact(

            session.engine,

            session.draft_text,

            body.scene_id,

            body.modified_text,

        )

    except ValueError as exc:

        raise HTTPException(status_code=422, detail=str(exc)) from exc



    return SimulateEditResponse(

        script_id=script_id,

        scene_id=impact["scene_id"],

        edited_scene=SceneSummary(**impact["edited_scene"]),

        edge_diff=_edge_diff_to_response(impact["edge_diff"]),

        orphan_delta=OrphanDelta(**impact["orphan_delta"]),

        scene_count_before=impact["scene_count_before"],

        scene_count_after=impact["scene_count_after"],

        downstream_at_risk=[

            DownstreamAtRiskScene(**record)

            for record in impact["downstream_at_risk"]

        ],

        summary=str(impact["summary"]),

        risk_level=impact["risk_level"],

        applied=False,

    )

