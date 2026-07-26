# ScriptLens Core

Structural editing intelligence for screenplays: **orphan scenes**, **simulate cut**, **simulate edit**, and a **non-destructive draft workflow** — without changing the writer's original upload.

The v3 **customer product** is structure-only. Plot contradiction detection (`plot_contradiction.py`) remains in the repo for **internal CI and corpus evaluation**; it is not exposed in the web app.

**Status:** Customer v1 features are implemented and testable locally. See [`docs/SCRIPTLENS_STATUS_REPORT.md`](docs/SCRIPTLENS_STATUS_REPORT.md) for gaps (deploy, auth, simulate regression corpus).

---

## Requirements

- Python **3.10+**
- Windows PowerShell (paths below use `venv\Scripts\`; adjust on macOS/Linux)

---

## Setup

```powershell
cd scriptlensCore

python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# First run only — caches the MiniLM model for orphan semantic edges
venv\Scripts\python.exe scripts/precache_osd_semantic.py
```

Always use the venv interpreter for commands in this repo.

---

## Run the web app

```powershell
venv\Scripts\python.exe run_api.py
```

Open **http://localhost:8000**, upload a `.fountain` or `.pdf`, then use the workspace:

- Scene list with orphan badges and summary
- **Story graph** (OSD timeline)
- **Simulate cut** / **Simulate edit** (preview only)
- **Delete scene**, **Apply edit**, **Undo draft**, **Export draft**

Sessions are in-memory and expire after **24 hours** (configurable via `SESSION_TTL_HOURS`).

---

## CLI (structure-only)

Matches the customer product scope (no contradictions):

```powershell
# Full structure report
.\run_scriptlens.ps1 tests\corpus\input\drama_5scene_errors.fountain --structure-only

# Simulate removing one scene
.\run_scriptlens.ps1 tests\corpus\input\drama_5scene_errors.fountain --structure-only --simulate-cut scene_002
```

Legacy full analysis (includes contradictions — internal use):

```powershell
.\run_scriptlens.ps1 tests\corpus\input\drama_5scene_errors.fountain
```

PDF conversion (manual pipeline):

```powershell
venv\Scripts\python.exe scripts\convert_pdf_to_fountain.py path\to\script.pdf
```

---

## API (quick reference)

Base URL: `http://localhost:8000/api`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| POST | `/upload` | Upload screenplay (multipart `file`) |
| GET | `/scripts/{id}` | Script metadata |
| GET | `/scripts/{id}/orphans` | Orphan list + types |
| GET | `/scripts/{id}/orphan-graph` | Story graph data |
| GET | `/scripts/{id}/scenes/{scene_id}` | Scene body for reader |
| POST | `/scripts/{id}/simulate/cut` | `{ "scene_id": "scene_002" }` |
| POST | `/scripts/{id}/simulate/edit` | `{ "scene_id", "modified_text" }` |
| POST | `/scripts/{id}/draft/delete` | `{ "scene_id" }` |
| POST | `/scripts/{id}/draft/apply-edit` | `{ "scene_id", "modified_text" }` |
| POST | `/scripts/{id}/draft/undo` | — |
| GET | `/scripts/{id}/draft/export` | Download draft `.fountain` |

Example upload:

```powershell
curl -X POST http://localhost:8000/api/upload `
  -F "file=@tests/corpus/input/drama_5scene_errors.fountain"
```

Full contracts: [`docs/ARCHITECTURE_v3_STRUCTURE.md`](docs/ARCHITECTURE_v3_STRUCTURE.md) §12.

---

## Tests and CI

```powershell
# Unit + API tests (236+)
venv\Scripts\python.exe -m pytest tests/ -q

# Orphan golden fixtures
venv\Scripts\python.exe scripts/run_orphan_spec_eval.py

# Planted contradiction corpus (internal CI gate)
venv\Scripts\python.exe scripts/run_corpus_batch.py --compare-ground-truth
venv\Scripts\python.exe scripts/score_corpus_baseline.py --check --min-recall 1.0 --max-false-positives 4

# Hollywood clean benchmark (local, gitignored PDFs)
venv\Scripts\python.exe scripts/run_clean_benchmark.py
```

GitHub Actions runs pytest, orphan spec eval, and corpus baseline on push/PR to `main`.

---

## Supported inputs (customer v1)

| Format | Web / API | Notes |
|--------|-----------|-------|
| `.fountain`, `.txt`, `.md` | Yes | Best quality |
| `.pdf` (text-based) | Yes | Auto `refined` conversion + ingest warnings |
| `.docx` | No | Converter exists; upload not wired |
| `.fdx` | No | Export to Fountain or PDF first |
| Scanned / image PDF | No | Clear error; OCR not implemented |

---

## Project layout

```text
scriptlensCore/
├── api/                       FastAPI routes + in-memory sessions
├── web/                       Static workspace UI
├── scriptlens_structure.py    Structure-only analysis (v3 product path)
├── orphan_scene_detector.py   Orphan scene detector (OSD)
├── osd_semantic.py            Optional semantic edges (MiniLM)
├── scene_dependency.py        Continuity graph (simulate cut/edit)
├── simulate_impact_summary.py Risk headlines for simulate UI
├── pdf_ingest.py              PDF upload metadata and errors
├── plot_contradiction.py        Internal / CI only
├── run_api.py                 Start FastAPI + web UI
├── run_scriptlens.py            CLI
├── scripts/                   Batch eval, PDF tools, benchmarks
├── tests/                     Unit and API tests
└── docs/                      Architecture, UX, status — see docs/README.md
```

---

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CORS_ORIGIN` | `*` | Allowed browser origins (comma-separated in production) |
| `SESSION_TTL_HOURS` | `24` | In-memory session TTL |
| `OSD_DISABLE_SEMANTIC` | unset | Set to `1` to skip MiniLM semantic edges (tests) |

---

## Documentation

| Start here | Purpose |
|------------|---------|
| [`docs/README.md`](docs/README.md) | Full documentation index |
| [`docs/SCRIPTLENS_STATUS_REPORT.md`](docs/SCRIPTLENS_STATUS_REPORT.md) | Current status, metrics, next steps |
| [`docs/ARCHITECTURE_v3_STRUCTURE.md`](docs/ARCHITECTURE_v3_STRUCTURE.md) | v3 architecture (authoritative) |
| [`docs/UX_SPEC_v1.md`](docs/UX_SPEC_v1.md) | UX spec + shipped checklist |
| [`docs/CLIENT_PITCH_SIMULATE_FEATURES.md`](docs/CLIENT_PITCH_SIMULATE_FEATURES.md) | Demo talking points |

Corpus and benchmarks: [`tests/corpus/README.md`](tests/corpus/README.md).

---

## Not in customer v1 yet

- Production hosting (Dockerfile / Hostinger)
- User accounts, billing, persistent storage
- `.docx` upload wiring
- High-risk scene badges in web UI (computed in engine)
- Simulate regression CI scorecard (ground-truth template exists)
- Contradiction panel in web UI (by design)
- Chrome extension, `.fdx` import, scanned PDF / OCR

---

*ScriptLens — Upload your script, see loose scenes, preview what breaks if you cut or rewrite.*
