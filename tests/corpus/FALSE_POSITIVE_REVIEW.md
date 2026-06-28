# False Positive Review — Planted-Error Corpus

Review date: 2026-06-27  
Baseline after fixes: **80/100 recall**, **2 corpus-level false positives** (82 detected, 80 matched).

Corpus-level false positives = engine contradictions whose `(type, {scene_a, scene_b})`
does not match any planted error. Per-script evaluation files live in
`tests/corpus/reports/*_evaluation.txt`.

## Summary

| Script | Extra detections | Verdict | Action |
|--------|------------------|---------|--------|
| family_5scene_errors | 2 | **Fixed** | Engine bugs (see below) |
| adventure_5scene_errors | 1 | **Accepted** | Valid prose slip, not planted |
| adventure_10scene_errors | 1 | **Accepted** | Intermediate chain in meter arc |
| heist_5scene_errors | 1 | **Fixed** | Duration seconds ≠ count noun |
| thriller_10scene_errors | 1 | **Fixed** | “every one of them” ≠ headcount |

After fixes, CI allows **≤ 4** false positives (two accepted adventure meter catches).

---

## family_5scene_errors (2 → 0 after fix)

### 1. `relationship_fact` sc1 vs sc2 — Antonio

- **Engine said:** Antonio has incompatible `parent_child` + `sibling`.
- **Problem:** Same character being someone’s child *and* someone’s sibling is normal.
- **Fix:** Character-level check now uses `SINGLE_CHARACTER_INCOMPATIBLE` (excludes
  parent/child + sibling).

### 2. `character_age` sc3 vs sc3 — Raul 65 vs 18

- **Engine said:** Raul age 65 and 18 in the same scene.
- **Problem:** Action line “table set for eighteen” matched `For N` age dialogue pattern;
  coref attached 18 to Raul on the same line as “RAUL MORALES, 65”.
- **Fix:** `For N` age extraction runs on **dialogue lines only**; same-scene age
  pairs are skipped in the checker.

---

## adventure_5scene_errors (1 — accepted)

### `numeric_count` sc2 vs sc5 — 50m vs 40m

- **Engine said:** Meters 50 (sc2, father turned back fifty meters) vs 40 (sc5, peak wrong by forty meters).
- **Verdict:** Legitimate continuity note in the script text; not one of the two planted errors (year + envelope).
- **Action:** Keep as **bonus catch**. Writers may find it useful; not added to ground truth.

---

## adventure_10scene_errors (1 — accepted)

### `numeric_count` sc4 vs sc8 — 50m vs 60m

- **Engine said:** Intermediate step in the meter timeline (50 → 60 → 40 planted at sc8/sc10).
- **Verdict:** Chain checker emits each value transition; planted pair sc8/sc10 is still matched.
- **Action:** Keep as **bonus catch**.

---

## heist_5scene_errors (1 → 0 after fix)

### `numeric_count` sc2 vs sc3 — 12 vs 30

- **Engine said:** “twelve-second gaps” vs “Thirty seconds” as the same count entity.
- **Problem:** Duration phrases are not head-count continuity.
- **Fix:** Added `second` / `seconds` to `COUNT_NOUN_BLOCKLIST`.

---

## thriller_10scene_errors (1 → 0 after fix)

### `numeric_count` sc5 vs sc7 — GROUP 1 vs 5

- **Engine said:** “every **one** of them” parsed as GROUP count = 1.
- **Problem:** Idiom “every one of them is burned”, not a headcount of one.
- **Fix:** `(?<!every )` guard on `N of them` count pattern.

---

## How to re-run this review

```powershell
venv\Scripts\python.exe scripts\run_corpus_batch.py --compare-ground-truth
venv\Scripts\python.exe scripts\score_corpus_baseline.py
```

Check per-script extras:

```powershell
Select-String -Path tests\corpus\reports\*_evaluation.txt -Pattern "Extra \(false positives\):     [1-9]"
```

CI enforces: `recall >= 80%`, `false positives <= 4`.
