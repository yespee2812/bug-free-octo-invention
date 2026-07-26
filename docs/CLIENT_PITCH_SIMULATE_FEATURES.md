# ScriptLens — Client Pitch: Orphan Scenes, Simulate Cut & Simulate Edit

| Field | Value |
|-------|-------|
| **Audience** | Writers, showrunners, script editors, producers |
| **Purpose** | Demo script and talking points for client presentations |
| **Date** | July 2026 |

---

## The one-line pitch

**Upload your script, see how scenes connect, preview what breaks if you cut or rewrite — without changing your original file.**

---

## What ScriptLens is actually tracking

Every scene introduces things the story carries forward: **props, objects, characters, setups**. ScriptLens builds a **dependency graph** — "Scene 3 only works because Scene 1 introduced the revolver."

That graph powers all three features below.

---

## Example script (use this in your demo)

```fountain
INT. ROOM ONE - DAY

A REVOLVER lies on the table.

INT. ROOM TWO - DAY

MARCUS grabs the revolver.

INT. ROOM THREE - NIGHT

MARCUS aims the revolver.
```

### Dependency chain

```
Scene 1 (Revolver introduced)
    ├──► Scene 2 (Marcus grabs it)
    │         └──► Scene 3 (Marcus aims it)
    └──► Scene 3 (direct setup link)
```

- **Scene 1** = setup
- **Scene 2** = carrier
- **Scene 3** = payoff

---

## 1. Orphan scenes — "What's floating loose?"

### What it means

A scene is an **orphan** when **no later scene depends on it**. Nothing downstream references what that scene introduced. It may be cuttable — or it may need a stronger tie-in.

**Pitch line:** *"These are scenes the rest of the script never looks back at."*

### Example

```fountain
INT. A - DAY

MARCUS holds a LEDGER.

INT. B - DAY

A lone STATUE sits in the dark.

INT. C - DAY

MARCUS reads the ledger.
```

| Scene | What happens | Orphan? |
|-------|----------------|---------|
| Scene 1 | Marcus gets a ledger | No — Scene 3 reads it |
| **Scene 2** | A statue appears | **Yes — nothing later uses it** |
| Scene 3 | Marcus reads the ledger | No — depends on Scene 1 |

### What the client sees in the UI

- Left panel: **ORPHANS — 1**
- Scene 2 flagged in the scene list
- Click orphans → jump to Scene 2

### How to say it to a client

> "You've got a beautiful statue scene, but the rest of the script never pays it off. ScriptLens flags that immediately — before your producer asks why it's in the cut."

### Writer actions orphans suggest

- **Cut it** (safe candidate)
- **Add a callback later** ("Marcus notices the same statue in the courthouse")
- **Merge it** into a scene that already carries story weight

---

## 2. Simulate cut — "If I delete this scene, what breaks?"

### What it means

Pick a scene, click **Simulate cut**. ScriptLens shows every **downstream scene** that would lose its setup. Your file is **never modified** — it's a preview only.

**Pitch line:** *"Cut with confidence. See the blast radius before you touch Final Draft."*

### Example: cut Scene 2 (the middle carrier)

You select **Scene 2 — INT. ROOM TWO** and simulate removing it.

**Result:**

| Impacted scene | Why it breaks | Dependency path |
|----------------|---------------|-----------------|
| **Scene 3** | Marcus aims the revolver, but the "grab" moment in Scene 2 is gone | Scene 2 → Scene 3 |

If you cut **Scene 1** instead, **both** Scene 2 and Scene 3 break — they both trace back to the revolver setup.

### What the client sees

- **Center panel:** Scene 2 shown as ghost/strikethrough — "Simulated removal"
- **Right panel:** "Impact of removing Scene 2"
- **Go to scene 3** — one click to the broken payoff
- **Banner:** *"Simulation only — your script is unchanged."*

### How to say it to a client

> "Writers cut constantly in development. Usually you find out three scenes later that something doesn't land. ScriptLens shows you that in one click — 'If I lose the pool scene, the custody climax loses its blanket setup.'"

### Real-world analogy for producers

> "It's like deleting a row in a spreadsheet and seeing which formulas break — but for story logic."

---

## 3. Simulate edit — "If I rewrite this scene, what changes?"

### What it means

Edit a scene's text in the workspace (e.g. remove the revolver from Scene 1), then click **Simulate edit**. ScriptLens **re-parses** the script with your change, rebuilds the graph, and shows:

- **Edges removed** (broken connections)
- **Scenes at risk** downstream
- **Orphan count** before vs. after

