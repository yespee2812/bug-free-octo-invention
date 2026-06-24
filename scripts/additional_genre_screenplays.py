"""Production-grade Hollywood starter screenplays for genres 7–20."""

from __future__ import annotations

from build_genre_starter_scripts import Screenplay, _screenplay_to_lines

Body = list[tuple[str, ...]]


def _thriller_5scene() -> Screenplay:
    """Return the thriller 5-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. PARKING GARAGE - LEVEL 4 - NIGHT"),
        (
            "action",
            "Rain hammers the concrete. AGENT LENA CROSS, 40s, waits beside a silver "
            "SUV. She checks her watch — 11:58 PM. A BLACK DUFFEL sits at her feet.",
        ),
        ("character", "LENA"),
        ("dialogue", "Package is clean. Where's your courier?"),
        ("scene", "INT. PARKING GARAGE - STAIRWELL - NIGHT"),
        (
            "action",
            "Footsteps echo down. DMITRI VOLKOV, 50s, limps into the light, one hand "
            "pressed to his ribs. Blood on his sleeve.",
        ),
        ("character", "DMITRI"),
        ("dialogue", "They made me at the bridge. Two blocks behind me."),
        ("character", "LENA"),
        ("dialogue", "Then we don't stand here admiring your tailoring."),
        ("scene", "INT. SILVER SUV - MOVING - NIGHT"),
        (
            "action",
            "Lena drives hard. Dmitri opens the duffel — stacks of microfilm canisters. "
            "Headlights flare in the rearview.",
        ),
        ("character", "DMITRI"),
        ("dialogue", "If they take this back, a city dies tomorrow."),
        ("character", "LENA"),
        ("dialogue", "Nobody takes anything. Not on my watch."),
        ("scene", "EXT. RIVER ROAD OVERPASS - NIGHT"),
        (
            "action",
            "The SUV screeches to a stop. Lena shoves the duffel into a maintenance "
            "hatch beneath the guardrail. A black sedan closes fast behind them.",
        ),
        ("character", "LENA"),
        ("dialogue", "When I say go, you go over the rail. Swim south."),
        ("scene", "INT. SILVER SUV - NIGHT"),
        (
            "action",
            "The sedan rams their bumper. Lena meets Dmitri's eyes — no sentiment, "
            "pure calculus. She reaches for the door.",
        ),
        ("character", "LENA"),
        ("dialogue", "Go."),
    ]
    return _screenplay_to_lines("COLD HANDOFF", "Rachel Stein", body)


def _thriller_10scene() -> Screenplay:
    """Return the thriller 10-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. SAFE HOUSE - KITCHEN - NIGHT"),
        ("action", "Lena tapes a burner phone shut. A map marks three exchange points in red."),
        ("character", "LENA"),
        ("dialogue", "One hour. In and out. No second chances."),
        ("scene", "INT. PARKING GARAGE - LEVEL 4 - NIGHT"),
        ("action", "Rain. The BLACK DUFFEL at her feet. No courier."),
        ("character", "LENA"),
        ("dialogue", "Package is clean. Where's your courier?"),
        ("scene", "INT. PARKING GARAGE - STAIRWELL - NIGHT"),
        ("action", "DMITRI VOLKOV limps into view, bleeding."),
        ("character", "DMITRI"),
        ("dialogue", "They made me at the bridge."),
        ("scene", "INT. SILVER SUV - MOVING - NIGHT"),
        ("action", "Lena weaves through traffic. Headlights follow."),
        ("character", "DMITRI"),
        ("dialogue", "If they take this back, a city dies tomorrow."),
        ("scene", "INT. UNDERPASS - NIGHT"),
        ("action", "Lena kills the lights, coasts into darkness. The sedan overshoots."),
        ("character", "LENA"),
        ("dialogue", "We have four minutes before they circle back."),
        ("scene", "EXT. RIVER ROAD OVERPASS - NIGHT"),
        ("action", "Lena pries open a maintenance hatch. Sirens distant."),
        ("character", "LENA"),
        ("dialogue", "Dmitri goes in the hatch. I draw the tail."),
        ("scene", "INT. SILVER SUV - NIGHT"),
        ("action", "The sedan rams them. Lena's knuckles white on the wheel."),
        ("character", "DMITRI"),
        ("dialogue", "I'm not leaving you with them."),
        ("character", "LENA"),
        ("dialogue", "You're leaving with the film. That's the job."),
        ("scene", "EXT. OVERPASS GUARDRAIL - NIGHT"),
        ("action", "Dmitri drops into the hatch. Lena slams the SUV into reverse."),
        ("character", "LENA"),
        ("dialogue", "Go."),
        ("scene", "INT. SILVER SUV - NIGHT"),
        ("action", "Three men exit the sedan — armed, professional. Lena smiles without warmth."),
        ("character", "LENA"),
        ("dialogue", "You want the package? Come get it."),
        ("scene", "EXT. RIVER ROAD OVERPASS - NIGHT"),
        (
            "action",
            "She accelerates toward the gap between sedan and rail. The duffel is gone. "
            "The city, for tonight, is not.",
        ),
        ("character", "LENA"),
        ("dialogue", "Let's see who's still standing when the rain stops."),
    ]
    return _screenplay_to_lines("COLD HANDOFF", "Rachel Stein", body)


def _romance_5scene() -> Screenplay:
    """Return the romance 5-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. CAPE COD INN - PORCH - DAWN"),
        (
            "action",
            "Salt air. CLAIRE HART, 32, novelist, sips coffee. A taxi drops off "
            "JAMES MERCER, 34, carrying a battered LEATHER SATCHEL.",
        ),
        ("character", "CLAIRE"),
        ("dialogue", "You said you'd never come back east."),
        ("character", "JAMES"),
        ("dialogue", "I said a lot of things at twenty-four."),
        ("scene", "INT. INN LOBBY - MORNING"),
        (
            "action",
            "The innkeeper slides a key across the desk — adjacent rooms. James and "
            "Claire reach for it at the same time. Fingers brush. Both pull back.",
        ),
        ("character", "CLAIRE"),
        ("dialogue", "I'm here for the writers' retreat. Not a reunion tour."),
        ("scene", "EXT. BEACH - AFTERNOON"),
        (
            "action",
            "Claire walks the tide line. James catches up, shoes in hand. He pulls a "
            "folded PHOTO from the satchel — the two of them, younger, on this same beach.",
        ),
        ("character", "JAMES"),
        ("dialogue", "I kept it because we looked happy. I forgot we were."),
        ("character", "CLAIRE"),
        ("dialogue", "We were. Until we weren't."),
        ("scene", "INT. CLAIRE'S ROOM - NIGHT"),
        (
            "action",
            "Knock on the connecting door. Claire opens it a crack. James holds two "
            "paper cups of tea.",
        ),
        ("character", "JAMES"),
        ("dialogue", "You still take honey when you're stuck on a chapter."),
        ("character", "CLAIRE"),
        ("dialogue", "I'm stuck on a lot of things."),
        ("scene", "EXT. BEACH - SUNSET"),
        (
            "action",
            "They sit on the dunes, shoulders almost touching. The satchel lies open "
            "between them — not the photo, but a manuscript draft with Claire's name on the dedication page.",
        ),
        ("character", "CLAIRE"),
        ("dialogue", "You wrote me into this before you wrote me out of your life."),
        ("character", "JAMES"),
        ("dialogue", "Maybe I came back to find out if there's a second draft."),
    ]
    return _screenplay_to_lines("SECOND COAST", "Emily Nakamura", body)


def _romance_10scene() -> Screenplay:
    """Return the romance 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. CAPE COD INN - ESTABLISHING - DAWN"),
        ("action", "Weathered shingles. Quiet Atlantic. A retreat week begins."),
        ("scene", "EXT. CAPE COD INN - PORCH - DAWN"),
        ("action", "CLAIRE HART watches a taxi arrive. JAMES MERCER steps out with a LEATHER SATCHEL."),
        ("character", "CLAIRE"),
        ("dialogue", "You said you'd never come back east."),
        ("scene", "INT. INN LOBBY - MORNING"),
        ("action", "Adjacent room keys. Awkward reach. The innkeeper pretends not to notice."),
        ("character", "CLAIRE"),
        ("dialogue", "I'm here to work. Not to time-travel."),
        ("scene", "INT. RETREAT WORKSHOP - DAY"),
        ("action", "Twelve writers around a table. Claire reads a passage. James listens, still."),
        ("character", "WORKSHOP LEADER"),
        ("dialogue", "Strong voice. Who's the 'you' in this scene?"),
        ("character", "CLAIRE"),
        ("dialogue", "Someone I used to know. Present tense optional."),
        ("scene", "EXT. BEACH - AFTERNOON"),
        ("action", "James produces the old PHOTO. Wind tries to take it."),
        ("character", "JAMES"),
        ("dialogue", "We looked happy. I forgot we were."),
        ("scene", "INT. INN DINING ROOM - NIGHT"),
        ("action", "Retreat dinner. Claire sits with a poet from Vermont. James watches from the bar."),
        ("character", "JAMES"),
        ("dialogue", "Buy you a drink for old times' sake?"),
        ("character", "CLAIRE"),
        ("dialogue", "Old times owe me interest."),
        ("scene", "INT. CLAIRE'S ROOM - NIGHT"),
        ("action", "Tea through the connecting door. Rain on the windows."),
        ("character", "CLAIRE"),
        ("dialogue", "Why now? Why this week?"),
        ("character", "JAMES"),
        ("dialogue", "Because your new book mentions a lighthouse I've never forgotten."),
        ("scene", "EXT. LIGHTHOUSE PATH - MORNING"),
        ("action", "They walk in silence. The LEATHER SATCHEL swings at James's side."),
        ("character", "CLAIRE"),
        ("dialogue", "You dedicated it to me before you told me goodbye."),
        ("scene", "INT. JAMES'S ROOM - AFTERNOON"),
        ("action", "Claire reads his manuscript — a love story that stops at page ninety."),
        ("character", "CLAIRE"),
        ("dialogue", "You left the ending blank."),
        ("character", "JAMES"),
        ("dialogue", "I didn't know if you'd give me one."),
        ("scene", "EXT. BEACH - SUNSET"),
        (
            "action",
            "Dunes, gold light. Claire closes the satchel — keeps the manuscript, "
            "not the photo.",
        ),
        ("character", "CLAIRE"),
        ("dialogue", "One chapter at a time. No promises past this week."),
        ("character", "JAMES"),
        ("dialogue", "I'll take one chapter. I've waited eight years for a page turn."),
    ]
    return _screenplay_to_lines("SECOND COAST", "Emily Nakamura", body)


