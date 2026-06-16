# ScriptLens Core Engines — Technical Review & Improvement Report

| Field | Value |
|-------|-------|
| **Scope** | `scene_dependency.py`, `plot_contradiction.py`, `scriptlens_analyser.py`, `pdf_screenplay_loader.py` |
| **Date** | June 13, 2026 |
| **Audience** | Engineering (you) — what the engines do today, where they are weak, and what to fix next |
| **Status of code** | Tier 1 + Tier 2 contradiction and full dependency engine implemented; recent Caveat-1 and Caveat-2 (partial) fixes committed |

---

## 1. Executive summary

ScriptLens Core is a **deterministic, rule + NLP screenplay analysis backend**. It has two engines:

1. **Scene Dependency Engine** — builds a directed graph of how scenes rely on each other (shared characters, props, locations) and answers "what breaks if I cut this scene?"
2. **Plot Contradiction Engine** — extracts structured facts and flags continuity conflicts (dead-then-alive, timeline, role/profession, object possession).

Both are **working and passing their current test suites** (contradiction precision/recall/F1 = 1.00 on the bundled fixtures). However, both rely heavily on **regex patterns + spaCy `en_core_web_sm`**, and that creates a consistent class of weaknesses: **narrow pattern coverage (recall gaps)** and **occasional over-capture (precision gaps)**. The single highest-leverage area to invest in next is a **labeled evaluation corpus**, because almost every remaining improvement (recurrence promotion, grammatical-role detection, Tier-2 thresholds, Tier-3 LLM) needs real precision/recall numbers to tune safely.

---

## 2. What the engines do today

### 2.1 Pipeline (orchestration)

`scriptlens_analyser.analyze_screenplay()` runs:

```
screenplay_text
  → SceneDependencyEngine.parse_fountain_text()   # scenes: characters/objects/locations
  → SceneDependencyEngine.build_graph()            # directed dependency graph
  → ContradictionEngine.run_analysis()             # facts → Tier 1 → Tier 2 → dedup
  → assemble report (summary, high-risk scenes, contradictions, health score)
```

Input can be Fountain/plain text or PDF (`pdf_screenplay_loader.py` → text via PyMuPDF/`fitz`).

### 2.2 Scene Dependency Engine — current behavior

**Parsing (`parse_fountain_text`)**
- Splits the script on scene headings: `INT.`, `EXT.`, `INT/EXT.`, `I/E.`.
- Per scene it extracts:

| Field | How it is detected today |
|-------|--------------------------|
| **Characters** | (a) ALL-CAPS dialogue cues; (b) caps spans in action that match a known cue; (c) multi-word caps spans starting with a **title** (`DETECTIVE`, `AGENT`, …); (d) **structural names** from fact phrasing ("`KESSLER is a surgeon`", "`COLE is dead`") — *added in the recent Caveat-2 fix*. |
| **Objects (props)** | (a) ALL-CAPS spans in action (screenwriting convention); (b) **objects of ownership verbs** "picks up / has / gives … to" even when lowercase (e.g. "the blue ledger") — *Caveat-1 fix*; (c) later lowercase mentions matched back to a known prop by exact or suffix match. |
| **Locations** | Primary place from the heading (text before `-`), uppercased. |

**Graph (`build_graph`)**
- Directed graph; a node per scene.
- "**First-seen**" model: when an entity first appears it is recorded; each later scene that reuses it gets an edge **from the first scene**.
- Edge weights: `character 1.0`, `object 0.7`, `location 0.4` (`fact 0.5` defined but **unused**). Multiple signals between the same pair sum their weights.

**Queries**
- `get_scene_dependencies` (upstream / ancestors), `get_delete_impact` (downstream / descendants), `get_orphan_scenes` (in-degree 0, excluding `scene_001`), `export_graph_summary`, plus high-risk ranking in the analyser.

### 2.3 Plot Contradiction Engine — current behavior

**Fact extraction (`extract_facts`)** — from **action lines only** (timeline also reads dialogue):

