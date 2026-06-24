# Writer outreach — send-ready message

Use the **Full email** below when sending materials to participants.  
Replace every `[bracket]` before sending.

---

## Subject line

**ScriptLens continuity corpus — your scripts, instructions & deadline**

---

## Full email (copy from here)

---

**Subject:** ScriptLens continuity corpus — your scripts, instructions & deadline

---

Dear [Writer name],

Thank you for agreeing to take part in this project. As discussed, I'm building **ScriptLens** — a tool that helps screenwriters catch **story continuity problems** (timeline slips, props that change hands with no explanation, characters who contradict their backstory, and similar logic breaks).

To make the tool work on **real production scripts**, I need your help. You will receive **three starter screenplays** from me. Your job is to inject **deliberate continuity mistakes** into each one, then return the edited scripts plus a **written answer sheet** documenting every mistake you planted.

**Important:** Write the way you normally would on a professional job — natural dialogue, action, and scene description. **Do not write for a machine.** We will run ScriptLens on your scripts and compare the tool's output to your answer sheet. The answer sheet is the key; we are testing the software, not you.

---

### What you are receiving from me

I am sending you **three scripts**:

| # | Script | Scenes | Your task |
|---|--------|--------|-----------|
| 1 | **5-scene script** | 5 | Inject **2–3** deliberate continuity errors |
| 2 | **10-scene script** | 10 | Inject **4–5** deliberate continuity errors |
| 3 | **Full-length feature script** | Full feature | Inject **8–12** deliberate continuity errors |

**Files attached / linked in this email:**
- `[WRITER_NAME]_5scene_script.fountain` *(or .pdf)*
- `[WRITER_NAME]_10scene_script.fountain` *(or .pdf)*
- `[WRITER_NAME]_feature_script.fountain` *(or .pdf)*
- **Error Injection Cheat Sheet** (PDF — 1-page quick reference)
- **Full brief** (`SCREENWRITER_ERROR_INJECTION_GUIDE.md`)
- **Blank answer sheet template** (`ERROR_INJECTION_LOG_TEMPLATE.yaml`)

Please **keep the original story, characters, and scene headings** wherever possible. Change or add only what you need to plant errors — like a light continuity pass, not a rewrite.

---

### What you need to return

For **each of the three scripts**, send back **two files**:

1. **The edited script** (same format: `.fountain`, `.pdf`, or `.txt`)
2. **One Error Injection Log** (answer sheet) — YAML or Word/Google Doc if YAML is awkward

**Total: 6 files** (3 scripts + 3 logs)

#### File naming (please follow exactly)

Use your surname or initials so we can track submissions:

```
[SURNAME]_5scene_errors.fountain
[SURNAME]_5scene_ERROR_LOG.yaml

[SURNAME]_10scene_errors.fountain
[SURNAME]_10scene_ERROR_LOG.yaml

[SURNAME]_feature_errors.fountain
[SURNAME]_feature_ERROR_LOG.yaml
```

Example: `Patel_5scene_errors.fountain` + `Patel_5scene_ERROR_LOG.yaml`

You may zip everything as: `[SURNAME]_scriptlens_submission.zip`

---

### Scene numbering (for your answer sheet)

**Scene 1** = the **first** `INT.` or `EXT.` heading in the file, top to bottom.  
**Scene 2** = the second heading, and so on.

Every error in your log must list:
- **Establishing scene** — where the first fact is set up  
- **Contradicting scene** — where the script breaks that fact  

---

### The 12 types of errors you can inject

Use **natural phrasing** — dialogue, action, or description. Pick types that fit each story. Across all three scripts combined, please use **at least 8 different categories**.

| # | Category | What the mistake looks like |
|---|----------|----------------------------|
| 1 | **Character dead then alive** | Character is clearly dead/killed, later appears active with no valid explanation (no prior on-page reveal, dream, flashback, twin, etc.) |
| 2 | **Timeline slip** | Days, dates, or "today/yesterday" references contradict each other in linear story order |
| 3 | **Role / profession clash** | Same character has two incompatible jobs or identities (e.g. surgeon then lawyer) with no transformation arc |
| 4 | **Prop — wrong owner** | A specific prop is with Character A, then Character B has it — **no scene showing it changed hands** |
| 5 | **Prop — destroyed but back** | Object is burned, smashed, or destroyed — then used or held again with no replacement |
| 6 | **Prop — lost then back** | Character loses or leaves something behind — **same character** has it again with no recovery scene |
| 7 | **Injury — wrong body side** | Same character: injury on left arm/leg, later same wound on the **opposite** side |
| 8 | **Injury — no recovery** | Character seriously hurt or unconscious — then fully fine shortly after, **no hospital, time jump, or treatment** |
| 9 | **Relationship — impossible** | Same two people: relations that cannot coexist (e.g. siblings who are also spouses, parent and child who are also married) |
| 10 | **Relationship — parent flip** | A is B's parent in one place, B is A's parent later |
| 11 | **Location clash** | Same place described in opposite ways (abandoned vs busy, burned down vs intact) without a time jump or rebuild |
| 12 | **World rule broken** *(optional)* | Script states a rule ("no one can leave the dome") — later breaks it with no on-page explanation |

#### Spread your errors