def _action_5scene() -> Screenplay:
    """Return the action 5-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. EMBASSY ANNEX - SECURITY HUB - NIGHT"),
        (
            "action",
            "Monitors flicker. CAPTAIN RICO SANTOS, 38, exfil specialist, studies "
            "thermal feeds. A HOSTAGE COUNT reads 3 in a basement vault.",
        ),
        ("character", "SANTOS"),
        ("dialogue", "We breach at 0400. Two minutes in, ninety seconds out."),
        ("scene", "INT. ROOFTOP STAGING - NIGHT"),
        (
            "action",
            "Santos's team — VEGA, PARK, OSEI — check carbines and breaching charges. "
            "A RED FLARE CANISTER clips to Vega's vest.",
        ),
        ("character", "VEGA"),
        ("dialogue", "Guard rotation shifts early. We lose the blind spot in six."),
        ("character", "SANTOS"),
        ("dialogue", "Then we don't use the blind spot. We make our own door."),
        ("scene", "INT. EMBASSY BASEMENT - NIGHT"),
        (
            "action",
            "Charges blow. Smoke. Santos moves low — two guards down, non-lethal. "
            "Three HOSTAGES crouch against a steel cage.",
        ),
        ("character", "SANTOS"),
        ("dialogue", "Eyes on me. Walk, don't run."),
        ("scene", "INT. STAIRWELL - NIGHT"),
        (
            "action",
            "Automatic fire tears plaster above them. Park returns fire. Osei shepherds "
            "hostages upward. An alarm wails.",
        ),
        ("character", "PARK"),
        ("dialogue", "They've locked the street exit!"),
        ("character", "SANTOS"),
        ("dialogue", "Roof. Always had a plan B."),
        ("scene", "EXT. EMBASSY ROOFTOP - NIGHT"),
        (
            "action",
            "Santos pops the RED FLARE. A helicopter crests the skyline. Hostages "
            "board first. Santos covers the ladder, last man up.",
        ),
        ("character", "SANTOS"),
        ("dialogue", "Count them. All three. Then we celebrate."),
    ]
    return _screenplay_to_lines("BREACH POINT", "Marcus Cole", body)


def _action_10scene() -> Screenplay:
    """Return the action 10-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. SAFE HOUSE - NIGHT"),
        ("action", "Santos spreads blueprints. Three hostages circled in red beneath the embassy."),
        ("character", "SANTOS"),
        ("dialogue", "Journalists. No ransom demand. Someone wants them quiet."),
        ("scene", "INT. EMBASSY ANNEX - SECURITY HUB - NIGHT"),
        ("action", "Thermal feeds. CAPTAIN RICO SANTOS watches guard patterns repeat."),
        ("character", "SANTOS"),
        ("dialogue", "Breath at 0400. Two minutes in, ninety out."),
        ("scene", "INT. ROOFTOP STAGING - NIGHT"),
        ("action", "VEGA, PARK, OSEI prep gear. RED FLARE CANISTER on Vega's vest."),
        ("character", "VEGA"),
        ("dialogue", "Rotation shifts early. Blind spot closes in six."),
        ("scene", "EXT. EMBASSY ALLEY - NIGHT"),
        ("action", "Osei disables a camera with a pellet. Santos signals — move."),
        ("scene", "INT. EMBASSY BASEMENT - NIGHT"),
        ("action", "Breaching charge blows. Santos enters low — targets neutralized."),
        ("character", "SANTOS"),
        ("dialogue", "Eyes on me. Walk, don't run."),
        ("scene", "INT. BASEMENT CORRIDOR - NIGHT"),
        ("action", "Hostages move. A locked service door blocks the exit route."),
        ("character", "PARK"),
        ("dialogue", "Street exit is sealed!"),
        ("scene", "INT. STAIRWELL - NIGHT"),
        ("action", "Gunfire from above. Park suppresses. Osei shields the civilians."),
        ("character", "SANTOS"),
        ("dialogue", "Roof. Plan B. Move."),
        ("scene", "INT. UPPER FLOOR - NIGHT"),
        ("action", "Santos clears corners — two more hostiles, disarmed fast."),
        ("character", "HOSTAGE #1"),
        ("dialogue", "They said if anyone came, we'd—"),
        ("character", "SANTOS"),
        ("dialogue", "You're not dying in a basement. Keep moving."),
        ("scene", "EXT. EMBASSY ROOFTOP - NIGHT"),
        ("action", "RED FLARE arcs skyward. Rotors beat closer."),
        ("character", "VEGA"),
        ("dialogue", "Bird's inbound. Thirty seconds!"),
        ("scene", "EXT. EMBASSY ROOFTOP - NIGHT"),
        (
            "action",
            "Hostages aboard. Santos climbs last, rounds snapping past his helmet. "
            "The helicopter lifts — city blurring below.",
        ),
        ("character", "SANTOS"),
        ("dialogue", "Count them. All three. Then tell me who ordered this."),
    ]
    return _screenplay_to_lines("BREACH POINT", "Marcus Cole", body)


