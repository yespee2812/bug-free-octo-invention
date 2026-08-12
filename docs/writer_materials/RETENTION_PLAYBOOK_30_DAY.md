# ScriptLens — 30-day retention playbook (cohort model)

Use this for **closed waves of 3–5 writers**, ~7 days of primary access, then a **30-day follow-through** so founding users don’t vanish after the demo week.

**Goals**

| Window | Success looks like |
|--------|--------------------|
| Days 1–7 | Uploaded a **real** script + ran ≥1 simulate |
| Days 8–14 | Marked ≥1 finding useful **or** ran a second pass |
| Days 15–30 | Returned for a rewrite checkpoint **or** said when they’ll rewrite next |

**Capacity rule:** one active cohort at a time; keep concurrent editors ≤ ~5.

---

## 0. Before Wave Day 0

### Waitlist → invite filter (ask these)

1. Fountain, PDF, or both?
2. Typical script length (short / feature)?
3. Next rewrite window (this week / this month / later)?
4. OK with a timed access window?

Invite people with a **rewrite in the next 2–4 weeks** first — they retain better.

### Cohort ops checklist

- [ ] VPS healthy (2 GB preferred); restart API before the wave
- [ ] Founding offer decided (e.g. $19–29/mo locked 3 months)
- [ ] Feedback form live (link below)
- [ ] Calendar: Wave start, mid-check (Day 3), close (Day 7), Day 14, Day 30
- [ ] Personal Slack/email thread for the 5 writers (optional but high leverage)

### Feedback form (same every wave)

1. Did you finish upload → simulate on a real script? (Y/N)
2. Which finding was most useful? (orphan / cut risk / other / none)
3. Did you trust it? (1–5)
4. What broke or confused you?
5. Would you pay? Range: $0 / $15 / $29 / $49 / $99+
6. When is your next rewrite?
7. One sentence: why you’d come back — or why not

---

## 1. Email sequence (copy/paste)

Replace bracketed fields. Keep subject lines short.

### E0 — Invite (Day −2 or Day 0 morning)

**Subject:** You’re in ScriptLens Wave {{WAVE}} ({{START}}–{{END}})

Hi {{NAME}},

You’re in the next ScriptLens writer cohort (**{{START}} → {{END}}**).

**Access:** {{APP_URL}}  
**Your window:** {{START}}–{{END}} (then we rotate the next set — you can still get founding access after).

**In one sitting (~15 min):**
1. Upload a script you’re actually rewriting (Fountain preferred; clean text PDF OK)
2. Open one high-risk / orphan finding
3. Run **Simulate** on a cut or edit you’d consider in real life
4. Reply to this email with: “useful / wrong / unclear” + scene number

**Founding note:** If Wave {{WAVE}} is useful, you can lock **{{FOUNDING_PRICE}}/mo for 3 months** before public pricing.

Questions → reply here. I’m reading every note this week.

— {{YOUR_NAME}}

---

### E1 — Kickoff (Day 0, when access opens)

**Subject:** Wave {{WAVE}} is open — one real script today

Hi {{NAME}},

Access is live: {{APP_URL}}

Ignore the tour. Do this today:

1. Upload **your** script (not a toy)
2. Click the finding that feels most dangerous
3. Simulate one cut/edit
4. Thumb / reply: useful or off?

If PDF looks wrong, try Fountain or see the cleanup guide we sent. If the session expires, just re-upload — early builds keep sessions in memory.

Form (2 min) whenever you’ve tried once: {{FEEDBACK_FORM}}

— {{YOUR_NAME}}

---

### E2 — Day 3 check-in (personal; send individually)

**Subject:** Quick check — Scene {{SCENE}} still the risky one?

Hi {{NAME}},

Checking in on Wave {{WAVE}}.

Have you had a chance to simulate on {{SCRIPT_OR_“your draft”}} yet?

If yes: which finding felt right, and which felt wrong?  
If not: what’s in the way — time, file format, or trust?

No essay needed — three lines is perfect.

— {{YOUR_NAME}}

---

### E3 — Day 7 wave close + founding offer

**Subject:** Wave {{WAVE}} closing — founding lock + next rewrite

Hi {{NAME}},

Wave {{WAVE}} primary access wraps **{{END}}**. Thank you for the real-script testing.