- **5-scene script:** errors across different scenes, not all in Scene 5  
- **10-scene script:** opening, middle, and end  
- **Feature script:** roughly **2–4 errors per act**

#### Do **not** count these as planted errors

- Enemies becoming friends, breakups, divorce (valid story arcs)  
- Fake death **explained on the page** before the character returns  
- Flashbacks, dreams, or clearly marked time jumps  
- Prop handoffs shown on page (`gives`, `hands`, `steals`, `finds`)  
- Anything you did **not** deliberately plant  

---

### How to fill in the answer sheet (Error Injection Log)

**One log per script.** Copy the template I attached, or use the structure below.

#### Header (top of each log)

```yaml
script_title: "Harbor Run"              # your title or ours
filename: "Patel_5scene_errors.fountain"
writer_name: "Alex Patel"
date: "2026-06-20"
script_type: "5-scene"                  # or "10-scene" or "full-length"
total_scenes: 5
base_script_provided_by_us: true        # true for all three scripts we send you
```

#### One block per planted error

```yaml
planted_errors:

  - error_number: 1
    category: "Timeline slip"           # plain English from the table above
    establishing_scene: 3               # integer
    contradicting_scene: 7              # integer
    characters_involved: ["DETECTIVE ROSS"]
    objects_involved: []                # e.g. ["blue ledger"] if relevant
    establishing_moment: |
      ROSS: Today's Monday. We move at dawn.
    contradicting_moment: |
      ROSS: Yesterday was Wednesday. I still can't explain it.
    how_a_reader_notices: "Monday and Wednesday cannot both be correct with no flashback."
    writer_intent: deliberate
```

**Required for every error:**
- `category` — which type from the table (plain English)  
- `establishing_scene` and `contradicting_scene`  
- `establishing_moment` — **quote or close paraphrase** from the script  
- `contradicting_moment` — **quote or close paraphrase** from the script  
- `how_a_reader_notices` — one sentence  
- `characters_involved` / `objects_involved` where relevant  

#### Scene index (required at end of each log)

List **every** scene heading in order so we can verify scene numbers:

```yaml
scene_index:
  - scene_number: 1
    heading: "INT. POLICE STATION - DAY"
  - scene_number: 2
    heading: "EXT. HARBOR - NIGHT"
  # ... all scenes
```

#### Summary (required)

```yaml
summary:
  total_planted_errors: 3
  categories_used:
    - "Timeline slip"
    - "Prop — wrong owner"
    - "Character dead then alive"
```

#### Notes (optional)

Use for anything ambiguous, genre, or story choices that are **not** errors.

---

### Quality checklist before you submit

- [ ] All **three** edited scripts returned  
- [ ] All **three** answer sheets returned  
- [ ] Every planted error is **documented** — nothing missing from the logs  
- [ ] Nothing in the logs that was **accidental** — only deliberate mistakes  
- [ ] Scripts still read like **production drafts**, not test exercises  
- [ ] No labels inside the script ("CONTINUITY ERROR HERE")  
- [ ] Errors are **not explained away** in the next scene (no handoff, flashback, or recovery that fixes the mistake)  
- [ ] File names follow the naming convention above  

---

### Timeline, payment & questions

- **Deadline:** [DATE — e.g. 4 weeks from today]  
- **Payment:** [AMOUNT / payment terms — e.g. ₹X on delivery, via UPI/bank transfer]  
- **Submit to:** [YOUR EMAIL / shared Drive link / WeTransfer]  
- **Questions:** Reply to this email anytime. If something is ambiguous, note it in the log's `notes` field rather than guessing.

---

### Rights & confidentiality

Your work will be used **only for internal testing and improving ScriptLens**. Scripts will not be published, produced, or shared publicly without separate permission. [Add NDA / agreement reference if applicable.]

Thank you again — this work directly helps build continuity checking that is useful for working screenwriters.

Warm regards,  
[Your full name]  
[Project name — ScriptLens]  
[Email] | [Phone optional]

---

## Attachments checklist (before you hit Send)

- [ ] 5-scene starter script  
- [ ] 10-scene starter script  
- [ ] Full-length starter script  
- [ ] `SCREENWRITER_ERROR_CHEAT_SHEET.pdf`  
- [ ] `SCREENWRITER_ERROR_INJECTION_GUIDE.md`  
- [ ] `ERROR_INJECTION_LOG_TEMPLATE.yaml`  

---

## Short text / WhatsApp version

If you need a shorter message (link to Drive for files):

---

 Hi [Name], thanks again for joining the ScriptLens continuity corpus.

 **You get:** 3 starter scripts from me — 5-scene, 10-scene, and full feature.

 **You do:** Inject deliberate continuity mistakes (timeline slips, props jumping owners, dead characters returning, etc.) using natural writing. Return **3 edited scripts + 3 answer sheets** (one log per script).

 **Error counts:** 2–3 errors in the 5-scene · 4–5 in the 10-scene · 8–12 in the feature. Use at least 8 different error types across all three. Full list & templates in the attached brief.

 **Answer sheet must include:** scene numbers (Scene 1 = first INT/EXT), quotes of establishing & breaking moments, and a scene index.

 **Deadline:** [DATE] · **Fee:** [AMOUNT] · **Send to:** [EMAIL/LINK]

 Full instructions + cheat sheet attached. Questions anytime!

 — [Your name]

---