def _mystery_5scene() -> Screenplay:
    """Return the mystery 5-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. ASHWORTH MANOR - LIBRARY - DAY"),
        (
            "action",
            "Rain on leaded glass. DETECTIVE MAYA QUINN, 45, examines an empty velvet "
            "case. MRS. ASHWORTH, 70s, trembles in a wingback chair.",
        ),
        ("character", "MAYA"),
        ("dialogue", "The GLASS KEY was here at midnight. Who had access after dinner?"),
        ("character", "MRS. ASHWORTH"),
        ("dialogue", "Only family. And the boy who tends the garden."),
        ("scene", "INT. MANOR - GREENHOUSE - DAY"),
        (
            "action",
            "Quinn interviews TOMAS, 22, gardener, mud on his boots. A silver locket "
            "peeks from his shirt.",
        ),
        ("character", "TOMAS"),
        ("dialogue", "I lock up at nine. I don't touch the old woman's trinkets."),
        ("character", "MAYA"),
        ("dialogue", "Trinket opens a wall safe in this house. Try again."),
        ("scene", "INT. MANOR - NORTH WING HALL - DAY"),
        (
            "action",
            "Quinn finds fresh scratches around a portrait of the late MR. ASHWORTH. "
            "The frame sits crooked.",
        ),
        ("action", "Behind the portrait: a narrow door, slightly ajar. Cold air slips through."),
        ("scene", "INT. HIDDEN STUDY - DAY"),
        (
            "action",
            "Dusty ledgers. A GLASS KEY replica on the desk — obvious decoy. A note in "
            "elegant script: For the one who asks the right question.",
        ),
        ("character", "MAYA"),
        ("dialogue", "Someone wanted us to look behind the painting."),
        ("scene", "INT. MANOR - LIBRARY - DAY"),
        (
            "action",
            "Quinn reassembles the room. Mrs. Ashworth pales as Maya holds up the decoy "
            "and the real case side by side.",
        ),
        ("character", "MAYA"),
        ("dialogue", "The key didn't leave the manor. It was moved to tell a story. "
            "Whose story, Mrs. Ashworth?"),
    ]
    return _screenplay_to_lines("THE GLASS KEY", "Helen Voss", body)


def _mystery_10scene() -> Screenplay:
    """Return the mystery 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. ASHWORTH MANOR - ESTABLISHING - DAY"),
        ("action", "Gothic stone. Rain. A single police cruiser in the drive."),
        ("scene", "INT. MANOR - LIBRARY - DAY"),
        ("action", "Empty velvet case. MRS. ASHWORTH watches DETECTIVE MAYA QUINN work."),
        ("character", "MAYA"),
        ("dialogue", "The GLASS KEY was here at midnight. Who had access?"),
        ("scene", "INT. MANOR - DINING ROOM - DAY"),
        ("action", "Quinn interviews the nephew, CALEB, 40s, nervous cuff adjustment."),
        ("character", "CALEB"),
        ("dialogue", "I left after port. I didn't need heirloom drama."),
        ("scene", "INT. MANOR - GREENHOUSE - DAY"),
        ("action", "TOMAS the gardener. Mud, locket, defensive posture."),
        ("character", "TOMAS"),
        ("dialogue", "I lock up at nine."),
        ("scene", "INT. MANOR - SERVANTS' STAIR - DAY"),
        ("action", "Quinn finds a muddy partial print — smaller than Tomas's boot."),
        ("character", "MAYA"),
        ("dialogue", "Someone ran through here after the rain started."),
        ("scene", "INT. MANOR - NORTH WING HALL - DAY"),
        ("action", "Scratches on the portrait frame. Hidden door behind MR. ASHWORTH's likeness."),
        ("scene", "INT. HIDDEN STUDY - DAY"),
        ("action", "Decoy GLASS KEY. Cryptic note on the desk."),
        ("character", "MAYA"),
        ("dialogue", "This room hasn't been opened in years. Except tonight."),
        ("scene", "INT. MANOR - MRS. ASHWORTH'S BEDROOM - DAY"),
        ("action", "Quinn finds a ledger entry — insurance revised upward last week."),
        ("character", "MAYA"),
        ("dialogue", "You reported the key missing before you called us."),
        ("scene", "INT. MANOR - LIBRARY - DAY"),
        ("action", "Caleb bursts in — heard about the hidden study."),
        ("character", "CALEB"),
        ("dialogue", "That key opens a safe with my father's will."),
        ("scene", "INT. MANOR - LIBRARY - DAY"),
        (
            "action",
            "Maya lays decoy and empty case before Mrs. Ashworth. The old woman's "
            "composure cracks — not grief, but calculation.",
        ),
        ("character", "MAYA"),
        ("dialogue", "The key didn't leave. You moved it to delay the reading. "
            "The question is who you're protecting."),
    ]
    return _screenplay_to_lines("THE GLASS KEY", "Helen Voss", body)


def _crime_5scene() -> Screenplay:
    """Return the crime 5-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. FISHING TRAWLER - WHEELHOUSE - NIGHT"),
        (
            "action",
            "Fog. CAPTAIN EDDIE MORAN, 50s, steers by radar alone. First mate "
            "CALLAHAN watches a blip trailing them port-side.",
        ),
        ("character", "CALLAHAN"),
        ("dialogue", "Coast Guard doesn't run dark on a night like this."),
        ("character", "EDDIE"),
        ("dialogue", "Then it's not Coast Guard."),
        ("scene", "EXT. TRAWLER DECK - NIGHT"),
        (
            "action",
            "Men in black climb from a rigid hull boat. Eddie nods — routine, ugly. "
            "Crates swap hands: fish out, shrink-wrapped bricks in.",
        ),
        ("scene", "INT. HARBOR OFFICE - NIGHT"),
        (
            "action",
            "DETECTIVE SARAH PELL, 40s, compares shipping logs to radar captures. "
            "Her partner, DUNN, sets down a PHOTO of Eddie's trawler.",
        ),
        ("character", "PELL"),
        ("dialogue", "Three runs this month. Same fog bank, same blind spot."),
        ("character", "DUNN"),
        ("dialogue", "Moran's been fishing these waters since we were in grade school."),
        ("scene", "INT. DOCKside BAR - NIGHT"),
        (
            "action",
            "Pell slides onto a stool near Eddie. He doesn't look up from his beer.",
        ),
        ("character", "PELL"),
        ("dialogue", "Your manifest says cod. Your hull rides like heroin."),
        ("character", "EDDIE"),
        ("dialogue", "You come down here with proof or sympathy. I can't use either."),
        ("scene", "EXT. HARBOR - PREDAWN"),
        (
            "action",
            "Eddie's trawler pulls out. Pell watches from the pier, a warrant in her "
            "pocket she isn't ready to use.",
        ),
        ("character", "PELL"),
        ("dialogue", "One more run, Eddie. Then I stop asking nicely."),
    ]
    return _screenplay_to_lines("LOW TIDE", "Vincent Marchetti", body)


def _crime_10scene() -> Screenplay:
    """Return the crime 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. HARBOR - ESTABLISHING - NIGHT"),
        ("action", "Working docks. Fog rolls in. Trawlers creak at moorings."),
        ("scene", "INT. FISHING TRAWLER - WHEELHOUSE - NIGHT"),
        ("action", "CAPTAIN EDDIE MORAN steers. CALLAHAN spots a dark contact on radar."),
        ("character", "CALLAHAN"),
        ("dialogue", "Coast Guard doesn't run dark."),
        ("scene", "EXT. TRAWLER DECK - NIGHT"),
        ("action", "Covert exchange — fish out, shrink-wrapped cargo in."),
        ("scene", "INT. HARBOR OFFICE - NIGHT"),
        ("action", "DETECTIVE SARAH PELL maps three identical runs. DUNN skeptical."),
        ("character", "PELL"),
        ("dialogue", "Same fog bank. Same blind spot. Moran's boat every time."),
        ("scene", "INT. PELL'S APARTMENT - NIGHT"),
        ("action", "Case files spread on the table. Photos of Eddie with his daughter at a pier picnic."),
        ("character", "PELL"),
        ("dialogue", "He's not a kingpin. He's a paycheck."),
        ("scene", "INT. DOCKside BAR - NIGHT"),
        ("action", "Pell confronts Eddie. He stays calm, tired."),
        ("character", "EDDIE"),
        ("dialogue", "You come with proof or sympathy."),
        ("scene", "EXT. HOSPITAL - DAY"),
        ("action", "Pell learns Eddie's daughter starts chemo next week — bills pinned to a fridge photo in the file."),
        ("character", "DUNN"),
        ("dialogue", "That doesn't make the run legal."),
        ("scene", "INT. WAREHOUSE - NIGHT"),
        ("action", "Surveillance: Eddie meets a buyer in a yellow slicker — not his usual contact."),
        ("character", "PELL"),
        ("dialogue", "Someone new is using his route."),
        ("scene", "INT. TRAWLER HOLD - NIGHT"),
        ("action", "Pell and a tac team board — empty hold, trapdoor open to the water."),
        ("character", "EDDIE"),
        ("dialogue", "I didn't run tonight. They used my name."),
        ("scene", "EXT. HARBOR - PREDAWN"),
        (
            "action",
            "Eddie in cuffs on the pier. Pell watches the real smuggler boat vanish "
            "into fog. She has a bigger fish — and a smaller man to cut loose.",
        ),
        ("character", "PELL"),
        ("dialogue", "Tell me who owns the yellow slicker. Then we talk about your daughter."),
    ]
    return _screenplay_to_lines("LOW TIDE", "Vincent Marchetti", body)


