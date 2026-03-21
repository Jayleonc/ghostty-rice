"""Tests for CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from ghostty_rice.cli import _choose_profile_interactively, _read_switch_action, cli
from ghostty_rice.fonts import FontPreset
from ghostty_rice.profile import Profile


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.1" in result.output


def test_cli_list() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    # Ghostty-style names (no extension)
    assert "Catppuccin Mocha" in result.output
    assert "One Dark Pro" in result.output
    assert "Cyber" in result.output


def test_cli_doctor() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0
    assert "ghostty-rice doctor" in result.output
    assert "Profiles available" in result.output


def test_read_switch_action_supports_arrow_up() -> None:
    with patch(
        "ghostty_rice.cli.click.getchar",
        side_effect=["\x1b", "[", "A"],
    ):
        assert _read_switch_action() == "up"


def test_read_switch_action_supports_compact_arrow_sequence() -> None:
    with patch("ghostty_rice.cli.click.getchar", return_value="\x1b[A"):
        assert _read_switch_action() == "up"


def test_choose_profile_interactively_applies_selected_profile() -> None:
    profiles = [
        Profile(
            name="Rose Pine",
            description="desc1",
            author="a",
            source="builtin",
            path=Path("rose"),
        ),
        Profile(
            name="Tokyo Night",
            description="desc2",
            author="a",
            source="builtin",
            path=Path("tokyo"),
        ),
    ]
    previewed: list[str] = []

    def _preview(profile: Profile) -> tuple[bool, str]:
        previewed.append(profile.name)
        return True, "ok"

    with (
        patch("ghostty_rice.cli._read_switch_action", side_effect=["down", "apply"]),
        patch("ghostty_rice.cli.console.clear"),
        patch("ghostty_rice.cli._render_switch_table"),
    ):
        selected = _choose_profile_interactively(
            profiles,
            current_name="Rose Pine",
            on_preview=_preview,
        )
    assert selected == profiles[1]
    assert previewed == ["Tokyo Night"]


def test_cli_switch_command() -> None:
    runner = CliRunner()
    current = Profile(
        name="Rose Pine",
        description="desc",
        author="a",
        source="builtin",
        path=Path("rose"),
    )
    selected = Profile(
        name="Cyber",
        description="desc",
        author="a",
        source="builtin",
        path=Path("cyber"),
    )
    with (
        patch("ghostty_rice.cli.list_profiles", return_value=[current, selected]),
        patch("ghostty_rice.cli.get_current_profile", return_value="Rose Pine"),
        patch("ghostty_rice.cli.get_profile", return_value=current),
        patch("ghostty_rice.cli._capture_config_snapshot", return_value=(True, "orig")),
        patch("ghostty_rice.cli._choose_profile_interactively", return_value=selected),
        patch("ghostty_rice.cli.apply_profile") as mock_apply,
        patch("ghostty_rice.cli.reload_ghostty", return_value=(True, "Config reloaded.")),
    ):
        result = runner.invoke(cli, ["switch"])

    assert result.exit_code == 0
    mock_apply.assert_called_once_with(selected)
    assert "Switched to:" in result.output
    assert "Cyber" in result.output
    assert "Config reloaded." in result.output


def test_cli_switch_cancel_reverts_previewed_profile() -> None:
    runner = CliRunner()
    current = Profile(
        name="Rose Pine",
        description="desc",
        author="a",
        source="builtin",
        path=Path("rose"),
    )
    preview = Profile(
        name="Tokyo Night",
        description="desc",
        author="a",
        source="builtin",
        path=Path("tokyo"),
    )

    def _choose_side_effect(
        profiles: list[Profile],
        current_name: str | None,
        on_preview,
    ) -> None:
        assert current_name == "Rose Pine"
        assert len(profiles) == 2
        on_preview(preview)
        return None

    with (
        patch("ghostty_rice.cli.list_profiles", return_value=[current, preview]),
        patch("ghostty_rice.cli.get_current_profile", return_value="Rose Pine"),
        patch("ghostty_rice.cli.get_profile", return_value=current),
        patch("ghostty_rice.cli._capture_config_snapshot", return_value=(True, "orig")),
        patch("ghostty_rice.cli._restore_config_snapshot") as mock_restore,
        patch("ghostty_rice.cli._choose_profile_interactively", side_effect=_choose_side_effect),
        patch("ghostty_rice.cli.apply_profile") as mock_apply,
        patch("ghostty_rice.cli.reload_ghostty", return_value=(True, "Config reloaded.")),
    ):
        result = runner.invoke(cli, ["switch"])

    assert result.exit_code == 0
    assert mock_apply.call_count == 1
    assert mock_apply.call_args_list[0].args[0] == preview
    mock_restore.assert_called_once_with(True, "orig")
    assert "Cancelled." in result.output
    assert "Restored previous config." in result.output


def test_cli_font_command() -> None:
    runner = CliRunner()
    selected = FontPreset(
        name="JetBrains Mono",
        description="desc",
        settings={"font-family": '"JetBrains Mono"', "font-size": "13"},
    )
    with (
        patch("ghostty_rice.cli.list_font_presets", return_value=[selected]),
        patch("ghostty_rice.cli.installed_font_families", return_value={"JetBrains Mono"}),
        patch("ghostty_rice.cli.current_font_family", return_value="Fira Code"),
        patch("ghostty_rice.cli._capture_config_snapshot", return_value=(True, "orig")),
        patch("ghostty_rice.cli._choose_font_interactively", return_value=selected),
        patch("ghostty_rice.cli.apply_font_preset") as mock_apply,
        patch("ghostty_rice.cli.reload_ghostty", return_value=(True, "Config reloaded.")),
    ):
        result = runner.invoke(cli, ["font"])

    assert result.exit_code == 0
    mock_apply.assert_called_once_with(selected)
    assert "Font preset:" in result.output
    assert "JetBrains Mono" in result.output
    assert "Config reloaded." in result.output


def test_cli_font_filters_to_installed_presets() -> None:
    runner = CliRunner()
    available = FontPreset(
        name="JetBrains Mono",
        description="desc",
        settings={"font-family": '"JetBrains Mono"', "font-size": "13"},
    )
    missing = FontPreset(
        name="Berkeley Mono",
        description="desc",
        settings={"font-family": '"Berkeley Mono"', "font-size": "13"},
    )
    with (
        patch("ghostty_rice.cli.list_font_presets", return_value=[available, missing]),
        patch("ghostty_rice.cli.installed_font_families", return_value={"JetBrains Mono"}),
        patch("ghostty_rice.cli.current_font_family", return_value="JetBrains Mono"),
        patch("ghostty_rice.cli._capture_config_snapshot", return_value=(True, "orig")),
        patch("ghostty_rice.cli._choose_font_interactively", return_value=available) as mock_choose,
        patch("ghostty_rice.cli.apply_font_preset"),
        patch("ghostty_rice.cli.reload_ghostty", return_value=(True, "Config reloaded.")),
    ):
        result = runner.invoke(cli, ["font"])

    assert result.exit_code == 0
    passed_presets = mock_choose.call_args.args[0]
    assert len(passed_presets) == 1
    assert passed_presets[0].name == "JetBrains Mono"
