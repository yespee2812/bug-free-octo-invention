"""Build the screenwriter error-injection cheat sheet as a PDF.

The cheat sheet lists the continuity-error categories ScriptLens currently
detects, so writers inject only errors the engine is built to catch. It is
regenerated from the data below; timeline/date slips are intentionally absent
because that detector is disabled, and world-rule violations are now a fully
supported category.
"""

from __future__ import annotations

from pathlib import Path

import fitz

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = (
    _REPO_ROOT / "docs" / "writer_materials" / "SCREENWRITER_ERROR_CHEAT_SHEET.pdf"
)
TOP_LEVEL_OUTPUT_PATH = (
    _REPO_ROOT / "docs" / "SCREENWRITER_ERROR_CHEAT_SHEET.pdf"
)

# (number, plant-this, example) for each detectable error category. Order is
# grouped: characters, props, injuries, relationships, place, world rules.
ERROR_CATEGORIES: tuple[tuple[str, str, str], ...] = (
    ("1", "Dead &rarr; alive", "Killed off, later walks in with no valid reveal"),
    ("2", "Role clash", "Surgeon in Act 1, lawyer in Act 2 &mdash; same person"),
    ("3", "Prop &mdash; wrong owner", "Elena's ledger, then Marcus has it, no transfer scene"),
    ("4", "Prop &mdash; destroyed but back", "Burns the letter, then reads the same letter"),
    ("5", "Prop &mdash; lost but back", "Drops the key, then has the key again, no recovery"),
    ("6", "Injury &mdash; wrong side", "Shot in the left arm, later wound on the right arm"),
    ("7", "Injury &mdash; vanishes", "Unconscious, then running the same day, no hospital"),
    ("8", "Relationship &mdash; impossible", "Siblings, later married &mdash; same two people"),
    ("9", "Relationship &mdash; parent flip", "He is her father, later she is his mother"),
    ("10", "Location clash", "Same place: 'abandoned for years' vs 'busy all day'"),
    ("11", "World rule broken", "'The machine cannot reach the future', later it does"),
)

_CSS = """
* { font-family: Helvetica, Arial, sans-serif; }
h1 { font-size: 18pt; color: #11324d; margin: 0 0 2pt 0; }
.tagline { font-size: 11pt; color: #11324d; font-weight: bold; margin: 0 0 8pt 0; }
h2 { font-size: 12pt; color: #11324d; margin: 12pt 0 4pt 0;
     border-bottom: 1px solid #c9d4df; padding-bottom: 2pt; }
p, li { font-size: 9.5pt; color: #1c1c1c; line-height: 1.35; }
ol, ul { margin: 2pt 0 2pt 0; padding-left: 16pt; }
table { width: 100%; border-collapse: collapse; margin-top: 4pt; }
th { background-color: #dbe4ee; color: #11324d; font-size: 9pt;
     text-align: left; padding: 4pt 6pt; border-bottom: 2px solid #11324d; }
td { font-size: 9pt; padding: 4pt 6pt; border-bottom: 1px solid #dde4ea;
     vertical-align: top; }
.num { width: 6%; text-align: center; color: #11324d; font-weight: bold; }
.plant { width: 32%; font-weight: bold; }
.note { font-size: 9pt; color: #5a4b00; background: #fff7d6;
        border: 1px solid #e6d27a; padding: 6pt 8pt; margin-top: 4pt; }
.dont { font-size: 9pt; color: #7a1f1f; }
code { font-family: 'Courier New', monospace; font-size: 8.5pt; }
.log { font-family: 'Courier New', monospace; font-size: 8.5pt;
       background: #f3f6f9; border: 1px solid #dde4ea; padding: 6pt 8pt;
       white-space: pre-wrap; color: #1c1c1c; }
"""


def _category_rows() -> str:
    """Return the HTML table rows for the detectable error categories."""
    cells = []
    for number, plant, example in ERROR_CATEGORIES:
        cells.append(
            f'<tr><td class="num">{number}</td>'
            f'<td class="plant">{plant}</td>'
            f"<td>{example}</td></tr>"
        )
    return "".join(cells)


