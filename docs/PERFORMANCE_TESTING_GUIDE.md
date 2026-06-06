# ScriptLens Core Engines — Performance Testing Guide

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | May 2026 |
| **Purpose** | Tune and validate `scene_dependency` and `plot_contradiction` before extension/API work |
| **Repo** | `scriptlensCore` |
| **Related** | [ARCHITECTURE.md](./ARCHITECTURE.md) |

---

## What you are testing

| Engine | Module | Main operations to time |
|--------|--------|-------------------------|
| **Scene dependency** | `scene_dependency.py` | `parse_fountain_text`, `build_graph`, `get_delete_impact`, `get_scene_dependencies`, `get_orphan_scenes` |
| **Plot contradiction** | `plot_contradiction.py` | `extract_facts`, `run_tier1`, `run_tier2`, `run_analysis` |
| **Combined** | `scriptlens_analyser.py` | `analyze_screenplay` (full pipeline) |

### Architecture targets (from product spec)

| Operation | Target p95 |
|-----------|------------|
| Fountain parse (~120 scenes) | < 200 ms |
| Dependency graph build | < 400 ms |
| Delete-impact query (single scene) | < 50 ms |
| Full continuity (Tier 1 + 2, no Tier 3) | < 800 ms |
| Combined `analyze_screenplay` (~120 scenes) | < 800 ms |

Use these as tuning goals, not hard failures on day one.

---

## Prerequisites

1. Use the project **venv** (required by `.cursorrules`):

   ```powershell
   cd c:\Users\subhi\Documents\Subhiksha_Files\scriptlensCore
   .\venv\Scripts\python.exe --version
   ```

2. Confirm spaCy model is installed:

   ```powershell
   .\venv\Scripts\python.exe -c "import spacy; spacy.load('en_core_web_sm'); print('spaCy OK')"
   ```

3. Close heavy apps during timed runs (browser with 50 tabs, etc.) so numbers are comparable.

4. Create a results folder (optional but recommended):

   ```powershell
   New-Item -ItemType Directory -Force -Path .\docs\perf_results
   ```

---

## Fifteen steps to test and tune performance

### Step 1 — Lock a baseline machine profile

Record once and reuse for every run:

- CPU model, RAM, Windows build
- Python version from venv
- Whether laptop is on power saver

Save in `docs/perf_results/baseline_machine.txt`. Performance numbers are only comparable on the same profile.

---

### Step 2 — Run accuracy regressions first (correctness gate)

Performance tuning is meaningless if results are wrong.

```powershell
.\venv\Scripts\python.exe run_dependency_test.py
.\venv\Scripts\python.exe run_contradiction_test.py
.\venv\Scripts\python.exe real_screenplay_test.py
```

**Pass criteria:**

- Dependency: expected delete-impact for `scene_005` and `scene_001`; orphans `scene_002`, `scene_004`
- Contradiction: 4/4 Tier 1 + 1/1 Tier 2 on gold screenplay; 0 false positives on clean scenes
- Real screenplay: ≥ 20 scenes, ≥ 1 edge, ≥ 2 of 3 planted contradiction types

Do not tune thresholds until these pass.

---

### Step 3 — Measure built-in fixture sizes

Know your baseline workload:

```powershell
.\venv\Scripts\python.exe -c "
from test_screenplay import SAMPLE_SCREENPLAY
from test_contradiction_screenplay import CONTRADICTION_SCREENPLAY
from real_screenplay_test import REAL_SCREENPLAY
from scene_dependency import SceneDependencyEngine
e = SceneDependencyEngine()
for name, text in [('sample', SAMPLE_SCREENPLAY), ('contradiction', CONTRADICTION_SCREENPLAY), ('real', REAL_SCREENPLAY)]:
    n = len(e.parse_fountain_text(text))
    print(f'{name}: {n} scenes, {len(text)} chars')
"
```

Expected ballpark today: **12 / 12 / 22 scenes**. Record in your results sheet.

---

### Step 4 — Time each engine stage (small scripts)

Run the benchmark snippet below and save output:

```powershell
.\venv\Scripts\python.exe scripts\benchmark_engines.py --fixture all --runs 10
```

Script location: `scripts/benchmark_engines.py` (included in this repo).

Record for each fixture:

- `parse_ms` (p50, p95)
- `build_graph_ms` (p50, p95)
- `delete_impact_ms` (p50, p95)
- `extract_facts_ms`, `tier1_ms`, `tier2_ms`, `full_analysis_ms` (p50, p95)

---

**Note:** On a cold run, most time is often **spaCy model load** inside `parse_fountain_text` (new `SceneDependencyEngine()` per iteration). `analyze_screenplay` also creates **two** engines (dependency + contradiction), so the full pipeline timing is higher than the sum of isolated stages. For production, load spaCy once and reuse — see Step 13.

### Step 5 — Time the combined pipeline (end-to-end)

