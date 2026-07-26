# ScriptLens documentation index

Quick map of everything in `docs/`. For setup and commands, start with the [root README](../README.md).

**Product scope (July 2026):** Customer v1 is **structure-only** — orphans, simulate cut/edit, draft workflow. Contradiction detection is **internal CI only**.

---

## Start here

| Document | Audience | Purpose |
|----------|----------|---------|
| [SCRIPTLENS_STATUS_REPORT.md](SCRIPTLENS_STATUS_REPORT.md) | Product, outreach | What ships today, metrics, gaps, next steps |
| [ARCHITECTURE_v3_STRUCTURE.md](ARCHITECTURE_v3_STRUCTURE.md) | Engineering | v3 system design, API contracts, implementation status |
| [UX_SPEC_v1.md](UX_SPEC_v1.md) | Product, design | Workspace UX, acceptance checklist, API map |
| [CLIENT_PITCH_SIMULATE_FEATURES.md](CLIENT_PITCH_SIMULATE_FEATURES.md) | Sales, demos | Talking points and example script for simulate/orphans |

---

## Architecture

| Document | Notes |
|----------|-------|
| [ARCHITECTURE_v3_STRUCTURE.md](ARCHITECTURE_v3_STRUCTURE.md) | **Current** — structure product, FastAPI, web |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Legacy v2.4 — contradiction engine + extension plan |
| [ENGINE_REDESIGN.md](ENGINE_REDESIGN.md) | Engine evolution notes |

Visual mockups (reference): [`ux/`](ux/) — main view, simulate active, contradictions (contradictions UI not shipped).

Demo scripts: [`demo_scripts/`](demo_scripts/) — orphan and revolver-chain fixtures.

---

## Engine and evaluation

| Document | Purpose |
|----------|---------|
| [ENGINE_REVIEW_PLAIN_ENGLISH.md](ENGINE_REVIEW_PLAIN_ENGLISH.md) | Non-technical engine overview |
| [ENGINE_REVIEW_REPORT.md](ENGINE_REVIEW_REPORT.md) | Detailed engine review |
| [CORPUS_EVALUATION_GUIDE.md](CORPUS_EVALUATION_GUIDE.md) | How to run and score the test corpus |
| [FINE_TUNING_BACKLOG.md](FINE_TUNING_BACKLOG.md) | Engine tuning queue after writer reviews |
| [PERFORMANCE_TESTING_GUIDE.md](PERFORMANCE_TESTING_GUIDE.md) | Performance testing notes |

Corpus folders and commands: [`../tests/corpus/README.md`](../tests/corpus/README.md).

Benchmark (clean Hollywood PDFs): [`../tests/corpus/benchmark/README.md`](../tests/corpus/benchmark/README.md).

---

## Writer outreach and materials

| Document | Purpose |
|----------|---------|
| [WRITER_OUTREACH_MESSAGE.md](WRITER_OUTREACH_MESSAGE.md) | Send-ready email template |
| [SCREENWRITER_ERROR_INJECTION_GUIDE.md](SCREENWRITER_ERROR_INJECTION_GUIDE.md) | How writers plant test errors |
| [SCREENWRITER_ERROR_CHEAT_SHEET.md](SCREENWRITER_ERROR_CHEAT_SHEET.md) | Error types quick reference |
| [writer_materials/README.md](writer_materials/README.md) | Word briefs, cleanup guides, PDFs |

---

## Internal reference

| Document | Purpose |
|----------|---------|
| [internal/CATEGORY_TO_ENGINE_MAPPING.md](internal/CATEGORY_TO_ENGINE_MAPPING.md) | Error category → engine mapping |

---

## Key commands (from repo root)

```powershell
venv\Scripts\python.exe run_api.py                              # Web UI
venv\Scripts\python.exe -m pytest tests/ -q                     # Tests
venv\Scripts\python.exe scripts/run_orphan_spec_eval.py         # Orphan goldens
venv\Scripts\python.exe scripts/run_corpus_batch.py --compare-ground-truth
```

---

## Document freshness

| Document | Last meaningful update |
|----------|------------------------|
| SCRIPTLENS_STATUS_REPORT.md | July 2026 — v3 web shipped |
| ARCHITECTURE_v3_STRUCTURE.md | July 2026 — §19 implementation status |
| UX_SPEC_v1.md | July 2026 — shipped checklist |
| ARCHITECTURE.md | July 2026 — §17 points to v3 |
| CORPUS_EVALUATION_GUIDE.md | July 2026 — customer = web workspace |

If a doc contradicts [SCRIPTLENS_STATUS_REPORT.md](SCRIPTLENS_STATUS_REPORT.md) or [ARCHITECTURE_v3_STRUCTURE.md](ARCHITECTURE_v3_STRUCTURE.md), treat those two as authoritative for product scope.