def _build_html() -> str:
    """Return the full cheat-sheet HTML document."""
    rows = _category_rows()
    return f"""
<h1>ScriptLens &mdash; Error Injection Cheat Sheet</h1>
<p class="tagline">Write normally. Plant mistakes. Log everything.</p>

<h2>What to send back</h2>
<ol>
  <li><b>Script</b> &mdash; .fountain, .pdf, or .txt (standard screenplay format)</li>
  <li><b>Error Log</b> &mdash; one file per script (template provided)</li>
</ol>

<h2>11 mistake types (pick what fits the story)</h2>
<table>
  <tr><th>#</th><th>Plant this mistake</th><th>Example</th></tr>
  {rows}
</table>

<div class="note"><b>World rules (new):</b> state the rule plainly as
"[Thing] cannot [do X]" (a concrete subject &mdash; a machine, a serum, a
person), then later show it doing X with no explanation. Conditional rules
("can only when&hellip;") and blanket rules ("no one can&hellip;") are not
auto-detected, so avoid relying on those.</div>

<div class="note"><b>Note:</b> calendar / day-of-week timeline slips
("Monday&hellip;yesterday was Friday") are <b>no longer auto-detected</b> &mdash;
please do not plant those as test errors.</div>

<h2>Before you submit</h2>
<ul>
  <li>Reads like a <b>production draft</b>, not a test file</li>
  <li>Every planted mistake is in the <b>Error Log</b></li>
  <li><b>Establishing scene</b> + <b>breaking scene</b> filled in for each error</li>
  <li>Errors <b>spread</b> across the script (not all in one scene)</li>
  <li>Scene index lists <b>every</b> scene heading</li>
  <li>No labels in the script ("CONTINUITY ERROR HERE")</li>
</ul>

<h2>Do NOT log as errors</h2>
<p class="dont">Enemies &rarr; friends &middot; breakups &middot; divorce &middot;
explained fake deaths &middot; flashbacks &middot; dreams &middot;
on-page handoffs (gives / hands / steals / finds) &middot; calendar slips</p>

<h2>Error Log (minimum per entry)</h2>
<div class="log">error_number: 1
category: "Prop &mdash; wrong owner"
establishing_scene: 4
contradicting_scene: 7
characters_involved: ["ELENA", "MARCUS"]
objects_involved: ["silver key"]
establishing_moment: "ELENA picks up the silver key."
contradicting_moment: "MARCUS has the silver key."
how_a_reader_notices: "No scene shows the key changing hands."
writer_intent: deliberate</div>

<p style="font-size:8.5pt;color:#5a6672;margin-top:8pt;">
Full guide: SCREENWRITER_ERROR_INJECTION_GUIDE.md &middot;
Log template: ERROR_INJECTION_LOG_TEMPLATE.yaml</p>
"""


def build_cheat_sheet_pdf(output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    """Render the error-injection cheat sheet to a PDF file.

    Args:
        output_path: Destination path for the generated ``.pdf``.

    Returns:
        Resolved path to the written PDF.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    story = fitz.Story(html=_build_html(), user_css=_CSS)
    writer = fitz.DocumentWriter(str(output_path))
    mediabox = fitz.paper_rect("letter")
    content_rect = mediabox + (54, 54, -54, -54)

    more = 1
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(content_rect)
        story.draw(device)
        writer.end_page()
    writer.close()
    return output_path.resolve()


def main() -> None:
    """CLI entry point: write the cheat sheet to both writer and docs paths."""
    primary = build_cheat_sheet_pdf(DEFAULT_OUTPUT_PATH)
    mirror = build_cheat_sheet_pdf(TOP_LEVEL_OUTPUT_PATH)
    print(f"Wrote cheat sheet: {primary}")
    print(f"Wrote cheat sheet: {mirror}")


if __name__ == "__main__":
    main()