def _western_5scene() -> Screenplay:
    """Return the western 5-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. DRY RIVER CROSSING - DAY"),
        (
            "action",
            "Dust devils. A cattle herd bunches at a vanished ford. RANCHER HOLT "
            "MCCREADY, 50s, scans the cracked bed with binoculars.",
        ),
        ("character", "HOLT"),
        ("dialogue", "Water's gone upstream. We move or we lose half the herd by sundown."),
        ("scene", "EXT. RIDGE TRAIL - DAY"),
        (
            "action",
            "Holt rides with his foreman, JESSE, 30s. Below, the DAWSON spread — "
            "a dam of stacked river rock, new and deliberate.",
        ),
        ("character", "JESSE"),
        ("dialogue", "Dawson diverts the flow to his south pasture. Always wanted this crossing."),
        ("character", "HOLT"),
        ("dialogue", "Then we ask before we shoot."),
        ("scene", "INT. DAWSON RANCH HOUSE - DAY"),
        (
            "action",
            "WILL DAWSON, 45, boots on the table, rifle within reach. Holt stands in "
            "the doorway, hat in hand.",
        ),
        ("character", "HOLT"),
        ("dialogue", "Your dam's killing my cattle. Tear it down."),
        ("character", "DAWSON"),
        ("dialogue", "River changed course on God's timetable. I just helped."),
        ("scene", "EXT. DRY RIVER CROSSING - DUSK"),
        (
            "action",
            "Holt's crew attempts a drive across cracked mud. A steer breaks leg-deep. "
            "Gunshots pop — warning shots from Dawson's ridge.",
        ),
        ("character", "JESSE"),
        ("dialogue", "They're herding us, not the cattle!"),
        ("scene", "EXT. DRY RIVER CROSSING - NIGHT"),
        (
            "action",
            "Holt walks the bed alone, lantern low. He finds a dynamite crate half-buried "
            "— not Dawson's mark. Someone else wants this fight bloody.",
        ),
        ("character", "HOLT"),
        ("dialogue", "Jesse, we got a third hand in this war. And he's lighting fuses."),
    ]
    return _screenplay_to_lines("DRY CROSSING", "Sam Whitaker", body)


def _western_10scene() -> Screenplay:
    """Return the western 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. MCCREADY RANCH - DAWN"),
        ("action", "Cattle low. Smoke from the cookhouse. Another dry month carved into every face."),
        ("scene", "EXT. DRY RIVER CROSSING - DAY"),
        ("action", "HOLT MCCREADY's herd stalled at a vanished ford."),
        ("character", "HOLT"),
        ("dialogue", "We move or lose half by sundown."),
        ("scene", "EXT. RIDGE TRAIL - DAY"),
        ("action", "Dawson's rock dam visible below. Jesse spits dust."),
        ("character", "JESSE"),
        ("dialogue", "He always wanted this crossing."),
        ("scene", "INT. DAWSON RANCH HOUSE - DAY"),
        ("action", "WILL DAWSON and Holt — tense, rifle within reach."),
        ("character", "DAWSON"),
        ("dialogue", "River changed on God's timetable."),
        ("scene", "EXT. MCCREADY RANCH - NIGHT"),
        ("action", "Holt's wife, CLARA, sets out food for riders. Worry unspoken."),
        ("character", "CLARA"),
        ("dialogue", "You go to Dawson with words. Come back with words."),
        ("scene", "EXT. DRY RIVER CROSSING - DUSK"),
        ("action", "Failed crossing. A steer trapped. Warning shots from the ridge."),
        ("scene", "EXT. DAWSON RIDGE - DUSK"),
        ("action", "Holt rides up — alone, hands visible. Dawson's men tense."),
        ("character", "HOLT"),
        ("dialogue", "You didn't fire those shots. Who did?"),
        ("scene", "INT. DAWSON RANCH - NIGHT"),
        ("action", "Holt and Dawson compare notes — both found dynamite near the bed."),
        ("character", "DAWSON"),
        ("dialogue", "Railroad man paid for a feud. Cheaper than buying us out."),
        ("scene", "EXT. DRY RIVER CROSSING - NIGHT"),
        ("action", "Holt finds a fuse line leading to the dam. Fresh footprints — city boots."),
        ("scene", "EXT. DRY RIVER CROSSING - NIGHT"),
        (
            "action",
            "Holt cuts the fuse. Dawson arrives from the opposite bank — first time "
            "without a rifle raised.",
        ),
        ("character", "HOLT"),
        ("dialogue", "We tear the dam together. Or we both lose the land to a track line."),
        ("character", "DAWSON"),
        ("dialogue", "God's timetable, huh. Grab a hammer."),
    ]
    return _screenplay_to_lines("DRY CROSSING", "Sam Whitaker", body)


def _war_5scene() -> Screenplay:
    """Return the war 5-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. FRONT LINE TRENCH - DAWN"),
        (
            "action",
            "Fog erases no-man's-land. SERGEANT TOM HALE, 28, checks his squad — "
            "RIVERS, KOWALSKI, NGUYEN. Artillery rumbles distant, rhythmic.",
        ),
        ("character", "HALE"),
        ("dialogue", "Stand-to. Eyes on the wire."),
        ("scene", "INT. DUGOUT - DAY"),
        (
            "action",
            "Hale reads orders by lantern. A map shows a German listening post "
            "200 meters out — marked for capture, not kill.",
        ),
        ("character", "HALE"),
        ("dialogue", "We bring back papers, not souvenirs. Quiet in, quiet out."),
        ("scene", "EXT. NO-MAN'S-LAND - NIGHT"),
        (
            "action",
            "The squad crawls through mud and wire. Flares burst — Kowalski freezes. "
            "Hale pulls him down inches from a trip line.",
        ),
        ("character", "HALE"),
        ("parenthetical", "whisper"),
        ("dialogue", "Breathe. Move on my count."),
        ("scene", "INT. ENEMY LISTENING POST - NIGHT"),
        (
            "action",
            "Close quarters. Nguyen covers the door. Hale shoves a satchel against "
            "the lone operator — young, barely shaving.",
        ),
        ("character", "HALE"),
        ("dialogue", "Papers. Radio codes. Nobody dies if you choose fast."),
        ("scene", "EXT. ALLIED TRENCH - PREDAWN"),
        (
            "action",
            "The squad drops back over the parapet, satchel secure. Hale stares at "
            "the captured map — coordinates match their own sector.",
        ),
        ("character", "HALE"),
        ("dialogue", "They weren't listening to us. They were marking us for tomorrow."),
    ]
    return _screenplay_to_lines("FOG LINE", "James O'Brien", body)


def _war_10scene() -> Screenplay:
    """Return the war 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. FRONT LINE TRENCH - DAWN"),
        ("action", "Fog. SERGEANT TOM HALE's squad at stand-to. Mud, wool, exhaustion."),
        ("character", "HALE"),
        ("dialogue", "Eyes on the wire."),
        ("scene", "INT. DUGOUT - DAY"),
        ("action", "Orders arrive — capture a listening post, bring back codes."),
        ("character", "HALE"),
        ("dialogue", "Quiet in, quiet out."),
        ("scene", "INT. DUGOUT - NIGHT"),
        ("action", "Hale briefs RIVERS, KOWALSKI, NGUYEN. Wire cutters, chalk marks on sleeves."),
        ("scene", "EXT. TRENCH LADDER - NIGHT"),
        ("action", "Over the top. Flares bloom. The squad becomes shadows."),
        ("scene", "EXT. NO-MAN'S-LAND - NIGHT"),
        ("action", "Kowalski freezes near a trip wire. Hale guides his boot aside."),
        ("character", "HALE"),
        ("parenthetical", "whisper"),
        ("dialogue", "On my count."),
        ("scene", "INT. ENEMY LISTENING POST - NIGHT"),
        ("action", "Young operator raises hands. Nguyen secures the door."),
        ("character", "HALE"),
        ("dialogue", "Papers. Codes. Choose fast."),
        ("scene", "INT. LISTENING POST - NIGHT"),
        ("action", "Hale finds a map — Allied positions marked in fresh ink."),
        ("character", "RIVERS"),
        ("dialogue", "That's our trench layout."),
        ("scene", "EXT. NO-MAN'S-LAND - NIGHT"),
        ("action", "Return crawl — mortar rounds walk closer. Kowalski hit, shoulder."),
        ("character", "HALE"),
        ("dialogue", "Drag him. Leave nothing."),
        ("scene", "EXT. ALLIED TRENCH - PREDAWN"),
        ("action", "Satchel handed up. Medics take Kowalski."),
        ("scene", "INT. COMMAND BUNKER - DAWN"),
        (
            "action",
            "Hale lays the map before CAPTAIN REED. Artillery coordinates match "
            "tomorrow's barrage.",
        ),
        ("character", "HALE"),
        ("dialogue", "They weren't listening. They were ranging us. We move the line today or lose it."),
    ]
    return _screenplay_to_lines("FOG LINE", "James O'Brien", body)


