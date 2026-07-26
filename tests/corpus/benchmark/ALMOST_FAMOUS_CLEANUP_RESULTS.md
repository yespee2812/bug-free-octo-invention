# Almost Famous (2000) — Benchmark Review Results

Script: `ALMOST_FAMOUS.pdf` → PDF → `refined` Fountain → `pdf_benchmark` analysis.

**Date:** July 2026  
**Review type:** Contradiction false-positive review (cast pass not yet done)

---

## Summary

| Metric | Value |
|--------|------:|
| Scenes | 186 |
| Contradiction flags | **3** |
| Health score | 0 (orphans + flags penalty) |
| All flags verdict | **3/3 false positive** |

**Pre-pipeline (Jul 4 raw):** 11 flags → **3 flags** after refined + `pdf_benchmark`.

---

## Per-flag review

| # | Type | Scenes | Engine claim | Verdict | Why |
|---|------|--------|--------------|---------|-----|
| 1 | object_identity | 14 vs 74 | leatherette **black** vs **red** | **FP** | Scene 14: William's black leatherette *travel bag*. Scene 74: hotel lobby *red-leatherette chairs*. Different objects, same material adjective. |
| 2 | object_identity | 25 vs 75 | door **steel** vs **glass** | **FP** | Scene 25: sports arena ramp (no single story door). Scene 75: hotel room *sliding glass door* to pool. Different locations. |
| 3 | numeric_count | 60 vs 163 | seating **0** vs **1000** | **FP** | Scene 60: hotel lobby key handoff. Scene 163: Penny's dialogue — *"a thousand people had the same idea"* at a concert. Not a seating count. |

---

## Cast list (not yet cleaned)

Engine reports **~70 character labels** with PDF junk, e.g. `ON RUSSELL`, `HANDHELD ON RUSSELL`, `HIGH-SCHOOL MARQUEE`, `ALMOST FAMOUS`.

**Do not show raw cast panel to writers.** Contradiction output is trustworthy after review above.

**Future (optional):** American Pie–style manual cast whitelist if Almost Famous is a demo script.

---

## Safe to demo?

| Panel | Ready? |
|-------|--------|
| Contradictions | **Yes** — 0 real flags after review |
| Cast list | **No** — needs manual pass |
| Props list | **No** — hide |

---

## Commands

```powershell
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir tests\corpus\benchmark\_batch_six `
  --output-dir tests\corpus\benchmark\reports\raw_pdf
```

Report: `tests/corpus/benchmark/reports/raw_pdf/ALMOST_FAMOUS_report.txt`
