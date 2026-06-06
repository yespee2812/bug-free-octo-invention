# ScriptLens Corpus Evaluation Guide

How to use **15–20 screenplays** you read manually, map dependencies and contradictions (including planted ones), run them through the engines, and compare to what a **customer would see**.

---

## What the customer sees today

There is **no Chrome extension UI yet**. The customer-facing output today is the **SCRIPTLENS STORY REPORT** printed by `pretty_print_results()` — the same text you get from the CLI.

It includes:

1. **Your script at a glance** — scene count, characters, props  
2. **How your scenes connect** — edges, orphans, average dependencies  
3. **Scenes you should not cut lightly** — delete-impact ranking (top 5)  
4. **Story consistency issues** — contradictions with scene numbers, explanation, confidence %  
5. **Overall script health** — score /100 + short message  

Later, the extension **Dependencies** and **Contradictions** tabs will show the same data in cards + **Go to scene**. For tuning, treat the `.txt` report as the customer view.

---

## Folder layout

Put your scripts and ground truth here:

```text
tests/corpus/
├── input/                    ← Drop your 15–20 scripts here (.fountain, .txt, .pdf)
├── ground_truth/             ← One YAML per script (your manual mapping)
│   ├── _template.yaml
│   └── my_script_01.yaml
├── reports/                  ← Generated (do not hand-edit)
│   ├── my_script_01_report.txt    ← Customer-style report
│   ├── my_script_01.json          ← Machine-readable (compare / diff)
│   └── manifest.csv               ← Summary of all scripts
└── README.md
```

---

## Step-by-step workflow

### 1. Prepare scripts as Fountain-friendly text

Each file must use scene headings the parser understands:

```text
INT. LOCATION - DAY
EXT. STREET - NIGHT
```

Supported inputs: `.fountain`, `.txt`, `.md`, `.screenplay`, `.pdf` (PDF is extracted first — prefer saving as `.fountain` after review).

**Naming:** `01_thriller_heist.fountain`, `02_romcom_clean.fountain`, … so reports sort clearly.

### 2. Read each script and fill ground truth (manual work)

Copy `tests/corpus/ground_truth/_template.yaml` to `tests/corpus/ground_truth/<same_stem>.yaml`.

Record:

| Section | What you write |
|---------|----------------|
| `expected_contradictions` | Real errors you see in the script (type + scene_a + scene_b) |
| `planted_contradictions` | Contradictions **you added on purpose** to test detection |
| `expected_simulate_delete` | Scene you would cut + scene IDs that **should** break |
| `notes` | Format quirks, false positive you expect, etc. |

Scene IDs must match engine numbering: **first `INT.`/`EXT.` in file = scene_001**, second = scene_002, etc. (same as future extension scroll-to-scene).

**Tip:** Run the script once without ground truth, open `reports/<name>.json`, check `script_summary.total_scenes` and headings, then complete YAML.

### 3. Run one script (preview customer output)

```powershell
cd c:\Users\subhi\Documents\Subhiksha_Files\scriptlensCore

# Customer-style report in terminal
.\run_scriptlens.ps1 tests\corpus\input\my_script_01.fountain

# Same report + JSON for your records
.\run_scriptlens.ps1 tests\corpus\input\my_script_01.fountain --json
```

### 4. Run all scripts in the corpus (batch)

```powershell
.\venv\Scripts\python.exe scripts\run_corpus_batch.py
```

Defaults:

- **Input:** `tests/corpus/input/`
- **Output:** `tests/corpus/reports/`

Options:

```powershell
.\venv\Scripts\python.exe scripts\run_corpus_batch.py --input-dir tests\corpus\input --output-dir tests\corpus\reports
.\venv\Scripts\python.exe scripts\run_corpus_batch.py --compare-ground-truth
```

Outputs per script:

| File | Contents |
|------|----------|
| `{name}_report.txt` | Full **SCRIPTLENS STORY REPORT** (customer view) |
| `{name}.json` | Full analysis dict (for diffing / tooling) |
| `manifest.csv` | One row per script: scenes, edges, contradictions, health |
| `{name}_evaluation.txt` | Only if `--compare-ground-truth` and matching YAML exists |

### 5. Compare engine vs your manual mapping

Open side by side:

- `reports/my_script_01_report.txt` — what the customer reads  
- `ground_truth/my_script_01.yaml` — what you expected  
- `reports/my_script_01_evaluation.txt` — matched / missed / extra flags  

Track in a spreadsheet:

| script | expected_contra | found | TP | FP | FN | notes |
|--------|-----------------|-------|----|----|-----|-------|

**False positive (FP):** engine flagged, you disagree  
**False negative (FN):** you listed in YAML, engine missed  

Target before product build: **FP < 10%** on this corpus.

### 6. Scripts with planted contradictions

For scripts you **edited** to add errors:

1. List them only under `planted_contradictions` in YAML  
2. Run batch with `--compare-ground-truth`  
3. **Recall** on planted set = how many you planted were caught  

Keep a few **clean** scripts (no planted errors) to measure false positives.

### 7. Dependency / simulate-delete validation

For each script, pick 2–3 scenes in YAML under `expected_simulate_delete`:

```yaml
expected_simulate_delete:
  - scene_id: scene_005
    expect_impacted:
      - scene_011
      - scene_012
```

The evaluation file checks whether `get_delete_impact` lists those scene IDs (subset match).

Full per-scene dependency lists are **not** in the customer report today — only summary + high-risk. For deep dependency review use JSON or:

```powershell
.\venv\Scripts\python.exe run_dependency_test.py
```

(Customize by pointing at your script in a small one-off script if needed.)

---

## What is NOT in the customer report yet

| Data | Customer report | Where to see it |
|------|-----------------|-----------------|
| Every scene’s upstream deps | No | JSON / `run_dependency_test` style dump |
| Simulate delete UI | No | CLI + future Dependencies tab |
| Go to scene | No | Future extension |
| Per-edge explanations | No | JSON / engine internals |

Your manual dependency map can be **richer** than v1 output — use YAML + JSON to tune the engine, then rely on the report for writer-facing checks.

---

## Quick reference

```powershell
# Single script — customer report
.\run_scriptlens.ps1 tests\corpus\input\01_my_script.fountain

# Single script — JSON only
.\run_scriptlens.ps1 tests\corpus\input\01_my_script.fountain --json > tests\corpus\reports\01_my_script.json

# All scripts + ground truth comparison
.\venv\Scripts\python.exe scripts\run_corpus_batch.py --compare-ground-truth

# PDF (extract once, then tune on .fountain)
.\run_scriptlens.ps1 tests\corpus\input\01_my_script.pdf --save-extracted tests\corpus\input\01_my_script_extracted.fountain
```

---

## Checklist for 15–20 scripts

- [ ] 15–20 files in `tests/corpus/input/`  
- [ ] Mix: clean, messy format, short, one long (~60+ scenes)  
- [ ] 3–5 scripts with **planted** contradictions  
- [ ] YAML ground truth per script  
- [ ] Batch run → `reports/*_report.txt` reviewed  
- [ ] `manifest.csv` + FP/FN spreadsheet filled  
- [ ] Tuning logged in `docs/perf_results/` (see PERFORMANCE_TESTING_GUIDE.md)  

---

*Related: [ARCHITECTURE.md](./ARCHITECTURE.md) · [PERFORMANCE_TESTING_GUIDE.md](./PERFORMANCE_TESTING_GUIDE.md)*
