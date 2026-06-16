"""Convert a Markdown document to a styled, paginated PDF using PyMuPDF."""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz
import markdown

PAGE_CSS = """
* { font-family: sans-serif; }
body { font-size: 10pt; color: #1a1a1a; line-height: 1.45; }
h1 { font-size: 20pt; color: #11324d; margin: 0 0 6pt 0; }
h2 { font-size: 14pt; color: #11324d; margin: 14pt 0 4pt 0; }
h3 { font-size: 11.5pt; color: #1f4e79; margin: 10pt 0 3pt 0; }
p { margin: 4pt 0; }
a { color: #1f4e79; }
code { font-family: monospace; font-size: 9pt; background: #f0f0f0; }
pre { font-family: monospace; font-size: 8.5pt; background: #f4f4f4;
      padding: 6pt; margin: 5pt 0; }
table { border: 1px solid #b0b0b0; width: 100%; margin: 6pt 0; }
th { background: #11324d; color: #ffffff; text-align: left; padding: 4pt;
     font-size: 9pt; }
td { border: 1px solid #cccccc; padding: 4pt; font-size: 9pt;
     vertical-align: top; }
hr { border: none; border-top: 1px solid #cccccc; margin: 10pt 0; }
ul, ol { margin: 4pt 0 4pt 16pt; }
li { margin: 2pt 0; }
strong { color: #11324d; }
"""


def markdown_to_html(markdown_text: str) -> str:
    """Render Markdown source text to an HTML fragment.

    Args:
        markdown_text: Raw Markdown document text.

    Returns:
        HTML string with tables and fenced code blocks expanded.
    """
    return markdown.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )


def html_to_pdf(html_body: str, output_path: Path, css: str = PAGE_CSS) -> Path:
    """Render an HTML fragment to a paginated A4 PDF via PyMuPDF Story.

    Args:
        html_body: HTML fragment to render.
        output_path: Destination PDF path.
        css: User CSS applied to the story.

    Returns:
        The resolved path to the written PDF.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    story = fitz.Story(html=html_body, user_css=css)
    writer = fitz.DocumentWriter(str(output_path))
    media_box = fitz.paper_rect("a4")
    content_box = media_box + (50, 50, -50, -50)

    more = 1
    while more:
        device = writer.begin_page(media_box)
        more, _ = story.place(content_box)
        story.draw(device)
        writer.end_page()

    writer.close()
    return output_path.resolve()


def convert_markdown_file(input_path: Path, output_path: Path) -> Path:
    """Convert a Markdown file on disk to a styled PDF.

    Args:
        input_path: Path to the source ``.md`` file.
        output_path: Path to the destination ``.pdf`` file.

    Returns:
        The resolved path to the written PDF.

    Raises:
        FileNotFoundError: If the input Markdown file does not exist.
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Markdown file not found: {input_path}")
    markdown_text = input_path.read_text(encoding="utf-8")
    html_body = markdown_to_html(markdown_text)
    return html_to_pdf(html_body, output_path)


def main() -> None:
    """CLI entry point: convert a Markdown file to a PDF."""
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF.")
    parser.add_argument("input", type=Path, help="Source .md file.")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="Destination .pdf file (defaults to input name with .pdf).",
    )
    args = parser.parse_args()
    output_path = args.output or args.input.with_suffix(".pdf")
    written = convert_markdown_file(args.input, output_path)
    print(f"Wrote PDF: {written}")


if __name__ == "__main__":
    main()