| Fact type | Trigger patterns | Key guards |
|-----------|------------------|------------|
| `character_status` | "X is/was dead/killed", "X died" | `DEAD_IDIOM_FOLLOWERS` ("dead tired", "dead ahead"…) |
| `character_trait` | "X is a <role>", "X works as <role>", one bespoke "the city's best …" pattern | `GENERIC_TRAIT_TERMS` ("good man", "kid"…) |
| `timeline` | "Today/It is <weekday>", "Yesterday was <weekday>", "N days later" | `TIME_OF_DAY_FOLLOWERS`, flashback markers |
| `object_ownership` | "picks up / has / gives … to" | dialogue excluded |
| `location` | heading + "the <place> was/had been <state>" | — |

**Detection tiers**

| Tier | Method | Status |
|------|--------|--------|
| **Tier 1** | Deterministic rules: `character_alive_status`, `timeline_consistency`, `character_trait_conflict`, `object_ownership` (with handoff detection) | Implemented |
| **Tier 2** | spaCy similarity between same-entity/same-type facts below a threshold; opposing-state term boost; skips Tier-1-covered pairs | Implemented |
| **Tier 3** | Claude Haiku for ambiguous cases | **Not implemented** |

**Health score**: `100 − (contradictions × 8) − (orphans × 3)`, floored at 0.

---

## 3. Recent improvements (this work)

| Caveat | What was fixed | Commit |
|--------|----------------|--------|
| **Caveat 1** — lowercase props missed | Objects of ownership/handling verbs are now tracked even when never capitalized (e.g. "the blue ledger"), with suffix-based canonicalization of later mentions. | `485db26` |
| **Caveat 2 (partial)** — cue-less characters | Title lexicon + title-case NER re-check (already present) **plus** new structural detection: the subject of "is dead / died / works as / is a `<role>`" is treated as a character, so a cue-less ALL-CAPS name is no longer misclassified as a prop. Pronoun / inanimate-death / generic-role guards keep it precise. | `4d1c8a4` |

---

## 4. Caveats & limitations (where the engines are weak)

### 4.1 Scene Dependency Engine

| # | Caveat | Impact | Severity |
|---|--------|--------|----------|
| D1 | **Tiny ownership-verb list** (only `picks up`, `has`, `gives … to`). Handling verbs from the design (grabs, holds, hands, pockets, carries, takes, hides, steals, drops, sets down) are not covered. | Lowercase props introduced via other verbs are still missed. | Medium |
| D2 | **NER-detected characters in action are excluded from props but never added as characters.** A cue-less, title-less name that *only* NER catches creates **no character edges** — it is silently dropped. | Recall gap in the dependency graph. | Medium |
| D3 | **ALL-CAPS is exactly where spaCy NER is weakest** (root of Caveat 2). Signal 3 (grammatical-role / agentive-subject detection) is **not yet implemented**. | Invented names with no title and no fact phrasing are missed or mis-typed. | Medium |
| D4 | **First-seen-only edges.** Reuse links back to the *first* scene, not each prior scene. Deleting an intermediate scene won't show downstream breakage that conceptually flows through it. | `get_delete_impact` can under-state ripple effects on chained setups. | Medium |
| D5 | **Suffix prop-matching can over-merge.** "THE KEY" could resolve to "SILVER KEY" *or* "MASTER KEY" (first match wins). | Wrong prop edges when two props share a head noun. | Low–Med |
| D6 | **`fact` and `causal` dependency edges are unimplemented** (`fact` weight exists but is never produced; causal/dialogue edges from the spec are absent). | Story dependencies carried by dialogue ("after what you did") are invisible. | Medium |
| D7 | **Performance: up to 2 spaCy passes per scene** (`nlp(action_text)` + a second pass on title-cased text), and the model is loaded **separately in each engine**. | ~2× NLP cost; risk against the <400ms/<800ms SLA on 120-scene scripts. | Medium |
| D8 | **Locations are single-level** (primary place only; time-of-day and sub-locations dropped). | "INT. HOUSE - KITCHEN" and "INT. HOUSE - BEDROOM" collapse to one location. | Low |