**Two asks:**
1. Feedback form if you haven’t: {{FEEDBACK_FORM}}
2. When is your **next rewrite**? (date or “sometime in {{MONTH}}”)

**Founding offer (optional):**  
Stay on ScriptLens at **{{FOUNDING_PRICE}}/mo for 3 months**, cancel anytime. I’ll ping you when that rewrite week hits so you’re not starting from zero.

Reply **FOUNDING** if you want the lock, or **LATER** if you only want a rewrite reminder.

— {{YOUR_NAME}}

---

### E4 — Day 14 (only if they activated; skip if never uploaded)

**Subject:** Second pass? Or save it for the rewrite

Hi {{NAME}},

It’s been a week since Wave {{WAVE}}.

Writers get the most from ScriptLens on a **second pass** — after you’ve changed an act break, cut a scene, or moved a reveal.

- If you’re mid-rewrite: re-upload and simulate the cut you’re debating  
- If not yet: tell me the week you expect to rewrite and I’ll nudge you then  

Link: {{APP_URL}}  
Still founding-eligible through {{FOUNDING_DEADLINE}}: reply **FOUNDING**

— {{YOUR_NAME}}

---

### E5 — Day 14 (never activated)

**Subject:** No stress — want a 20-min walkthrough?

Hi {{NAME}},

Looks like Wave {{WAVE}} got buried (happens).

Want either:
- **A)** a 20-min screenshare on *your* script, or  
- **B)** a slot in Wave {{NEXT_WAVE}}

Reply A or B. No guilt either way.

— {{YOUR_NAME}}

---

### E6 — Day 30 rewrite nudge

**Subject:** Rewrite checkpoint — {{SCRIPT_TITLE_OR_“your script”}}

Hi {{NAME}},

You flagged a rewrite around now (or it’s been ~30 days).

**Checkpoint:**
1. Re-upload the current draft  
2. Simulate the cut/edit you’re least sure about  
3. Reply with one line: kept / changed / ignored the suggestion

{{APP_URL}}

If the timing slipped, send a new date — I’ll move the reminder.

— {{YOUR_NAME}}

---

### E7 — Cancel / pause (when someone says they’re out)

**Subject:** Pausing is fine — one question

Hi {{NAME}},

Totally fine to pause.

For my notes (one line): was it **trust**, **workflow** (not in your daily tools), **timing**, **price**, or **bugs**?

If it’s timing, I’ll leave you alone until {{OPTIONAL_DATE}}.  
If it’s bugs/trust, I want the scene number — that’s gold.

— {{YOUR_NAME}}

---

## 2. In-app prompts (ship when you can; fake with email until then)

Use short copy. One job per prompt. No badge spam.

### P1 — First landing (empty state)

**Headline:** Upload a script you’re actually rewriting  
**Body:** Fountain works best. Clean text PDF is OK. You’ll get structure risk + simulate — not a grade.  
**CTA:** Upload script  
**Secondary:** Have a messy PDF? Open cleanup tips

### P2 — Right after first analysis completes

**Headline:** Pick the finding you’d argue about with a producer  
**Body:** Start with high-risk or orphan. Then simulate a cut/edit you’d really consider.  
**CTA:** Review top finding  
**Microcopy under list:** Wrong? Tell us — it trains what we fix next.

### P3 — On each finding (orphan / cut risk)

**Title line:** Why this fired (one sentence from engine)  
**Actions:**  
- `Useful`  
- `Wrong`  
- `Unclear`  
**After Useful:** “Simulate this?”  
**After Wrong:** “Thanks — optional: what’s wrong?” (short text)

### P4 — Before first simulate (if they only browsed)

**Headline:** Simulation is the point  
**Body:** Preview what breaks if you cut or edit a scene — before you do it in Final Draft.  
**CTA:** Simulate a cut

### P5 — After first simulate

**Headline:** Save this decision for your rewrite  
**Body:** Early builds may lose sessions on restart. Screenshot or note Scene {{ID}} + what you’d cut.  
**CTA:** Run another simulate  
**Secondary:** Send feedback (2 min)

*(When accounts exist, replace with: “Saved to your project — resume anytime.”)*

### P6 — Session expired / re-upload

