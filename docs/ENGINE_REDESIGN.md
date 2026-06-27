# ScriptLens Contradiction Engine — Redesign

Status: **in progress (P1 complete, P2 underway)** · Owner: core engine · Last updated: 2026-06

This document captures (1) the measured baseline, (2) a root-cause analysis of
why the current engine fails on natural prose, (3) the target architecture, and
(4) a sequenced implementation plan. It is the reference for the rewrite that
begins with **entity canonicalization** and **value normalization**.

---

## 1. Baseline (measured)

A 40-script corpus (20 genres × 5-scene + 10-scene) with **100 planted errors**
in natural, screenwriter-style prose was run through the core engine.

| Metric | Result |
|---|---|
| Planted errors | 100 |
| Detected (any) | 0 |
| True positives | 0 |
| False positives | 0 |
| **Recall** | **0.0%** |
| Recall on engine's *own* supported types | **0.0% (0/9)** |

Reproduce with:

```powershell
venv\Scripts\python.exe scripts\run_corpus_batch.py --compare-ground-truth
venv\Scripts\python.exe scripts\score_corpus_baseline.py
```

Artifacts: `tests/corpus/BASELINE_SCORE.md`, `tests/corpus/PLANTED_ERROR_LOG.md`,
`tests/corpus/reports/`.

---

## 2. Root-cause analysis

### 2.1 Two failure modes

| Mode | Errors | Cause |
|---|---|---|
| **A. Capability gap** — no fact type exists | ~82 | Detection impossible by design |
| **B. Extraction brittleness** — pattern too narrow | ~18 | Capability exists; phrasing missed |

**Bucket A (no extractor exists):** `numeric_count` (28), `object_identity` (16),
`character_age` (13), `date_year` (8), `character_knowledge` (8),
`location_continuity` (4), `name_consistency` (2), `character_fact`/`fact_consistency` (3).

**Bucket B (exists but missed):** `object_ownership` (6), `relationship` (9),
`character_trait_conflict` (2), `medical_state` (1).

### 2.2 Concrete code evidence (Bucket B)

- **Ownership** fires only on `OWNER <verb> object` where the verb is a closed
  whitelist (`has, grabs, holds, pockets, carries, takes, hides, steals, drops`,
  + `picks up / sets down / gives / hands`). Natural verbs like `keeps`, `clips`,
  `pulls`, `sits in`, and possessive `Tom's guest book` never match.
- **Trait** fires only on `X is a <trait>`, `X works as <trait>`, and a
  fixture-specific `X, the city's best <trait>, entered`. Appositives like
  `CLAIRE HART, 32, novelist` and `Claire, the poet,` match nothing.
- **Relationship** expects `PERSON is PERSON's <rel>` / `PERSON, PERSON's <rel>,`.
  Natural possessor-first order (`Antonio's sister Diana`) and pronouns
  (`Alma, his sister`) are not matched / are rejected (no coreference).
- **Medical** requires copula + condition + `in the <part>` (or `breaks his leg`).
  `Kowalski hit, shoulder` / `bind Kowalski's leg` match nothing.

### 2.3 Cross-cutting weaknesses (hurt every category)

1. **No entity canonicalization.** Pronouns rejected; possessive order not
   normalized; name drift creates new entities; aliases (`Eddie` /
   `Captain Eddie Moran`) not unified. Cross-scene facts cannot line up.
2. **No value normalization.** Comparisons are string-level: `three` ≠ `3`,
   `1987` vs `1985` never computed, `silver band` ≠ `silver wedding band`.
3. **Surface-pattern, fixture-driven extraction.** Tier 2 (spaCy similarity) is
   inert because `en_core_web_sm` ships no word vectors.

### 2.4 Meta-cause

The engine was built test-first against a single hand-crafted fixture
screenplay. Each regex was added to pass one sentence, never generalized
(the `the city's best … entered` trait pattern is the clearest proof). Result:
~100% on its own fixtures, ~0% on natural prose, 0 false positives because it
rarely fires — precision is "free" only because the system is mostly silent.

---

## 3. Target architecture