def _family_5scene() -> Screenplay:
    """Return the family 5-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. MORALES HOME - KITCHEN - DAY"),
        (
            "action",
            "Preparation chaos. MARIA MORALES, 60s, directs grandchildren with oven "
            "mitts. Her son ANTONIO, 40s, chops onions in silence.",
        ),
        ("character", "MARIA"),
        ("dialogue", "Twenty people at six. Nobody fights at my table tonight."),
        ("scene", "INT. MORALES HOME - LIVING ROOM - DAY"),
        (
            "action",
            "Antonio's sister DIANA, 38, hangs old photos. One frame turned face-down — "
            "their father, absent twenty years.",
        ),
        ("character", "DIANA"),
        ("dialogue", "Mom still sets a plate for a ghost."),
        ("character", "ANTONIO"),
        ("dialogue", "Then let the ghost stay in the closet with the picture."),
        ("scene", "INT. MORALES HOME - DINING ROOM - NIGHT"),
        (
            "action",
            "Full table. Laughter brittle. The doorbell rings. Maria freezes. "
            "On the porch: RAUL MORALES, 65, thin envelope in hand.",
        ),
        ("character", "MARIA"),
        ("dialogue", "You don't get to walk in like the years were a nap."),
        ("scene", "INT. MORALES HOME - DINING ROOM - NIGHT"),
        (
            "action",
            "Raul sits at the empty place. Antonio pushes back his chair. Grandchildren "
            "watch, sensing the temperature drop.",
        ),
        ("character", "RAUL"),
        ("dialogue", "I didn't come for forgiveness. I came to tell you what the lawyers kept."),
        ("scene", "INT. MORALES HOME - KITCHEN - NIGHT"),
        (
            "action",
            "Diana opens the envelope — deed papers, a key. Maria reads, hands shaking "
            "not with anger but disbelief.",
        ),
        ("character", "MARIA"),
        ("dialogue", "He left the house to all of us. Not to me alone."),
        ("character", "ANTONIO"),
        ("dialogue", "So he buys his way back with brick and mortar?"),
        ("character", "DIANA"),
        ("dialogue", "No. He finally put our names on the same page."),
    ]
    return _screenplay_to_lines("THE REUNION TABLE", "Carmen Delgado", body)


def _family_10scene() -> Screenplay:
    """Return the family 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. MORALES HOME - ESTABLISHING - DAY"),
        ("action", "A full porch. Streamers. A reunion twenty years in the making."),
        ("scene", "INT. KITCHEN - DAY"),
        ("action", "MARIA commands the stove. ANTONIO chops, silent."),
        ("character", "MARIA"),
        ("dialogue", "Nobody fights at my table tonight."),
        ("scene", "INT. LIVING ROOM - DAY"),
        ("action", "DIANA hangs photos. One frame face-down — their father."),
        ("character", "DIANA"),
        ("dialogue", "Mom still sets a plate for a ghost."),
        ("scene", "INT. GUEST BEDROOM - DAY"),
        ("action", "Antonio's wife packs a go-bag — ready to leave if it goes bad."),
        ("character", "ANTONIO'S WIFE"),
        ("dialogue", "Give her tonight. Then we decide."),
        ("scene", "INT. DINING ROOM - NIGHT"),
        ("action", "Twenty chairs. Wine poured. The doorbell."),
        ("scene", "EXT. FRONT PORCH - NIGHT"),
        ("action", "RAUL MORALES — older, tired, envelope in hand."),
        ("character", "MARIA"),
        ("dialogue", "You don't walk in like the years were a nap."),
        ("scene", "INT. DINING ROOM - NIGHT"),
        ("action", "Raul at the empty place. Children stare. Antonio stands."),
        ("character", "RAUL"),
        ("dialogue", "I came to tell you what the lawyers kept."),
        ("scene", "INT. KITCHEN - NIGHT"),
        ("action", "Diana reads the deed. Maria sinks onto a stool."),
        ("character", "MARIA"),
        ("dialogue", "He left the house to all of us."),
        ("scene", "EXT. BACK PORCH - NIGHT"),
        ("action", "Antonio and Raul alone. Crickets. Long pause."),
        ("character", "RAUL"),
        ("dialogue", "I didn't fix anything. I only stopped lying about who owns what."),
        ("scene", "INT. DINING ROOM - NIGHT"),
        (
            "action",
            "Maria raises a glass. Antonio does not join — yet. Diana reaches under "
            "the table, finds his hand, pulls him back to sit.",
        ),
        ("character", "MARIA"),
        ("dialogue", "Same roof. Same names. We eat first. We talk after."),
    ]
    return _screenplay_to_lines("THE REUNION TABLE", "Carmen Delgado", body)


def _sports_5scene() -> Screenplay:
    """Return the sports 5-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. UNIVERSITY POOL - MORNING"),
        (
            "action",
            "Lane lines cut still water. COACH ALMA REYES, 50s, watches NINA VASQUEZ, "
            "22, sprint intervals — fast, angry, precise.",
        ),
        ("character", "ALMA"),
        ("dialogue", "Elbows higher on the turn. You're racing the clock, not your ghost."),
        ("scene", "INT. ATHLETIC TRAINING ROOM - DAY"),
        (
            "action",
            "Nina ices her shoulder. A TV replays last year's nationals — Nina "
            "finishing fourth, touching the wall a breath too late.",
        ),
        ("character", "NINA"),
        ("dialogue", "One hundredth of a second. That's not a ghost. That's math."),
        ("scene", "INT. COACH'S OFFICE - DAY"),
        (
            "action",
            "Alma slides a meet invitation across the desk — SENIOR INVITATIONAL, "
            "Nina's last eligible meet.",
        ),
        ("character", "ALMA"),
        ("dialogue", "You swim or you retire wondering. No middle lane."),
        ("scene", "INT. UNIVERSITY POOL - NIGHT"),
        (
            "action",
            "Empty stands. Nina dives alone — brutal pace. Her stroke falters at 150 "
            "meters. She slams the lane rope, gasping.",
        ),
        ("character", "NINA"),
        ("dialogue", "I can't hit the split. Not clean. Not ever."),
        ("scene", "INT. UNIVERSITY POOL - DAY"),
        (
            "action",
            "Meet day. Blocks set. Alma touches Nina's cap — wordless. Nina settles "
            "into stillness. The starter raises his pistol.",
        ),
        ("character", "NINA"),
        ("parenthetical", "to herself"),
        ("dialogue", "Not fourth. Not almost."),
    ]
    return _screenplay_to_lines("FINAL LAP", "Tyler Brooks", body)


def _sports_10scene() -> Screenplay:
    """Return the sports 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. UNIVERSITY CAMPUS - ESTABLISHING - DAY"),
        ("action", "Autumn. Banners for the Senior Invitational flutter over the aquatics center."),
        ("scene", "INT. UNIVERSITY POOL - MORNING"),
        ("action", "NINA VASQUEZ attacks intervals. COACH ALMA REYES watches, arms crossed."),
        ("character", "ALMA"),
        ("dialogue", "You're racing the clock, not your ghost."),
        ("scene", "INT. TRAINING ROOM - DAY"),
        ("action", "Shoulder iced. Replay of nationals — Nina fourth by a hundredth."),
        ("character", "NINA"),
        ("dialogue", "That's math, not mythology."),
        ("scene", "INT. LOCKER ROOM - DAY"),
        ("action", "Teammates celebrate invites. Nina stares at her lane assignment."),
        ("scene", "INT. COACH'S OFFICE - DAY"),
        ("action", "Alma slides the invitational invite — last eligible meet."),
        ("character", "ALMA"),
        ("dialogue", "Swim or retire wondering."),
        ("scene", "INT. DORM ROOM - NIGHT"),
        ("action", "Nina's father calls. She doesn't pick up. Medal in a drawer, face down."),
        ("scene", "INT. UNIVERSITY POOL - NIGHT"),
        ("action", "Solo session. Split fails at 150. Nina hits the lane rope."),
        ("character", "NINA"),
        ("dialogue", "Not clean. Not ever."),
        ("scene", "EXT. POOL DECK - MORNING"),
        ("action", "Alma finds Nina stretching in the cold — two hours before warm-ups."),
        ("character", "ALMA"),
        ("dialogue", "Fourth isn't a sentence. It's a split you already survived."),
        ("scene", "INT. UNIVERSITY POOL - DAY"),
        ("action", "Blocks. Crowd noise muffled. Nina's world narrows to water."),
        ("character", "NINA"),
        ("parenthetical", "to herself"),
        ("dialogue", "Not fourth. Not almost."),
        ("scene", "INT. UNIVERSITY POOL - DAY"),
        (
            "action",
            "Turn at 150 — elbows high, exactly as coached. Nina drives for the wall. "
            "Alma doesn't look at the board yet. She watches Nina's face break open.",
        ),
        ("character", "ALMA"),
        ("dialogue", "There she is. That's the split."),
    ]
    return _screenplay_to_lines("FINAL LAP", "Tyler Brooks", body)


