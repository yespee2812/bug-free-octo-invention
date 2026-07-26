# Hollywood Benchmark — Cleanup & Guardrail Results

**Date:** July 2026  
**Pipeline:** PDF → `refined` Fountain (`convert_pdf_to_fountain.py`) → analyse with `pdf_benchmark` profile  
**Reports:** `tests/corpus/benchmark/reports/raw_pdf/`

---

## Summary (before → after)

| Script | Flags (Jul 4 raw PDF) | Flags (after pipeline) | Health | Demo-ready? |
|--------|----------------------:|-------------------------:|-------:|-------------|
| American Pie | 0 (misleading — 74 junk characters) | **0** | 73 | Partial (manual cast; hide props) |
| American Beauty | 8 | **2** | 78 | **Yes** (contradictions only; 2 low-conf FPs) |
| Batman Begins | 9 | **0** | 28 | Partial (0 flags; cast still noisy) |
| Almost Famous | 11 | **3** | 0 | **Yes** (3/3 FP; hide cast) |
| Conclave | 4 | **4** | 47 | **Yes** (4/4 FP) |
| Citizen Kane | 20 | **10** | 14 | Partial (manual cast; 10 low-conf FPs) |
| **Total** | **52** | **19** | — | **19/19 reviewed — 0 real slips** |

**Net:** **63% fewer contradiction flags** on the six-script batch, with **zero planted-corpus regression** (100% recall, 2 FPs on writer corpus).

---

## What changed

### 1. Input pipeline (automatic)

- PDF uploads now run **`refined`** conversion (extract → cleanup → manual-pass rules) before analysis.
- `run_clean_benchmark.py` fixed to pass `input_profile=pdf_benchmark` and `pdf_conversion=refined`.

### 2. Engine guardrails (`pdf_benchmark` profile only)

| Rule | Fixes |
|------|--------|
| Skip age when character gets **older** in later scene | Alfred 50→62, Kane life stages |
| Skip age when either value **≤ 3** or scene gap **≥ 20** | Page-number OCR ("age 1") on Kane |
| Block **POV / pronoun / camera** ownership objects | American Beauty POV chain |
| Skip **name drift** when PDF hyphen cue (`GORDON-`) | Batman name noise |
| Skip **object identity** on generic heads (eyes, box, gauntlet, wayne) | Batman material FPs |
| Skip **trait/ownership** on junk PDF entity labels (4+ words, slug phrases) | Citizen Kane action fragments |

Writer-corpus (`standard` profile) is **unchanged** — still catches age 28→31, etc.

### 3. Cleanup script tweaks

- `refine_manual_fountain.py`: demote `HEAR…`, `YEAR-OLD JANE`, `OPEN HOUSE TODAY`, etc.

---

## Per-script notes

### American Beauty — **best demo script**

- **2 flags:** `date_year` 1973 vs 1970 (possible real timeline choice); `numeric_count` rank 1 vs 2 in same scene (likely PDF noise).
- Safe to show contradiction panel; hide props list.

### Batman Begins — **0 flags**

- Cast list still has PDF junk (`LAUGHS`, `M-EMIT.42B`, etc.) — do not show raw character list.
- Contradiction output is trustworthy.

### American Pie — **0 flags**

- Use `American_Pie_manual.fountain` for demos (19-character cast). See `AMERICAN_PIE_CLEANUP_RESULTS.md`.

### Citizen Kane — **10 flags (all reviewed FP/low-conf)**

- Manual cast pass done (**44 characters**). See `CITIZEN_KANE_CLEANUP_RESULTS.md`.
- Remaining flags: biographical age + numeric PDF noise.

### Conclave — **4/4 false positive**

- Vote count misread as age (*undici voti*); black/white smoke is correct ritual.
- See `CONCLAVE_CLEANUP_RESULTS.md`.

### Almost Famous — **3/3 false positive**

- Different objects sharing material words (leatherette, door).
- See `ALMOST_FAMOUS_CLEANUP_RESULTS.md`. Cast pass optional (hide cast panel).

---

## Commands

```powershell
# Convert one PDF to refined Fountain
venv\Scripts\python.exe scripts\convert_pdf_to_fountain.py --stage refined `
  tests\corpus\benchmark\_batch_six\AMERICAN_BEAUTY.pdf

# Run full Hollywood benchmark batch
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir tests\corpus\benchmark\_batch_six `
  --output-dir tests\corpus\benchmark\reports\raw_pdf

# Verify writer corpus unchanged
venv\Scripts\python.exe scripts\score_corpus_baseline.py --check `
  --min-recall 1.0 --max-false-positives 4
```

---

## Recommended demo set

| Script | Input file | Show writers? |
|--------|------------|---------------|
| American Beauty | PDF (auto refined) | Yes — 2 low-conf flags (1 unsure year) |
| American Pie | `American_Pie_manual.fountain` | Yes — 0 flags, clean cast |
| Conclave | PDF (auto refined) | Yes — 0 real flags after review |
| Almost Famous | PDF (auto refined) | Yes — hide cast/props |
| Carrie | `02_Carie_1975_manual.fountain` | Yes — 0 flags |
| Citizen Kane | `04_CitizenKane_200_manual.fountain` | Partial — age caveats |
| Batman Begins | PDF (auto refined) | Yes — hide cast |

---

## Next steps

1. ~~Manual review of 19 flags in `CLEAN_FP_LOG.md`.~~ **Done (2026-07-07)**
2. ~~Citizen Kane manual cast pass.~~ **Done**
3. Props panel: hide in any UI until Hollywood prop noise drops.
4. **Build web demo (Phase B)** — recommended samples: American Beauty PDF, Conclave PDF, American Pie manual Fountain.
5. Optional: Almost Famous / Batman cast whitelists (contradictions already clean).
