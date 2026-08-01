"""Render the story6 ScriptLens writer brief to a styled PDF.

Reuses the Markdown-to-PDF pipeline in ``scripts/md_to_pdf.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.md_to_pdf import html_to_pdf, markdown_to_html  # noqa: E402

OUTPUT_PATH = _REPO_ROOT / "docs" / "SCRIPTLENS_WRITER_BRIEF_STORY6.pdf"

DOCUMENT_MARKDOWN = """
# ScriptLens writer brief — RECLAIMED (story6)

*Worked example of the three product tools: orphan scenes, simulate cut, and
simulate edit. Numbers below are from running ScriptLens on
``scripts/regression testing/story6.fountain`` (analyze_structure + cut/edit
impact APIs).*

---

## What ScriptLens checks

| Product tool | Question | What writers may label |
| --- | --- | --- |
| **Orphan scenes** | Which scenes are structurally disconnected? | Scene ids (or none) + short quote |
| **Simulate cut** | If we delete scene X, what loses support later? | 2–4 cut rows: id → impacted ids + risk |
| **Simulate edit** | If we rewrite scene X, which links change? | 1–2 edits: what changed + what should break |

Structure-only: characters, locations, props, continuity, some story-function
intros. Not prose quality, theme, or “is the twist good.”

---

## Scene map (ScriptLens numbering)

| Scene id | # | Heading |
| --- | --- | --- |
| `scene_001` | 1 | INT. KITCHEN - DAY |
| `scene_002` | 2 | EXT. BACK GARDEN - CONTINUOUS (THROUGH WINDOW) |
| `scene_003` | 3 | INT. KITCHEN - CONTINUOUS |
| `scene_004` | 4 | EXT. STREET / EMMA'S FRONT PORCH - MOMENTS LATER |
| `scene_005` | 5 | INT. EMMA'S LIVING ROOM - CONTINUOUS |
| `scene_006` | 6 | INT. KITCHEN - HOUR EARLIER (DIFFERENT ANGLE) |
| `scene_007` | 7 | INT. EMMA'S LIVING ROOM - PRESENT |
| `scene_008` | 8 | EXT. BACK GARDEN - LATER (DUSK) |

**8 scenes, full structure mode.** The bare `FLASHBACK:` line is not its own
scene — scene 6 is the flashback kitchen; scene 7 returns to Emma’s living room.

**Format rule:** every scene break must be a real Fountain slugline
(`INT.` / `EXT.` / `INT/EXT.` / `I/E.`). Prose without sluglines collapses into
one scene and orphan/cut labels become meaningless.

---

## 1. Orphan scenes — ScriptLens result

**Orphans found: 0** (empty list).

Why that fits this script:

- Jessica / Tom / kitchen / garden / Emma / Gracie recur
- Flashback (scene 6) shares kitchen + Jessica + Tom / bench wound with 1 and 3
- Closing garden (scene 8) pays off Gracie + garden from scene 2

### Writer label (clean / Family B)

```yaml
expected_orphans: []
notes: >
  Clean connected thriller short. No hard orphan intended.
  Continuity via Jessica, kitchen/garden, Emma, Gracie.
```

To plant a hard orphan instead: add a scene with no shared named character,
no location family, and no tracked CAPS prop with the rest of the script.

---

## 2. Simulate cut — ScriptLens result (every scene)

| Cut this | Risk | ScriptLens summary | Impacted later scenes |
| --- | --- | --- | --- |
| `scene_001` Kitchen / death | **high** | Drops Introduces Jessica; affects 6 later scenes | 3, 4, 5, 6, 7, 8 |
| `scene_002` Garden / Gracie | **low** | Beats not uniquely required later | _(none listed)_ |
| `scene_003` Kitchen / police | **low** | Drops Introduces Female Officer | 4 |
| `scene_004` Porch → Emma | **low** | Drops Introduces Emma | 5 |
| `scene_005` Emma’s living room | **low** | Not uniquely required later | _(none)_ |
| `scene_006` Flashback kitchen | **low** | Not uniquely required later | _(none)_ |
| `scene_007` Living room present | **low** | Not uniquely required later | _(none)_ |
| `scene_008` Garden dusk / end | **none** | Terminal; safe structurally | _(none)_ |

**“Low risk” ≠ “useless scene.”** It means later scenes are not uniquely
structurally dependent on it. Drama can still break.

### Suggested cut labels (pick 2–4, not all eight)

