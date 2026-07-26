# ScriptLens — PDF-to-Fountain Cleanup Guide

**Purpose:** Prepare Hollywood PDF screenplays for accurate ScriptLens analysis by fixing PDF extraction noise before you run the engine.

**Audience:** You (internal benchmark work) or anyone cleaning produced scripts for the clean benchmark corpus.

**Pilot script:** *Carrie* (1976 shooting script PDF) — smallest file in the current Hollywood batch.

---

## Why cleanup matters

PDF extraction does not produce real Fountain. It usually gives you:

- **One phrase per line** — action reads like a broken list instead of paragraphs.
- **Camera slugs as standalone ALL-CAPS lines** — e.g. `ANGLE`, `THE HOUSE`, `OMITTED`, `STELIA HORAN - DAY`. The parser treats these as **character names**.
- **OCR typos** — e.g. `CHIUS` instead of `CHRIS`, `TOHMY` instead of `TOMMY`.
- **Revision / page noise** — `REVISION PAGES 51-52`, bare page numbers.

ScriptLens then flags **false positives**: name consistency pairs between slug lines, and numeric-count chains across merged scene text.

Cleanup does **not** invent story fixes. It makes the file **parse correctly** so real continuity issues (if any) stand out.

---

## What you need

| Item | Location |
|------|----------|
| Python venv | `venv\Scripts\python.exe` at repo root |
| Benchmark drop folder | `tests\corpus\benchmark\clean_produced\` |
| Extracted Fountain (optional subfolder) | `tests\corpus\benchmark\clean_produced\fountain\` |
| Cleanup script | `scripts\cleanup_extracted_fountain.py` |
| Batch runner | `scripts\run_clean_benchmark.py` |
| Single-script runner | `run_scriptlens.py` |
| FP review log | `tests\corpus\benchmark\CLEAN_FP_LOG.md` |

**Copyright:** Do not commit PDFs or Fountain files to a public repo unless you have rights. The benchmark folder is gitignored for script files.

---

## Step-by-step workflow

### Step 1 — Drop the PDF in the benchmark folder

Copy your screenplay PDF into:

```text
tests\corpus\benchmark\clean_produced\
```

Use a sortable name, e.g. `02_carrie_1975.pdf`. Double extensions like `.pdf.pdf` still work.

Update the inventory table in `tests\corpus\benchmark\MANIFEST.md` (metadata only — safe to commit).

---

### Step 2 — Run a baseline analysis (optional but recommended)

See how noisy the raw PDF is before cleanup:

```powershell
cd C:\Users\subhi\Documents\Subhiksha_Files\scriptlensCore

venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir tests\corpus\benchmark\clean_produced `
  --output-dir tests\corpus\benchmark\reports
```

Open the report:

```text
tests\corpus\benchmark\reports\<stem>_report.txt
```

Note **Scenes**, **Characters** (count and absurd names), and **Found N possible inconsistency(ies)**.

---

### Step 3 — Extract PDF text to Fountain

**Option A — During analysis (quick):**

```powershell
venv\Scripts\python.exe run_scriptlens.py `
  tests\corpus\benchmark\clean_produced\02_Carie_1975.pdf.pdf `
  --save-extracted tests\corpus\benchmark\clean_produced\fountain\02_Carie_1975.fountain
```

**Option B — Bulk convert (if you already ran the batch):**  
The batch runner uses the same PDF loader internally. Copy or save extracted text to `clean_produced\fountain\` for editing.

The extracted file will be **long** (one short line per phrase) and **not** writer-ready Fountain.

---

### Step 4 — Run automated cleanup

The cleanup script reflows action into paragraphs, keeps real scene headings and character cues, and demotes common camera slugs to action text.

```powershell
venv\Scripts\python.exe scripts\cleanup_extracted_fountain.py `
  tests\corpus\benchmark\clean_produced\fountain\02_Carie_1975.fountain
```

**Default output:** same folder, `<stem>_clean.fountain`  
Example: `02_Carie_1975_clean.fountain`

**Custom output path (optional):**