Replace the monolithic regex pipeline with a layered pipeline where each layer
has one job and is independently testable.

```
              ┌─────────────────────────────────────────────┐
  screenplay  │ 1. Parse  → scenes, action vs dialogue        │
      │       └─────────────────────────────────────────────┘
      ▼
┌──────────────────────┐   ┌──────────────────────────────────┐
│ 2. Entity            │   │ 3. Value normalization            │
│    canonicalization  │   │  number words→int, years, ages,   │
│  cue/alias registry, │   │  colors/materials, descriptors    │
│  title & possessive  │   └──────────────────────────────────┘
│  stripping, name-    │                  │
│  drift detection     │                  │
└──────────────────────┘                  │
      │                                    │
      ▼                                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Fact extraction → typed facts                              │
│    {entity_id, attribute, value(normalized), scene,           │
│     evidence_span, source}                                    │
│    (deterministic rules now; LLM-assisted later)              │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Contradiction reasoning over the fact timeline             │
│    per (entity, attribute): flag value change without a       │
│    sanctioned transition; keep false-positive guards          │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
   6. Report  (+ evaluation against ground truth / clean control)
```

Layers 2 and 3 are **foundations**: every fact type depends on them. They are
built first, as standalone modules with **no spaCy / heavy imports**, so they
stay fast and unit-testable.

### 3.1 New fact model (target)

```python
@dataclass(frozen=True)
class Fact:
    entity_id: str          # canonical id from the EntityRegistry
    attribute: str          # "alive", "age", "owner", "material", "count", ...
    value: NormalizedValue  # typed + comparable (int, year, descriptor set, ...)
    scene_number: int
    evidence: str           # the source span, for citations
    source: str             # "action" | "dialogue"
```

Contradiction = two facts with the same `(entity_id, attribute)` whose
normalized values are incompatible and no sanctioned transition explains the
change.

---

## 4. Sequenced plan

| Phase | Deliverable | Recovers |
|---|---|---|
| **P0 ✅ done** | `entity_canonicalization.py`, `value_normalization.py` + tests | foundation only |
| **P1 ✅ done** | New deterministic extractors on top of P0: `age`, `object_identity`, `numeric_count`, `date_year` | **38/100 caught**, 92.7% precision |
| **P2** | Widen + re-base existing extractors (ownership verbs, trait appositives, relationship possessor-order, medical phrasing) through P0 | ~18 errors (Bucket B) |
| **P3** | Entity-aware reasoning: relationship via canonical pairs, name-drift report, location-of-thing | ~15 errors |
| **P4** | LLM-assisted extraction + judge pass for `character_knowledge` and implied relations | remainder |

### 4.1 Evaluation discipline (every phase)

- Re-run `score_corpus_baseline.py` → compare recall vs this 0% baseline.
- Run the engine on the **clean, un-injected starters** in
  `docs/genre_starter_scripts/` to track the **false-positive rate**; recall
  gains must not silently destroy precision.
- Consider upgrading spaCy to `en_core_web_md`/transformer if similarity checks
  are retained.

---

## 5. Foundations being built now (P0)

### 5.1 `entity_canonicalization.py`

- `normalize_name(raw)` — uppercase, collapse spaces, strip punctuation,
  parentheticals, and possessive `'s`.
- `EntityRegistry`:
  - `register(name)` → canonical id, merging alias variants
    (full, article-stripped, title-stripped, first/last token).
  - `resolve(mention)` → canonical id or `None` (handles titles, possessives,
    partial names; unique-token disambiguation).
  - `near_duplicate_pairs(max_distance)` → candidate **name-drift** pairs to
    *report* (not silently merge), enabling `name_consistency` detection.

### 5.2 `value_normalization.py`

- `words_to_int` / `extract_count` — number words + digits → `int`.
- `extract_age` — `", 12"`, `twelve`, `ten-year-old`, `barely forty`, `for eleven`.
- `extract_year` — 4-digit years and apostrophe years (`'94` → 1994).
- descriptor vocab (`COLORS`, `MATERIALS`) + `descriptor_axes(text)` and
  `descriptors_conflict(a, b)` for `object_identity`.

