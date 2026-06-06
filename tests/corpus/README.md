# ScriptLens test corpus

## Folders

| Folder | You put | Generated |
|--------|---------|-----------|
| `input/` | Your `.fountain`, `.txt`, or `.pdf` screenplays | — |
| `ground_truth/` | One `.yaml` per script (manual mapping) | — |
| `reports/` | — | `*_report.txt`, `*.json`, `manifest.csv`, `*_evaluation.txt` |

## Commands

```powershell
# One script — customer report in terminal
..\..\run_scriptlens.ps1 input\my_script.fountain

# All scripts in input/
..\..\venv\Scripts\python.exe ..\..\scripts\run_corpus_batch.py

# With comparison to your YAML
..\..\venv\Scripts\python.exe ..\..\scripts\run_corpus_batch.py --compare-ground-truth
```

See `docs/CORPUS_EVALUATION_GUIDE.md` for the full workflow.
