"""CLI entry point for ScriptLens screenplay analysis (PDF or text)."""

from pathlib import Path

import click

from scriptlens_analyser import analyze_from_path, pretty_print_results


@click.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--save-extracted",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Save normalized text extracted from a PDF to this .txt/.fountain path.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Print raw results dict instead of the screenwriter report.",
)
def main(
    input_path: Path,
    save_extracted: Path | None,
    output_json: bool,
) -> None:
    """Analyze a screenplay PDF or Fountain/text file."""
    include_text = save_extracted is not None
    results = analyze_from_path(input_path, include_extracted_text=include_text)

    if save_extracted is not None:
        extracted = results.get("input", {}).get("extracted_text", "")
        if not extracted:
            raise click.ClickException(
                "--save-extracted only applies to PDF inputs."
            )
        save_extracted.write_text(extracted, encoding="utf-8")
        click.echo(f"Saved extracted screenplay text to {save_extracted}")

    if output_json:
        import json

        click.echo(json.dumps(results, indent=2))
        return

    click.echo(f"Analyzing: {results['input']['filename']} ({results['input']['format']})")
    pretty_print_results(results)


if __name__ == "__main__":
    main()