**Pitch line:** *"You don't have to cut a whole scene to break the story — sometimes you just rewrite one line. Simulate edit catches that too."*

### Example: rewrite Scene 1 without the revolver

**Original Scene 1:**

```fountain
INT. ROOM ONE - DAY

A REVOLVER lies on the table.
```

**Your edit:**

```fountain
INT. ROOM ONE - DAY

An empty table.
```

**Result:**

| Change | Detail |
|--------|--------|
| **Removed edge** | Scene 1 → Scene 2 (revolver setup gone) |
| **Downstream at risk** | Scene 2 |
| **Orphans** | Unchanged (same count) |

Scene 3 is still linked through Scene 2, but Scene 2 itself now has a **broken setup** — Marcus grabs a revolver that was never introduced.

### What the client sees

- Side-by-side or textarea edit mode for the selected scene
- Right panel: edge diff — "Removed: revolver introduced in Scene 1"
- Orphan delta: `Orphans: 0 → 0`
- **Go to scene** links for at-risk scenes

### How to say it to a client

> "Simulate cut is for restructuring — 'Do I need this scene at all?' Simulate edit is for polishing — 'Can I simplify this beat without killing the gun payoff in Act 3?'"

---

## Side-by-side comparison (slide-ready)

| Feature | Question it answers | Writer action | Touches your file? |
|---------|---------------------|---------------|-------------------|
| **Orphan scenes** | "What's disconnected from the rest of the story?" | Review, cut, or add callbacks | No |
| **Simulate cut** | "If I delete this entire scene, what breaks later?" | Restructure, reorder, tighten page count | No |
| **Simulate edit** | "If I change this scene's content, what connections drop?" | Rewrite setups, trim props, simplify action | No |

---

## 60-second live demo script

1. **Upload** the 3-scene revolver script (or a client's Fountain/PDF).
2. **Point to Orphans** — "Right now, zero orphans — every scene is wired in."
3. **Select Scene 2 → Simulate cut** — "Scene 3 loses its bridge. You'd need to move the grab into Scene 1 or 3."
4. **Clear simulation → Edit Scene 1** (remove revolver) → **Simulate edit** — "Same problem, different cause — you didn't cut a scene, you rewrote one line."
5. **Close with the promise:** "Your original file never changes. This is a writer's sandbox for structure."

---

## Real-script examples (for "does this work on real scripts?")

On a custody drama (*The Weight of Water* — 5-scene sample):

- **Orphans** might flag a scene that introduces something never referenced again
- **Simulate cut** on the court scene might show the finale losing the silver wedding band thread
- **Simulate edit** on the pool scene (blanket vs. towel wording) would show continuity edges shifting — pairs well with contradiction detection

---

## Closing lines for the pitch

| Audience | Line |
|----------|------|
| **Writers** | "Stop guessing whether a cut is safe." |
| **Showrunners / script editors** | "See structural risk before the table read." |
| **Producers** | "Fewer continuity surprises in production — cheaper fixes in development." |

### Tagline

**"Upload your script. See what breaks. Simulate the cut — without changing your file."**

---

## FAQ for client Q&A

### Does ScriptLens change my script?

**No.** All three features are read-only previews. Your uploaded file is never modified.

### What's the difference between simulate cut and simulate edit?

- **Simulate cut** = remove an entire scene and see downstream impact
- **Simulate edit** = rewrite one scene's content and see which story connections break

### What makes a scene an orphan?

A scene with **no incoming dependency edges** from later scenes (excluding the opening scene). Nothing in the rest of the script references what that scene set up.

### Can I use this on PDFs?

Yes. Upload Fountain, PDF, or FDX. PDFs are extracted and scene breaks are listed for review.

### Who is this for?

- Feature and TV writers doing structural passes
- Script editors evaluating cuts before notes go out
- Development executives assessing draft readiness
- Writing rooms exploring reorder options without breaking setups

---

## Technical summary (for technical buyers)

| Feature | Engine method | API endpoint |
|---------|---------------|--------------|
| Orphan scenes | `get_orphan_scenes()` | `GET /api/scripts/{id}/orphans` |
| Simulate cut | `get_simulate_cut_impact()` | `POST /api/scripts/{id}/simulate/cut` |
| Simulate edit | `get_simulate_edit_impact()` | `POST /api/scripts/{id}/simulate/edit` |

All three use the **scene dependency graph** built from continuity edges (props, objects, character setups). The graph is rebuilt on simulate edit; simulate cut walks downstream descendants of the removed scene.

---

*ScriptLens — structure intelligence for screenwriters.*
