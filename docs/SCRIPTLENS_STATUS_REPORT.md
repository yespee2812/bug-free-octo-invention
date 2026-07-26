# ScriptLens — Status Report

**Prepared for:** Product planning and writer outreach  
**Date:** July 2026  
**Version:** v3 structure product — engine + web app (local / pre-deploy)

---

## 1. Executive summary

ScriptLens is a **structural editing intelligence layer** for screenplays. Writers upload a script and get:

1. **Orphan scenes** — scenes with weak downstream ties in the story graph  
2. **Simulate cut** — preview what breaks if a scene is removed  
3. **Simulate edit** — preview dependency changes when scene text is rewritten  
4. **Draft workflow** — delete or apply edits to a working copy, undo, export Fountain  

**What exists today:** A working structure engine, FastAPI service, browser workspace (`web/`), PDF ingest with automatic cleanup, orphan graph visualization, draft undo/export, **236 automated tests**, CI gates on the planted contradiction corpus and orphan golden fixtures.

**What does not exist yet:** Cloud hosting, user accounts, billing, `.docx` upload wiring, contradiction UI (deliberately out of customer v1 scope), Chrome extension, and large-scale simulate regression corpus.

**Bottom line:** The **customer v1 feature set is built and testable locally**. Before paid writers touch it: deploy to a URL, run simulate regression on labeled fixtures, and validate Hollywood PDF cleanup at scale.

---

## 2. Product scope (customer v1)

### In scope

| Capability | Status |
|------------|--------|
| Upload Fountain / PDF | Shipped (API + web) |
| Orphan detection (OSD: C/L/P + semantic E) | Shipped |
| Orphan type + reasons in UI | Shipped |
| Story graph (orphan graph) viewer | Shipped |
| Simulate cut with risk summary | Shipped |
| Simulate edit with edge diff | Shipped |
| Draft delete / apply edit / undo / export | Shipped |
| PDF auto-cleanup (`refined` stage) + ingest warnings | Shipped |
| Non-destructive preview (original upload unchanged) | Shipped |

### Out of scope (customer v1)

| Capability | Notes |
|------------|-------|
| Plot contradiction UI | Engine kept for internal CI only |
| Auth / accounts / billing | Planned v3.1 |
| Chrome extension | Planned v3.1 |
| `.fdx` native import | Export to PDF or Fountain first |
| Scanned PDF / OCR | Clear error today; no OCR pipeline |
| Multi-scene batch simulate | Future |

---

## 3. How to run it

```powershell
venv\Scripts\python.exe run_api.py
# Open http://localhost:8000
```

CLI (structure-only, no contradictions):

```powershell
venv\Scripts\python.exe run_scriptlens.py your_script.fountain --structure-only
```

| Input format | Customer v1 support |
|--------------|---------------------|
| Fountain / `.txt` / `.md` | Full — best quality |
| PDF (text-based) | Full — auto `refined` conversion |
| `.docx` | Converter exists; **upload API not wired yet** |
| Final Draft `.fdx` | Not supported — export to Fountain or PDF |
| Scanned / image PDF | Fails with friendly error |

---

## 4. Architecture today

```text
[Browser: web/]  →  POST /api/upload
                         ↓
                   scriptlens_structure.py
                         ↓
              scene_dependency.py  (simulate cut/edit)
              orphan_scene_detector.py  (orphans / OSD)
                         ↓
              In-memory SessionStore (24h TTL)
                         ↓
              JSON + static UI (simulate, draft, graph)
```

**Two graphs (by design):**

- **OSD weighted graph** — orphan classification (C/L/P/E, threshold 0.20)  
- **Continuity graph** — simulate cut and simulate edit impact  

Plot contradiction detection (`plot_contradiction.py`) runs only on the **legacy CLI path** and **CI corpus batch** — not on the v3 upload API.

---

## 5. API surface (implemented)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness |
| POST | `/api/upload` | Upload + analyse |
| GET | `/api/scripts/{id}` | Script metadata |
| GET | `/api/scripts/{id}/orphans` | Orphan list + types |
| GET | `/api/scripts/{id}/orphan-graph` | Graph for story view |
| GET | `/api/scripts/{id}/scenes/{scene_id}` | Scene body for reader |
| POST | `/api/scripts/{id}/simulate/cut` | Simulate cut |
| POST | `/api/scripts/{id}/simulate/edit` | Simulate edit |
| POST | `/api/scripts/{id}/draft/delete` | Delete scene from draft |
| POST | `/api/scripts/{id}/draft/apply-edit` | Apply edit to draft |
| POST | `/api/scripts/{id}/draft/undo` | Undo draft change |
| GET | `/api/scripts/{id}/draft/export` | Download draft `.fountain` |

Static UI is served from `/` when `web/` is present.