```yaml
expected_simulate_delete:
  - scene_id: scene_001
    expect_impacted:
      - scene_003
      - scene_004
      - scene_005
      - scene_006
      - scene_007
      - scene_008
    expect_risk_in: [high, medium]
    anchor: >
      Scene 1 introduces Jessica and the kitchen death; later scenes
      depend on her.

  - scene_id: scene_008
    expect_impacted: []
    expect_risk_in: [none, low]
    anchor: >
      Ending garden beat; nothing comes after it.

  - scene_id: scene_004
    expect_impacted: [scene_005]
    expect_risk_in: [low, medium]
    anchor: >
      Emma is introduced on the porch; living-room scene needs her.
```

---

## 3. Simulate edit — ScriptLens results on story6

Four teaching edits were run through ScriptLens. Only Edit A changed structure.

### Edit A — Strip dog/bone plant (`scene_002`) → structure changes

**Intent:** remove Gracie burying the bone (plant for the ending).

**ScriptLens:** risk **low**; **1 link changed** (`scene_002 → scene_008`):
object channel **GRACIE** dropped; location **BACK GARDEN** remains.
Orphan count still 0.

```yaml
expected_simulate_edit:
  - scene_id: scene_002
    modified_text: |
      EXT. BACK GARDEN - CONTINUOUS (THROUGH WINDOW)

      Outside, the vegetable patch is quiet. Fresh rocket seedlings
      sit undisturbed in the soil.
    expect_edges_changed_min: 1
    expect_edges_removed_min: 0
    expect_risk_in: [low, medium]
    anchor: >
      Removing Gracie weakens the object link to the dusk garden payoff.
```

### Edit B — Strip gold locket (`scene_003`) → no dependency change

Dramatic detail; not treated as a tracked continuity prop here.
**ScriptLens:** no story dependencies changed.

### Edit C — Strip shoelace beat (`scene_006`) → no dependency change

Clever crime beat, but not a recurring tracked prop across scenes.
**ScriptLens:** no dependency change.

### Edit D — Cosmetic “Tea” → “Coffee” (`scene_005`) → no-op

**ScriptLens:** no dependency change. Good control edit.

```yaml
  - scene_id: scene_005
    modified_text: |
      (same scene; Emma says "Coffee." instead of "Tea.")
    expect_edges_changed_min: 0
    expect_edges_removed_min: 0
    expect_risk_in: [none, low]
    anchor: >
      Cosmetic word swap only; no continuity referent removed.
```

**Writer tip:** not every object is structural. Prefer CAPS plants that recur
(`GRACIE`, `BRASS KEY`, `STEEL BRIEFCASE`).

---

## 4. Variation menu (practice on clones of this script)

| Code | Variation | What to change | Expected label |
| --- | --- | --- | --- |
| **B** | Clean | Keep as-is | `expected_orphans: []` |
| **H1** | Hard orphan | Insert unrelated diner + new cast | that scene in orphans |
| **F1** | Chekhov reinforce | CAPS prop in scene 1, reuse in 8 | still `[]` orphans |
| **F4** | Imagined insert | `(IMAGINED)` / DREAM slugline | exempt / not orphan |
| **C1** | Cut intro | Label cut of `scene_001` | high impact set |
| **C2** | Cut ending | Label cut of `scene_008` | empty impact |
| **C4** | Edit plant | Strip Gracie from scene 2 | edges changed ≥ 1 |
| **C6** | Edit no-op | Tea→Coffee in scene 5 | edges changed = 0 |

---

## 5. What to submit per script

1. Scene count you believe is correct  
2. Orphans: list or `none`, each with one evidence quote  
3. Cuts: max 2–4 rows (scene → impacted → risk)  
4. Edits: max 1–2 rows (what changed → what should break / not break)

Label **story structure intent + quotes**. Do not invent engine output.
ScriptLens is an advisory cross-check later — not the definition of gold.

---

## Bottom line for story6

- **Orphans:** none — clean connected example  
- **Simulate cut:** scene 1 is high-risk; scene 8 is safe; 3 and 4 matter as intros  
- **Simulate edit:** stripping **Gracie** from the garden plant is the clear
  structural edit; locket / shoelace / tea→coffee are non-structural here  

Source file: `scripts/regression testing/story6.fountain`
"""


def main() -> None:
    """Build the story6 writer-brief PDF."""
    html = markdown_to_html(DOCUMENT_MARKDOWN)
    path = html_to_pdf(html, OUTPUT_PATH)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
