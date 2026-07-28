"""Render the ScriptLens ground-truth annotation guideline to a styled PDF.

Reuses the Markdown-to-PDF pipeline in ``scripts/md_to_pdf.py`` so the PDF
matches the house style used across the ``docs`` folder.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.md_to_pdf import html_to_pdf, markdown_to_html  # noqa: E402

OUTPUT_PATH = _REPO_ROOT / "docs" / "SCRIPTLENS_ANNOTATION_GUIDELINE.pdf"

DOCUMENT_MARKDOWN = r"""
# ScriptLens — Ground-Truth Annotation Guideline

*How to label, and how to validate, orphan scenes and simulate cut / edit impact
for the v3 structure corpus*

## 1. Why this document exists

ScriptLens is graded against a "ground truth" — a set of screenplays paired with
the *correct answers* for what the engine should find. But there is no oracle: an
"orphan scene" is not a physical fact you can measure, it is a **human judgment
against a definition**. This is true of every serious labeled corpus (linguistic
treebanks, medical imaging, sentiment). They do not solve it by finding truth;
they solve it by making labels **reproducible and traceable**.

So the goal of annotation is not "is this label cosmically correct?" It is:

> Would any trained reader, following this rulebook, produce the same label — and
> can they point to the exact text that justifies it?

If yes, the label is defensible. If it rests on "I just feel it's disconnected,"
it is opinion and does not belong in gold data.

## 2. The four validation levers

Every label in the corpus is made trustworthy by four mechanisms working
together. The rest of this guide operationalises them.

| Lever | What it does |
| --- | --- |
| 1. Operational definition | Turns a fuzzy judgment into a checkable rule (Section 4). |
| 2. Multiple annotators + agreement | Independent labels, measured with kappa, adjudicated (Section 7). |
| 3. Traceable anchors | Every label cites the concrete text that justifies it (Section 5). |
| 4. Natural experiments | Deleted scenes and draft diffs cross-check labels (Section 8). |

## 3. The objectivity hierarchy

Not all labels are equally hard to validate. Weight annotation effort
accordingly.

| Label | Objectivity | Consequence |
| --- | --- | --- |
| Simulate delete / edit ripple | High — mechanical dependency tracing | Achievable high agreement; strongest gold data |
| Hard orphan (no C/L/P/E links) | Medium-high — rule-checkable | One annotator + adjudication often enough |
| Soft / semantic orphan ("earns its place") | Low — interpretive | Requires 2+ annotators; may never reach gold |

Headline features (simulate delete and edit) are the *most* validatable, because
they are claims about concrete dependencies you can trace to specific lines.

## 4. Operational definitions

### 4.1 Orphan scene

A scene is an **orphan** when it has no structural link to any other scene in the
script, on all four linkage channels used by the OSD weighted graph:

- **C — Character:** shares no named character with any other scene.
- **L — Location:** shares no location / setting with any other scene.
- **P — Prop / plot object:** shares no tracked object, document, or plot device.
- **E — Semantic:** has no significant semantic-embedding link (E = 0) to the
  rest of the graph.

A scene is an orphan **only if all four channels are empty** *and* it is not on
the exemption list.

**Orphan sub-types:**

- **Hard orphan:** zero links on C, L, P, and E. Unambiguous.
- **Loose / soft orphan:** technically linked but only weakly (for example a
  single incidental shared extra), such that removing the scene would not affect
  any downstream payoff. Interpretive — requires a second annotator.

**Exemptions (never label these as orphans):** opening prologue / cold open,
collapsed montage block, flashback that shares a main-plot character, dream or
fantasy insert, framing device, and deliberate thematic interlude. If a scene
looks disconnected but serves one of these functions, it is **not** an orphan;
record the exemption reason instead.

### 4.2 Simulate delete (cut impact)

Removing scene *X* **impacts** scene *Y* when *Y* depends on something that *X*
uniquely establishes — an object, a piece of information, a character
introduction, or a causal precondition — such that cutting *X* leaves *Y*
unsupported.

- **Impacted set:** all scenes *Y* that lose required support when *X* is cut.
- **Risk tier:** the headline severity the engine reports (`low`, `medium`,
  `high`). Label using a *set* of acceptable tiers (`expect_risk_in`) rather than
  a single value, because tier boundaries are inherently fuzzy.
- A cut that impacts **nothing** is itself a valid, important label (it exercises
  the false-positive guard).

### 4.3 Simulate edit (edge delta)

Editing scene *X* (replacing its text) **removes an edge** when the edit strips a
referent (object, character, or information) that a dependency was built on.

- **Edges removed (minimum):** the floor number of dependency edges that must
  disappear (`expect_edges_removed_min`).
- **Orphan delta:** the orphan count before vs. after the edit — an edit can
  *create* an orphan by severing a scene's last link.
- **Risk tier:** as in 4.2, an acceptable set.

## 5. Required anchors (what makes a label "gold")

**No anchor, not gold.** Every label must carry the concrete evidence a reviewer
can check. A label without a traceable anchor is downgraded to silver (Section 6).

| Label type | Required anchor fields |
| --- | --- |
| Orphan (hard) | The four channels checked, each recorded empty ("no shared character / location / object / semantic link found") |
| Orphan (exempt) | The exemption category and the scene role that justifies it |
| Simulate delete | The specific setup->payoff thread: what *X* establishes and where each impacted *Y* consumes it, with scene / line references |
| Simulate edit | The referent removed by the edit and the specific edges tied to it |