### 4.2 Plot Contradiction Engine

| # | Caveat | Impact | Severity |
|---|--------|--------|----------|
| C1 | **Entity over-capture / no pronoun guard in fact extraction.** The trait/status entity regex is lazy and allows periods, so on multi-sentence lines it can grab the wrong span, and there is no pronoun stoplist. **Observed real bug:** a run flagged a `character_trait_conflict` with entity **"THERE"** and garbage trait values ("long moment as Marty looks…" vs "similar rig on the real DeLorean"). | False-positive contradictions; erodes trust. | **High** |
| C2 | **Tier 2 similarity uses `en_core_web_sm`, which has no real word vectors.** `.similarity()` falls back to context/tagger vectors and is unreliable. | Tier-2 semantic results are noisy/low-quality. | **High** |
| C3 | **Narrow status/trait coverage.** Death = only "dead/killed/died" (misses "murdered", "passed away", "gone", "we lost him"). Trait = "is a / works as" + one bespoke pattern (misses appositives "X, a doctor,", "became a lawyer"). | Missed real contradictions (false negatives). | Medium |
| C4 | **No coreference resolution.** Facts about "he/she/they" are lost; only explicitly named subjects are captured. | Large recall gap on natural prose. | Medium |
| C5 | **Timeline is weekday-only** (+ "N days later"). No calendar dates, "next morning", "that night", or relative ordering. | Most real timeline conflicts go undetected. | Medium |
| C6 | **`character_alive_status` appearance test is a substring match.** `_character_appears_in_scene` regex-matches the name in any line, which can match partial/incidental mentions and ignores legitimate flashback resurrection. | Occasional false positives. | Low–Med |
| C7 | **Trait conflict = "no overlapping words".** Two non-conflicting roles with disjoint vocabulary ("detective" vs "negotiator") can be flagged. | False positives on complementary roles. | Medium |
| C8 | **Health score weights are arbitrary** (8/contradiction, 3/orphan) and unvalidated against any rubric. | Score is a rough signal, not calibrated. | Low |

### 4.3 Cross-cutting / infrastructure

| # | Caveat | Impact |
|---|--------|--------|
| X1 | **No automated pytest CI for the engines.** Tests are manual runner scripts (`run_*_test.py`, `real_screenplay_test.py`) with embedded screenplays; only `tests/test_pdf_loader.py` is pytest-style. | Regressions can slip in silently. |
| X2 | **Evaluation corpus is essentially empty** (only `demo_real`). The harness exists (`scripts/run_corpus_batch.py` + ground-truth YAML template) but has no labeled data. | Can't measure precision/recall, so risky heuristics can't be tuned. |
| X3 | **spaCy model loaded twice** (once per engine). | Extra memory + startup time. |

---

## 5. Where to work next — prioritized roadmap

> Ordering principle: **fix precision bugs first** (they directly hurt user trust), then **safe recall wins**, then **anything that needs tuning** (gate those behind the corpus).