def _adventure_5scene() -> Screenplay:
    """Return the adventure 5-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. NEPAL BASE CAMP - DAY"),
        (
            "action",
            "Prayer flags snap in thin air. CLIMBER JUNE OKAFOR, 35, checks crampons. "
            "Guide TENZIN adjusts her harness. A WAX-SEALED ENVELOPE bulges in June's chest pocket.",
        ),
        ("character", "TENZIN"),
        ("dialogue", "Summit window closes in thirty-six hours. Weather turns after."),
        ("scene", "EXT. ICE FALL - DAY"),
        (
            "action",
            "The team picks through blue ice. June pauses at a cairn — a tin box with "
            "a name: M. OKAFOR, 1987.",
        ),
        ("character", "JUNE"),
        ("dialogue", "My father turned back fifty meters below the ridge. Never told me why."),
        ("scene", "INT. TENT - NIGHT"),
        (
            "action",
            "June opens the envelope by headlamp — her father's handwriting. Coordinates, "
            "a sketch of a cave below the summit.",
        ),
        ("character", "JUNE"),
        ("dialogue", "He wasn't turning back from the mountain. He was turning toward something."),
        ("scene", "EXT. SUMMIT RIDGE - DAWN"),
        (
            "action",
            "Wind screams. June and Tenzin crest the ridge — not the true summit, but a "
            "fissure in the face, exactly where the sketch indicated.",
        ),
        ("character", "TENZIN"),
        ("dialogue", "We have twenty minutes. Then we descend or we die polite."),
        ("scene", "INT. ICE CAVE - DAY"),
        (
            "action",
            "Lantern glow on stacked survey crates — British expedition, 1987. June finds "
            "her father's journal, last entry unfinished.",
        ),
        ("character", "JUNE"),
        ("dialogue", "He found proof the peak was wrong by forty meters. They buried it to keep the record."),
    ]
    return _screenplay_to_lines("THE SUMMIT NOTE", "Alex Rivera", body)


def _adventure_10scene() -> Screenplay:
    """Return the adventure 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. KATHMANDU - ESTABLISHING - DAY"),
        ("action", "Gear shops. Permits stamped. A expedition assembles."),
        ("scene", "EXT. NEPAL BASE CAMP - DAY"),
        ("action", "JUNE OKAFOR and guide TENZIN review the route. WAX-SEALED ENVELOPE in June's pocket."),
        ("character", "TENZIN"),
        ("dialogue", "Summit window closes in thirty-six hours."),
        ("scene", "EXT. KHUMBU GLACIER - DAY"),
        ("action", "Loads carried. Ropes fixed. June lags, reading the envelope again."),
        ("scene", "EXT. ICE FALL - DAY"),
        ("action", "Cairn with tin box — M. OKAFOR, 1987."),
        ("character", "JUNE"),
        ("dialogue", "He turned back fifty meters below the ridge."),
        ("scene", "INT. TENT - NIGHT"),
        ("action", "Father's coordinates, cave sketch, unfinished sentences."),
        ("character", "JUNE"),
        ("dialogue", "He wasn't quitting. He was hiding something."),
        ("scene", "EXT. HIGH CAMP - NIGHT"),
        ("action", "Storm rolls early. Tenzin wants descent. June argues for one push."),
        ("character", "TENZIN"),
        ("dialogue", "The mountain doesn't care about your family."),
        ("scene", "EXT. SUMMIT APPROACH - DAWN"),
        ("action", "Wind drops — brief gift. They climb toward the fissure, not the ceremonial summit."),
        ("scene", "INT. ICE CAVE - DAY"),
        ("action", "Survey crates. 1987 British labels. Journal with June's father's name."),
        ("character", "JUNE"),
        ("dialogue", "They measured the peak wrong. He wouldn't lie on a map."),
        ("scene", "EXT. SUMMIT RIDGE - DAY"),
        ("action", "Tenzin watches the weather clock. June copies the journal's final page."),
        ("character", "TENZIN"),
        ("dialogue", "We leave now with proof, or we leave forever without it."),
        ("scene", "EXT. DESCENT TRAIL - DUSK"),
        (
            "action",
            "June descends with the journal photographed, envelope burned for warmth. "
            "Behind her, the true summit gleams — forty meters higher than history says.",
        ),
        ("character", "JUNE"),
        ("dialogue", "Next season, we put his name on the right line."),
    ]
    return _screenplay_to_lines("THE SUMMIT NOTE", "Alex Rivera", body)


def _heist_5scene() -> Screenplay:
    """Return the heist 5-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. ART MUSEUM - CLOSED GALLERY - NIGHT"),
        (
            "action",
            "Laser grids faint in the dark. MARCUS VELA, 40s, thief-planner, studies "
            "a floor plan on a tablet. His crew — SLOANE, REESE, PAK — wait in black.",
        ),
        ("character", "MARCUS"),
        ("dialogue", "The DIAMOND STUDY is a decoy. We take the sketch behind it."),
        ("scene", "INT. SERVICE CORRIDOR - NIGHT"),
        (
            "action",
            "Pak bypasses a keypad. Sloane loops camera feeds — twelve-second gaps. "
            "Reese carries a rolled CANVAS TUBE, empty for now.",
        ),
        ("character", "SLOANE"),
        ("dialogue", "Guard rotation in ninety. After that, we're tourists who forgot to leave."),
        ("scene", "INT. VAULT ANTEROOM - NIGHT"),
        (
            "action",
            "Marcus lifts the decoy painting — behind it, a charcoal sketch worth more "
            "than the jewel beside it. Vermeer study, unauthenticated, real.",
        ),
        ("character", "REESE"),
        ("dialogue", "Swap clean?"),
        ("character", "MARCUS"),
        ("dialogue", "Replica's in the tube. Thirty seconds."),
        ("scene", "INT. MUSEUM LOBBY - NIGHT"),
        (
            "action",
            "Alarms stay silent. They walk out as maintenance — hi-vis vests over black. "
            "An ACTUAL GUARD nods, bored.",
        ),
        ("character", "GUARD"),
        ("dialogue", "Elevator's slow tonight. Don't miss your train."),
        ("scene", "EXT. MUSEUM LOADING DOCK - NIGHT"),
        (
            "action",
            "Van doors close. Marcus unrolls the sketch — breath catches. Sloane's phone "
            "buzzes: a text from an unknown number. THEY KNOW.",
        ),
        ("character", "MARCUS"),
        ("dialogue", "Job's not over when we leave the building. Someone wanted us to take this."),
    ]
    return _screenplay_to_lines("VAULT FOURTEEN", "Daniel Crowe", body)


def _heist_10scene() -> Screenplay:
    """Return the heist 10-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. WAREHOUSE LOFT - NIGHT"),
        ("action", "Marcus briefs the crew. Museum floor plan projected on brick."),
        ("character", "MARCUS"),
        ("dialogue", "We don't touch the diamond. We take the sketch behind it."),
        ("scene", "INT. VAN - NIGHT"),
        ("action", "Gear check. CANVAS TUBE, replica painting, maintenance vests."),
        ("scene", "EXT. MUSEUM - NIGHT"),
        ("action", "Rain. Sloane watches guard patterns from a parked car."),
        ("scene", "INT. SERVICE CORRIDOR - NIGHT"),
        ("action", "Pak kills the keypad. Camera loop live."),
        ("character", "PAK"),
        ("dialogue", "Twelve-second holes. Don't blink."),
        ("scene", "INT. CLOSED GALLERY - NIGHT"),
        ("action", "Laser grid. Reese mirrors a path with chalk on the floor."),
        ("scene", "INT. VAULT ANTEROOM - NIGHT"),
        ("action", "Decoy lifted. Vermeer study revealed. Swap begins."),
        ("character", "MARCUS"),
        ("dialogue", "Replica in. Original out. Thirty seconds."),
        ("scene", "INT. MUSEUM LOBBY - NIGHT"),
        ("action", "Maintenance disguise. Guard nods them through."),
        ("scene", "EXT. LOADING DOCK - NIGHT"),
        ("action", "Van pulls away clean. No alarms."),
        ("scene", "INT. VAN - MOVING - NIGHT"),
        ("action", "Sloane's phone — unknown number: THEY KNOW."),
        ("character", "SLOANE"),
        ("dialogue", "We had no digital footprint. Who's texting?"),
        ("scene", "INT. WAREHOUSE LOFT - NIGHT"),
        (
            "action",
            "Sketch unrolled under lights. Marcus finds a micro-dot on the frame — "
            "museum inventory sticker, fresh.",
        ),
        ("character", "MARCUS"),
        ("dialogue", "We weren't stealing art. We were delivering it. Question is to who."),
    ]
    return _screenplay_to_lines("VAULT FOURTEEN", "Daniel Crowe", body)


