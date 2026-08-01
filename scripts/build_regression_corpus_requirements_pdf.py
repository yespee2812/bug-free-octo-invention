"""Render the ScriptLens regression-corpus requirements to a styled PDF.

Reuses the Markdown-to-PDF pipeline in ``scripts/md_to_pdf.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.md_to_pdf import html_to_pdf, markdown_to_html  # noqa: E402

OUTPUT_PATH = _REPO_ROOT / "docs" / "SCRIPTLENS_REGRESSION_CORPUS_REQUIREMENTS.pdf"

DOCUMENT_MARKDOWN = """
# ScriptLens — Regression Corpus Requirements

*What to create, how to format it, what to label, and which variations to cover
for the v3 structure engine (orphans, simulate cut/edit, clean false-positive
guards, and NLP stress cases).*

---

## 0. Quick targets

| Item | Target |
| --- | --- |
| Corpus families | 4 (A planted orphans, B clean, C cut/edit, D stress) |
| Micro-scripts (5–10 scenes) | 50–60 |
| Clean / connected scripts | ~10–15 short + ~10 longer |
| Required format | Fountain (`.fountain`), UTF-8 |
| Blind workflow | Keep labels private → run engine → cross-check → promote gold YAML to CI |

**Hard rule:** every scene break must be a real Fountain slugline starting with
`INT.` / `EXT.` / `INT/EXT.` / `I/E.`. Prose without sluglines collapses into one
scene — orphan results become meaningless.

---

## 1. Four corpus families

| Family | Purpose | Size | Labels you keep | CI? |
| --- | --- | --- | --- | --- |
| **A. Planted orphan micro-scripts** | Recall: engine must find known orphans | 40–50 × 5–10 scenes | `expected_orphans` + anchors | Yes — gate |
| **B. Clean / connected scripts** | Precision: must NOT invent orphans | 10–15 short + ~10 longer | `expected_orphans: []` | Yes — FP gate |
| **C. Simulate cut / edit goldens** | Cut & rewrite impact correctness | 15–20 (can overlap A) | delete + edit YAML rows | Yes — when labeled |
| **D. Stress / edge variations** | NLP resilience & exemptions | 20–30 micro cases | Per-variation expectation | Unit + corpus |

Blind workflow: hold labels privately → run ScriptLens → cross-check → only then
copy gold YAML into `tests/corpus/ground_truth/structure/`.

---

## 2. File format requirements (every script)

### Required

- Extension: `.fountain` (prefer not `.fountain.txt`)
- Encoding: UTF-8
- Scene headings on their own line, e.g. `INT. LOCATION - DAY`
- Important props in **ALL CAPS** on first plant
- Character cues in ALL CAPS above dialogue
- Stable id in filename, e.g. `A_H1_03_hard_orphan.fountain`

### Avoid / defer

- PDF-only drafts (convert to Fountain first)
- Scanned / OCR PDFs without cleanup
- Prose with no `INT.` / `EXT.` breaks
- Copyrighted Hollywood PDFs in a public git repo
- Soft “feels disconnected” labels without anchors

### Folder layout

- Blind batch drop: `scripts/regression testing/`
- CI gold pairs: `tests/corpus/structure/input/` + `tests/corpus/ground_truth/structure/`
- Register each gold pair in `tests/corpus/ground_truth/structure/manifest.yaml`
- Template: `tests/corpus/ground_truth/_template.yaml`
- Annotation rules: `docs/SCRIPTLENS_ANNOTATION_GUIDELINE.pdf`

---

## 3. Label schema (what to write for each gold script)

Scene numbers = order of `INT.`/`EXT.` headings (1 = first). Scene ids =
`scene_001`, `scene_002`, … matching that order.

