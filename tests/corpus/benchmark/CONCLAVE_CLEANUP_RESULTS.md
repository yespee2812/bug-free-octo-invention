# Conclave (2024) — Benchmark Review Results

Script: `05_Conclave_2004.pdf.pdf` → PDF → `refined` Fountain → `pdf_benchmark` analysis.

**Date:** July 2026  
**Review type:** Contradiction false-positive review

---

## Summary

| Metric | Value |
|--------|------:|
| Scenes | 156 |
| Contradiction flags | **4** |
| Health score | 47 |
| All flags verdict | **4/4 false positive** |

**Pre-pipeline (Jul 4 raw):** 4 flags → **4 flags** (same count; pipeline did not introduce new issues).

---

## Per-flag review

| # | Type | Scenes | Engine claim | Verdict | Why |
|---|------|--------|--------------|---------|-----|
| 1 | character_age | 98 vs 101 | CARDINAL LAWRENCE age **30** vs **11** | **FP** | Scene 101 is ballot reading: *"Cardinale Lawrence: **undici voti**"* (11 **votes** in Italian). Engine misread vote count as age. Scene 98 has no Lawrence age statement. |
| 2 | object_identity | 68 vs 150 | smoke **black** vs **white** | **FP** | Intentional conclave ritual: **black smoke** = no pope (scene 68); **white smoke** = pope elected (scene 150). Correct story progression, not a continuity error. |
| 3 | numeric_count | 72 vs 96 | rank **3** vs **1** | **FP** | Scene 72 dialogue: *"**Third place**. Not what we had hoped."* — election position, not a persistent count entity. |
| 4 | numeric_count | 96 vs 104 | rank **1** vs **3** | **FP** | Scenes 96/104: cardinal vote tallies and support discussions. PDF/ballot prose, not a contradictory rank fact. |

---

## Cast list

~30 labels; mostly real cardinal names. Minor junk: `CONCLAVE`, `ON LAWRENCE`, `TITLES BEGIN` — acceptable for demo if cast panel is shown; contradictions are the main trust surface.

---

## Engine follow-up (backlog — not implemented)

| ID | Pattern | Example |
|----|---------|---------|
| C1 | Age vs ballot votes | `undici voti`, `eleven votes` after cardinal name |
| C2 | Smoke color | Black/white smoke as conclave signals (suppress object_identity) |

Wait for **3+ similar examples** before tuning (project rule).

---

## Safe to demo?

| Panel | Ready? |
|-------|--------|
| Contradictions | **Yes** — all 4 reviewed FPs; explain smoke if shown |
| Cast list | **Partial** — mostly clean |
| Props list | **No** — hide |

---

## Commands

```powershell
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir tests\corpus\benchmark\_batch_six `
  --output-dir tests\corpus\benchmark\reports\raw_pdf
```

Report: `tests/corpus/benchmark/reports/raw_pdf/05_Conclave_2004.pdf_report.txt`