Example (delete anchor): *"Cutting scene 1 impacts scenes 3, 4, 5 — scene 1
establishes the STEEL BRIEFCASE (line 4); scene 3 tracks it to the docks, scene 4
opens it, scene 5 is the payoff. Thread: briefcase."*

## 6. Gold vs. silver data

- **Gold:** labelled by two or more annotators, adjudicated, agreement reported,
  every label anchored. Use for published recall / false-positive metrics. Small
  and expensive.
- **Silver:** single annotator, heuristic, or natural-experiment derived. Use for
  development and iteration, never for headline metrics.

The **original writer's labels are silver, not gold** — they know intent but are
biased toward their own script. Treat writer labels as a signal and confirm with
independent readers.

## 7. Annotation workflow

1. **Read the rulebook.** Every annotator works from Section 4 definitions.
2. **Label independently.** Two or three trained, screenplay-literate annotators
   (story analysts, script readers, story editors) label the same script without
   conferring.
3. **Measure agreement.** Compute inter-annotator agreement (Cohen's kappa for
   two annotators, Fleiss' kappa for three or more). Target **kappa >= 0.7**. Low
   agreement means the *definition* is too vague — fix Section 4, do not just
   overrule people.
4. **Adjudicate.** A senior adjudicator resolves every disagreement and records
   the deciding rationale.
5. **Attach anchors.** Confirm each surviving label carries its required anchor
   (Section 5). Strip or downgrade any that do not.

## 8. Natural experiments (cross-checks that are close to an oracle)

For produced scripts, use empirical signals that do not depend on one reader's
taste:

- **Deleted scenes / DVD extras:** a scene cut from the release while the film
  still worked is strong evidence of a low-dependency (orphan-like) scene —
  professionals ran the "simulate delete" and shipped the result.
- **Draft-to-shooting-script diffs:** scenes that vanished between drafts are
  candidate orphans; scenes that survived every draft are load-bearing.
- **The released cut itself:** a dependency graph validated by professional
  editors — the finished film is coherent, so its kept scenes are largely
  non-orphan by professional consensus.

Use these to triangulate, especially for the low-objectivity soft-orphan calls.

## 9. How a "clean" produced script is actually used

You do **not** know a produced Hollywood script is orphan-free a priori — that is
a *weak prior* for structural soundness, not a guarantee. Franchise seed scenes,
cold opens, and studio-mandated additions are real "looks like an orphan but
isn't" cases. Therefore:

> Clean produced scripts measure **false positives**, and a human validates each
> flag. Run the engine; every scene it flags is a *candidate* false positive; an
> annotator rules "real disconnection" vs. "legit narrative device" using the
> rulebook and natural-experiment evidence. The adjudicated residual is the
> false-positive rate.

You never claim the script is clean — you *measure* how often the engine cries
wolf and have humans confirm.

## 10. Label record — required schema

Each labelled script produces a YAML answer key. Every entry carries its anchor.

```yaml
script_id: example_01
filename: example_01.fountain
annotators: [reader_a, reader_b]
adjudicator: editor_c
agreement_kappa: 0.82

expected_orphans:
  - scene_id: scene_002
    type: hard
    anchor: "No shared character, location, object, or semantic link with any
      other scene."

exemptions:
  - scene_id: scene_001
    reason: prologue
    anchor: "Cold open; standard opening device, exempt from orphan flags."

expected_simulate_delete:
  - scene_id: scene_001
    expect_impacted: [scene_003, scene_004, scene_005]
    expect_risk_in: [medium, high]
    anchor: "Scene 1 establishes the STEEL BRIEFCASE (line 4); consumed in 3/4/5.
      Thread: briefcase."

expected_simulate_edit:
  - scene_id: scene_001
    modified_text: |
      INT. WAREHOUSE - NIGHT
      GINA pries open an EMPTY CRATE. Nothing inside.
    expect_edges_removed_min: 1
    expect_risk_in: [medium, high]
    orphan_delta: {before: 1, after: 1}
    anchor: "Edit removes the briefcase referent; briefcase-thread edges drop."

notes: >
  Free text: formatting caveats, expected borderline calls, natural-experiment
  evidence (deleted-scene lists, draft diffs).
```

## 11. Quick checklist for an annotator

- [ ] I labelled against the Section 4 definitions, not my gut.
- [ ] For each orphan, I checked all four channels (C, L, P, E).
- [ ] I recorded exemptions (prologue, montage, flashback, dream, framing) rather
      than mislabelling them as orphans.
- [ ] Every delete / edit label names the concrete thread and cites scene / line
      references.
- [ ] No label ships without its anchor.
- [ ] Disagreements went to the adjudicator; kappa is recorded.
"""


def build_pdf() -> Path:
    """Render the annotation-guideline Markdown to a styled PDF.

    Returns:
        The resolved path to the written PDF.
    """
    html_body = markdown_to_html(DOCUMENT_MARKDOWN)
    return html_to_pdf(html_body, OUTPUT_PATH)


def main() -> None:
    """Write the annotation-guideline PDF to the docs folder."""
    written = build_pdf()
    print(f"Wrote PDF: {written}")


if __name__ == "__main__":
    main()