| Field | Required? | What to write |
| --- | --- | --- |
| `expected_orphans` | Yes | List of `scene_XXX`, or `[]` if clean |
| `orphan_types` | Yes if orphans | `hard` \| `loose` \| `subplot_chain` |
| `orphan_exemptions` | If applicable | prologue / montage / flashback / imagined / dream |
| `orphan_anchors` | Yes for gold | C/L/P/E empty checks + evidence quote |
| `expected_simulate_delete` | For family C | cut `scene_id` → impacted ids + `expect_risk_in` |
| `expected_simulate_edit` | For family C | `modified_text` + removed and/or changed edge floors |
| `expected_scene_functions` | Optional | plant / payoff / setup roles |
| `notes` | Recommended | Intent of the planted situation |

Soft / semantic orphans need two annotators. No anchor → silver only (do not
CI-gate).

---

## 4. Family A — Planted orphan variations

Aim ~40–50 five-scene scripts. Each script plants **one primary situation**.

### 4.1 Hard orphans (engine must flag)

| Code | Variation | How to plant | Expected |
| --- | --- | --- | --- |
| H1 | Detached location + new cast | Unique place + characters never reused | That `scene_id` orphan |
| H2 | Detached prop beat | Unique CAPS prop never mentioned again | orphan |
| H3 | Mid-script digression | Orphan in scene 3 of 5 (not only edges) | orphan |
| H4 | Late orphan | Orphan as penultimate scene | orphan |
| H5 | Two hard orphans | Two unrelated digressions | both ids |
| H6 | Orphan subplot chain (short) | 2–3 scenes linked only to each other | `subplot_chain` or hard per rules |

### 4.2 Must NOT be orphans (false-positive traps)

| Code | Variation | How to plant | Expected |
| --- | --- | --- | --- |
| F1 | Prop Chekhov chain | Plant CAPS prop → reuse later (briefcase/bowl/key) | `[]` |
| F2 | Character continuity only | Same character, changing locations | `[]` |
| F3 | Location continuity only | Same place, rotating cast | `[]` |
| F4 | Imagined / dream insert | Slugline contains `(IMAGINED)` / `DREAM` / `VISION` | `[]` (exempt) |
| F5 | Flashback + shared lead | `FLASHBACK` heading; same main character | `[]` (exempt) |
| F6 | Prologue / cold open | `PROLOGUE` in early scenes | `[]` (exempt) |
| F7 | Montage block | `MONTAGE` / `SERIES OF SHOTS` | `[]` (exempt) |
| F8 | Soft prop alias | `STEEL BRIEFCASE` then “the briefcase” / “the case” | `[]` |
| F9 | CONTINUOUS adjacency | Same place via `CONTINUOUS` / `MOMENTS LATER` | `[]` |

---

## 5. Family B — Clear / clean corpus

### Short clean (10–15)

- 5–10 scenes, fully connected on purpose
- Label: `expected_orphans: []`
- Cover genres: drama, comedy, action, mystery, romance, etc.

### Longer clear (~10)

- 15–40 scenes; still Fountain with sluglines
- Same label: no hard orphans
- Keep copyrighted sources private / gitignored

**Pass rule:** engine orphan set must be empty (or only scenes you explicitly
exempted). Any unexpected orphan is a false positive to log.

---

## 6. Family C — Simulate cut / edit variations

Can reuse Family A/B scripts. Add 1–2 labeled checks per script.

| Code | Variation | Label |
| --- | --- | --- |
| C1 | Cut plant scene → payoffs break | `expect_impacted` = later payoff ids; risk high/medium |
| C2 | Cut orphan → nothing breaks | `expect_impacted: []` |
| C3 | Cut bridge scene | multiple downstream ids impacted |
| C4 | Edit strips prop from plant | `expect_edges_changed_min` or `removed_min` ≥ 1 |
| C5 | Edit removes only character name | edges change/remove; note risk set |
| C6 | Edit that should be no-op | cosmetic rewrite; removed/changed floors = 0 |

---

## 7. Family D — Stress / NLP edge variations

