# ScriptLens — Fine-Tuning & Product Backlog

**Purpose:** Single place to park engine tuning, writer-corpus findings, and
benchmark work **after** you review a full script submission. Revisit this
document when a writer package or Hollywood benchmark batch is complete.

**Last updated:** 2026-07-15  
**Owner:** Core engine / corpus evaluation

> **Product note (July 2026):** Customer v1 is the **structure-only** web app (orphans, simulate, draft). Contradiction tuning in this backlog applies to **internal CI**, not the customer UI.

---

## How to use this document

1. **During writer review** — Add rows under [Writer corpus findings](#writer-corpus-findings) with verdict ACCEPT / REVISE / REJECT.
2. **After full script evaluated** — Move ACCEPT items into [Engine tuning queue](#engine-tuning-queue) if `engine_detectable: false` today.
3. **Before implementing** — Run planted corpus check (`score_corpus_baseline.py --check --min-recall 1.0 --max-false-positives 4`).
4. **After implementing** — Move item to [Completed](#completed) with date and test file reference.

**Do not implement one-off rules for a single script.** Wait for **3+ similar
planted examples** (or clear corpus pattern) unless marked **Hotfix**.

---

## Revisit checklist (after entire script reviewed)

- [ ] All writer log entries have quotes + scene numbers verified against scene index
- [ ] Continuity errors counted separately from format/attribution (v2)
- [ ] Accepted errors copied to ground truth or writer evaluation folder
- [ ] `compare_writer_log.py` run on accepted continuity errors only
- [ ] Hollywood benchmark batch updated (if applicable)
- [ ] Items below re-prioritized (P0 / P1 / P2)
- [ ] `docs/ENGINE_REDESIGN.md` phase note updated if recall target changes

---

## Completed

| Item | Date | Notes |
|------|------|-------|
| `pdf_benchmark` input profile for `numeric_count` | 2026-06 | Generic number+noun pairing disabled; Carrie manual 15→0 flags |
| PDF/Fountain cleanup pipeline | 2026-06 | `cleanup_extracted_fountain.py`, `refine_manual_fountain.py` |
| `compare_writer_log.py` + `writer_log_eval.py` | 2026-06 | Writer answer sheet vs engine report |
| Carrie pilot results | 2026-06 | `tests/corpus/benchmark/CARRIE_CLEANUP_RESULTS.md` |
| Writer cleanup guide PDF | 2026-06 | `docs/writer_materials/FOUNTAIN_PDF_CLEANUP_GUIDE.pdf` |
| Families + exchange points `numeric_count` patterns | 2026-06 | Standard profile; corpus still 100% recall |

---

## Writer process (Gate 1 — not engine code)

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| W1 | Revised `ERROR_INJECTION_LOG` with `establishing_quote` / `contradicting_quote` | P0 | **Pending** | Send to all writers; reject logs without quotes |
| W2 | Brief paragraph: continuity required vs attribution optional (v2) | P0 | **Pending** | See conversation 2026-06-27 |
| W3 | `review_writer_submission.py` (scene index, quotes in script, diff vs base) | P1 | **Pending** | Structural pre-review before human read |
| W4 | Standard REVISE template for weak log entries | P1 | **Done (in chat)** | Reuse for errors #4, #5, **#8**, **#9**, etc. |
| W6 | Writer brief note: **slugline time** vs **action time** are valid continuity targets | P1 | **Pending** | #8 logged as cross-scene “Timeline Slip” but error is slugline NIGHT vs “Later in the Morning” in one scene |
| W5 | Optional 5-min audio only for flagged errors | P2 | **Pending** | Not required for corpus |

---

## Writer corpus findings

Log each planted error from writer submissions here **before** engine work.

| Script / scene | Category (writer) | Verdict | Engine today? | Backlog ID | Notes |
|----------------|-------------------|---------|---------------|------------|-------|
| Scene 10 store | Wrong dialogue speaker (Parker/Solomon) | REVISE log | No | **V2-A1** | Parker asks → SOLOMON has Parker lines; format, not v1 |
| Scene 16 tavern | Moon vs Hamilton at table | ACCEPT concept | Unlikely | **E1** | Presence / stage direction; needs quotes in log |
| Scene 16 tavern | Brown's dialogue (#4) | REVISE log | No | **V2-A1** | Too vague |
| Scene 29 kitchen | Property / chair (#5) | REVISE log | No | **—** | Empty objects; or reframe in/out action line |
| Scene 32 cell | Window / first light (# wrong description) | ACCEPT concept | No | **E2** | Window opens early vs Radburn opens later; **flagship example for E2** |
| Scene 32 cell | Radburn `(to Robert)` | TBD | No | **E3** or V2 | Robert not in scene — wrong addressee |
| **#8** Scene 42 cell | Timeline Slip (writer) | **REVISE log** / **ACCEPT concept** | No | **E5** | Writer means **slugline NIGHT** vs action “Later in the Morning.” Scene 44 “deep of EVENING” is fine progression — **not** a 42→44 slip. Recategorize as slugline vs action **within scene 42**; add slugline + action quotes. Eliza lament scene. |
| **#9** Scene 65 deck | Wrong Description (writer) | **REVISE log** / **ACCEPT concept** | **Yes** (E6 pattern) | **E6** | Blanket vs towel burial wrap — same-scene `object_referent_swap`. Engine now catches sewn/wrapped/placed/shoved-into thread swaps when nouns share a synonym group (blanket/towel, etc.). |
| **#10** Scene 83 ward | Wrong Description (writer) | **REVISE log** / **ACCEPT concept** | **No** (tested) | **E7** | Scene 83 opens on **Solomon + Clemens** in beds; action then says **“Eliza is nearly blind… His cries…”** — wrong character name and/or **Eliza + masculine “His”** mismatch. Scene 82 is generic ward intake (no Eliza); error is **within scene 83**, not 82→83. Recategorize as **Character Reference Mismatch**, both scenes **83**, quotes: `"Solomon lays in bed next to Clemens Ray…"` vs `"Eliza is nearly blind with pain and suffering. His cries are pitiable…"` Engine **misses today**: no name↔pronoun or wrong-subject-in-scene check. |

---

## Engine tuning queue

Implement **after** full script evaluation and when **3+ examples** exist (unless noted).

| ID | Feature | Priority | Trigger | Example | Implementation sketch |
|----|---------|----------|---------|---------|------------------------|
| **E1** | Character **presence** vs stage direction (who is in scene) | P1 | 3+ writer examples | Moon at table vs Hamilton drinks/speaks | Extract characters in opening action; compare to later action/speakers |
| **E2** | **Setting / fixture state** (window, door, light) + **within-scene order** | P1 | 3+ examples; **1 ready (scene 32)** | First light through window before “Opens the window some” | Facts: `window→open`, `first_light`; flag earlier open before explicit open in same scene |
| **E3** | Dialogue **addressee** mismatch `(to X)` when X absent | P2 | 3+ examples | `(to Robert)` but only Solomon present | Parenthetical vs `scene.characters` |
| **P4-K** | Remaining **character_knowledge** (4 misses in planted corpus) | P0 | Corpus CI | See `ENGINE_REDESIGN.md` P4 | Deterministic + optional LLM judge |
| **P4-O** | **object_identity** semantic / photo edge cases | P2 | Corpus miss list | 1 miss in redesign doc | Tier 2 or hardened patterns |
| **E4** | **Intra-scene** fact ordering (generalize beyond windows) | P2 | After E2 | Any “first time X” vs “X happens” later in scene | Ordered fact timeline per scene |
| **E5** | **Slugline time-of-day** vs action-line time (DAY/NIGHT/MORNING/EVENING) | P2 | 3+ examples; **1 ready (#8 scene 42)** | Slugline `- NIGHT` but action opens “Later in the Morning.” | Parse slugline time token; compare to time phrases in first action block(s) of same scene |
| **E6** | **Same-referent prop, different head noun** (blanket → towel) | P2 | **Done** — 3 planted + `object_referent_swap` detector | Sewn/wrapped/placed/shoved into X then Y (same scene) | Action-thread patterns + synonym groups; see `tests/test_object_referent_swap.py` |
| **E7** | **Wrong character in action** + **name/pronoun agreement** (Eliza + His) | P2 | 3+ examples; **1 ready (#10 scene 83)** | Solomon/Clemens in bed, then “Eliza… His cries” | Track scene focal characters; flag named subject inconsistent with prior sentence subjects or pronoun gender |

**Not v1 — park in v2:**

| ID | Feature | Notes |
|----|---------|-------|
| **V2-A1** | Dialogue **cue vs action** speaker mismatch | Parker store; Brown/Hamilton ping-pong; customer value later, Fountain-first |
| **V2-F1** | PDF **format hygiene** on raw extracts | Overlaps cleanup scripts; don’t tune continuity engine on PDF cue noise |

---

## Benchmark & infrastructure

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| B1 | Run cleanup + benchmark on **Batman Begins** | P1 | **Pending** | Same pipeline as Carrie |
| B2 | Run cleanup + benchmark on **Citizen Kane** | P1 | **Pending** | |
| B3 | Run cleanup + benchmark on **Conclave** | P1 | **Pending** | |
| B4 | Fill `MANIFEST.md` + `CLEAN_FP_LOG.md` from batch | P1 | **Pending** | |
| B5 | Commit benchmark infra + `pdf_benchmark` + writer tools (PR) | P2 | **Pending** | User decision |
| B6 | Crime + noir **100%** recall patterns — commit if local only | P2 | **Verify git** | |

---

## Product / positioning (no code)

| Decision | Status |
|----------|--------|
| v1 = **story continuity** only in marketing and writer brief | **Agreed** |
| Ground truth = planted **continuity** errors; Hollywood = no ground truth (FP benchmark) | **Agreed** |
| `standard` profile for writer `.fountain`; `pdf_benchmark` for PDF / clean benchmark | **Agreed** |
| Don’t tune engine on single-script one-offs | **Agreed** |

---

## Commands reference

```powershell
# Planted corpus (must stay green after any engine change)
venv\Scripts\python.exe scripts\score_corpus_baseline.py --check --min-recall 1.0 --max-false-positives 4

# Writer script vs log (after Gate 1 ACCEPT)
venv\Scripts\python.exe scripts\compare_writer_log.py script.fountain ERROR_LOG.yaml --output evaluation.txt

# Hollywood / clean benchmark
venv\Scripts\python.exe scripts\run_clean_benchmark.py

# Single script (Fountain = standard; PDF = pdf_benchmark by default)
venv\Scripts\python.exe run_scriptlens.py path\to\script.fountain
```

---

## Related docs

- `docs/ENGINE_REDESIGN.md` — Phases P1–P4, corpus metrics
- `docs/CORPUS_EVALUATION_GUIDE.md` — Ground truth workflow
- `docs/SCREENWRITER_ERROR_INJECTION_GUIDE.md` — Writer-facing categories
- `docs/internal/CATEGORY_TO_ENGINE_MAPPING.md` — Log → engine type
- `tests/corpus/benchmark/CARRIE_CLEANUP_RESULTS.md` — PDF cleanup pilot
- `tests/corpus/benchmark/README.md` — Hollywood benchmark layout

---

*Add new rows as you finish each writer script review. Revisit this file before starting the next tuning sprint.*