def _noir_5scene() -> Screenplay:
    """Return the noir 5-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. MERIDIAN AVENUE - RAIN - NIGHT"),
        (
            "action",
            "Neon bleeds on wet asphalt. PRIVATE INVESTIGATOR FRANK MERCER, 45, "
            "turns up his collar. A CLIENT waits under a broken awning.",
        ),
        ("character", "CLIENT"),
        ("dialogue", "My husband keeps late hours at the Meridian Hotel. I want names."),
        ("scene", "INT. MERCER'S OFFICE - DAY"),
        (
            "action",
            "Frank develops photos — a woman in a RED HAT entering room 514. Not the "
            "client's husband. The husband follows, two hours later.",
        ),
        ("character", "FRANK"),
        ("dialogue", "Case wasn't infidelity. It was timing."),
        ("scene", "INT. MERIDIAN HOTEL - HALLWAY - NIGHT"),
        (
            "action",
            "Frank picks the lock on 514. Empty room — suitcase gone, bed still made. "
            "A matchbook on the nightstand: BLUE PARROT CLUB.",
        ),
        ("scene", "INT. BLUE PARROT CLUB - NIGHT"),
        (
            "action",
            "Smoke and jazz. The woman in the RED HAT sits with a man in a gray suit — "
            "the client's husband. They exchange a METAL CASE, not kisses.",
        ),
        ("character", "FRANK"),
        ("dialogue", "Ma'am, your husband isn't cheating. He's laundering."),
        ("scene", "INT. MERCER'S OFFICE - NIGHT"),
        (
            "action",
            "Rain hammers the window. The client returns — not worried wife, cold eyes. "
            "She slides an envelope across Frank's desk.",
        ),
        ("character", "CLIENT"),
        ("dialogue", "You were supposed to find a cheating husband. Not a partner."),
        ("character", "FRANK"),
        ("dialogue", "Then hire a worse detective next time."),
    ]
    return _screenplay_to_lines("RAIN ON MERIDIAN", "Walter Kane", body)


def _noir_10scene() -> Screenplay:
    """Return the noir 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. MERIDIAN AVENUE - RAIN - NIGHT"),
        ("action", "Neon, wet asphalt. PI FRANK MERCER meets a nervous CLIENT."),
        ("character", "CLIENT"),
        ("dialogue", "My husband keeps late hours. I want names."),
        ("scene", "INT. MERCER'S OFFICE - DAY"),
        ("action", "Frank files the retainer. Photos still in the envelope, undeveloped."),
        ("scene", "INT. MERCER'S OFFICE - NIGHT"),
        ("action", "Darkroom tray. RED HAT woman enters room 514. Husband follows later."),
        ("character", "FRANK"),
        ("dialogue", "Not infidelity. Timing."),
        ("scene", "INT. MERIDIAN HOTEL - LOBBY - NIGHT"),
        ("action", "Desk clerk remembers the husband — checked in, never checked out."),
        ("scene", "INT. MERIDIAN HOTEL - HALLWAY - NIGHT"),
        ("action", "Room 514 empty. Matchbook: BLUE PARROT CLUB."),
        ("scene", "INT. BLUE PARROT CLUB - NIGHT"),
        ("action", "RED HAT and husband swap a METAL CASE under the table."),
        ("character", "FRANK"),
        ("dialogue", "He's not cheating. He's laundering."),
        ("scene", "EXT. ALLEY BEHIND CLUB - NIGHT"),
        ("action", "Frank tailing the husband — ambush. A sap to the ribs, darkness."),
        ("scene", "INT. MERCER'S OFFICE - DAY"),
        ("action", "Frank bruised, angry. Client on the phone — sweet voice, wrong words."),
        ("character", "CLIENT"),
        ("dialogue", "Did you get the photos I paid for?"),
        ("scene", "INT. MERCER'S OFFICE - NIGHT"),
        ("action", "Client in person. Envelope on the desk. Rain like nails."),
        ("character", "CLIENT"),
        ("dialogue", "You were supposed to find a cheating husband."),
        ("scene", "INT. MERCER'S OFFICE - NIGHT"),
        (
            "action",
            "Frank slides the photos back — undeveloped lies removed, truth printed "
            "on the last frame: the client with the gray suit man.",
        ),
        ("character", "FRANK"),
        ("dialogue", "I found a partner. Yours. Hire a worse detective next time."),
    ]
    return _screenplay_to_lines("RAIN ON MERIDIAN", "Walter Kane", body)


def _coming_of_age_5scene() -> Screenplay:
    """Return the coming-of-age 5-scene starter screenplay."""
    body: Body = [
        ("scene", "INT. HIGH SCHOOL HALLWAY - DAY"),
        (
            "action",
            "Last week of senior year. MAYA CHEN, 18, pins a rehearsal schedule to "
            "the drama board. Her best friend JORDAN, 18, slumps beside her.",
        ),
        ("character", "MAYA"),
        ("dialogue", "We promised one perfect week before the world splits us up."),
        ("scene", "EXT. SCHOOL ROOFTOP - AFTERNOON"),
        (
            "action",
            "They sit with yearbooks and stolen sparkling cider. Jordan signs Maya's "
            "page — inside joke, looping handwriting.",
        ),
        ("character", "JORDAN"),
        ("dialogue", "State school for me. Coast for you. Facetime isn't a friendship."),
        ("character", "MAYA"),
        ("dialogue", "Then we make something here that doesn't fit in a dorm box."),
        ("scene", "INT. AUDITORIUM - NIGHT"),
        (
            "action",
            "Maya directs a guerrilla senior show — lights duct-taped, cast of twelve. "
            "Jordan runs sound, headphones around his neck.",
        ),
        ("character", "MAYA"),
        ("dialogue", "Places in five. If admin catches us, we run."),
        ("scene", "INT. BACKSTAGE - NIGHT"),
        (
            "action",
            "The principal's footsteps echo. Jordan kills the mains — sudden dark. "
            "Maya grabs his hand, laughing, terrified.",
        ),
        ("character", "JORDAN"),
        ("dialogue", "Worth it?"),
        ("character", "MAYA"),
        ("dialogue", "Ask me when we're sixty."),
        ("scene", "EXT. SCHOOL PARKING LOT - NIGHT"),
        (
            "action",
            "Cast scattered, safe. Maya and Jordan sit on the hood of her beat-up car. "
            "The auditorium glows behind them — one light still on.",
        ),
        ("character", "MAYA"),
        ("dialogue", "We didn't get a perfect week. We got a real one."),
        ("character", "JORDAN"),
        ("dialogue", "Same thing if you're paying attention."),
    ]
    return _screenplay_to_lines("SENIOR WEEK", "Priya Shah", body)


