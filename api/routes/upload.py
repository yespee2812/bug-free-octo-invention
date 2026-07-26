"""Upload route for screenplay structure analysis."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from api.schemas import SceneSummary, UploadResponse
from api.sessions import AnalysisSession, SessionStore, make_script_id
from pdf_ingest import ScreenplayLoadError
from scriptlens_structure import analyze_structure_from_bytes

router = APIRouter(tags=["upload"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def _get_store(request: Request) -> SessionStore:
    """Return the shared session store from application state.

    Args:
        request: Current FastAPI request.

    Returns:
        Application-wide ``SessionStore`` instance.
    """
    return request.app.state.session_store


@router.post("/upload", response_model=UploadResponse)
async def upload_screenplay(
    request: Request,
    file: UploadFile = File(...),
) -> UploadResponse:
    """Upload a screenplay and run structure-only analysis.

    Args:
        request: Current FastAPI request (for session store access).
        file: Multipart screenplay upload (PDF or Fountain/text).

    Returns:
        Script id, scene list, orphan count, and structure mode.

    Raises:
        HTTPException: On empty file, oversize upload, or unsupported type.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    try:
        results, engine, screenplay_text = analyze_structure_from_bytes(
            content,
            file.filename,
        )
    except (ValueError, ScreenplayLoadError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    script_id = make_script_id(screenplay_text)
    summary = results["script_summary"]
    structure = results["structure"]
    input_meta = results["input"]

    session = AnalysisSession(
        script_id=script_id,
        filename=input_meta["filename"],
        original_text=screenplay_text,
        draft_text=screenplay_text,
        draft_revision=0,
        input_format=input_meta["format"],
        structure_mode=summary["structure_mode"],
        scenes=results["scenes"],
        orphan_count=structure["orphan_count"],
        orphans=structure["orphans"],
        graph_summary=structure["graph_summary"],
        high_risk_scenes=structure["high_risk_scenes"],
        engine=engine,
    )
    _get_store(request).put(session)

    scenes = [SceneSummary(**scene) for scene in results["scenes"]]
    return UploadResponse(
        script_id=script_id,
        filename=session.filename,
        scene_count=summary["total_scenes"],
        orphan_count=structure["orphan_count"],
        structure_mode=summary["structure_mode"],
        scenes=scenes,
        draft_revision=0,
        input_format=input_meta.get("format", "text"),
        pdf_conversion=input_meta.get("pdf_conversion"),
        ingest_method=input_meta.get("ingest_method"),
        slugline_count=input_meta.get("slugline_count"),
        ingest_warnings=list(input_meta.get("ingest_warnings", [])),
    )