**Headline:** Session expired — your file isn’t gone from your machine  
**Body:** Re-upload the same draft to continue. We’re adding saved projects next.  
**CTA:** Re-upload

### P7 — Limited structure / bad PDF parse

**Headline:** We couldn’t fully trust this layout  
**Body:** Orphans and cut risk may be unreliable. Try Fountain or a cleaner text PDF before you decide cuts.  
**CTA:** Upload Fountain  
**Secondary:** Cleanup guide

### P8 — Analysis busy (queue / 503)

**Headline:** Another script is analysing  
**Body:** This machine runs a small writer lab — try again in a minute.  
**CTA:** Retry  
*(Later: “You’re in queue — ~N min”)*

### P9 — Day 3 equivalent (return visit, no simulate yet)

**Headline:** You haven’t simulated yet  
**Body:** Browse-only rarely changes a draft. Pick one cut you’d consider and preview the blast radius.  
**CTA:** Simulate now

### P10 — Return visit after ≥1 simulate (second session)

**Headline:** Second pass?  
**Body:** Re-upload after act-break / scene-cut changes. That’s when ScriptLens usually earns its keep.  
**CTA:** Upload new draft

### P11 — Founding banner (Days 5–14, cohort only)

**Banner:** Wave {{WAVE}} founding: {{FOUNDING_PRICE}}/mo for 3 months  
**CTA:** I want founding  
**Dismiss:** Not now

### P12 — Cancel flow (when billing exists)

**Step 1:** Pause for 1 month instead of cancel?  
**Step 2:** Reason: trust / workflow / price / bugs / timing  
**Step 3:** If bugs/trust → “Which scene?”  
**Close:** “We’ll nudge at your next rewrite date” if timing

---

## 3. 30-day calendar (one cohort)

| Day | Channel | Action |
|-----|---------|--------|
| −2 | Email E0 | Invite |
| 0 | Email E1 + P1 | Kickoff |
| 0–2 | In-app P2–P5 | Drive first simulate |
| 3 | Email E2 | Personal check-in |
| 5–7 | In-app P11 | Founding banner |
| 7 | Email E3 | Close wave + founding + next rewrite date |
| 14 | Email E4 or E5 | Second pass **or** walkthrough offer |
| Rewrite date or 30 | Email E6 | Checkpoint |
| Anytime exit | Email E7 + P12 | Pause / learn reason |

**Your daily ops (15 min):** reply to every Useful/Wrong note; log bugs; don’t invite Wave N+1 until top crash is fixed.

---

## 4. Metrics to log per wave (spreadsheet is enough)

| Writer | Uploaded | Simulated | Useful≥1 | Wrong notes | Founding? | Next rewrite date | Day 14 back? | Day 30 back? | Churn reason |
|--------|----------|-----------|----------|-------------|-----------|-------------------|--------------|--------------|--------------|
| | Y/N | Y/N | Y/N | | Y/N | | Y/N | Y/N | |

**Wave health**

- Activation rate = Simulated ÷ Invited *(aim ≥ 60%)*  
- Trust signal = Useful≥1 ÷ Simulated *(aim ≥ 40%)*  
- Founding conversion = Founding ÷ Activated *(bonus)*  
- Day-30 return = back for rewrite ÷ Activated *(aim ≥ 30% early)*

If activation &lt; 40%: fix onboarding/PDF, don’t buy ads.  
If useful &lt; 25%: fix false positives before growing cohorts.

---

## 5. Merge fields cheat sheet

| Token | Example |
|-------|---------|
| `{{WAVE}}` | B |
| `{{START}}` / `{{END}}` | 10 Mar / 16 Mar |
| `{{APP_URL}}` | https://app.yoursite.com |
| `{{FEEDBACK_FORM}}` | Google Form link |
| `{{FOUNDING_PRICE}}` | $29 |
| `{{FOUNDING_DEADLINE}}` | 23 Mar |
| `{{NEXT_WAVE}}` | C |
| `{{YOUR_NAME}}` | Subhi |

---

## 6. What not to do

- Don’t email “We miss you” with no script-specific hook  
- Don’t invite the next 5 while the current 5 are still crashing  
- Don’t promise always-on multi-user until sessions persist (Postgres/Redis)  
- Don’t add five CTAs on first paint — upload → one finding → simulate
