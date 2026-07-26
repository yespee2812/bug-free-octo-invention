# Five-scene action demo — simulate cut, simulate edit, orphan

Script: [`action_5scene_simulate_demo.fountain`](action_5scene_simulate_demo.fountain)

| Scene | Heading | Role in demo |
|-------|---------|--------------|
| 1 | INT. ABANDONED WAREHOUSE - NIGHT | **Setup** — Gina opens **STEEL BRIEFCASE** (cut + edit target) |
| 2 | INT. RAIN-SLICK ALLEY - NIGHT | **Orphan** — motorcycle idles; nothing downstream references it |
| 3 | INT. PARKING GARAGE - NIGHT | Briefcase into trunk |
| 4 | INT. SAFEHOUSE - NIGHT | Rivals block Gina; briefcase threatened |
| 5 | EXT. DOCKS - NIGHT | Handoff to buyer |

---

## 1. Orphan scene

**Expected:** Scene **2** flagged as **hard orphan**.

```powershell
venv\Scripts\python.exe run_scriptlens.py docs\demo_scripts\action_5scene_simulate_demo.fountain --structure-only
```

Look for `LOOSELY CONNECTED SCENES` → Scene 2.

---

## 2. Simulate cut (1 scene)

**Remove:** Scene **1** (`scene_001`) — the warehouse briefcase setup.

**Expected:** **High** risk; downstream **Scenes 3, 4, 5** at risk.

```powershell
.\run_scriptlens.ps1 docs\demo_scripts\action_5scene_simulate_demo.fountain --structure-only --simulate-cut scene_001
```

**Web:** Upload script → select Scene 1 → **Simulate cut**.

---

## 3. Simulate edit (1 scene)

**Edit:** Scene **1** — replace the briefcase setup so the prop thread breaks.

**Original action line:**

```text
Gina pries open a STEEL BRIEFCASE … Stacks of banded cash inside.
```

**Modified action line (paste in edit panel):**

```text
Gina pries open an EMPTY CRATE … Nothing inside.
```

**Expected:** **Medium** risk; at least **1 dependency edge removed**; orphan count stays **1** (Scene 2 still orphan).

**Web:** Select Scene 1 → **Edit scene** → change text → **Run simulate edit**.

**API:**

```json
POST /api/scripts/{id}/simulate/edit
{
  "scene_id": "scene_001",
  "modified_text": "INT. ABANDONED WAREHOUSE - NIGHT\n\nGINA VASQUEZ, 32, ex-driver, pries open an EMPTY CRATE on a crate. Nothing inside.\n\nGINA\nStill heavy. Good."
}
```

---

## Quick verify script

```powershell
venv\Scripts\python.exe scripts\run_action_5scene_demo.py
```

Ground truth: [`tests/corpus/ground_truth/action_5scene_simulate_demo.yaml`](../../tests/corpus/ground_truth/action_5scene_simulate_demo.yaml)

**Word documents:**

| File | Purpose |
|------|---------|
| [`Action_5Scene_Simulate_Analysis_Packet.docx`](Action_5Scene_Simulate_Analysis_Packet.docx) | Blank worksheet for your own notes |
| [`Action_5Scene_Simulate_Analysis_Results.docx`](Action_5Scene_Simulate_Analysis_Results.docx) | **Completed engine results** (live run) |

Regenerate:

```powershell
venv\Scripts\python.exe scripts\build_action_5scene_demo_docx.py
```
