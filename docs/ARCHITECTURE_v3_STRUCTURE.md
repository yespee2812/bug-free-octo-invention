# ScriptLens — Architecture Specification v3.0 (Structure-Only)

| Field | Value |
|-------|-------|
| **Version** | 3.0 — Structure-only product |
| **Date** | July 2026 |
| **Status** | Implemented (customer v1 local) — deploy + corpus regression pending |
| **Audience** | Solo builder, future contributors, product review |
| **Supersedes** | `ARCHITECTURE.md` v2.4 (contradiction + extension-first) |

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Product definition](#2-product-definition)
3. [Scope lock](#3-scope-lock)
4. [System architecture](#4-system-architecture)
5. [Thin client (browser)](#5-thin-client-browser)
6. [Backend (FastAPI)](#6-backend-fastapi)
7. [Core engine — scene dependency](#7-core-engine--scene-dependency)
8. [Simulate cut](#8-simulate-cut)
9. [Simulate edit](#9-simulate-edit)
10. [Orphan scenes](#10-orphan-scenes)
11. [PDF ingestion](#11-pdf-ingestion)
12. [API contracts](#12-api-contracts)
13. [Data models](#13-data-models)
14. [User workflows](#14-user-workflows)
15. [UI architecture](#15-ui-architecture)
16. [Security and privacy](#16-security-and-privacy)
17. [Performance and reliability](#17-performance-and-reliability)
18. [Deployment — Hostinger](#18-deployment--hostinger)
19. [Implementation status](#19-implementation-status)
20. [Build sequence (solo)](#20-build-sequence-solo)
21. [Out of scope](#21-out-of-scope)
22. [Appendix A — System diagram](#appendix-a--system-diagram)
23. [Appendix B — Competitive positioning](#appendix-b--competitive-positioning)
24. [Appendix C — Glossary](#appendix-c--glossary)

---

## 1. Executive summary

ScriptLens is a **structural editing intelligence layer** for screenplays. Writers upload a script and receive:

1. **Orphan scene count** — scenes that sit loosely in the story graph
2. **Simulate cut** — preview what downstream scenes break if one scene is removed
3. **Simulate edit** — preview how dependency edges change when scene text is rewritten

**All analysis runs on the server.** The customer browser is a thin client. Writers on **4 GB laptops** with many tabs open are supported because spaCy, PDF parsing, and graph logic never run on the client.

**Plot contradiction detection is removed from the product.** The `plot_contradiction.py` module remains in the repository for internal regression tests but is **not called** by the v3 product path.

### Product promise (one sentence)

**Upload your script, see loose scenes, and preview what breaks if you cut or rewrite — without changing your original file.**

### Architecture principles

| Principle | Rule |
|-----------|------|
| **Thin client** | Browser sends uploads and simulation requests; server returns JSON |
| **Non-destructive** | Original file never modified; all operations are preview |
| **Deterministic core** | Scene graph and impact paths are explainable, not LLM-black-box |
| **No LLM in v1** | Zero API cost; high margin; fast responses |
| **Solo-deployable** | Hostinger VPS + static HTML + single FastAPI process |

---

## 2. Product definition

### 2.1 Target user

| Segment | Primary need |
|---------|--------------|
| Working screenwriters | “Can I cut this scene?” |
| Writing partners | “What happens if we change this beat?” |
| Development readers | Quick structural map before notes |

### 2.2 Core value proposition

| Problem | ScriptLens answer |
|---------|-------------------|
| “If I cut this scene, what breaks?” | **Simulate cut** + dependency paths |
| “If I rewrite this scene, what connections change?” | **Simulate edit** + edge diff |
| “Which scenes sit loosely in the story?” | **Orphan count** + scroll-to-scene |
| “Where is that scene?” | Scene list + **Go to scene** from impact panel |

### 2.3 What ScriptLens is not

- Not a screenplay editor (writers stay in Final Draft / WriterDuet)
- Not a continuity police tool (no “you made a mistake” flags in v3)
- Not a production breakdown tool (no cast/props scheduling)
- Not a story-universe platform (no franchise canon DB)
- Not a local Chrome extension with on-device NLP (v3 is web-first)

### 2.4 Platform (v3)

| Layer | Technology |
|-------|------------|
| **Frontend** | Static HTML + CSS + vanilla JavaScript on Hostinger |
| **Backend** | FastAPI + uvicorn on Hostinger VPS |
| **Engine** | Existing `scriptlensCore` Python modules |
| **CLI** | `run_scriptlens.py --structure-only` for dev smoke tests |

---

## 3. Scope lock

### 3.1 In scope (v3.0)

| Feature | Ship |
|---------|------|
| Upload Fountain / PDF | Yes |
| Scene list + script reader | Yes |
| Orphan count + list | Yes |
| Simulate cut | Yes |
| Simulate edit | Yes |
| Go-to-scene from impact panel | Yes |
| PDF auto `refined` conversion | Yes |
| Full / Limited structure mode banner | Yes |
| Server-side session (in-memory) | Yes |

### 3.2 Out of scope (v3.0 — do not build)

| Feature | Status |
|---------|--------|
| Plot contradiction UI or API | **Removed** |
| Health score from contradiction count | **Removed** |
| Cast / props panels (especially on PDF) | **Hidden** |
| Chrome extension | v3.1+ |
| User accounts / Supabase | v3.1+ |
| Stripe billing | v3.1+ |
| Redis / Postgres | v3.1+ |
| Tier 3 LLM summaries | Never in structure-only path |
| Final Draft `.fdx` native import | Export to PDF/Fountain first |

### 3.3 Repository modules — product vs internal

| Module | v3 product path | Internal / CI only |
|--------|-----------------|-------------------|
| `scene_dependency.py` | **Yes** | — |
| `scriptlens_structure.py` | **Yes** (new) | — |
| `pdf_to_fountain.py` | **Yes** | — |
| `pdf_screenplay_loader.py` | **Yes** | — |
| `nlp_shared.py` | **Yes** | — |
| `plot_contradiction.py` | **No** | Corpus regression |
| `scriptlens_analyser.py` (full) | **No** | Legacy CLI |

---

## 4. System architecture

### 4.1 High-level topology

```
┌────────────────────────────────────────────────────────────────────┐
│  CUSTOMER DEVICE (4 GB RAM, many browser tabs)                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Static web app (~50–150 MB tab RAM)                         │  │
│  │  Upload │ Scene list │ Reader │ Simulate panels              │  │
│  └────────────────────────────┬─────────────────────────────────┘  │
└───────────────────────────────┼──────────────────────────────────────┘
                                │ HTTPS (JSON + multipart upload)
┌───────────────────────────────▼──────────────────────────────────────┐
│  HOSTINGER VPS (1–2 GB RAM for API process)                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI (single worker, spaCy loaded once at startup)         │  │
│  │  Session store (in-memory dict, TTL 24h)                       │  │
│  └────────────────────────────┬───────────────────────────────────┘  │
│  ┌────────────────────────────▼───────────────────────────────────┐  │
│  │  scriptlens_structure.py                                       │  │
│  │  → SceneDependencyEngine (parse, build_graph, query)           │  │
│  │  → pdf_to_fountain (refined stage for PDF uploads)             │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Zone responsibilities

| Zone | Owns | Must not own |
|------|------|--------------|
| **Browser** | Upload UI, scene selection, reader render, simulate UX | NLP, PDF extraction, graph math |
| **API server** | Parse, graph build, simulate cut/edit, session | Long-term user accounts (v3) |
| **Engine** | Deterministic dependency edges | LLM calls, contradiction rules |

### 4.3 Request lifecycle

```
POST /upload
  → save text in session[script_id]
  → parse_fountain_text
  → build_graph (no ContradictionEngine)
  → return { script_id, scenes[], orphan_count, structure_mode }

POST /simulate/cut { scene_id }
  → get_delete_impact(scene_id)
  → return impacted scenes + paths

POST /simulate/edit { scene_id, modified_text }
  → splice text → re-parse → rebuild graph
  → diff edges before/after
  → return edge_diff + impact_delta
```

---

## 5. Thin client (browser)

### 5.1 Design constraints for 4 GB customer laptops

| Constraint | Implementation |
|------------|----------------|
| No client-side NLP | All analysis server-side |
| No client-side PDF parsing | File sent as multipart upload |
| Small JS bundle | Vanilla JS; no React for v3 |
| Lazy scene rendering | Render visible scenes only (virtual scroll) |
| No large in-memory script copy | Server holds canonical text; client holds scene summaries |

### 5.2 Estimated client RAM

| Component | RAM |
|-----------|-----|
| Static page + JS | ~20–40 MB |
| Scene list (210 items) | ~5 MB |
| Visible script blocks (lazy) | ~30–80 MB |
| **Total tab** | **~50–150 MB** |

### 5.3 Frontend file structure (planned)

```
web/
├── index.html      # Upload + workspace shell
├── app.js          # API client, state, simulate handlers
├── reader.js       # Lazy scene renderer
└── styles.css      # 3-panel layout (280px | flex | 320px)
```

### 5.4 CORS

API allows the Hostinger frontend origin only. No credentials cookies in v3.

---

## 6. Backend (FastAPI)

### 6.1 Process model

| Setting | Value | Reason |
|---------|-------|--------|
| Workers | **1** | spaCy singleton; 8 GB dev / 1–2 GB VPS |
| spaCy load | **At startup** | `get_shared_nlp()` once per process |
| Model | `en_core_web_sm` | Smallest viable; ~100 MB Python heap |
| Session store | `dict[str, AnalysisSession]` | No Redis in v3 |
| Session TTL | 24 hours | Privacy + memory bound |
| Max upload size | 15 MB | Typical screenplay PDF |

### 6.2 AnalysisSession (server-side)

```python
@dataclass
class AnalysisSession:
    script_id: str           # SHA256 prefix of normalized text
    screenplay_text: str     # Canonical fountain text
    scenes: list[SceneBlock]
    engine: SceneDependencyEngine
    structure_mode: str      # "full" | "limited"
    created_at: datetime
```

### 6.3 New module: `scriptlens_structure.py`

Thin wrapper — **no import of ContradictionEngine**.

```python
def analyze_structure(screenplay_text: str) -> StructureReport:
    nlp = get_shared_nlp()
    engine = SceneDependencyEngine(nlp=nlp)
    scenes = engine.parse_fountain_text(screenplay_text)
    engine.build_graph(scenes)  # fact_store=None
    return StructureReport(
        scenes=scenes,
        orphans=engine.get_orphan_scenes(),
        graph_summary=engine.export_graph_summary(),
        high_risk_scenes=rank_by_delete_impact(engine, scenes),
    )
```

### 6.4 API directory (planned)

```
api/
├── main.py           # FastAPI app, CORS, startup spaCy load
├── routes/
│   ├── upload.py
│   ├── orphans.py
│   └── simulate.py
├── sessions.py       # In-memory store + TTL sweep
└── schemas.py        # Pydantic request/response models
```

---

## 7. Core engine — scene dependency

### 7.1 Purpose

Build a **directed scene graph** where edges represent narrative dependencies (characters, objects, locations, introductions) between earlier and later scenes.

### 7.2 Existing implementation

| Component | File | Status |
|-----------|------|--------|
| Fountain parser | `scene_dependency.py` | Done |
| Graph builder | `scene_dependency.py` | Done |
| Orphan query | `get_orphan_scenes()` | Done |
| Delete impact | `get_delete_impact()` | Done |
| Graph summary | `export_graph_summary()` | Done |
| Shared spaCy | `nlp_shared.py` | Done |

### 7.3 Graph model

| Element | Definition |
|---------|------------|
| **Node** | One per scene (`scene_id`, e.g. `scene_047`) |
| **Edge** | Directed `from_scene → to_scene` with `weight`, `edge_type`, `explanation` |
| **Order** | Edges only from earlier scene to later scene (no cycles) |
| **Merge** | Multiple signals between same pair → weights summed |

### 7.4 Edge types (v3)

| Type | Weight (typical) | Signal |
|------|------------------|--------|
| Character presence | 0.5–0.7 | Shared character across scenes |
| Object introduction | 0.8–1.0 | Object introduced, reused later |
| Location continuity | 0.4 | Location from heading repeats |
| Character fact | 0.6 | Established status/trait in action |

### 7.5 Query operations (product-facing)

| Operation | Method | UI use |
|-----------|--------|--------|
| Orphans | `get_orphan_scenes()` | Left panel count |
| Simulate cut | `get_delete_impact(scene_id)` | Right panel impact list |
| Upstream deps | `get_scene_dependencies(scene_id)` | v3.1 optional |
| High-risk rank | Derived from impact count | Optional “do not cut lightly” hint |

---

## 8. Simulate cut

### 8.1 Definition

**Read-only preview** of removing one scene. Does not modify the script.

### 8.2 Algorithm (implemented)

```
Input:  graph G, scene_id S
Process:
  1. descendants = nx.descendants(G, S)
  2. For each D in descendants:
       path = shortest_path(G, S, D)
       weight = sum(edge weights on path)
  3. Sort by weight descending
Output: list of { scene_id, heading, dependency_path, total_weight }
```

### 8.3 API response shape

```json
{
  "removed_scene": {
    "scene_id": "scene_047",
    "scene_number": 47,
    "heading": "INT. KITCHEN - DAY"
  },
  "impacted_scenes": [
    {
      "scene_id": "scene_062",
      "scene_number": 62,
      "heading": "INT. CAR - NIGHT",
      "dependency_path": ["scene_047", "scene_051", "scene_062"],
      "total_weight": 1.4,
      "explanation": "object: knife"
    }
  ]
}
```

### 8.4 UI behavior

| State | Center panel | Right panel |
|-------|--------------|-------------|
| Before cut | Normal reader | Empty or placeholder |
| After cut | Removed scene = ghost overlay + “Simulated removal” chip | Impact list + Go to scene |
| Clear | Restore normal | Clear panel |

---

## 9. Simulate edit

### 9.1 Definition

**Read-only preview** of rewriting one scene’s Fountain text. Shows how dependency edges change.

### 9.2 Algorithm (v3 — full rebuild)

```
Input:  session, scene_id S, modified_scene_text T
Process:
  1. edges_before = snapshot(engine.graph)
  2. screenplay' = splice(scene S body → T) into full text
  3. scenes' = parse_fountain_text(screenplay')
  4. engine'.build_graph(scenes')
  5. edges_after = snapshot(engine'.graph)
  6. diff = compare(edges_before, edges_after)
  7. impact_delta = scenes that lost incoming edges from S
Output: { added_edges, removed_edges, changed_weights, orphan_delta }
```

**v3.1 optimization:** Incremental rebuild for scene S only (same diff output, faster).

### 9.3 v3 UI scope

- Textarea pre-filled with selected scene’s raw Fountain block
- Button: **Simulate edit**
- Right panel: edge diff list (human-readable)
- No inline WYSIWYG screenplay editor in v3

### 9.4 API response shape

```json
{
  "scene_id": "scene_047",
  "edge_diff": {
    "added": [
      { "from": "scene_047", "to": "scene_051", "type": "object", "explanation": "knife" }
    ],
    "removed": [
      { "from": "scene_047", "to": "scene_062", "type": "object", "explanation": "knife" }
    ],
    "changed": []
  },
  "orphan_delta": { "before": 3, "after": 4 },
  "downstream_at_risk": ["scene_062", "scene_088"]
}
```

---

## 10. Orphan scenes

### 10.1 Definition

A scene that **introduces** narrative elements (characters, objects, locations) that **no later scene depends on** through the graph — and has **no meaningful downstream edges** from its introductions.

### 10.2 UX framing

| Do | Don't |
|----|-------|
| “3 loosely connected scenes” | “3 errors” |
| “May be safe to trim — verify dramatically” | “Delete these scenes” |

Montage, comedy tags, and breathers may appear as orphans — this is expected.

### 10.3 Interaction

- Left panel: **ORPHANS 3** (tap → filter scene list or scroll to first)
- Scene row badge: optional dot for orphan scenes

---

## 11. PDF ingestion

### 11.1 Pipeline

```
PDF upload
  → convert_pdf_to_fountain(stage="refined")
  → analyze_structure(text)
  → structure_mode detection
```

### 11.2 Structure modes

| Mode | Condition | User banner |
|------|-----------|-------------|
| **Full** | ≥ 1 extractable INT/EXT slugline | “Full structure mode” |
| **Limited** | 0 sluglines (image PDF) | “Limited structure mode — scene breaks not detected. Upload a text-based PDF or Fountain for full analysis.” |

### 11.3 Hollywood benchmark reference

Tested scripts (refined pipeline): American Beauty (162 scenes), Carrie, Almost Famous, Conclave, Batman Begins, Citizen Kane.

### 11.4 Product rules for PDF

| Rule | Action |
|------|--------|
| Auto `refined` on upload | Always |
| Show cast/props list | **Never** in v3 UI |
| Contradiction pass | **Never** |

---

## 12. API contracts

### 12.1 Endpoints (v3.0)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness check |
| `POST` | `/api/upload` | Multipart file → create session |
| `GET` | `/api/scripts/{id}` | Scene list + structure metadata |
| `GET` | `/api/scripts/{id}/scenes/{scene_id}` | Single scene body for reader / edit textarea |
| `GET` | `/api/scripts/{id}/orphans` | Orphan list |
| `POST` | `/api/scripts/{id}/simulate/cut` | Delete impact preview |
| `POST` | `/api/scripts/{id}/simulate/edit` | Edge diff preview |

### 12.2 Upload response

```json
{
  "script_id": "a1b2c3...",
  "filename": "my_script.pdf",
  "scene_count": 162,
  "orphan_count": 2,
  "structure_mode": "full",
  "scenes": [
    { "scene_id": "scene_001", "scene_number": 1, "heading": "INT. HOUSE - DAY" }
  ]
}
```

### 12.3 Error codes

| HTTP | Meaning |
|------|---------|
| 400 | Unsupported file type / empty script |
| 404 | Session expired or unknown script_id |
| 413 | File too large |
| 422 | Invalid scene_id |
| 500 | Engine failure (log script_hash only, not body) |

---

## 13. Data models

### 13.1 SceneBlock (engine)

| Field | Type | Description |
|-------|------|-------------|
| `scene_id` | str | Stable ID (`scene_NNN`) |
| `scene_number` | int | Display order |
| `heading` | str | Slugline |
| `characters` | list[str] | Dialogue cues |
| `objects` | list[str] | Extracted props |
| `locations` | list[str] | From heading |
| `action_text` | str | Raw action lines |
| `dialogue_blocks` | list | Character + lines |

### 13.2 DependencyEdge

| Field | Type |
|-------|------|
| `from_scene_id` | str |
| `to_scene_id` | str |
| `weight` | float |
| `edge_type` | str |
| `explanation` | str |

### 13.3 Pydantic schemas (API layer)

- `UploadResponse`
- `SceneSummary`
- `OrphanListResponse`
- `SimulateCutRequest` / `SimulateCutResponse`
- `SimulateEditRequest` / `SimulateEditResponse`

---

## 14. User workflows

### 14.1 Primary flow

```
1. Land on upload page
2. Drop PDF or Fountain
3. Wait for "Building scene graph..." (10–20s for large PDF)
4. Workspace loads:
   - Orphan count (left)
   - Scene list (left)
   - Script reader (center)
5. Select scene → Simulate cut OR Edit scene
6. Review impact (right) → Go to scene
7. Clear simulation → back to normal
```

### 14.2 Non-destructive rule

The uploaded file on the writer’s machine is **never modified**. ScriptLens does not integrate with Final Draft for write-back in v3.

### 14.3 Session end

- User closes tab → session remains until TTL
- No account required in v3
- Privacy copy: “Your script is processed on our server and deleted within 24 hours.”

---

## 15. UI architecture

### 15.1 Layout (desktop, min width 1024px)

| Column | Width | Contents |
|--------|-------|----------|
| Left | 280px fixed | Orphans, scene list, Simulate cut, Edit scene |
| Center | flex 1 | Script reader (lazy render) |
| Right | 320px fixed | Simulation results |

### 15.2 Left panel (v3)

```
┌─────────────────────────┐
│  ORPHANS            3   │
├─────────────────────────┤
│  SCENES                 │
│  1  INT. HOUSE - DAY    │
│  5  EXT. ROAD - NIGHT ◀ │
├─────────────────────────┤
│  [ Simulate cut ]       │
│  [ Edit scene ]         │
└─────────────────────────┘
```

**Removed from v2 UX:** Plot issues count, contradictions tab, View all continuity.

### 15.3 Right panel — simulate cut

```
Impact of removing Scene 5
──────────────────────────
⚠ Scene 12 — downstream dependent
   Path: 5 → 9 → 12
   Object: knife
   [ Go to scene 12 ]

[ Clear simulation ]
```

### 15.4 Right panel — simulate edit

```
Changes if you edit Scene 5
──────────────────────────
− Removed link: knife → Scene 12
+ Added link: flashlight → Scene 12
Orphans: 3 → 4

[ Clear edit preview ]
```

### 15.5 Mobile (v3)

Read-only scene list + upload. Simulate on desktop only; banner: “Open on desktop for simulate.”

---

## 16. Security and privacy

| Concern | Mitigation |
|---------|------------|
| Script sensitivity | HTTPS only; 24h TTL; no full-body logging |
| Logs | `script_hash`, `scene_count`, `duration_ms` — never screenplay text |
| Upload validation | Extension whitelist: `.fountain`, `.txt`, `.pdf` |
| Session isolation | `script_id` = hash; no cross-session access |
| CORS | Frontend origin only |

---

## 17. Performance and reliability

### 17.1 Latency targets (server)

| Step | p50 | p95 |
|------|-----|-----|
| Fountain parse (120 scenes) | < 100ms | < 200ms |
| Graph build (120 scenes) | < 200ms | < 400ms |
| PDF convert + analyse (160 scenes) | < 8s | < 20s |
| Simulate cut | < 50ms | < 100ms |
| Simulate edit (full rebuild) | < 500ms | < 2s |

### 17.2 RAM targets

| Environment | RAM | Notes |
|-------------|-----|-------|
| Customer browser tab | 50–150 MB | Thin client |
| API process (steady) | 300–600 MB | spaCy sm + one session |
| API peak (210 scenes) | < 800 MB | American Pie-scale |
| Developer machine | 8 GB OK | Close tabs during PDF dev |
| Hostinger VPS | ≥ 1 GB (2 GB preferred) | Single worker |

### 17.3 Failure modes

| Failure | UX |
|---------|-----|
| 0 scenes parsed | “Could not detect scenes — try Fountain or a text-based PDF” |
| Limited structure mode | Banner + orphans/cut may be unreliable |
| Session expired | “Session expired — please re-upload” |
| Server timeout | Retry button; spinner max 30s |

### 17.4 Concurrency (v3)

Single worker = one heavy analysis at a time. Optional: simple queue with “Analysing…” if second upload arrives.

---

## 18. Deployment — Hostinger

### 18.1 Topology

| Component | Host |
|-----------|------|
| Static frontend | Hostinger `public_html/` |
| FastAPI | Same VPS, subdomain `api.yourdomain.com` |
| SSL | Hostinger Let's Encrypt |
| Process manager | systemd or supervisord → `uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1` |

### 18.2 Environment

```
PYTHONPATH=/path/to/scriptlensCore
SPACY_MODEL=en_core_web_sm
SESSION_TTL_HOURS=24
MAX_UPLOAD_MB=15
CORS_ORIGIN=https://yourdomain.com
```

### 18.3 Deploy checklist

- [ ] `pip install -r requirements.txt` + `python -m spacy download en_core_web_sm`
- [ ] `GET /api/health` returns 200
- [ ] Upload American Beauty PDF → scene_count > 100
- [ ] Simulate cut returns ≥ 1 impact on known demo scene
- [ ] CORS from production domain
- [ ] Privacy page linked from upload screen

### 18.4 Cost (year 1)

| Item | Cost |
|------|------|
| Hostinger (existing) | $0 incremental |
| LLM APIs | $0 |
| **Total** | **$0** cash (solo build) |

---

## 19. Implementation status

*Last updated: July 2026.*

### 19.1 Shipped (customer v1)

| Component | Status | Notes |
|-----------|--------|-------|
| `scriptlens_structure.py` | Done | Structure-only entry; no contradictions |
| `orphan_scene_detector.py` + `osd_semantic.py` | Done | OSD graph; optional MiniLM E_ij |
| `SceneDependencyEngine` | Done | Continuity graph for simulate |
| `get_delete_impact()` / simulate cut | Done | API + web + CLI |
| `get_simulate_edit_impact()` | Done | API + web |
| Draft delete / apply / undo / export | Done | `api/routes/draft.py` |
| `simulate_impact_summary.py` | Done | Plain-English risk headlines |
| `pdf_ingest.py` | Done | Metadata, warnings, HTTP 400 errors |
| `api/` FastAPI service | Done | Upload, scripts, simulate, draft, health |
| `web/` frontend | Done | Upload, reader, simulate, draft, story graph |
| Orphan graph view | Done | `GET /orphan-graph` + `web/orphan-graph.js` |
| Unit + API tests | Done | 236+ tests; CI on GitHub Actions |
| Orphan spec golden eval | Done | `scripts/run_orphan_spec_eval.py` |
| PDF → Fountain pipeline | Done | `refined` default on upload |
| UX mockups (cut flow) | Done | Reference for web layout |

### 19.2 Not done (post–customer v1)

| Component | Status | Notes |
|-----------|--------|-------|
| Hostinger / production deploy | Not started | `run_api.py` local only |
| User auth + billing | Not started | v3.1 |
| `.docx` upload API | Not started | `docx_to_fountain.py` exists |
| High-risk scene badges in web UI | Not started | Computed in engine; not exposed in API response |
| Simulate regression CI scorecard | Not started | `expected_simulate_delete` template only |
| Mobile/tablet desktop-only banner | Not started | UX spec item |
| Chrome extension | Not started | v3.1 |

### 19.3 Internal only (not customer product)

| Component | Status | Notes |
|-----------|--------|-------|
| `plot_contradiction.py` | Done | CI + legacy CLI; not v3 upload path |
| Planted contradiction corpus | Done | 100% recall gate in CI |
| Hollywood clean benchmark | Partial | Manual FP review; 6–7 scripts |

---

## 20. Build sequence (solo)

| Week | Deliverable | Status |
|------|-------------|--------|
| 1 | `scriptlens_structure.py` + CLI `--structure-only` | **Done** |
| 2 | FastAPI upload + orphans + health | **Done** |
| 3 | Simulate cut endpoint | **Done** |
| 4 | Frontend upload + scene list + reader | **Done** |
| 5 | Simulate cut UI | **Done** |
| 6–7 | Simulate edit backend + UI | **Done** |
| 8 | PDF path + structure mode banner | **Done** |
| 9 | Draft undo + export | **Done** |
| 10 | Orphan graph + OSD semantic | **Done** |
| 11 | Hostinger deploy | Pending |
| 12 | Simulate regression corpus + scorecard | Pending |
| 13 | Demo polish + writer beta | Pending |

**MVP milestone (orphans + simulate cut on web):** **Complete** (local).

---

## 21. Out of scope

| Item | Notes |
|------|-------|
| Plot contradiction product surface | Engine kept for CI only |
| Chrome extension | v3.1 |
| Auth / billing | v3.1 |
| `.fdx` import | Export to PDF first |
| AI rewrite / dialogue generation | Never |
| Production breakdown | Studiovity lane |
| Franchise / series canon | Othelia lane |

---

## Appendix A — System diagram

```
Writer
  │
  ▼
[ Browser: upload.html ]
  │ POST /api/upload (multipart)
  ▼
[ FastAPI ]
  │ convert_pdf (if PDF)
  │ analyze_structure()
  ▼
[ SceneDependencyEngine ]
  │ parse → build_graph
  │
  ├─► GET orphans
  ├─► POST simulate/cut  → get_delete_impact()
  └─► POST simulate/edit → rebuild + diff
  │
  ▼
[ JSON response ]
  │
  ▼
[ Browser: render impact + scroll ]
```

---

## Appendix B — Competitive positioning

| | Othelia | Final Draft | **ScriptLens v3** |
|--|---------|-------------|-------------------|
| Scope | Franchise / multi-format | Writing + production | **Single screenplay** |
| Simulate cut | Beta / vague | No | **Core feature** |
| Simulate edit | Beta / vague | No | **Core feature** |
| Orphans | No | No | **Core feature** |
| Contradiction flags | Yes | No | **No (removed)** |
| Customer RAM | Server-side assumed | Local app | **4 GB OK (thin client)** |
| Price | Enterprise beta | $250+ | **$0–15/mo planned** |

**Positioning line:** *“See what breaks before you cut.”*

---

## Appendix C — Glossary

| Term | Definition |
|------|------------|
| **Orphan scene** | Scene with weak or no downstream dependency edges |
| **Simulate cut** | Preview of removing a scene without editing the file |
| **Simulate edit** | Preview of rewriting a scene’s text and its graph impact |
| **Dependency path** | Ordered list of scene IDs linking setup to payoff |
| **Structure mode** | Full (sluglines detected) vs Limited (image PDF) |
| **Thin client** | Browser UI only; no local NLP |
| **Fountain** | Plain-text screenplay format |
| **refined** | PDF conversion stage with cleanup + manual-pass rules |

---

*Document version 3.0 — Structure-only final spec. Generated July 2026.*
