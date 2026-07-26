# Clean Produced Scripts — Benchmark Manifest

Scripts go in `clean_produced/` (same folder name, one level down). This file
tracks metadata only — safe to commit. Screenplay files are gitignored.

**Copyright:** Do not commit PDF or Fountain files to a public repo unless you
have rights.

## File naming

Use a sortable prefix and neutral slug in `clean_produced/`:

```text
clean_produced/01_inception_2010.fountain
clean_produced/02_social_network_2010.pdf
```

Supported: `.fountain`, `.pdf`, `.txt`, `.screenplay`, `.fadein`

Avoid dropping `.md` files in `clean_produced/` — the batch runner treats them
as screenplays. Use this manifest for notes instead.

For PDFs, prefer saving an extracted `.fountain` after the first run and
re-analysing that copy (PDF extraction can be noisy).

---

## Script inventory

Fill one row per script after you drop files in. Leave review columns blank
until you run the benchmark batch.

| # | Filename | Title | Year | Pages | Scenes | Format | Source / notes |
|---|----------|-------|------|-------|--------|--------|----------------|
| 01 | | | | | | | |
| 02 | | | | | | | |
| 03 | | | | | | | |
| 04 | | | | | | | |
| 05 | | | | | | | |
| 06 | | | | | | | |
| 07 | | | | | | | |
| 08 | | | | | | | |
| 09 | | | | | | | |
| 10 | | | | | | | |

---

## After first batch run

Update `CLEAN_FP_LOG.md` with contradiction counts and your manual verdict
(real slip vs false positive). Reports live in `reports/`.

```powershell
venv\Scripts\python.exe scripts\run_clean_benchmark.py
```

Or, if scripts are stored outside the repo:

```powershell
venv\Scripts\python.exe scripts\run_clean_benchmark.py `
  --input-dir "C:\path\to\hollywood_clean"
```
