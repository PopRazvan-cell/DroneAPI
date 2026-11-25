"""CLI smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agridrone.cli import app

runner = CliRunner()


def test_help_lists_required_subcommands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0, result.output
    for command in ("mock", "analyze", "mission", "openapi", "db"):
        assert command in result.output


def test_openapi_command_writes_and_checks(tmp_path: Path) -> None:
    out = tmp_path / "openapi" / "openapi.json"

    write_result = runner.invoke(app, ["openapi", "--out", str(out)])
    assert write_result.exit_code == 0, write_result.output
    assert out.is_file()
    assert out.read_text(encoding="utf-8").endswith("\n")

    specification = json.loads(out.read_text(encoding="utf-8"))
    assert "/api/v1/healthz" in specification["paths"]
    assert "/api/v1/meta/classes" in specification["paths"]

    check_result = runner.invoke(app, ["openapi", "--check", "--out", str(out)])
    assert check_result.exit_code == 0, check_result.output


def test_openapi_check_detects_drift(tmp_path: Path) -> None:
    out = tmp_path / "openapi.json"
    out.write_text("{}\n", encoding="utf-8")

    result = runner.invoke(app, ["openapi", "--check", "--out", str(out)])

    assert result.exit_code == 1
    assert "out of date" in result.output


def test_openapi_check_detects_missing_file(tmp_path: Path) -> None:
    result = runner.invoke(app, ["openapi", "--check", "--out", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "missing" in result.output
