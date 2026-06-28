# Baseline Score — Core Engine vs Planted Errors

Corpus: 40 scripts, 100 planted errors.
Matching is order-insensitive on (contradiction_type, {scene_a, scene_b}).

## Headline

- Planted errors (ground truth):        **100**
- Detected by engine (any):             **92**
- True positives (correct catches):     **90**
- False positives:                      **2**
- **Recall (overall): 90.0%** (90/100)
- Precision: 97.8%
- F1: 93.8%

## On the engine's own supported categories

Subset = planted errors whose type the engine claims to support (object_ownership, character_trait_conflict, medical_state).

- Supported-subset planted: **9**
- Supported-subset caught:  **9**
- **Subset recall: 100.0%**

## Recall by planted error type

| Type | Planted | Caught | Recall |
|------|---------|--------|--------|
| character_age | 13 | 12 | 92% |
| character_fact | 2 | 0 | 0% |
| character_knowledge | 8 | 4 | 50% |
| character_trait_conflict | 2 | 2 | 100% |
| date_year | 8 | 8 | 100% |
| fact_consistency | 1 | 0 | 0% |
| location_continuity | 4 | 4 | 100% |
| medical_state | 1 | 1 | 100% |
| name_consistency | 2 | 2 | 100% |
| numeric_count | 28 | 28 | 100% |
| object_identity | 16 | 15 | 94% |
| object_ownership | 6 | 6 | 100% |
| relationship_fact | 9 | 8 | 89% |

## Per-script

| Script | Planted | Detected | Matched |
|--------|---------|----------|---------|
| action_5scene_errors | 2 | 2 | 2 |
| action_10scene_errors | 3 | 3 | 3 |
| crime_5scene_errors | 2 | 2 | 2 |
| crime_10scene_errors | 3 | 2 | 2 |
| romance_5scene_errors | 2 | 2 | 2 |
| romance_10scene_errors | 3 | 2 | 2 |
| scifi_5scene_errors | 2 | 1 | 1 |
| scifi_10scene_errors | 3 | 3 | 3 |
| horror_5scene_errors | 2 | 2 | 2 |
| horror_10scene_errors | 3 | 3 | 3 |
| adventure_5scene_errors | 2 | 3 | 2 |
| adventure_10scene_errors | 3 | 4 | 3 |
| comedy_5scene_errors | 2 | 2 | 2 |
| comedy_10scene_errors | 3 | 2 | 2 |
| coming_of_age_5scene_errors | 2 | 1 | 1 |
| coming_of_age_10scene_errors | 3 | 2 | 2 |
| drama_5scene_errors | 2 | 2 | 2 |
| drama_10scene_errors | 3 | 3 | 3 |
| family_5scene_errors | 2 | 2 | 2 |
| family_10scene_errors | 3 | 3 | 3 |
| fantasy_5scene_errors | 2 | 2 | 2 |
| fantasy_10scene_errors | 3 | 3 | 3 |
| heist_5scene_errors | 2 | 2 | 2 |
| heist_10scene_errors | 3 | 3 | 3 |
| historical_fiction_5scene_errors | 2 | 2 | 2 |
| historical_fiction_10scene_errors | 3 | 3 | 3 |
| mystery_5scene_errors | 2 | 2 | 2 |
| mystery_10scene_errors | 3 | 2 | 2 |
| noir_5scene_errors | 2 | 2 | 2 |
| noir_10scene_errors | 3 | 2 | 2 |
| sports_5scene_errors | 2 | 2 | 2 |
| sports_10scene_errors | 3 | 2 | 2 |
| supernatural_5scene_errors | 2 | 2 | 2 |
| supernatural_10scene_errors | 3 | 3 | 3 |
| thriller_5scene_errors | 2 | 2 | 2 |
| thriller_10scene_errors | 3 | 3 | 3 |
| war_5scene_errors | 2 | 2 | 2 |
| war_10scene_errors | 3 | 3 | 3 |
| western_5scene_errors | 2 | 2 | 2 |
| western_10scene_errors | 3 | 2 | 2 |
