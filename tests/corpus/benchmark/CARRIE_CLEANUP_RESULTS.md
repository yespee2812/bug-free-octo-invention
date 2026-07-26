# Carrie (1976) — Cleanup Pilot Results

Script: `02_Carie_1975.pdf.pdf` → extracted → auto clean → manual pass.

**Date:** June 2026

---

## Three-stage comparison

| Stage | File | Characters parsed | Total flags | name_consistency | numeric_count |
|-------|------|-------------------|-------------|------------------|---------------|
| 1. Raw PDF extract | `02_Carie_1975.fountain` | **267** | 13 | 6 | 7 |
| 2. Automated cleanup | `02_Carie_1975_clean.fountain` | **98** | 15 | 1 | 14 |
| 3. Manual pass | `02_Carie_1975_manual.fountain` | **29** | 15 | **0** | 15 |
| 4. Manual + `pdf_benchmark` profile | same | **29** | **0** | **0** | **0** |

**Scenes:** 82 at all stages (structure preserved).

**Health score:** 0/100 (standard profile, 15 flags) → **82/100** (`pdf_benchmark` profile, 0 flags).

---

## What each stage fixed

### Stage 1 → 2 (`cleanup_extracted_fountain.py`)

- Merged broken action lines into paragraphs
- Demoted obvious camera slugs (`THE HOUSE`, `OMITTED`, `ANGLE`, etc.)
- Removed page/revision noise
- **Removed 5 of 6 false name_consistency flags** (slug pairs)

### Stage 2 → 3 (`refine_manual_fountain.py`)

- Whitelist of real character cues (Carrie cast)
- OCR fixes: `CHIUS`→`CHRIS`, `TOHMY`→`TOMMY`, `GOLLINS`→`COLLINS`, etc.
- Demoted remaining slug cues (`STELIA HORAN - DAY`, `CARRIE'S VOICE`, revision markers)
- **Eliminated last name_consistency flag** (CHRIS/CHIUS)

---

## Remaining flags (all numeric_count — assessed as noise)

All 15 flags are low-confidence word-count chains from merged PDF text, e.g.:

- `'group'`, `'ext'`, `'continued'` — slug/editorial words in action
- `'carrie'` 2 → 204 — prom scene density, not a story error
- `'vote'` 63 → 1 — ballot scene wording
- `'set'` within same scene — formatting artifact

**Manual verdict:** 15/15 false positives on this clean Hollywood script.

---

## Remaining character list (29)

Real cast plus 3 extraction artifacts from action text:

`BILLY, BOBBY, CARRIE, CHRIS, COLLINS, CORA, ELEANOR, ERNEST, FRIEDA, FROMM, GEORGE, HELEN, MARGARET, MORTON, MRS. HORAN, NORMA, RHONDA, STELIA, SUE, TOMMY, WATSON, …`

Artifacts: `ANGLE ON MARGARET WHITE`, `JESUS`, `OMIT`, `POV` (from inline action/slug text, not cues).

---

## Commands used

```powershell
# Auto cleanup
venv\Scripts\python.exe scripts\cleanup_extracted_fountain.py `
  tests\corpus\benchmark\clean_produced\fountain\02_Carie_1975.fountain

# Manual pass
venv\Scripts\python.exe scripts\refine_manual_fountain.py `
  tests\corpus\benchmark\clean_produced\fountain\02_Carie_1975_clean.fountain

# Analyse (clean benchmark — uses pdf_benchmark automatically)
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir tests\corpus\benchmark\clean_produced\fountain `
  --output-dir tests\corpus\benchmark\reports\fountain_clean

# Or single file with explicit profile
venv\Scripts\python.exe -c "
from scriptlens_analyser import analyze_from_path
from plot_contradiction import INPUT_PROFILE_PDF_BENCHMARK
r = analyze_from_path('tests/corpus/benchmark/clean_produced/fountain/02_Carie_1975_manual.fountain', input_profile=INPUT_PROFILE_PDF_BENCHMARK)
print(r['contradictions']['total_found'], r['health_score'])
"
```

Reports: `tests/corpus/benchmark/reports/fountain_clean/02_Carie_1975_manual_report.txt`

---

## Takeaways for engine tuning

1. **PDF cleanup is essential** before trusting name_consistency on produced scripts.
2. **name_consistency** on Carrie went 6 → 0 with no engine code changes — input quality was the bottleneck.
3. **numeric_count** does not improve with cleanup alone; use **`pdf_benchmark` input profile** for Hollywood PDF/benchmark runs (disables generic number+noun pairing).
4. **Health score** on Carrie manual: **82/100** with `pdf_benchmark` (0 flags; remaining penalty from orphan-scene graph heuristics).
