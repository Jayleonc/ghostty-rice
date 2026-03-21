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
    assert "catppuccin-mocha" in result.output
    assert "rosepine" in result.output
    assert "cyber" in result.output