| Code | Variation | Why |
| --- | --- | --- |
| D1 | Lowercased sluglines (`int. kitchen - day`) | Ingest / limited mode |
| D2 | OCR noise (random chars, missing punctuation) | Graceful degradation |
| D3 | Prop casing variants (Brass Key vs BRASS KEY) | Extraction robustness |
| D4 | Dialogue-only prop callbacks | Soft alias / nickname |
| D5 | Entity rename isomorphism seed | Same graph after rename map |
| D6 | Adjacent independent digressions swap | Permutation locality |
| D7 | Nested location (MUSEUM - FOYER vs HALL) | Spatial linkage nuance |
| D8 | V.O. / O.S. heavy scenes | Speaker vs presence |
| D9 | Same head-noun different props (two BOWLs) | Avoid over-linking |
| D10 | Imagined without shared cast names | Exemption (story5 class) |

Also extend `tests/corpus/ground_truth/structure/rename_and_chekhov_patterns.yaml`
with rename maps and Chekhov plant/mid/payoff wording pairs.

---

## 8. Naming & packaging convention

| Pattern | Example |
| --- | --- |
| Family + code + index | `A_H1_03_hard_orphan.fountain` |
| Clean set | `B_clean_drama_02.fountain` |
| Cut/edit set | `C_cut_plant_01.fountain` |
| Stress set | `D_imagined_01.fountain` |
| Private labels sheet | `labels_blind.xlsx` or `labels_private.yaml` |
| CI gold YAML | same stem under `ground_truth/structure/` |

### Private label sheet columns (blind eval)

| Column | Example |
| --- | --- |
| `script_id` | story5 |
| `scene_count_expected` | 9 |
| `orphan_scene_numbers` | none / 5 |
| `orphan_type` | hard / exempt:imagined |
| `anchor_quote` | short quote |
| `cut_check` | optional |
| `notes` | free text |

---

## 9. Suggested build order

| Phase | Deliver | Count |
| --- | --- | --- |
| **1 — Now** | H1–H4 hard orphans + F1–F4 non-orphans + B clean shorts | ~20 scripts |
| **2 — Next** | F5–F9 exemptions + C1–C4 cut/edit on best scripts | +15 |
| **3 — Scale** | Fill to 50–60 micros; add 10 longer cleans | +25–35 |
| **4 — Stress** | D1–D10 edge pack; rename/Chekhov pattern lists | +20 |

---

## 10. How batches are run

1. Put Fountain files in `scripts/regression testing/`.
2. Run: `venv\\Scripts\\python.exe scripts\\run_regression_orphans.py`
3. Receive a per-script table (scene count, orphan count, orphan ids + headings).
4. Cross-check against your private sheet.
5. Send only misses/extras for engine fixes or gold promotion.
6. When promoting to CI: add YAML + `manifest.yaml` entry, then
   `venv\\Scripts\\python.exe scripts\\score_structure_baseline.py --check`.

---

## 11. Companion documents in this repo

| Document | Path |
| --- | --- |
| Testing process (conventional + unconventional) | `docs/SCRIPTLENS_TESTING_PROCESS.pdf` |
| Annotation guideline | `docs/SCRIPTLENS_ANNOTATION_GUIDELINE.pdf` |
| Owner checklist (markdown) | `docs/STRUCTURE_CORPUS_OWNER_CHECKLIST.md` |
| Ground-truth template | `tests/corpus/ground_truth/_template.yaml` |
| Structure manifest | `tests/corpus/ground_truth/structure/manifest.yaml` |
| Rename / Chekhov patterns | `tests/corpus/ground_truth/structure/rename_and_chekhov_patterns.yaml` |
"""


def main() -> None:
    """Build the regression-corpus requirements PDF."""
    html = markdown_to_html(DOCUMENT_MARKDOWN)
    path = html_to_pdf(html, OUTPUT_PATH)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
