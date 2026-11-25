"""Command line interface: ``agridrone ...``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

DEFAULT_OPENAPI_PATH = Path("openapi/openapi.json")

app = typer.Typer(
    name="agridrone",
    help="AgriDrone API command line interface.",
    no_args_is_help=True,
    add_completion=False,
)

mock_app = typer.Typer(help="Generate or download mock/public datasets (step 02).", no_args_is_help=True)
analyze_app = typer.Typer(help="Run water/gaps analyses (steps 07–08).", no_args_is_help=True)
mission_app = typer.Typer(help="Plan and export missions (step 14).", no_args_is_help=True)
db_app = typer.Typer(help="Database migrations and seed data (step 03).", no_args_is_help=True)

app.add_typer(mock_app, name="mock")
app.add_typer(analyze_app, name="analyze")
app.add_typer(mission_app, name="mission")
app.add_typer(db_app, name="db")


def _render_openapi() -> str:
    from agridrone.api.main import create_app
    from agridrone.core.config import get_settings

    specification = create_app(get_settings()).openapi()
    return json.dumps(specification, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


@app.command("openapi")
def openapi_command(
    out: Annotated[
        Path,
        typer.Option("--out", help="Output path for the generated OpenAPI document."),
    ] = DEFAULT_OPENAPI_PATH,
    check: Annotated[
        bool,
        typer.Option("--check", help="Only verify that the committed document is up to date."),
    ] = False,
) -> None:
    """Write ``openapi/openapi.json``, the contract with agridrone-web."""
    payload = _render_openapi()

    if check:
        try:
            current = out.read_text(encoding="utf-8")
        except FileNotFoundError:
            typer.echo(f"OpenAPI document is missing: {out}", err=True)
            raise typer.Exit(code=1) from None
        if current != payload:
            typer.echo(f"OpenAPI document is out of date: {out}", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"OpenAPI document is up to date: {out}")
        return

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(payload, encoding="utf-8")
    typer.echo(f"Wrote {out}")
