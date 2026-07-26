# Citizen Kane (1941) — Cleanup Pilot Results

Script: `04_CitizenKane_200.pdf.pdf` → extracted → auto clean → Kane manual pass.

**Date:** July 2026

---

## Four-stage comparison

| Stage | File | Characters parsed | Total flags | Health |
|-------|------|-------------------:|------------:|-------:|
| 1. Raw PDF extract | `04_CitizenKane_200.fountain` | **125** | 5 | 48 |
| 2. Automated cleanup | `04_CitizenKane_200_clean.fountain` | **75** | 10 | 14 |
| 3. Generic refined | `04_CitizenKane_200_refined.fountain` | **61** | 10 | 14 |
| 4. Kane manual pass | `04_CitizenKane_200_manual.fountain` | **44** | **10** | 14 |

**Scenes:** 99 at all stages (structure preserved).

**Profile:** `pdf_benchmark` for all analysis runs.

---

## What each stage fixed

### Stage 1 → 2 (`cleanup_extracted_fountain.py`)

- Merged broken action lines into paragraphs
- Demoted camera slugs and miniature headings
- **Characters: 125 → 75**

### Stage 2 → 4 (`refine_manual_fountain.py` + Kane whitelist)

- **43-character cast whitelist** (Thompson, Kane, Bernstein, Leland, Susan, etc.)
- Whitelist-only mode for paths containing `CitizenKane`
- Demoted headline slugs: `FRAUD AT POLLS`, `LABOR RIOTS`, `QUICK DISSOLVE`, `NO. 9182`, etc.
- Demoted `*'S VOICE` cues and miniature location slugs
- **Characters: 75 → 44** (demo-quality cast)

---

## Remaining character list (44)

Real cast — no headline or miniature slug artifacts:

`ASSISTANT, BERNSTEIN, BERTHA, CARTER, CHARLES FOSTER KANE, CITY EDITOR, DR. COREY, EMILY, ETHEL, FIRST CIVIC LEADER, FOREMAN, FRED, GEORGIE, GUARD, HIRELING, INVESTIGATOR, JUNIOR, KANE, KATHERINE, LELAND, MARIE, MATISTI, MIKE, MISS ANDERSON, MISS TOWNSEND, MRS. KANE, NARRATOR, PHOTOGRAPHER, PRESIDENT, RAWLSTON, RAYMOND, REILLY, ROGERS, SECOND ASSISTANT, SECOND LEADER, SECOND NEWSPAPERMAN, SMATHERS, SPEAKER, SUSAN, THATCHER, THIRD MAN, THIRD NEWSPAPERMAN, THOMPSON`

Note: `RAIN` may appear once from action-line extraction (sound cue), not from a character cue.

---

## Remaining contradiction flags (10 — assessed)

| # | Type | Verdict | Notes |
|---|------|---------|-------|
| 1–5 | character_age (Kane) | **Mostly FP** | Biographical flashbacks (adult vs child ages across montage) |
| 6 | object_identity (floor) | **Unsure** | wooden vs stone — may be different rooms at Xanadu |
| 7–10 | numeric_count | **FP** | rank / seating / clock chains from PDF prose |

**Manual verdict:** Cast is demo-ready. Contradiction panel safe to show with caveat that biographical scripts trigger age *possible* flags.

---

## Safe to show writer?

| Input | Cast list | Contradictions | Demo-ready? |
|-------|-----------|----------------|-------------|
| Raw PDF | No | Misleading | **No** |
| Manual fountain | **Yes (44)** | 10 low-conf | **Partial** (continuity OK with caveats; hide props) |

---

## Commands used

```powershell
# Full Kane pipeline
venv\Scripts\python.exe scripts\convert_pdf_to_fountain.py --stage clean `
  tests\corpus\benchmark\_batch_six\04_CitizenKane_200.pdf.pdf `
  --output tests\corpus\benchmark\clean_produced\fountain\04_CitizenKane_200_clean.fountain

venv\Scripts\python.exe scripts\refine_manual_fountain.py `
  tests\corpus\benchmark\clean_produced\fountain\04_CitizenKane_200_clean.fountain

# Or one step from PDF (refined applies Kane whitelist when path matches)
venv\Scripts\python.exe scripts\convert_pdf_to_fountain.py --stage refined `
  tests\corpus\benchmark\_batch_six\04_CitizenKane_200.pdf.pdf `
  --output tests\corpus\benchmark\clean_produced\fountain\04_CitizenKane_200_manual.fountain

# Analyse
venv\Scripts\python.exe -c "
from scriptlens_analyser import analyze_from_path
from plot_contradiction import INPUT_PROFILE_PDF_BENCHMARK
r = analyze_from_path(
    'tests/corpus/benchmark/clean_produced/fountain/04_CitizenKane_200_manual.fountain',
    input_profile=INPUT_PROFILE_PDF_BENCHMARK,
)
print(len(r['script_summary']['total_characters']), r['contradictions']['total_found'], r['health_score'])
"
```

---

## Takeaways

1. **Same pattern as Carrie and American Pie:** manual cast whitelist is required for Hollywood PDF trust.
2. **Citizen Kane cast noise was extreme** (125 raw → 44 manual).
3. **10 remaining flags** are age/biography and numeric PDF noise — not cast-list artifacts.
4. **Biographical scripts** need writer-facing copy: *"Age flags may appear across life-stage montages — confirm before treating as errors."*
