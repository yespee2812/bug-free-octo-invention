"""Pydantic models for the ScriptLens structure API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

StructureMode = Literal["full", "limited"]
OrphanType = Literal["hard", "subplot_chain"]
RiskLevel = Literal["none", "low", "medium", "high"]
ImpactSeverity = Literal["direct", "indirect"]
InputFormat = Literal["pdf", "text"]
IngestMethod = Literal["slugline_extract", "numbered_prose_fallback"]


class HealthResponse(BaseModel):
    """Liveness response for load balancers and deploy checks."""

    ok: bool = True
    service: str = "scriptlens-structure"


class SceneSummary(BaseModel):
    """Lightweight scene row for lists and navigation."""

    scene_id: str
    scene_number: int
    heading: str


class UploadResponse(BaseModel):
    """Response after a screenplay upload and structure analysis."""

    script_id: str
    filename: str
    scene_count: int
    orphan_count: int
    structure_mode: StructureMode
    scenes: list[SceneSummary]
    draft_revision: int = 0
    input_format: InputFormat = "text"
    pdf_conversion: str | None = None
    ingest_method: IngestMethod | None = None
    slugline_count: int | None = None
    ingest_warnings: list[str] = Field(default_factory=list)


class OrphanRecord(BaseModel):
    """One orphan scene with OSD classification metadata."""

    scene_id: str
    scene_number: int
    heading: str
    orphan_type: OrphanType
    reasons: list[str] = Field(default_factory=list)
    component_scenes: list[str] = Field(default_factory=list)


class OrphanListResponse(BaseModel):
    """Orphan scenes for a stored script session."""

    script_id: str
    orphan_count: int
    orphans: list[OrphanRecord]


class OrphanGraphNode(BaseModel):
    """One scene node in the OSD orphan graph view."""

    scene_id: str
    scene_number: int
    heading: str
    is_orphan: bool = False
    orphan_type: OrphanType | None = None
    in_degree: int = 0
    out_degree: int = 0


class OrphanGraphEdge(BaseModel):
    """One weighted OSD link between scenes."""

    from_scene_id: str
    to_scene_id: str
    weight: float
    explanation: str = ""
    character: float = 0.0
    spatial: float = 0.0
    prop: float = 0.0
    semantic: float = 0.0


class OrphanGraphStats(BaseModel):
    """Summary counts for the orphan graph viewer."""

    scene_count: int
    edge_count: int
    orphan_count: int
    link_threshold: float


class OrphanGraphResponse(BaseModel):
    """Orphan graph payload for client visualization."""

    script_id: str
    nodes: list[OrphanGraphNode]
    edges: list[OrphanGraphEdge]
    stats: OrphanGraphStats


class ScriptDetailResponse(BaseModel):
    """Full structure metadata for a stored script session."""

    script_id: str
    filename: str
    scene_count: int
    orphan_count: int
    structure_mode: StructureMode
    scenes: list[SceneSummary]
    graph_summary: dict[str, object] = Field(default_factory=dict)


class SimulateCutRequest(BaseModel):
    """Request body for simulate-cut preview."""

    scene_id: str


class ImpactedScene(BaseModel):
    """One downstream scene affected by a simulated cut."""

    scene_id: str
    scene_number: int
    heading: str
    dependency_path: list[str]
    total_weight: float
    explanation: str = ""
    impact_reason: str = ""
    link_hops: int = 0
    severity: ImpactSeverity = "direct"


class SimulateCutResponse(BaseModel):
    """Impact preview when removing a single scene."""

    script_id: str
    removed_scene: SceneSummary
    impacted_scenes: list[ImpactedScene]
    impacted_count: int
    summary: str
    risk_level: RiskLevel


class SceneDetailResponse(BaseModel):
    """Full text for one scene in the script reader."""

    script_id: str
    scene_id: str
    scene_number: int
    heading: str
    body: str


class SimulateEditRequest(BaseModel):
    """Request body for simulate-edit preview."""

    scene_id: str
    modified_text: str


class EdgeDiffRecord(BaseModel):
    """One dependency edge in an edit diff."""

    from_scene_id: str
    to_scene_id: str
    weight: float
    edge_type: str
    explanation: str


class EdgeChangeRecord(BaseModel):
    """One dependency edge whose metadata changed after an edit."""

    from_scene_id: str
    to_scene_id: str
    before: EdgeDiffRecord
    after: EdgeDiffRecord


class EdgeDiffResponse(BaseModel):
    """Added, removed, and changed edges after a simulated edit."""

    added: list[EdgeDiffRecord]
    removed: list[EdgeDiffRecord]
    changed: list[EdgeChangeRecord]


class OrphanDelta(BaseModel):
    """Orphan count before and after a simulated edit."""

    before: int
    after: int
    message: str = ""


class DownstreamAtRiskScene(BaseModel):
    """One downstream scene that would lose a setup after an edit."""

    scene_id: str
    scene_number: int
    heading: str
    reason: str


class SimulateEditResponse(BaseModel):
    """Impact preview when rewriting a single scene."""

    script_id: str
    scene_id: str
    edited_scene: SceneSummary
    edge_diff: EdgeDiffResponse
    orphan_delta: OrphanDelta
    scene_count_before: int
    scene_count_after: int
    downstream_at_risk: list[DownstreamAtRiskScene]
    summary: str
    risk_level: RiskLevel
    applied: bool = False


class DraftDeleteRequest(BaseModel):
    """Request body for deleting one scene from the working draft."""

    scene_id: str


class DraftApplyEditRequest(BaseModel):
    """Request body for applying an edited scene to the working draft."""

    scene_id: str
    modified_text: str


class DraftMutationResponse(BaseModel):
    """Response after a draft delete or applied edit rebuilds structure."""

    script_id: str
    draft_revision: int
    scene_count: int
    previous_scene_count: int
    orphan_count: int
    structure_mode: StructureMode
    scenes: list[SceneSummary]
    graph_summary: dict[str, object] = Field(default_factory=dict)
    affected_scene: SceneSummary | None = None
    can_undo: bool = False
