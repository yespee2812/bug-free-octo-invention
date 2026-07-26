# Clean Produced Scripts — False Positive Log

Manual review log for Hollywood benchmark scripts.  
**Pipeline (Jul 2026):** PDF → `refined` Fountain → analyse with `pdf_benchmark`.

**Goal:** Low false-positive rate on real produced screenplays (writer trust).

**Last batch run:** 2026-07-07  
**Scripts analysed:** 6  
**Total contradiction flags:** **19**  
**Reviewed flags:** **19/19**  
**Confirmed real slips on clean scripts:** **0**  
**Profile:** `pdf_benchmark` · `pdf_conversion=refined`

See **`HOLLYWOOD_BENCHMARK_RESULTS.md`** for demo recommendations.

---

## Summary

| Script | Scenes | Flags | Reviewed | Real slips | Demo contradictions? |
|--------|--------|------:|----------|------------|----------------------|
| American_Pie | 210 | **0** | yes | 0 | **Yes** (manual cast) |
| AMERICAN_BEAUTY | 162 | **2** | yes | 0 | **Yes** (1 unsure year) |
| 01_batmanBegins_2005 | 320 | **0** | yes | 0 | **Yes** (hide cast) |
| ALMOST_FAMOUS | 186 | **3** | yes | 0 | **Yes** (hide cast) |
| 05_Conclave_2004 | 156 | **4** | yes | 0 | **Yes** |
| 04_CitizenKane_200 | 99 | **10** | yes | 0 | **Partial** (age caveats) |
| Carrie (prior) | 82 | **0** | yes | 0 | **Yes** (manual cast) |

Reports: `tests/corpus/benchmark/reports/raw_pdf/manifest.csv`

**Verdict:** Hollywood benchmark review **complete**. All 19 flags assessed; **none are confirmed real continuity errors** on these produced scripts. Input quality phase done for contradictions; optional cast passes remain for Almost Famous and Batman.

---

## Per-script review

### `American_Pie` — **Complete**

See `AMERICAN_PIE_CLEANUP_RESULTS.md`. **0 flags** · manual cast · demo-ready.

---

### `AMERICAN_BEAUTY` — **Complete**

| # | Type | Scenes | Verdict | Notes |
|---|------|--------|---------|-------|
| 1 | date_year | 72 vs 100 | **Unsure** | 1973 vs 1970 — may be intentional structure |
| 2 | numeric_count (rank) | 148 vs 148 | **FP** | Same-scene PDF noise |

**Demo:** Yes (note flag 1 if shown).

---

### `01_batmanBegins_2005` — **Complete**

**0 flags.** Hide cast list (PDF junk).

---

### `ALMOST_FAMOUS` — **Complete (2026-07-07)**

See `ALMOST_FAMOUS_CLEANUP_RESULTS.md`.

| # | Type | Scenes | Verdict | Notes |
|---|------|--------|---------|-------|
| 1 | object_identity (leatherette) | 14 vs 74 | **FP** | Travel bag vs lobby chairs |
| 2 | object_identity (door) | 25 vs 75 | **FP** | Arena vs hotel glass door |
| 3 | numeric_count (seating) | 60 vs 163 | **FP** | "Thousand people" dialogue |

**Demo:** Yes for contradictions; hide cast/props.

---

### `05_Conclave_2004` — **Complete (2026-07-07)**

See `CONCLAVE_CLEANUP_RESULTS.md`.

| # | Type | Scenes | Verdict | Notes |
|---|------|--------|---------|-------|
| 1 | character_age | 98 vs 101 | **FP** | *Undici voti* (11 votes) misread as age |
| 2 | object_identity (smoke) | 68 vs 150 | **FP** | Black vs white smoke = valid conclave ritual |
| 3 | numeric_count (rank) | 72 vs 96 | **FP** | "Third place" dialogue |
| 4 | numeric_count (rank) | 96 vs 104 | **FP** | Ballot/support prose |

**Demo:** Yes; optional note on smoke if educating writers.

---

### `04_CitizenKane_200` — **Complete**

See `CITIZEN_KANE_CLEANUP_RESULTS.md`. Manual cast **44 characters**. **10 flags** — biographical age + numeric noise; **0 confirmed real**.

---

## Aggregate by contradiction type (all scripts)

| Type | Count | Reviewed FP | Unsure | Action |
|------|------:|------------:|-------:|--------|
| character_age | ~15 | ~15 | 0 | Kane biography; Conclave votes-as-age (backlog C1) |
| object_identity | ~4 | ~4 | 0 | Generic noun / different objects |
| numeric_count | ~7 | ~7 | 0 | PDF prose / dialogue |
| date_year | 1 | 0 | 1 | American Beauty only |
| object_ownership | 0 | — | — | POV guardrail worked |
| name_consistency | 0 | — | — | Hyphen guardrail worked |
| character_trait | 0 | — | — | Junk-entity filter worked |

---

## Re-run

```powershell
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir tests\corpus\benchmark\_batch_six `
  --output-dir tests\corpus\benchmark\reports\raw_pdf
```

---

## Next (post-review)

1. **Web demo (Phase B)** — use American Beauty, American Pie manual, Conclave PDF.
2. **Optional cast passes** — Almost Famous, Batman (contradictions already clean).
3. **Engine backlog** — Conclave votes-as-age (C1); only after 3+ planted examples.
