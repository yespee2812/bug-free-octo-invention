# ScriptLens test corpus

## Folders

| Folder | You put | Generated |
|--------|---------|-----------|
| `input/` | Planted-error `.fountain` / `.pdf` screenplays (CI) | — |
| `ground_truth/` | v3 fixtures only: orphan-spec + simulate demo (`_template.yaml`, `action_5scene_simulate_demo.yaml`, `orphan_spec/`) | — |
| `../../legacy/corpus/ground_truth/` | Legacy contradiction ground truth (de-scoped; used only by the manual `legacy-contradiction-baseline` CI job) | — |
| `reports/` | — | `*_report.txt`, `*.json`, `manifest.csv`, `*_evaluation.txt` |
| `benchmark/clean_produced/` | Clean Hollywood / produced scripts (local, gitignored) | — |
| `benchmark/MANIFEST.md` | Script inventory metadata (committed) | — |
| `benchmark/reports/` | — | Clean-benchmark reports (gitignored) |

## Commands

```powershell
# One script — customer report in terminal
..\..\run_scriptlens.ps1 input\my_script.fountain

# Planted-error corpus (CI)
..\..\venv\Scripts\python.exe ..\..\scripts\run_corpus_batch.py

# With comparison to planted ground truth
..\..\venv\Scripts\python.exe ..\..\scripts\run_corpus_batch.py --compare-ground-truth

# Clean produced-script benchmark (false positives only)
..\..\venv\Scripts\python.exe ..\..\scripts\run_clean_benchmark.py
```

See `docs/CORPUS_EVALUATION_GUIDE.md`, `docs/SCRIPTLENS_STATUS_REPORT.md`, and `benchmark/README.md`.
