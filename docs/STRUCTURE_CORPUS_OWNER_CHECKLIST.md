# Structure Corpus — Owner Checklist

What **you** (product / domain) must provide so engineering can score the v3
structure engine honestly. Engineering builds scorers, generators, and CI;
it cannot invent trustworthy story “right answers.”

Companion docs:

- [SCRIPTLENS_TESTING_PROCESS.pdf](SCRIPTLENS_TESTING_PROCESS.pdf) — conventional + unconventional methods
- [SCRIPTLENS_ANNOTATION_GUIDELINE.pdf](SCRIPTLENS_ANNOTATION_GUIDELINE.pdf) — how to label with anchors
- Template: [`tests/corpus/ground_truth/_template.yaml`](../tests/corpus/ground_truth/_template.yaml)
- Seeded goldens: [`tests/corpus/ground_truth/structure/`](../tests/corpus/ground_truth/structure/)
- Scorer: `scripts/score_structure_baseline.py`

---

## Must provide (blocks a honest CI gate)

### 1. Sign off the checklist schema

Confirm these YAML fields are the gold contract (already seeded in `_template.yaml`):

| Field | Purpose |
| --- | --- |
| `expected_orphans` | Scene ids that must be flagged (or `[]`) |
| `orphan_types` | `hard` vs loose / `subplot_chain` |
| `orphan_anchors` | C/L/P/E empty-channel evidence + quote |
| `expected_simulate_delete` | Cut scene → impacted ids + `expect_risk_in` |
| `expected_simulate_edit` | Modified text + `expect_edges_removed_min` and/or `expect_edges_changed_min` + risk set |
| `expected_scene_functions` | Optional plant / payoff / setup roles |

Soft / semantic orphans need **two annotators** (see annotation guideline).

### 2. Micro-scripts (target 15–20)

Short Fountain scripts (5–10 scenes), each with a deliberate situation:

- at least one hard orphan **or** a clear plant→payoff chain
- paired YAML with the **same stem** as the `.fountain` file
- place scripts under `docs/demo_scripts/` or `tests/corpus/structure/input/`
- place YAML under `tests/corpus/ground_truth/structure/`
- register each pair in `tests/corpus/ground_truth/structure/manifest.yaml`

**Already seeded (4):** action simulate demo, statue orphan, revolver chain, prologue exemption. You still need ~11–16 more for the full target.

Reuse existing demos as seeds. Quality over quantity.

### 3. Anchors on every gold label

Not gold without a traceable quote / channel check. Silver labels may exist for
review but must **not** gate CI.

### 4. Pass / fail thresholds

Decide numbers for `score_structure_baseline.py --check`, for example:

| Metric | Suggested starting gate |
| --- | --- |
| Orphan recall | `1.0` on hard-orphan goldens |
| Orphan precision | `≥ 0.9` (or max N false positives) |
| Simulate-cut recall | `1.0` on labeled cut checks |
| Simulate-edit floor | every labeled edit meets removed and/or changed mins |

Until you set these, CI uses the defaults in the scorer CLI flags
(`--min-orphan-recall 1.0`, `--min-orphan-precision 0.9`, cut/edit recall `1.0`).

---

## Should provide (high ROI next)

### 5. Clean false-positive set (5–10 scripts)

Professionally written Fountain (preferred) with **no** hard orphans and no
spurious high-risk cuts. Keep copyrighted PDFs gitignored; metadata only in
manifests.

### 6. Entity-swap rename map

Edit [`tests/corpus/ground_truth/structure/rename_and_chekhov_patterns.yaml`](../tests/corpus/ground_truth/structure/rename_and_chekhov_patterns.yaml).
Seed maps for the action and revolver demos are already filled — extend them
or add new script entries. Renamed tokens must still look like Fountain
entities (CAPS props / character names).

Engineering automates the isomorphism test from this map.

### 7. Chekhov pattern list (8–12 pairs)

Same YAML file, `chekhov_patterns:` list. Four seed patterns ship today; add
more plant/mid/payoff wording you consider “must always link.” Prefer CAPS
plants so prop extraction fires.

---

## Nice later

- 1–2 noisy real PDFs for the graceful-degradation curve
- Second annotator for soft orphans
- Human ranking panel (Spearman) — only after the corpus exists

---

## This week (minimum)

1. [ ] Approve `_template.yaml` fields (or note changes).
2. [ ] Fully label **3 more** micro-scripts (orphan + one cut + one edit) beyond the 4 seeded demos.
3. [ ] Extend `rename_and_chekhov_patterns.yaml` (extra Chekhov pairs / rename maps).
4. [ ] Drop 5 clean scripts into a private / gitignored folder for FP review.

## Engineering already ships (you do not build these)

- Structure baseline scorer (`scripts/score_structure_baseline.py`)
- Entity-swap isomorphism + Chekhov generator tests
- Orphan-spec eval + unit/API tests
- CI wiring for the structure gate