```powershell
venv\Scripts\python.exe scripts\cleanup_extracted_fountain.py `
  tests\corpus\benchmark\clean_produced\fountain\02_Carie_1975.fountain `
  tests\corpus\benchmark\clean_produced\fountain\02_Carie_1975_v2.fountain
```

**What the script does automatically:**

| Problem | Automated fix |
|---------|----------------|
| Split scene headings (`INT.` on one line, location on the next) | Merges into one `INT. … - DAY` line |
| Action split across many short lines | Joins into action paragraphs |
| Obvious slug ALL-CAPS (`ANGLE`, `THE HOUSE`, `OMITTED`, `POV`, …) | Merged into action, not character cues |
| Bare page numbers, draft titles, revision page headers | Removed |
| Real character cues before dialogue | Preserved (e.g. `CARRIE`, `MARGARET`) |

---

### Step 5 — Manual review (required for best results)

Open `<stem>_clean.fountain` in a text editor. Work top to bottom once; fix patterns the script cannot guess.

#### 5a. Demote remaining slug lines to action

If a line is **camera direction**, prefix it with a space or merge it into the paragraph above — do **not** leave it as a standalone ALL-CAPS line.

**Before (parsed as character):**

```text
STELIA HORAN - DAY
An All-American sunbathing beauty...
```

**After (action):**

```text
An All-American sunbathing beauty of eighteen...
```

**Common slug patterns to demote:**

- `ANGLE …`, `CLOSEUP …`, `POV …`, `TWO SHOT …`, `TRACKING …`
- `THE HOUSE`, `THE GYM`, `THE STAGE`, `THE HORAN HOUSE`
- `STELIA'S POV - …`, `CARRIE'S POV - …`
- `(CONTINUED)`, `CONT'D`, `OMITTED` mid-scene

#### 5b. Fix OCR / typo character names

Search for known character names and fix scan errors:

| Wrong (PDF) | Fix |
|-------------|-----|
| `CHIUS` | `CHRIS` |
| `TOHMY`, `TOIYIMY`, `TOM'.MY` | `TOMMY` |
| `STELIA` (if you standardize on STELLA) | Pick one spelling and use it in **character cues** |
| `GEORGE DAWSON'` | `GEORGE DAWSON` |
| `GOLLINS` | `COLLINS` |

Only character **cue lines** (ALL CAPS alone on a line before dialogue) need to be consistent. Action text can keep variant spellings if you prefer.

#### 5c. Merge dialogue with action on the same line

PDF often glues slug + dialogue:

```text
STELIA
(at something of a loss) Well, I'm a good girl.
```

If dialogue is stuck in an action paragraph without a cue, split it: cue line, then dialogue.

#### 5d. Remove or inline revision markers

Delete standalone lines like:

```text
REVISION PAGES 51-52
OMITTED
```

If `OMITTED` marks a cut scene, remove the block or replace with a brief action note in sentence case.

#### 5e. Save as your “analysis copy”

Keep the cleaned file separate from the raw extract:

```text
02_Carie_1975.fountain          ← raw extract (keep for diff)
02_Carie_1975_clean.fountain    ← after automated cleanup
02_Carie_1975_manual.fountain   ← optional: after your manual pass
```

---

### Step 6 — Re-run ScriptLens on the cleaned file

**Single script (full report to terminal):**

```powershell
venv\Scripts\python.exe run_scriptlens.py `
  tests\corpus\benchmark\clean_produced\fountain\02_Carie_1975_clean.fountain
```

**Save report to file:**

```powershell
venv\Scripts\python.exe run_scriptlens.py `
  tests\corpus\benchmark\clean_produced\fountain\02_Carie_1975_clean.fountain `
  | Out-File -Encoding utf8 `
    tests\corpus\benchmark\reports\fountain_clean\02_Carie_1975_clean_report.txt
```

**Batch (only cleaned files in a folder):**  
Put `*_clean.fountain` files alone in a folder, then:

```powershell
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir tests\corpus\benchmark\clean_produced\fountain `
  --output-dir tests\corpus\benchmark\reports\fountain_clean
