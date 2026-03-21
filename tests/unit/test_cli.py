"""Tests for CLI commands."""

from __future__ import annotations

from click.testing import CliRunner

from ghostty_rice.cli import cli


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_list() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    # Ghostty-style names (no extension)
    assert "Catppuccin Mocha" in result.output
    assert "Rose Pine" in result.output
    assert "Cyber" in result.output