```powershell
.\venv\Scripts\python.exe -c "
import time
from statistics import median
from scriptlens_analyser import analyze_screenplay
from real_screenplay_test import REAL_SCREENPLAY

times = []
for _ in range(10):
    t0 = time.perf_counter()
    analyze_screenplay(REAL_SCREENPLAY)
    times.append((time.perf_counter() - t0) * 1000)
times.sort()
print(f'analyze_screenplay (22 scenes): p50={median(times):.1f}ms min={times[0]:.1f}ms max={times[-1]:.1f}ms')
"
```

Repeat after every tuning change. Target: stay well under 800 ms on ~22 scenes; extrapolate for 120 scenes.

---

### Step 6 — Scale test with a long script (structural stress)

Built-in fixtures are small. Add **one long Fountain file** (aim **60–120 scenes**):

1. Export a full draft as `.fountain` or `.txt` into `tests/corpus/long_script.fountain`
2. Run:

   ```powershell
   .\run_scriptlens.ps1 tests\corpus\long_script.fountain
   ```

3. Time it:

   ```powershell
   .\venv\Scripts\python.exe scripts\benchmark_engines.py --path tests\corpus\long_script.fountain --runs 5
   ```

**Watch for:**

- Parse time growing linearly with scene count
- Graph build time growing with scenes × entities
- Tier 2 growing roughly with fact pairs (can spike on wordy scripts)

If p95 exceeds 800 ms on ~120 scenes, tune before building the API.

---

### Step 7 — Stress delete-impact and upstream queries

Dependency simulation must feel instant in the UI.

```powershell
.\venv\Scripts\python.exe -c "
import time
from statistics import median
from scene_dependency import SceneDependencyEngine
from real_screenplay_test import REAL_SCREENPLAY

engine = SceneDependencyEngine()
scenes = engine.parse_fountain_text(REAL_SCREENPLAY)
engine.build_graph(scenes)

def bench(fn, label, n=50):
    times = [(time.perf_counter(), fn(), time.perf_counter()) for _ in range(n)]
    ms = sorted((t1-t0)*1000 for t0,_,t1 in times)
    print(f'{label}: p50={median(ms):.2f}ms max={ms[-1]:.2f}ms')

bench(lambda: engine.get_delete_impact('scene_001'), 'delete_impact scene_001')
bench(lambda: engine.get_scene_dependencies('scene_015'), 'upstream scene_015')
bench(lambda: engine.get_orphan_scenes(), 'orphans')
"
```

**Target:** delete-impact p95 < 50 ms even on long scripts (usually much lower).

---

### Step 8 — Profile memory (spaCy loads once per engine instance)

```powershell
.\venv\Scripts\python.exe -c "
import tracemalloc
from scriptlens_analyser import analyze_screenplay
from real_screenplay_test import REAL_SCREENPLAY

tracemalloc.start()
analyze_screenplay(REAL_SCREENPLAY)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'Peak RAM during one analyze_screenplay: {peak / 1024 / 1024:.1f} MB')
"
```

Run twice: cold start vs reusing engines. In production, load spaCy **once** at API startup — measure that steady-state peak.

**Target:** comfortable on 8 GB machines (architecture assumes ~24 MB extension; backend will be higher due to spaCy).

---

### Step 9 — Test PDF ingestion path separately

PDF adds extraction cost before engines run.

```powershell
.\run_scriptlens.ps1 path\to\your_screenplay.pdf --save-extracted tests\corpus\extracted.txt
```

Time PDF vs the saved `.txt` on the same script:

```powershell
.\venv\Scripts\python.exe scripts\benchmark_engines.py --path tests\corpus\extracted.txt --runs 5
```

Record PDF extract time separately from engine time. Writers using PDF should not pay duplicate spaCy loads.

---

### Step 10 — Tune dependency engine (if graph build is slow)

| Knob | Location | Effect |
|------|----------|--------|
| Object extraction | `_extract_objects_from_action` | Fewer noun chunks → fewer edges, faster build |
| Object normalization | `_normalize_object_key` | Stops duplicate edges from “the briefcase” vs “briefcase” |
| Edge merge cap | `_upsert_edge` | Consider capping merged weight so graph stats stay stable |

**How to tune:**

1. Change one knob at a time
2. Re-run Step 2 (accuracy) + Step 4 (timing)
3. Log before/after in `docs/perf_results/dependency_tuning_log.md`

**Do not** remove character edges to gain speed unless accuracy tests still pass.

---

### Step 11 — Tune contradiction engine (if Tier 2 is slow or noisy)

| Knob | Location | Default | Tradeoff |
|------|----------|---------|----------|
| `TIER2_SIMILARITY_THRESHOLD` | `plot_contradiction.py` | `0.35` | Higher → fewer Tier 2 flags, faster comparisons |
| `TIER2_MIN_CONFIDENCE` | `plot_contradiction.py` | `0.55` | Higher → fewer items shown |
| `OPPOSING_STATE_TERMS` | `plot_contradiction.py` | list | More terms → better recall, slightly more work |
| Fact types extracted | `_extract_*_facts` methods | all on | Disable noisy types to speed up |

**Tuning procedure:**

