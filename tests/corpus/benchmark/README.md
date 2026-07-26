# ScriptLens benchmark corpus (clean produced scripts)

Tier **B** evaluation: real-world screenplays with **no planted errors**.
Used to measure **false positives** and writer-facing report quality — separate
from the planted-error CI corpus in `../input/`.

## Layout

| Path | Purpose |
|------|---------|
| `clean_produced/` | Drop scripts here (gitignored except `.gitkeep`) |
| `MANIFEST.md` | Title/metadata inventory (committed) |
| `reports/` | Generated reports and JSON (gitignored) |
| `CLEAN_FP_LOG.md` | Manual false-positive review log (committed) |

## Quick start

1. Copy up to 10 scripts into `clean_produced/` (see naming in `MANIFEST.md`).
2. Fill the inventory table in `MANIFEST.md` (parent folder).
3. Run:

```powershell
venv\Scripts\python.exe scripts\run_clean_benchmark.py
```

4. Open `reports/*_report.txt` and log verdicts in `CLEAN_FP_LOG.md`.

## External folder (copyright-safe)

If scripts must stay outside the repo:

```powershell
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir "C:\Users\subhi\Documents\ScriptLens_benchmark\hollywood_clean"
```

Reports still write to `tests/corpus/benchmark/reports/` unless you pass
`--output-dir`.

## Not for CI

Do **not** add these files to `tests/corpus/input/` or run
`--compare-ground-truth` on this set. CI uses the 100 planted-error corpus only.

**Engine profile:** `run_clean_benchmark.py` analyses scripts with the
``pdf_benchmark`` input profile, which disables generic ``numeric_count``
pairing that PDF extraction noise triggers on clean Hollywood scripts. PDF
inputs analysed via ``run_scriptlens.py`` also default to ``pdf_benchmark``.

See also: `docs/CORPUS_EVALUATION_GUIDE.md`.
