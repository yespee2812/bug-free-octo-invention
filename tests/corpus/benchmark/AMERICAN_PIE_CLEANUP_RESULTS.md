# American Pie (1999) — Cleanup Pilot Results

Script: `American_Pie.pdf` → extracted → auto clean → manual pass.

**Date:** July 2026

---

## Three-stage comparison

| Stage | File | Characters parsed | Objects | Total flags | Orphans | Health |
|-------|------|-------------------|---------|-------------|---------|--------|
| 1. Raw PDF extract | `American_Pie.fountain` | **74** | 158 | **0** | 10 | 70 |
| 2. Automated cleanup | `American_Pie_clean.fountain` | **41** | 160 | **0** | 9 | 73 |
| 3. Manual pass | `American_Pie_manual.fountain` | **19** | 160 | **0** | 9 | 73 |

**Scenes:** 210 at all stages (structure preserved). User edition may list 211 — see scene-count note in `CLEAN_FP_LOG.md`.

**Profile:** `pdf_benchmark` for all analysis runs.

---

## What each stage fixed

### Stage 1 → 2 (`cleanup_extracted_fountain.py`)

- Merged broken action lines into paragraphs
- Demoted obvious camera slugs (`ANGLE ON JIM`, `INTERCUT WITH`, `ALL THE GUYS`, etc.)
- Removed page/revision noise and sound-effect cues (`LAUGHING.`, `WHISTLES.`, `ROCK MUSIC.`)
- **Characters: 74 → 41** (33 slug/camera cues removed)

### Stage 2 → 3 (`refine_manual_fountain.py`)

- Whitelist of real American Pie cast cues (Jim, Kevin, Oz, Finch, Stifler, etc.)
- Demoted crowd/generic cues (`BAND DORK`, `COLLEGE CHICK`, `ROLL CREDITS`, `YET ANOTHER GIRL`, …)
- Lowercased demoted slug text so caps-span extraction does not re-promote junk
- Sanitized embedded slug phrases in action (`The CHOIR TEACHER` → `The choir teacher`)
- **Characters: 41 → 19** (clean cast list)

---

## Remaining character list (19)

All real cast — no extraction artifacts after manual pass:

`ALBERT, COACH MARSHALL, FINCH, HEATHER, JESSICA, JIM, JIM'S DAD, JIM'S MOM, KEVIN, KEVIN'S BROTHER, MICHELLE, NADIA, OZ, SHERMAN, STIFLER, STIFLER'S BROTHER, STIFLER'S MOM, VICKY, VICKY'S MOM`

---

## Props / objects

Object count stays high (~160) on all stages. Many entries are dialogue fragments and sound cues from PDF extraction (`CHEERS`, `HOLY SHIT`, `COUNTRY MUSIC`), not story props. **Do not show raw props list to writers** until a props cleanup pass exists (engine-side blocklist or second refine pass).

---

## Contradiction flags

**0 flags** at all stages on this script with `pdf_benchmark`. Raw PDF had misleadingly “clean” contradiction output while cast/props were unusable.

---

## Safe to show writer?

| Input | Cast list | Props list | Contradictions | Demo-ready? |
|-------|-----------|------------|----------------|-------------|
| Raw PDF | No | No | OK (0) | **No** |
| Manual fountain | **Yes** | No | OK (0) | **Partial** (continuity/simulate OK; hide props panel) |

---

## Commands used

```powershell
# Extract PDF (if not already done)
venv\Scripts\python.exe -m pdf_screenplay_loader `
  tests\corpus\benchmark\clean_produced\American_Pie.pdf `
  tests\corpus\benchmark\clean_produced\fountain\American_Pie.fountain

# Auto cleanup
venv\Scripts\python.exe scripts\cleanup_extracted_fountain.py `
  tests\corpus\benchmark\clean_produced\fountain\American_Pie.fountain

# Manual pass
venv\Scripts\python.exe scripts\refine_manual_fountain.py `
  tests\corpus\benchmark\clean_produced\fountain\American_Pie_clean.fountain

# Analyse manual file
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir tests\corpus\benchmark\clean_produced\fountain `
  --output-dir tests\corpus\benchmark\reports\fountain_clean
```

---

## Takeaways

1. **Same pattern as Carrie:** PDF cleanup is essential; 0 flags on raw PDF is not enough for writer trust.
2. **American Pie cast noise was worse than Carrie** (74 vs 267 raw cues — but many Carrie cues were OCR fragments).
3. **Manual pass + American Pie whitelist** in `refine_manual_fountain.py` brings cast to demo quality.
4. **Props remain a gap** for all Hollywood PDFs — next cleanup target after cast.