```

*(If raw and cleaned files share a folder, the batch will analyse both — use a subfolder or rename filter by moving files.)*

---

### Step 7 — Compare before/after and log false positives

Compare these fields in the report header:

| Metric | What to look for |
|--------|------------------|
| **Characters** | Should drop sharply (fewer slug “names”) |
| **name_consistency** flags | Should drop (slug pairs removed) |
| **numeric_count** flags | May stay or **increase** — see note below |
| **Overall health score** | May stay low until flag count is low |

Log your verdicts in `tests\corpus\benchmark\CLEAN_FP_LOG.md`:

- **FP** — engine wrong; PDF/cleanup artifact  
- **Real** — surprising catch on a clean script (rare)  
- **Unsure** — needs second read  

---

## Carrie pilot — before vs after automated cleanup

| Metric | Raw PDF extract | After `cleanup_extracted_fountain.py` |
|--------|-----------------|--------------------------------------|
| Scenes | 82 | 82 |
| Character names parsed | 267 | 98 |
| Total contradiction flags | 13 | 15 |
| name_consistency | 6 | 1 |
| numeric_count | 7 | 14 |

**Interpretation:**

- **Big win:** Slug false names (`THE HOUSE` vs `THE HOSE`, `CARRIE AND TOMMY` vs `TOHMY`, `OMITTED` variants) mostly gone — character list is usable.
- **Remaining name flag:** `CHRIS` vs `CHIUS` — OCR typo; fix manually in Step 5b.
- **numeric_count increased:** Reflowing merges more words into each scene, so word-count chains (`group`, `ext`, `continued`, `carrie`) fire more often. Treat these as **noise** on PDF-derived scripts unless you see an obvious story mistake.
- **Next step for Carrie:** Manual pass (Step 5) then re-run; expect name_consistency → 0 and slightly better character count.

---

## Quick reference — all commands

```powershell
# 1. Baseline batch
venv\Scripts\python.exe scripts\run_clean_benchmark.py

# 2. PDF → Fountain extract
venv\Scripts\python.exe run_scriptlens.py path\to\script.pdf `
  --save-extracted path\to\script.fountain

# 3. Automated cleanup
venv\Scripts\python.exe scripts\cleanup_extracted_fountain.py path\to\script.fountain

# 4. Analyse cleaned file
venv\Scripts\python.exe run_scriptlens.py path\to\script_clean.fountain

# 5. External scripts folder (copyright-safe)
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir "C:\path\to\hollywood_clean" `
  --output-dir tests\corpus\benchmark\reports
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Hundreds of “characters” like `ANGLE`, `THE GYM` | Slug lines parsed as cues | Run cleanup script + manual demote (Step 5a) |
| Same person flagged twice (`CHRIS` / `CHIUS`) | OCR typo in cue line | Fix spelling in Step 5b |
| Flags unchanged PDF vs Fountain | Fountain is same extract as PDF path | Cleanup + manual edit required |
| `numeric_count` only flags | Word-count detector on merged action | Usually FP on PDF scripts; log as FP |
| Scene count seems wrong | Split/merged headings | Fix `INT.` / `EXT.` lines at scene breaks |
| Health score 0 / 100 | Many flags depress score | Normal for unclean PDFs; focus on flag **types** |

---

## Files produced by this workflow

| File | Committed to git? |
|------|-------------------|
| `clean_produced/*.pdf` | No (gitignored) |
| `clean_produced/fountain/*.fountain` | No (gitignored) |
| `reports/*_report.txt` | No (gitignored) |
| `MANIFEST.md`, `CLEAN_FP_LOG.md` | Yes (metadata / review) |
| This guide (`.md` / `.pdf`) | Yes |

---

## Related docs

- Benchmark README: `tests/corpus/benchmark/README.md`
- Corpus evaluation: `docs/CORPUS_EVALUATION_GUIDE.md`
- Writer error examples: `docs/writer_materials/ERROR_TYPE_EXAMPLES_GUIDE.pdf`

---

*ScriptLens — internal benchmark workflow. Last updated: June 2026.*
