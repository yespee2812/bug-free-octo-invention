# Dialogue-as-Structure Design

| Field | Value |
|-------|-------|
| **Status** | Phases A–C implemented — Phase D (product copy) not started |
| **Date** | July 2026 |
| **Product path** | Customer v3 structure-only (orphans, simulate, draft) |
| **Goal** | Raise product depth by treating dialogue as a **structure channel**, not as literary/dialect NLP |

---

## 1. Product stance (one paragraph)

ScriptLens does **not** judge how characters speak (voice, slang, subtext, comedy).  
ScriptLens **does** use dialogue to answer: *who is bound to whom, what object or place is referenced, and which earlier beat is being called back — including when that payload is spoken rather than written in action.*

**Promise to writers:**  
*We follow structural cargo in what is said. We do not “understand” Cockney, Scouse, or other dialects as language.*

---

## 2. Problem today

| Already works | Gap |
|---------------|-----|
| Dialogue **cues** → `characters_speaking` | Spoken **prop nicknames** often miss (`piece` ≠ `REVOLVER`) |
| Soft prop match on last-two-words / `X thing` | No closed nickname lexicon |
| Known character names in dialogue/action | Location callouts in speech weakly handled |
| `CAUSAL_DIALOGUE_PATTERNS` exist | **On** for v3 structure path (`include_causal_edges=True`) |
| MiniLM embeds full `raw_text` | Embeds heading + action + structure-bearing dialogue (capped) |

Writers experience this as: *“The scene is mostly dialogue — why is the graph thin?”*

---

## 3. What we extract from dialogue (signals)

Only signals that feed **structure graphs** (OSD C/L/P/E and continuity simulate edges).

### S1 — Speakers (already strong)

| Field | Source | Feeds |
|-------|--------|-------|
| Who speaks | Fountain cue lines | C_ij, character edges, simulate |

**Rule:** Cue wins over body text. Wrong-speaker format errors are **out of scope** (attribution / v2).

### S2 — Character mentions in spoken lines (strengthen)

| Field | Source | Feeds |
|-------|--------|-------|
| Named people already established as cues | Dialogue + parentheticals `(to X)` | C_ij, presence |

**Rules:**
- Only link to **already-known** character aliases (same as `_match_known_character_mentions` today).
- Do **not** invent new characters from random capitalized slang.
- Prefer full name / unique first name; suppress stopwords (`YOU`, `MAN`, `KID` alone).

### S3 — Prop / object references (high priority)

| Field | Source | Feeds |
|-------|--------|-------|
| Reference to a prop **already planted** (usually CAPS in action earlier) | Dialogue soft match + nickname map | P_ij, object edges, simulate cut |

**Pipeline:**
1. Prop must be **established** earlier (or in same scene action) in `props_detected` / known props.
2. Dialogue may refer via:
   - Exact / last-two-word soft match (existing)
   - `X thing` pattern (existing)
   - **Closed nickname table** (new) — see §5
3. Never create a brand-new prop from slang alone.

### S4 — Location callouts in speech (medium)

| Field | Source | Feeds |
|-------|--------|-------|
| Spoken place that matches a known slug location or established location token | Dialogue | L_ij (soft), location edges |

**Examples that should link:** “Meet me at the docks” when `EXT. DOCKS` exists; “back at the warehouse.”  
**Examples that should not:** “go to hell,” “out of this world,” pure idiom.

**Rules:**
- Match against **known location keys** from headings / prior scenes only.
- Require token length ≥ 4 or multi-word place; block idiom list (§6).

### S5 — Causal / callback phrases (medium — enable carefully on v3)

| Field | Source | Feeds |
|-------|--------|-------|
| Backward temporal commitment | Dialogue patterns | Continuity `causal` edges → simulate cut paths |

**Existing patterns** (`CAUSAL_DIALOGUE_PATTERNS`): “after what you did”, “since that night”, etc.