def _coming_of_age_10scene() -> Screenplay:
    """Return the coming-of-age 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. HIGH SCHOOL - ESTABLISHING - DAY"),
        ("action", "Banners: CLASS OF 2026. Last bell energy everywhere."),
        ("scene", "INT. HALLWAY - DAY"),
        ("action", "MAYA pins a senior-week schedule. JORDAN watches, skeptical."),
        ("character", "MAYA"),
        ("dialogue", "One perfect week before everything splits."),
        ("scene", "INT. GUIDANCE OFFICE - DAY"),
        ("action", "Maya gets financial aid confirmation — coast school real. Jordan fakes a smile."),
        ("scene", "EXT. ROOFTOP - AFTERNOON"),
        ("action", "Yearbooks, cider, signatures."),
        ("character", "JORDAN"),
        ("dialogue", "Facetime isn't a friendship."),
        ("scene", "INT. MAYA'S GARAGE - NIGHT"),
        ("action", "They build flats for an unauthorized senior play."),
        ("character", "MAYA"),
        ("dialogue", "Something that doesn't fit in a dorm box."),
        ("scene", "INT. AUDITORIUM - NIGHT"),
        ("action", "Guerrilla show begins — small audience, big heart."),
        ("scene", "INT. BACKSTAGE - NIGHT"),
        ("action", "Principal's footsteps. Jordan kills the lights. Hands find hands."),
        ("scene", "EXT. LOADING DOCK - NIGHT"),
        ("action", "Cast escapes laughing. Security flashlight sweeps empty aisles."),
        ("scene", "INT. PRINCIPAL'S OFFICE - NEXT DAY"),
        ("action", "Maya and Jordan sit, not sorry. Suspension threatened, then reduced."),
        ("character", "PRINCIPAL"),
        ("dialogue", "You broke three rules. You also gave twelve seniors a memory."),
        ("scene", "EXT. PARKING LOT - NIGHT"),
        (
            "action",
            "Graduation eve. Hood of Maya's car. Jordan hands her a USB — the show "
            "recorded from the sound board.",
        ),
        ("character", "JORDAN"),
        ("dialogue", "Same thing if you're paying attention. Perfect or real."),
        ("character", "MAYA"),
        ("dialogue", "Real. Always real."),
    ]
    return _screenplay_to_lines("SENIOR WEEK", "Priya Shah", body)


def _supernatural_5scene() -> Screenplay:
    """Return the supernatural 5-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. ABANDONED FARMHOUSE - DUSK"),
        (
            "action",
            "Weeds choke the porch. PARANORMAL RESEARCHER ELISE VOSS, 30s, sets up "
            "EMF meters. Her skeptic cameraman, DAN, 30s, rolls his eyes.",
        ),
        ("character", "ELISE"),
        ("dialogue", "Three families left in six months. Same bedroom, same story."),
        ("scene", "INT. FARMHOUSE - UPSTAIRS HALL - NIGHT"),
        (
            "action",
            "Temperature drops visible on breath. The THRESHOLD of the east bedroom "
            "glows faintly — not light, absence of it.",
        ),
        ("character", "DAN"),
        ("dialogue", "Draft from a cracked window. Relax."),
        ("character", "ELISE"),
        ("dialogue", "Windows don't whisper names."),
        ("scene", "INT. EAST BEDROOM - NIGHT"),
        (
            "action",
            "Elise steps across the THRESHOLD. Audio recorder spins — a child's voice, "
            "clear: Don't let her close the door.",
        ),
        ("scene", "INT. UPSTAIRS HALL - NIGHT"),
        (
            "action",
            "Dan searches for Elise — the hall stretches, doors multiply. His camera "
            "feed shows the hall empty seconds ago, now she's behind him.",
        ),
        ("character", "DAN"),
        ("dialogue", "Elise, we pack up. Now."),
        ("scene", "INT. EAST BEDROOM - NIGHT"),
        (
            "action",
            "Elise finds a child's DRAWING under the floorboard — the THRESHOLD outlined "
            "in red crayon, labeled THE OTHER SIDE OF AWAKE.",
        ),
        ("character", "ELISE"),
        ("dialogue", "Dan, this isn't a haunting. It's a door. And someone left it open."),
    ]
    return _screenplay_to_lines("THE THRESHOLD", "Morgan Blake", body)


def _supernatural_10scene() -> Screenplay:
    """Return the supernatural 10-scene starter screenplay."""
    body: Body = [
        ("scene", "EXT. FARMHOUSE - ESTABLISHING - DUSK"),
        ("action", "Remote county road. One light in an upper window — no power on record."),
        ("scene", "EXT. FARMHOUSE PORCH - DUSK"),
        ("action", "ELISE VOSS sets EMF gear. DAN films B-roll, unconvinced."),
        ("character", "ELISE"),
        ("dialogue", "Three families. Same bedroom. Same exit story."),
        ("scene", "INT. LIVING ROOM - NIGHT"),
        ("action", "Interviews on camera — former tenant: The door wouldn't stay open."),
        ("scene", "INT. UPSTAIRS HALL - NIGHT"),
        ("action", "Breath fog. The THRESHOLD of the east bedroom pulses dark."),
        ("character", "DAN"),
        ("dialogue", "Cracked window. Draft."),
        ("scene", "INT. EAST BEDROOM - NIGHT"),
        ("action", "Elise crosses the line. Recorder captures a child's warning."),
        ("character", "ON RECORDER — CHILD"),
        ("dialogue", "Don't let her close the door."),
        ("scene", "INT. UPSTAIRS HALL - NIGHT"),
        ("action", "Dan turns — hall longer than before. Elise behind him, though she never left the room on his feed."),
        ("scene", "INT. EAST BEDROOM - NIGHT"),
        ("action", "Floorboard pried. Child's DRAWING — THE OTHER SIDE OF AWAKE."),
        ("character", "ELISE"),
        ("dialogue", "A door. Left open."),
        ("scene", "INT. LIVING ROOM - NIGHT"),
        ("action", "Gear spins wild. Dan's camera catches a woman in period dress — not in the room when they blink."),
        ("character", "DAN"),
        ("dialogue", "We leave. We leave now."),
        ("scene", "EXT. PORCH - NIGHT"),
        ("action", "They stumble out. Upstairs window slams shut — from inside."),
        ("scene", "INT. EAST BEDROOM - NIGHT"),
        (
            "action",
            "Camera left behind keeps recording. The THRESHOLD flares. A small hand "
            "reaches through, closes the door gently — latched from the other side.",
        ),
        ("character", "ON RECORDER — CHILD"),
        ("dialogue", "Thank you for not closing it."),
    ]
    return _screenplay_to_lines("THE THRESHOLD", "Morgan Blake", body)


def additional_genre_screenplays() -> list[tuple[str, Screenplay]]:
    """Return genre slug and screenplay pairs for genres 7 through 20."""
    return [
        ("thriller", _thriller_5scene()),
        ("thriller", _thriller_10scene()),
        ("romance", _romance_5scene()),
        ("romance", _romance_10scene()),
        ("action", _action_5scene()),
        ("action", _action_10scene()),
        ("mystery", _mystery_5scene()),
        ("mystery", _mystery_10scene()),
        ("crime", _crime_5scene()),
        ("crime", _crime_10scene()),
        ("western", _western_5scene()),
        ("western", _western_10scene()),
        ("war", _war_5scene()),
        ("war", _war_10scene()),
        ("family", _family_5scene()),
        ("family", _family_10scene()),
        ("sports", _sports_5scene()),
        ("sports", _sports_10scene()),
        ("adventure", _adventure_5scene()),
        ("adventure", _adventure_10scene()),
        ("heist", _heist_5scene()),
        ("heist", _heist_10scene()),
        ("noir", _noir_5scene()),
        ("noir", _noir_10scene()),
        ("coming_of_age", _coming_of_age_5scene()),
        ("coming_of_age", _coming_of_age_10scene()),
        ("supernatural", _supernatural_5scene()),
        ("supernatural", _supernatural_10scene()),
    ]