---

## 6. Quality gates (automated)

| Gate | What it enforces |
|------|------------------|
| `pytest tests/` | 236+ unit and API tests |
| `run_orphan_spec_eval.py` | 5 golden orphan fixtures (incl. semantic) |
| `run_corpus_batch.py --compare-ground-truth` | Planted **contradiction** corpus (internal) |
| `score_corpus_baseline.py --check` | 100% recall, ≤4 FPs on contradiction corpus |

**Gap:** Simulate cut/edit has unit tests and manual corpus template fields (`expected_simulate_delete`) but **no populated ground truth or CI scorecard yet**.

---

## 7. Measured performance (honest numbers)

### 7.1 Planted contradiction corpus (internal CI)

- **40 scripts**, **100 planted errors**  
- **Recall: 100%** (100/100)  
- **False positives: 2** across entire corpus  

This validates the **contradiction engine**, not the customer v1 UI.

### 7.2 Orphan golden fixtures

- **5 fixtures** in `tests/corpus/ground_truth/orphan_spec/manifest.yaml`  
- Covers hard orphan, prologue/montage/flashback exemptions, semantic thread  

### 7.3 Hollywood clean benchmark (manual)

- **6–7 PDFs** reviewed (Carrie, American Pie, Batman, Kane, Conclave, American Beauty, Almost Famous)  
- After cleanup pipeline: **63% fewer contradiction flags** on raw batch; **0 real slips** on reviewed set  
- **Do not demo raw PDF cast/prop lists** to writers without cleanup  

### 7.4 Product readiness (estimated)

| Dimension | Estimate | Notes |
|-----------|----------|-------|
| Structure engine + API | ~95% | Feature-complete for v1 |
| Web workspace | ~90% | Missing high-risk badges, mobile banner, docx |
| Writer-trustworthy on real PDFs | ~65% | Needs scale benchmark + Fountain-first messaging |
| Deploy / revenue-ready | ~25% | No hosting, auth, or billing yet |

---

## 8. Known gaps (fixable without large corpus)

| Gap | Priority |
|-----|----------|
| High-risk scene badges in web UI | High — data already in session |
| `.docx` upload wiring | High |
| Simulate regression runner + golden YAML | High — small synthetic fixtures OK |
| Root deploy (Dockerfile, env docs) | High for beta |
| Stale docs | In progress |
| Mobile/tablet “desktop only” banner | Medium |
| Orphan-only scene list filter | Medium |

---

## 9. Known gaps (needs corpus or real scripts)

| Gap | Why |
|-----|-----|
| Simulate recall on long features | Labeled cut/edit ground truth at scale |
| Hollywood false-positive rates | 30–40 clean PDFs + manual review |
| TV format edge cases | Pilot/episode scripts |
| PDF ingest quality metrics | Diverse real PDFs |

---

## 10. Next course of action

### Phase A — Pre-beta hardening (1–2 weeks)

1. Deploy FastAPI + static UI to a public URL (Hostinger or similar).  
2. Wire `.docx` upload; expose high-risk scenes in UI.  
3. Add simulate regression runner on 10–15 synthetic golden scripts.  
4. Label `expected_simulate_delete` on existing genre corpus scripts.

### Phase B — Writer validation (2 weeks)

1. Send URL to **10 screenwriters** (not engineers).  
2. Demo orphans + simulate cut/edit on **their** Fountain or cleaned PDF.  
3. Track: “Would you pay for this?” — do not tune engine on one script alone.

### Phase C — Scale benchmark (parallel)

1. Build simulate + orphan regression corpus (see prior planning doc).  
2. Expand Hollywood clean benchmark to 30–40 scripts.  
3. Add TV pilot/episode bucket.

### What NOT to do before beta

- Do not expose contradiction UI to customers (scope lock).  
- Do not show raw Hollywood PDF analysis without cleanup.  
- Do not build Chrome extension before hosted beta works.

---

## 11. Summary table

| Capability | Jul 2026 (this report) |
|------------|------------------------|
| Web upload + workspace | **Yes** |
| Orphans + story graph | **Yes** |
| Simulate cut / edit | **Yes** |
| Draft delete / undo / export | **Yes** |
| PDF auto-cleanup | **Yes** |
| Contradiction UI | **No** (internal engine only) |
| Auth / billing / cloud | **No** |
| Simulate CI scorecard | **No** (template only) |
| 100% planted contradiction CI | **Yes** |

---

## 12. Document history

| Date | Change |
|------|--------|
| Jul 2026 (early) | Engine + CLI focus; web “not built” |
| Jul 2026 (mid) | v3 structure product shipped locally: API, web, draft, OSD, simulate |

---

*ScriptLens — Upload your script, see loose scenes, preview what breaks if you cut or rewrite — without changing your file.*
