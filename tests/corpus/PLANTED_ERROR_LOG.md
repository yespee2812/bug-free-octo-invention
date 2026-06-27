# Planted Error Log — Genre Starter Scripts

Errors injected into the genre starter scripts for engine testing.
Scene numbers are 1-indexed by INT./EXT. heading order (matches the
"scene N" numbering in the customer report).

- Scripts: **40** (20 genres x 5-scene + 10-scene)
- 5-scene scripts: 2 planted errors each; 10-scene scripts: 3 each
- Total planted errors: **100**
- Currently engine-detectable (Tier 1/2): **9** (ownership / trait / medical-state types)

Inputs live in `tests/corpus/input/`; ground truth in `tests/corpus/ground_truth/`.

| Script | # | Type | Establish | Contradict | Characters | Objects | Engine? | Description |
|--------|---|------|-----------|------------|------------|---------|---------|-------------|
| action_5scene_errors | 1 | object_ownership | sc2 | sc5 | SANTOS, VEGA | RED FLARE CANISTER | yes | Flare clips to Vega's vest (sc2); Santos pulls his own flare (sc5). |
| action_5scene_errors | 2 | numeric_count | sc1 | sc5 | — | HOSTAGES | no | Hostage count reads 3 (sc1, sc3) vs 'All four' (sc5). |
| action_10scene_errors | 1 | numeric_count | sc1 | sc10 | — | HOSTAGES | no | Three hostages circled (sc1) vs 'All four' (sc10). |
| action_10scene_errors | 2 | object_ownership | sc3 | sc9 | VEGA, PARK | RED FLARE CANISTER | yes | Flare on Vega's vest (sc3); Park fires the flare (sc9). |
| action_10scene_errors | 3 | name_consistency | sc3 | sc7 | OSEI | — | no | Operative named Osei (sc3, sc4) vs 'Oshea' (sc7). |
| crime_5scene_errors | 1 | numeric_count | sc3 | sc5 | EDDIE, PELL | — | no | 'Three runs this month' (sc3) vs 'Four runs this month' (sc5). |
| crime_5scene_errors | 2 | character_age | sc1 | sc4 | EDDIE MORAN | — | no | Eddie introduced as 50s (sc1) vs 'barely forty' (sc4). |
| crime_10scene_errors | 1 | character_knowledge | sc8 | sc4 | PELL | yellow slicker buyer | no | Pell names the yellow-slicker buyer (sc4) before discovering them (sc8). |
| crime_10scene_errors | 2 | relationship_fact | sc5 | sc7 | EDDIE | — | no | Eddie's daughter (sc5) vs Eddie's niece (sc7). |
| crime_10scene_errors | 3 | numeric_count | sc4 | sc6 | PELL | — | no | 'three identical runs' (sc4) vs 'Four runs in a month' (sc6). |
| romance_5scene_errors | 1 | object_identity | sc1 | sc5 | JAMES | SATCHEL | no | Leather satchel (sc1) vs canvas satchel (sc5). |
| romance_5scene_errors | 2 | character_trait_conflict | sc1 | sc4 | CLAIRE HART | — | yes | Claire is a novelist (sc1) vs 'the poet' (sc4). |
| romance_10scene_errors | 1 | object_identity | sc2 | sc8 | JAMES | SATCHEL | no | Leather satchel (sc2) vs canvas satchel (sc8). |
| romance_10scene_errors | 2 | object_identity | sc5 | sc10 | JAMES, CLAIRE | PHOTO | no | Photo of the two of them (sc5) vs photo of her parents (sc10). |
| romance_10scene_errors | 3 | numeric_count | sc7 | sc10 | — | — | no | 'Six years of silence' (sc7) vs 'eight years' (sc10). |
| scifi_5scene_errors | 1 | object_identity | sc1 | sc3 | KARA | DATA CHIP | no | Gold data chip (sc1) vs silver data chip (sc3). |
| scifi_5scene_errors | 2 | character_knowledge | sc5 | sc2 | NOLAN | signal | no | Nolan says the signal is 'meant for me' (sc2) before the reveal (sc5). |
| scifi_10scene_errors | 1 | object_identity | sc1 | sc3 | KARA | DATA CHIP | no | Gold data chip (sc1) vs silver data chip (sc3). |
| scifi_10scene_errors | 2 | date_year | sc2 | sc6 | HALE | Meridian | no | Meridian missing in 2014 (sc2) vs lost in 2009 (sc6). |
| scifi_10scene_errors | 3 | numeric_count | sc4 | sc7 | — | — | no | 'four-person team' (sc4) vs 'All six of us' (sc7). |
| horror_5scene_errors | 1 | date_year | sc2 | sc3 | LEAH | VHS tape | no | Tape labeled CHRISTMAS '94 (sc2) vs '93 (sc3). |
| horror_5scene_errors | 2 | character_knowledge | sc4 | sc5 | LEAH | trapdoor | no | Trapdoor 'stepped over a thousand times' (sc4) vs 'never noticed' (sc5). |
| horror_10scene_errors | 1 | numeric_count | sc1 | sc9 | LEAH | — | no | 'One week to empty it' (sc1) vs 'Three weeks in this house' (sc9). |
| horror_10scene_errors | 2 | date_year | sc3 | sc5 | LEAH | VHS tape | no | CHRISTMAS '94 (sc3) vs '93 (sc5). |
| horror_10scene_errors | 3 | character_age | sc7 | sc10 | LEAH | — | no | 'when I was twelve' (sc7) vs 'Not since I was eight' (sc10). |
| adventure_5scene_errors | 1 | date_year | sc2 | sc5 | M. OKAFOR | expedition | no | Tin box 'M. OKAFOR, 1987' (sc2) vs 'British expedition, 1985' (sc5). |
| adventure_5scene_errors | 2 | object_identity | sc1 | sc3 | JUNE | ENVELOPE | no | Wax-sealed envelope (sc1) vs 'leather pouch' (sc3). |
| adventure_10scene_errors | 1 | numeric_count | sc8 | sc10 | JUNE | — | no | 'measured the peak wrong by sixty meters' (sc8) vs 'forty meters higher' (sc10). |
| adventure_10scene_errors | 2 | date_year | sc4 | sc8 | M. OKAFOR | expedition | no | Tin box 1987 (sc4) vs '1985 British labels' (sc8). |
| adventure_10scene_errors | 3 | name_consistency | sc2 | sc9 | TENZIN | — | no | Guide Tenzin (sc2) vs 'Tensing' (sc9). |
| comedy_5scene_errors | 1 | object_ownership | sc2 | sc4 | DAVE, TOM | MAGNETIC GUEST BOOK | yes | Guest book in Dave's backpack (sc2) vs 'Tom's MAGNETIC GUEST BOOK' (sc4). |
| comedy_5scene_errors | 2 | relationship_fact | sc3 | sc4 | DIANE, DAVE | — | no | Dave's future mother-in-law Diane (sc3) vs 'Dave's aunt Diane' (sc4). |
| comedy_10scene_errors | 1 | object_ownership | sc3 | sc6 | DAVE, TOM | MAGNETIC GUEST BOOK | yes | Dave reveals the guest book (sc3) vs 'Tom's guest book' (sc6). |
| comedy_10scene_errors | 2 | relationship_fact | sc4 | sc9 | DIANE, MAYA | — | no | Diane is the mother-in-law (sc4) vs 'Maya's sister Diane' (sc9). |
| comedy_10scene_errors | 3 | relationship_fact | sc1 | sc6 | PETE, TOM | — | no | Cousin Pete / best man Tom (sc1) vs 'best man Pete' (sc6). |
| coming_of_age_5scene_errors | 1 | numeric_count | sc3 | sc5 | — | cast | no | 'cast of twelve' (sc3) vs 'all fifteen of them' (sc5). |
| coming_of_age_5scene_errors | 2 | character_fact | sc2 | sc5 | JORDAN | — | no | Jordan bound for state school (sc2) vs 'Coast school for me' (sc5). |
| coming_of_age_10scene_errors | 1 | character_fact | sc3 | sc10 | MAYA | — | no | Maya's coast school confirmed (sc3) vs 'State school' (sc10). |
| coming_of_age_10scene_errors | 2 | numeric_count | sc9 | sc9 | PRINCIPAL, JORDAN | — | no | Principal 'You broke three rules' vs Jordan 'Five rules' (both sc9). |
| coming_of_age_10scene_errors | 3 | date_year | sc1 | sc6 | — | class banner | no | Banner CLASS OF 2026 (sc1) vs CLASS OF 2025 (sc6). |
| drama_5scene_errors | 1 | object_ownership | sc1 | sc5 | RICHARD, ELENA | SILVER WEDDING BAND | yes | Richard holds the band (sc1) vs 'stays in Elena's pocket' (sc5). |
| drama_5scene_errors | 2 | character_age | sc2 | sc3 | SOFIA | — | no | Sofia, 12 (sc2) vs 'fastest ten-year-old' (sc3). |
| drama_10scene_errors | 1 | object_ownership | sc1 | sc10 | RICHARD, ELENA | SILVER WEDDING BAND | yes | Richard holds the band (sc1) vs 'Elena keeps the SILVER BAND' (sc10). |
| drama_10scene_errors | 2 | character_age | sc2 | sc3 | SOFIA | — | no | Sofia, 12 (sc2) vs 'For eleven' (sc3). |
| drama_10scene_errors | 3 | relationship_fact | sc3 | sc8 | ALMA, RICHARD | — | no | Coach Alma (sc3) vs 'Alma, his sister' (sc8). |
| family_5scene_errors | 1 | numeric_count | sc1 | sc3 | MARIA | — | no | 'Twenty people at six' (sc1) vs 'a table set for eighteen' (sc3). |
| family_5scene_errors | 2 | numeric_count | sc2 | sc4 | RAUL | — | no | Father 'absent twenty years' (sc2) vs 'Fifteen years' (sc4). |
| family_10scene_errors | 1 | numeric_count | sc1 | sc9 | RAUL | — | no | 'reunion twenty years in the making' (sc1) vs 'Twenty-five years of silence' (sc9). |
| family_10scene_errors | 2 | numeric_count | sc5 | sc10 | MARIA | — | no | 'Twenty chairs' (sc5) vs 'a table set for eighteen' (sc10). |
| family_10scene_errors | 3 | relationship_fact | sc3 | sc8 | DIANA, ANTONIO | — | no | Antonio's sister Diana (sc3) vs 'Antonio's cousin Diana' (sc8). |
| fantasy_5scene_errors | 1 | object_identity | sc1 | sc5 | MIRA | COMPASS | no | Brass compass (sc1) vs 'iron compass' (sc5). |
| fantasy_5scene_errors | 2 | object_identity | sc2 | sc4 | STRANGER | payment | no | Stranger pays with a silver thimble (sc2) vs 'paid with a brass coin' (sc4). |
| fantasy_10scene_errors | 1 | object_identity | sc1 | sc5 | MIRA | COMPASS | no | Brass compass (sc1) vs 'iron compass' (sc5). |
| fantasy_10scene_errors | 2 | character_age | sc2 | sc6 | ELI | — | no | Eli, 10 (sc2) vs 'barely seven' (sc6). |
| fantasy_10scene_errors | 3 | object_identity | sc3 | sc5 | STRANGER | payment | no | Stranger offers a silver thimble (sc3) vs 'paid with a brass coin' (sc5). |
| heist_5scene_errors | 1 | object_identity | sc3 | sc5 | MARCUS | sketch | no | Vermeer study (sc3) vs 'Rembrandt charcoal' (sc5). |
| heist_5scene_errors | 2 | character_knowledge | sc5 | sc2 | SLOANE | — | no | Sloane says 'somebody already knows' (sc2) before the THEY KNOW text (sc5). |
| heist_10scene_errors | 1 | object_identity | sc6 | sc10 | MARCUS | sketch | no | Vermeer study (sc6) vs 'a Rembrandt' (sc10). |
| heist_10scene_errors | 2 | character_knowledge | sc9 | sc3 | SLOANE | — | no | Sloane 'they know we're coming' (sc3) before the THEY KNOW text (sc9). |
| heist_10scene_errors | 3 | numeric_count | sc4 | sc6 | PAK, MARCUS | — | no | 'Twelve-second holes' (sc4) vs 'Twenty-second holes' (sc6). |
| historical_fiction_5scene_errors | 1 | relationship_fact | sc1 | sc4 | LUC, MARIE | — | no | 'Her brother Luc' (sc1) vs 'Luc, her cousin' (sc4). |
| historical_fiction_5scene_errors | 2 | date_year | sc1 | sc4 | — | — | no | Slug dated 1943 (sc1) vs 'the autumn of 1942' (sc4). |
| historical_fiction_10scene_errors | 1 | date_year | sc1 | sc5 | — | — | no | Slug dated 1943 (sc1) vs 'this one of 1941' (sc5). |
| historical_fiction_10scene_errors | 2 | numeric_count | sc5 | sc8 | MARIE | couriers | no | 'blesses three couriers' (sc5) vs 'Four of us left that church' (sc8). |
| historical_fiction_10scene_errors | 3 | relationship_fact | sc1 | sc4 | LUC, MARIE | — | no | 'Her brother Luc' (sc1) vs 'Luc, her cousin' (sc4). |
| mystery_5scene_errors | 1 | character_age | sc2 | sc5 | TOMAS | — | no | Tomas, 22 (sc2) vs 'A nineteen-year-old gardener' (sc5). |
| mystery_5scene_errors | 2 | character_knowledge | sc1 | sc3 | MAYA | GLASS KEY | no | Key 'here at midnight' (sc1) vs 'gone since last week, not midnight' (sc3). |
| mystery_10scene_errors | 1 | character_age | sc4 | sc10 | TOMAS | — | no | Tomas, 22 (sc4) vs 'a nineteen-year-old gardener' (sc10). |
| mystery_10scene_errors | 2 | relationship_fact | sc3 | sc9 | CALEB | — | no | Caleb introduced as the nephew (sc3) vs 'I'm the only son' (sc9). |
| mystery_10scene_errors | 3 | fact_consistency | sc5 | sc10 | TOMAS | footprint | no | Print 'smaller than Tomas's boot' (sc5) vs 'matched Tomas exactly' (sc10). |
| noir_5scene_errors | 1 | numeric_count | sc2 | sc3 | — | hotel room | no | Room 514 (sc2) vs room 415 (sc3). |
| noir_5scene_errors | 2 | object_identity | sc2 | sc4 | — | RED HAT | no | Woman in a red hat (sc2) vs 'green hat' (sc4). |
| noir_10scene_errors | 1 | numeric_count | sc3 | sc5 | — | hotel room | no | Room 514 (sc3) vs room 415 (sc5). |
| noir_10scene_errors | 2 | object_identity | sc3 | sc6 | — | RED HAT | no | Woman in a red hat (sc3) vs 'Green hat' (sc6). |
| noir_10scene_errors | 3 | character_knowledge | sc10 | sc2 | FRANK, CLIENT | — | no | Frank states the client is the partner (sc2) before the final reveal (sc10). |
| sports_5scene_errors | 1 | numeric_count | sc2 | sc4 | NINA | — | no | Nationals finish 'fourth' (sc2) vs 'Third by a fingernail' (sc4). |
| sports_5scene_errors | 2 | character_age | sc1 | sc5 | NINA | — | no | Nina Vasquez, 22 (sc1) vs 'Nina, twenty' (sc5). |
| sports_10scene_errors | 1 | numeric_count | sc3 | sc8 | NINA, ALMA | — | no | 'Nina fourth by a hundredth' (sc3) vs 'Third isn't a sentence' (sc8). |
| sports_10scene_errors | 2 | numeric_count | sc7 | sc10 | NINA | — | no | Split fails at 150 (sc7) vs 'Turn at 175' (sc10). |
| sports_10scene_errors | 3 | character_age | sc2 | sc6 | NINA | — | no | Nina Vasquez, 22 (sc2) vs 'Twenty years old' (sc6). |
| supernatural_5scene_errors | 1 | numeric_count | sc1 | sc5 | ELISE | — | no | 'Three families left' (sc1) vs 'Four families' (sc5). |
| supernatural_5scene_errors | 2 | location_continuity | sc2 | sc5 | ELISE | haunted bedroom | no | East bedroom (sc2, sc3) vs WEST BEDROOM (sc5). |
| supernatural_10scene_errors | 1 | numeric_count | sc2 | sc8 | ELISE, DAN | — | no | 'Three families' (sc2) vs 'Four families' (sc8). |
| supernatural_10scene_errors | 2 | location_continuity | sc4 | sc7 | ELISE | haunted bedroom | no | East bedroom (sc4) vs WEST BEDROOM (sc7). |
| supernatural_10scene_errors | 3 | character_trait_conflict | sc2 | sc6 | DAN | — | yes | Dan the skeptic, 'unconvinced' (sc2) vs 'I knew this place was alive' (sc6). |
| thriller_5scene_errors | 1 | object_identity | sc1 | sc4 | LENA | DUFFEL | no | Black duffel (sc1) vs 'gray duffel' (sc4). |
| thriller_5scene_errors | 2 | numeric_count | sc1 | sc3 | LENA | — | no | Watch reads 11:58 PM (sc1) vs 'not even eleven yet' (sc3). |
| thriller_10scene_errors | 1 | object_identity | sc2 | sc6 | LENA | DUFFEL | no | Black duffel (sc2) vs 'gray duffel' (sc6). |
| thriller_10scene_errors | 2 | numeric_count | sc1 | sc5 | LENA | — | no | 'three exchange points' (sc1) vs 'Four exchange points' (sc5). |
| thriller_10scene_errors | 3 | numeric_count | sc7 | sc9 | DMITRI, LENA | — | no | 'Five of them, I counted five' (sc7) vs 'Three men exit the sedan' (sc9). |
| war_5scene_errors | 1 | numeric_count | sc2 | sc5 | HALE | listening post | no | Listening post '200 meters out' (sc2) vs 'Three hundred meters' (sc5). |
| war_5scene_errors | 2 | character_age | sc1 | sc3 | TOM HALE | — | no | Sergeant Tom Hale, 28 (sc1) vs 'thirty-one' (sc3). |
| war_10scene_errors | 1 | character_age | sc1 | sc8 | TOM HALE | — | no | Sergeant Tom Hale, 28 (sc1) vs 'thirty-one' (sc8). |
| war_10scene_errors | 2 | medical_state | sc8 | sc9 | KOWALSKI | — | yes | Kowalski hit in the shoulder (sc8) vs medics 'bind Kowalski's leg' (sc9). |
| war_10scene_errors | 3 | numeric_count | sc2 | sc10 | HALE | listening post | no | Listening post '200 meters out' (sc2) vs 'Three hundred meters out' (sc10). |
| western_5scene_errors | 1 | location_continuity | sc2 | sc3 | DAWSON | pasture | no | Diverts flow to 'his south pasture' (sc2) vs 'My north pasture finally drinks' (sc3). |
| western_5scene_errors | 2 | character_age | sc2 | sc4 | JESSE | — | no | Foreman Jesse, 30s (sc2) vs 'barely twenty-five' (sc4). |
| western_10scene_errors | 1 | location_continuity | sc3 | sc4 | DAWSON | pasture | no | 'his south pasture' (sc3) vs 'My north fields finally drink' (sc4). |
| western_10scene_errors | 2 | character_knowledge | sc8 | sc3 | JESSE | railroad plot | no | Jesse names the railroad feud (sc3) before Dawson reveals it (sc8). |
| western_10scene_errors | 3 | character_age | sc4 | sc8 | WILL DAWSON | — | no | Will Dawson, 45 (sc4) vs 'Dawson, fifty now' (sc8). |