### P0 — Precision fixes (do now, low risk, high trust impact)
1. **Fix contradiction entity over-capture (C1).** Reuse the same guard approach already added to the dependency engine: extract the trailing proper-name span, and reject pronouns/indefinites (`NON_CHARACTER_WORDS`). This kills the "THERE is described as…" class of false positives.
2. **Add a pronoun/non-name guard to `character_trait` and `character_status` extraction (C1/C6).**
3. **Constrain the trait entity regex** so it cannot span across sentence boundaries (don't allow `.` inside the captured entity, or anchor to line start).

### P1 — Safe recall wins (low/medium risk)
4. **Expand the interaction-verb list (D1)** — add grabs, holds, hands, pockets, carries, takes, hides, steals, drops, sets down. Or switch to spaCy dependency parse: direct objects of a handling-verb set. Share the list between both engines (already shared as `OBJECT_OWNERSHIP_PATTERNS`).
5. **Add death/status synonyms (C3)** — "murdered", "passed away", "killed off", "his body".
6. **Promote NER-detected action characters to scene characters (D2)** — close the dependency recall gap, gated by the existing person filters.

### P2 — Higher-value but needs the corpus first (tune against real numbers)
7. **Signal 3 — grammatical-role character detection (D3).** Classify a caps span as a character when it is the `nsubj` of an agentive verb (vs `dobj`/`pobj` for props). This is the real fix for invented names NER misses, **but** it has known false-positive risk (e.g. "DELOREAN races") and needs threshold/lexicon tuning.
8. **Recurrence promotion for weak props** — a recurring lowercase noun chunk across 2+ scenes becomes a low-weight prop. Reintroduces a noise channel; only ship with corpus measurement.
9. **Upgrade Tier-2 to `en_core_web_md` (C2)** — real word vectors make semantic similarity meaningful; re-tune `TIER2_SIMILARITY_THRESHOLD`.
10. **Coreference resolution (C4)** — pronoun → entity, to recover dropped facts.

### P3 — Infrastructure & product
11. **Build the labeled corpus (X2)** — this unblocks P2. Use the existing `tests/corpus/ground_truth/_template.yaml` + `run_corpus_batch.py --compare-ground-truth`. Target ~10–20 annotated scripts.
12. **Add a pytest suite + CI (X1)** — convert the manual runners into assertions so precision/recall are checked on every change.
13. **Single shared spaCy load (D7/X3)** — load `en_core_web_sm` once and inject into both engines; reduce to one NLP pass per scene where possible.
14. **Implement fact/causal dependency edges (D6)** — the `fact` weight is already reserved.
15. **Tier 3 (Haiku) for ambiguous Tier-2 candidates** — only after the corpus shows where Tier 1+2 fall short.

### Suggested sequence

```
P0 (precision) → P1 (safe recall) → build corpus (P3.11) → P2 (tuned heuristics) → remaining P3
```

---

## 6. Evaluation infrastructure (already in place)

You don't have to build the harness from scratch — it exists and just needs data:

- `scripts/run_corpus_batch.py` — runs every script in `tests/corpus/input/`, writes per-script `*_report.txt`, `*.json`, and a `manifest.csv`. With `--compare-ground-truth` it diffs against YAML ground truth and reports matched / missed (false negatives) / extra (false positives) + simulate-delete checks.
- `tests/corpus/ground_truth/_template.yaml` — the annotation format (expected + planted contradictions, expected delete-impact).
- `scripts/benchmark_engines.py` + `docs/PERFORMANCE_TESTING_GUIDE.md` — latency/throughput measurement (relevant to D7 SLA concerns).

**Action:** annotate ~10–20 scripts to turn "I think this is a false positive" into a measured precision number. This single step de-risks every P2 item.

---

## 7. File map (core)

```
scriptlensCore/
├── scene_dependency.py        # parsing + dependency graph + queries
├── plot_contradiction.py      # fact store + Tier 1 / Tier 2 rules
├── scriptlens_analyser.py     # orchestration + health score + report
├── pdf_screenplay_loader.py   # PDF → Fountain-ish text (PyMuPDF)
├── run_scriptlens.py          # CLI entry point
├── run_dependency_test.py     # manual runner (sample script)
├── run_contradiction_test.py  # manual runner (accuracy fixture)
├── real_screenplay_test.py    # end-to-end check with planted contradictions
├── scripts/run_corpus_batch.py# batch eval + ground-truth diff
├── tests/corpus/              # evaluation corpus (currently almost empty)
└── docs/ARCHITECTURE.md       # full product/architecture spec
```

---

## 8. One-paragraph takeaway

The engines are **functionally solid and well-guarded for their bundled fixtures**, but they are **pattern-bound**: recall is limited by the breadth of the regexes/verb lists, and precision is occasionally undermined by entity over-capture (the "THERE" trait bug) and by Tier-2 running on a vectorless spaCy model. **Fix the precision bugs (P0) immediately**, take the **safe recall wins (P1)**, then **invest in a labeled corpus** so the genuinely valuable but risky improvements (grammatical-role character detection, recurrence promotion, better semantic similarity, Tier 3) can be tuned with real numbers instead of guesswork.

*End of report.*
