# Internal mapping — writer categories → ScriptLens engine

**Audience:** ScriptLens team only (not for screenwriters).

Use this when converting a writer's **Error Injection Log** into `tests/corpus/ground_truth/*.yaml` and when interpreting evaluation results.

---

## How matching works today

The batch evaluator compares on **exact keys**:

```
(type, scene_number_a, scene_number_b)
```

- Scene numbers = order of `INT.` / `EXT.` headings in the file (same as customer report).
- Writer logs use **plain English categories**; you map to **`type`** below.
- If the engine finds the right issue but **wrong scene pair**, it counts as **missed** — note in evaluation notes and consider manual review.
- Tier 2 types are prefixed with `semantic_` (e.g. `semantic_location`).

---

## Master mapping table

| # | Writer category (plain English) | Engine `type` | Customer report label | Confidence tier | Maps from writer log |
|---|--------------------------------|---------------|-------------------------|-----------------|----------------------|
| 1 | Character dead then alive | `character_alive_status` | A character is dead in one scene but alive in another | Confirmed (~95%) | `category`, `establishing_scene`, `contradicting_scene`, `characters_involved` |
| 2 | Timeline slip / calendar doesn't line up | `timeline_consistency` | The timeline or day of the week does not line up | Confirmed (~92%) | `establishing_moment`, `contradicting_moment`, scenes |
| 3 | Role / profession clash | `character_trait_conflict` | A character's job or role contradicts an earlier scene | Confirmed (~85%) | `characters_involved`, both moments |
| 4 | Prop — wrong owner (no handoff) | `object_ownership` | An important object changes hands with no explanation | Confirmed (~80%) | `objects_involved`, characters in each moment |
| 5 | Prop — destroyed but back | `object_destroyed` | An object is destroyed but appears again later | Confirmed (~82%) | `objects_involved`, destroy vs reappear scenes |
| 6 | Prop — lost then back (same person) | `object_lost` | An object is lost or left behind but turns up again | Possible (~60%) | `objects_involved`, same character both times |
| 7 | Injury — wrong body side | `medical_laterality` | An injury switches sides of the body between scenes | Possible (~60%) | `characters_involved`, injury descriptions |
| 8 | Injury — no recovery | `medical_recovery` | A serious injury or condition vanishes with no recovery | Possible (~60%) | `characters_involved`, injury → “fine” scenes |
| 9 | Relationship — impossible (siblings + spouses, etc.) | `relationship_conflict` | Two characters' relationship contradicts an earlier scene | Confirmed (~85%) | `characters_involved`, both relation moments |
| 10 | Relationship — parent/child reversed | `relationship_role_inversion` | A family role is reversed between two characters | Confirmed (~85%) | `characters_involved`, both moments |
| 11 | Location — same place, opposite description | `semantic_location` | A place is described differently in two scenes | Tier 2 (~75% variable) | location name, both descriptions, scenes |
| 12 | World rule broken | *(none yet)* | — | Capture only | Log under `notes`; not auto-flagged — do not add to `planted_contradictions` unless manually verified |

---

## Valid arcs — do NOT map to engine types

These are **intentional story changes**, not continuity errors. If a writer logs them, move to `notes` only.

| Writer description | Why we skip |
|--------------------|-------------|
| Enemies → friends | Social ties change legitimately |
| Dating → breakup → back together | Romantic arc |
| Married → divorced | Valid plot |
| Fake death with on-page reveal before return | Explained twist, not pure continuity break |
| Flashback / dream / time jump clearly marked | Valid structure |
| Prop handoff on page (`gives`, `hands`, `steals`) | Not an ownership error |

---

## YAML conversion cheat sheet

Writer log field → ground truth field:

| Writer log | Ground truth YAML |
|------------|-------------------|
| `category` | Map to `type` using table above |
| `establishing_scene` | `scene_number_a` |
| `contradicting_scene` | `scene_number_b` |
| `establishing_moment` + `contradicting_moment` | `note` (short summary) |
| `how_a_reader_notices` | Append to `notes` at file level |
| Full log entry | Always under `planted_contradictions` (not `expected_contradictions`) |

**Example conversion:**

Writer log:
```yaml
category: "Character dead then alive"
establishing_scene: 3
contradicting_scene: 18
```

Ground truth:
```yaml
planted_contradictions:
  - type: character_alive_status
    scene_number_a: 3
    scene_number_b: 18
    note: "Vance KIA at harbor; active again scene 18"
```

---

## Category overlap / disambiguation

| Writer might write… | Prefer engine type | Notes |
|---------------------|-------------------|-------|
| "She's his sister" then "his wife" | `relationship_conflict` | Not `character_trait_conflict` |
| Marcus is a surgeon then a lawyer | `character_trait_conflict` | Not relationship |
| Object with Character B, never with A | `object_ownership` | Need two different holders |
| Burns letter, reads same letter | `object_destroyed` | Not `object_lost` unless same owner lost it |
| Drops key, picks up key (no find scene) | `object_lost` | Same owner; not `object_ownership` |
| Left arm wound → right arm wound | `medical_laterality` | Not `medical_recovery` unless also "fine" |
| Unconscious → running same day | `medical_recovery` | |
| Monday then Wednesday with no flashback | `timeline_consistency` | |
| Warehouse empty vs warehouse busy | `semantic_location` | Same slug or clearly same place |

---

## Tier 2 catch-all

If the engine reports a type starting with `semantic_` that you did not plant:

| Engine type | Meaning |
|-------------|---------|
| `semantic_location` | Location description clash |
| `semantic_character_trait` | Trait similarity check flagged mismatch |
| `semantic_timeline` | Timeline fact similarity mismatch |
| `semantic_character_status` | Status fact similarity mismatch |

When reviewing **extra** flags: if it describes a real planted error but wrong `type`, record as **semantic match (manual)** in your spreadsheet — automated eval will still show **extra + missed**.

---

## Evaluation spreadsheet columns (recommended)

| Column | Source |
|--------|--------|
| `script_id` | filename stem |
| `writer_category` | from log |
| `engine_type` | mapped type |
| `scene_a` / `scene_b` | from log |
| `auto_match` | Y/N from `*_evaluation.txt` |
| `manual_match` | Y if engine caught it under different type/scenes |
| `FN_reason` | e.g. natural phrasing ("murdered" not "dead") |
| `FP_note` | engine-only flag |

---

## Production corpus targets (reminder)

| Package | Scripts | Errors each | Min categories (combined) |
|---------|---------|-------------|---------------------------|
| 5-scene | 3 | 2–3 | 4 |
| 10-scene | 2 | 4–5 | 7 |
| Full-length | 1 | 8–12 | 8 |

---

*Related: [SCREENWRITER_ERROR_INJECTION_GUIDE.md](../SCREENWRITER_ERROR_INJECTION_GUIDE.md) · [CORPUS_EVALUATION_GUIDE.md](../CORPUS_EVALUATION_GUIDE.md)*