**v3 proposal:**
- Turn **on** `include_causal_edges=True` for structure path **only after** golden fixtures pass.
- Keep resolution rule: link to most recent prior scene sharing a speaker (current behavior); do not open-domain resolve “what.”
- Expand patterns modestly (British-friendly variants) without phonetic dialect engines — e.g. optional `after what you done` as a **literal alternate regex**, not a Scouse parser.

### S6 — Semantic embedding input (refine, don’t drop dialogue)

| Today | Proposed |
|-------|----------|
| Heading + full `raw_text` | Heading + **action** + **structure-bearing dialogue only** |

**Structure-bearing dialogue lines** = lines that contributed to S2–S5 hits, else (fallback) first N dialogue lines capped by length **or** cues-only if no hits.

**Rationale:** Keep topic signal from important spoken lines; reduce slang-only chatter dominating MiniLM.

---

## 4. Weighting (how much dialogue should move the needle)

### OSD (`orphan_scene_detector.py`)

Current blend (approx): character / spatial / prop / semantic with `DELTA_SEMANTIC = 0.15`, `LINK_THRESHOLD = 0.20`.

| Change | Proposal |
|--------|----------|
| C_ij | No formula change — better mention recall improves Jaccard naturally |
| P_ij | No formula change — nickname hits improve Jaccard |
| L_ij | Allow soft location-from-dialogue into location entity set (capped) |
| E_ij | Rebuild embedding text per §3 S6; keep weight 0.15 |

**Guard:** A single soft dialogue hit must not alone push a pair over threshold if all of C/L/P are ~0 — prefer requiring soft hits to **strengthen** an existing weak link, or count soft prop/location at **0.7×** confidence in entity sets (implementation detail: duplicate key with reduced weight **or** tag `source=dialogue_soft` and downscale in Jaccard). Prefer simplest v1: **full credit once nickname map is closed and gated**.

### Continuity / simulate (`scene_dependency.py`)

| Edge type | Dialogue role |
|-----------|---------------|
| Character presence | Mentions + speakers (existing + S2) |
| Object | Soft + nicknames (S3) |
| Location | Soft callouts (S4) |
| Causal | Enable on v3 after fixtures (S5) |

Fact/contradiction edges stay **off** on customer path.

---

## 5. Closed nickname table (prop aliases)

**Design:** small, curated, English-common production slang — **not** regional dictionaries.

```text
# Conceptual map: alias (dialogue) → only matches if canonical prop already known
# Matching is many-alias → one established prop key (substring/token rules TBD)

gun-family:  piece, shooter, heater, gat, firearm, pistol (if REVOLVER/GUN/PISTOL planted)
blade-family: shiv, sticker, blade (if KNIFE/BLADE planted)
money-family: cash, loot, score (if MONEY/CASH/BAG OF CASH planted)
car-family:  wheels, ride (if CAR/TRUCK planted)
phone-family: mobile, cell (if PHONE/MOBILE planted)
```

**Hard rules:**
1. Alias never creates a prop; only attaches to an existing one.
2. Prefer longest/most specific planted prop when multiple could match.
3. Genre packs later (heist, crime) — start with ≤30 aliases.
4. No Cockney rhyming slang tables in v1.

---

## 6. False-positive rules (must pass before ship)

| ID | Rule | Example blocked |
|----|------|-----------------|
| FP1 | No new entities from dialogue alone | “Trust the process” ≠ prop PROCESS |
| FP2 | Idiom / metaphor blocklist for locations | hell, world, town (bare), nowhere |
| FP3 | Pronoun-only lines add no entities | “He did it.” |
| FP4 | Causal needs shared speaker with prior candidate | Stranger’s “since then” doesn’t link random prior scene |
| FP5 | Nickname requires prior plant | “Where’s the piece?” with no gun ever planted → no prop |
| FP6 | Parenthetical emotion ignored | `(laughing)` not an entity |
| FP7 | Semantic text must not be dialogue-only walls of slang | Cap dialogue chars in embed blob |
| FP8 | Do not enable contradiction-style status from speech | “I’m dead” ≠ death fact (already out of v3) |