Both modules are pure-Python, fully typed, documented, and covered by unit tests
in `tests/`.

---

## 6. Progress log

### P1 — first detectors on the foundations (`age`, `object_identity`)

Wired the foundation layers into `plot_contradiction.py` and shipped the two
highest-precision detectors first to validate the architecture before tackling
the noisier `count` / `date_year` families.

- **Entity registry per script** (`_build_entity_registry`) from every character
  cue; later mentions (`Eddie`, `Captain Eddie Moran`) resolve to one id.
- **Age extractor** (`_extract_age_facts` + `_parse_head_age`): appositive
  `Name, <age>` with digit / number-word / `Ns` decade forms and hedge words
  (`barely forty`). The age must be the **head** of the clause, so pronouns like
  `this one` and `on a Tuesday` can never be misread as age 1.
- **Object-identity extractor** (`_extract_object_descriptor_facts`): records
  `(prop head noun, axis:token)` from colour/material descriptors; the
  contradiction check compares each later descriptor against the **first**
  descriptor per axis, so a recurring baseline never double-counts.
- Both detectors emit `status = possible` (writer-confirm), since long time
  jumps / distinct same-named props can be legitimate.

**Measured impact** (`scripts/score_corpus_baseline.py`):

| Metric | Baseline | After P1 (age + identity) |
|---|---|---|
| Recall | 0.0% | **17.0%** (17/100) |
| Precision | n/a (silent) | **100.0%** (17/17) |
| F1 | 0.0% | **29.1%** |
| `character_age` recall | 0% | **54%** (7/13) |
| `object_identity` recall | 0% | **62%** (10/16) |
| False positives on 40 **clean** starters | 0 | **0** |

Remaining age/identity misses need coreference (pronoun/role-noun ages like
"the ten-year-old") or object-swap reasoning (thimble→coin), deferred to P3/P4.

**Tests:** `tests/test_age_identity_extraction.py` (13 cases) + the P0 module
tests; full suite 85 passing.

### P1 (cont.) — `numeric_count` and `date_year`

- **Year detector** (`_extract_year_facts` + `_check_date_year`): scans the full
  scene text (slug lines included), normalizes apostrophe years (`'94` → 1994),
  and only fires when a script asserts **exactly two distinct years within
  `MAX_YEAR_GAP` (10)** — a likely slip, not an intentional multi-period story.
- **Count detector** (`_extract_count_facts` + `_check_numeric_count`): pairs a
  number run (`three hundred`) with its head noun; singularizes (`runs`→`run`)
  so counts align across scenes. Guards: clock times and 4-digit years are
  stripped first; appositive-comma numbers (`Dawson, 45`) are skipped so ages
  never leak in; the noun-before-number fallback is limited to a whitelist of
  identifier nouns (`Room 514`); a blocklist drops free-varying nouns
  (`minute`, `day`, `time`, …); only the **first divergence per noun** is
  reported, as `possible`.

**Measured impact (full P1):**

| Metric | Baseline | After P1 |
|---|---|---|
| Recall | 0.0% | **38.0%** (38/100) |
| Precision | — | **92.7%** (38/41) |
| F1 | 0.0% | **53.9%** |
| `date_year` | 0% | **100%** (8/8) |
| `object_identity` | 0% | **62%** (10/16) |
| `character_age` | 0% | **54%** (7/13) |
| `numeric_count` | 0% | **46%** (13/28) |
| FPs on 40 clean starters | 0 | **4** (all `numeric_count`) |

**Honest limitation — `numeric_count` precision.** Counts legitimately change
in a story (hostages rescued, a measurement re-stated, a race time). The 3
corpus + 4 clean false flags are all *real count changes* the engine cannot
distinguish from errors without intent. Blocklisting the offending nouns
(`meter`, `second`) would also kill the planted war/heist catches, so the count
detector stays **low-confidence `possible`** rather than asserted. This is the
precision/recall tension that the eventual LLM judge pass (P4) should arbitrate.

**Tests:** `tests/test_count_year_extraction.py` (14 cases); full suite 99 passing.
```