1. Run `run_contradiction_test.py` after each change
2. Run on 3–5 real scripts manually; note false positives
3. Target architecture FP rate **< 10%** before shipping

---

### Step 12 — Build a 3-script performance matrix

Create `docs/perf_results/matrix.csv`:

```csv
script_id,scenes,chars,parse_p95_ms,graph_p95_ms,delete_impact_p95_ms,tier1_ms,tier2_ms,full_p95_ms,contradictions_found,notes
synthetic_12,12,,,,,,,,
contradiction_12,12,,,,,,,,
real_22,22,,,,,,,,
long_120,,,,,,,,,,
```

Fill one row per script after Steps 4–6. This is your tuning dashboard.

---

### Step 13 — Run repeated cold vs warm benchmarks

Simulates API behavior:

| Mode | What it means | How to test |
|------|---------------|-------------|
| **Cold** | New `SceneDependencyEngine()` + `ContradictionEngine()` each request | New instance per run in benchmark |
| **Warm** | Reuse one engine instance | Single instance, loop 10× |

Warm should be much faster on parse+NLP because spaCy is already loaded. **Production must use warm mode.**

```powershell
.\venv\Scripts\python.exe scripts\benchmark_engines.py --fixture real --runs 10 --cold
.\venv\Scripts\python.exe scripts\benchmark_engines.py --fixture real --runs 10 --warm
```

---

### Step 14 — Define exit criteria before moving to FastAPI/extension

Check all boxes:

| # | Criterion | Target |
|---|-----------|--------|
| 1 | Accuracy regressions | All three test runners pass |
| 2 | `analyze_screenplay` on ~22 scenes | p95 < 200 ms (local dev) |
| 3 | Long script (~120 scenes) | p95 < 800 ms (Tier 1+2 only) |
| 4 | `get_delete_impact` | p95 < 50 ms |
| 5 | False positives on 5 real scripts | < 10% dismissed as wrong |
| 6 | Memory peak (one warm analysis) | Documented; acceptable on 8 GB |
| 7 | Tuning log | At least one recorded change with before/after timings |
| 8 | PDF path | Extract + analyse timed separately |

If long-script p95 fails, tune Steps 10–11 before building the extension.

---

### Step 15 — Archive results and freeze engine version

1. Commit `docs/perf_results/matrix.csv` and tuning logs (no full screenplays if confidential).
2. Tag the commit or note git SHA in `docs/perf_results/ENGINE_BASELINE.txt`:

   ```
   date=2026-05-26
   commit=<sha>
   tier2_threshold=0.35
   notes=Baseline before FastAPI
   ```

3. Only then start FastAPI (`/analyse/dependencies`, `/scene/delete-impact`, continuity on demand).

---

## Quick reference — commands

```powershell
# From repo root
cd c:\Users\subhi\Documents\Subhiksha_Files\scriptlensCore

# Correctness
.\venv\Scripts\python.exe run_dependency_test.py
.\venv\Scripts\python.exe run_contradiction_test.py
.\venv\Scripts\python.exe real_screenplay_test.py

# Benchmark (after scripts/benchmark_engines.py exists)
.\venv\Scripts\python.exe scripts\benchmark_engines.py --fixture all --runs 10
.\venv\Scripts\python.exe scripts\benchmark_engines.py --path tests\corpus\long_script.fountain --runs 5

# Full report on a file
.\run_scriptlens.ps1 tests\corpus\long_script.fountain
```

---

## What to do when a step fails

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Parse returns 0 scenes | Non-Fountain formatting | Fix headings (`INT.` / `EXT.`); add to corpus notes |
| Graph build very slow | Too many object noun chunks | Filter generic objects in `_extract_objects_from_action` |
| Tier 2 very slow | Many facts × pairwise compare | Raise `TIER2_SIMILARITY_THRESHOLD` slightly; re-test accuracy |
| Many false positives | Tier 2 too aggressive | Raise `TIER2_MIN_CONFIDENCE`; expand flashback markers |
| Missed contradictions | Tier 2 too weak | Lower threshold slightly; add opposing term pairs |
| Delete-impact slow | Huge graph | Rare; check scene count; profile `nx.descendants` |

---

## Tuning checklist (printable)

- [ ] Step 1: Machine baseline recorded
- [ ] Step 2: All regression tests pass
- [ ] Step 3: Fixture sizes recorded
- [ ] Step 4: Per-stage timings recorded
- [ ] Step 5: Combined pipeline timed
- [ ] Step 6: Long script (60–120 scenes) tested
- [ ] Step 7: Delete-impact / upstream timed
- [ ] Step 8: Memory peak recorded
- [ ] Step 9: PDF path timed (if used)
- [ ] Step 10: Dependency knobs tuned (if needed)
- [ ] Step 11: Contradiction knobs tuned (if needed)
- [ ] Step 12: Performance matrix filled
- [ ] Step 13: Cold vs warm benchmark compared
- [ ] Step 14: Exit criteria met
- [ ] Step 15: Baseline archived in git

---

*End of guide — ScriptLens Core Engines Performance Testing v1.0*