---

## 7. Explicit non-goals

- Dialect translation / phonetic normalization (Cockney, Scouse, AAVE, …)
- Multilingual understanding beyond clear shared proper nouns
- Subtext, joke detection, “good dialogue” scoring
- Fixing wrong cue attribution
- LLM rewriting or explaining dialogue in the core graph path

---

## 8. Implementation phases (after design approval)

### Phase A — Extract & wire (depth without new models) ✅

1. Inventory + tests for current soft mention / character mention behavior.
2. Add `PROP_DIALOGUE_ALIAS_GROUPS` + gate in `_match_prop_soft_mentions` / `_props_for_dialogue_aliases`.
3. ~~Add location soft-from-dialogue~~ — deferred (not in “aliases + tests only” slice).
4. Unit fixtures: gun→piece, wheels→car, negative no-plant — `tests/test_dialogue_prop_aliases.py`.

### Phase B — Causal on structure path ✅

1. Golden fixtures for causal dialogue → simulate cut path — `tests/test_dialogue_causal_structure.py`.
2. Enable `include_causal_edges=True` in `analyze_structure`.
3. Expand literal pattern variants (`after what you done`, `after what ya did`, `because of what … done`, `since what happened`).

### Phase C — Semantic text refine ✅

1. Change `scene_semantic_text` to heading + action + structure-bearing dialogue (capped) — `osd_semantic.py`.
2. Re-run orphan golden fixtures + semantic unit tests — passing.
3. Unit coverage: `tests/test_dialogue_semantic_text.py`.

### Phase D — Product copy

1. UI/help one-liner: structure includes spoken references.
2. Blueprint / status report note: dialogue-as-structure, not dialect NLP.

**Do not start Phase B/C until Phase A fixtures are green.**

---

## 9. Acceptance criteria

| Criterion | Pass condition |
|-----------|----------------|
| Depth | Dialogue-only callback to a planted prop creates P link / simulate impact where today’s engine misses |
| Safety | Idiom + no-plant negatives add zero props/locations |
| Orphans | Existing `orphan_spec` golden fixtures still pass |
| Scope | No contradiction UI; no dialect lexicon files |
| Explainability | Edge/orphan reason strings can say `dialogue reference` / `spoken prop alias` when soft |

---

## 10. Test matrix (minimum fixtures)

| ID | Setup | Expect |
|----|-------|--------|
| T1 | Action plants `REVOLVER`; later scene dialogue “Bring the piece.” | Prop link / shared P; not orphan solely for missing prop |
| T2 | Same as T1 but **no** revolver planted | No prop created |
| T3 | Prior `EXT. DOCKS`; dialogue “Meet me at the docks.” | Location soft link |
| T4 | Dialogue “Go to hell.” | No location |
| T5 | Cue DAVE; other scene “(to Dave)” / “Dave knows.” | Character mention |
| T6 | “After what you did” + shared prior speaker | Causal edge when Phase B on |
| T7 | Dense slang dialogue, clear shared cast in cues | Orphan status stable vs baseline (no wild E swing) |

---

## 11. Decision log

| Decision | Choice | Why |
|----------|--------|-----|
| Analyse dialogue? | **Yes, for structure** | Depth without becoming a critic |
| Dialect engines? | **No** | ROI / FP / scope |
| Enable causal on v3? | **Yes, after fixtures** | Already built; currently disabled |
| Semantic drop dialogue? | **No — filter** (Phase C done) | Keep signal, cut noise |
| Nickname map? | **Closed, small** | Biggest win for “piece/gun” class misses |

---

## 12. Next step

Review this design → approve Phase A scope → implement Phase A with tests only (no landing/UI work).

---

*Related: `scene_dependency.py` (`_match_prop_soft_mentions`, `_match_known_character_mentions`, `CAUSAL_DIALOGUE_PATTERNS`), `osd_semantic.scene_semantic_text`, `scriptlens_structure.analyze_structure`, `docs/ARCHITECTURE_v3_STRUCTURE.md`.*
