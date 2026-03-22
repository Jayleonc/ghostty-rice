"""Tests for CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from ghostty_rice.cli import (
    _choose_font_interactively,
    _choose_profile_interactively,
    _read_switch_action,
    cli,
)
from ghostty_rice.fonts import FontPreset
from ghostty_rice.profile import Profile
from ghostty_rice.prompt import PromptPreset


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.2.0" in result.output


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


def test_read_switch_action_supports_plus() -> None:
    with patch("ghostty_rice.cli.click.getchar", return_value="+"):
        assert _read_switch_action() == "bigger"


def test_read_switch_action_supports_right_arrow_compact_sequence() -> None:
    with patch("ghostty_rice.cli.click.getchar", return_value="\x1b[C"):
        assert _read_switch_action() == "bigger"


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


def test_cli_font_command() -> None:
    runner = CliRunner()
    selected = FontPreset(
        name="JetBrains Mono",
        description="desc",
        settings={"font-family": '"JetBrains Mono"', "font-size": "13"},
    )
    with (
        patch("ghostty_rice.cli.installed_font_families", return_value={"JetBrains Mono"}),
        patch("ghostty_rice.cli.build_font_candidates", return_value=[selected]),
        patch("ghostty_rice.cli.current_font_family", return_value="Fira Code"),
        patch("ghostty_rice.cli.current_font_size", return_value=13.0),
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


def test_cli_font_passes_dynamic_candidates_to_picker() -> None:
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
        patch(
            "ghostty_rice.cli.installed_font_families",
            return_value={"JetBrains Mono", "Berkeley Mono"},
        ),
        patch("ghostty_rice.cli.build_font_candidates", return_value=[available, missing]),
        patch("ghostty_rice.cli.current_font_family", return_value="JetBrains Mono"),
        patch("ghostty_rice.cli.current_font_size", return_value=13.0),
        patch("ghostty_rice.cli._capture_config_snapshot", return_value=(True, "orig")),
        patch("ghostty_rice.cli._choose_font_interactively", return_value=available) as mock_choose,
        patch("ghostty_rice.cli.apply_font_preset"),
        patch("ghostty_rice.cli.reload_ghostty", return_value=(True, "Config reloaded.")),
    ):
        result = runner.invoke(cli, ["font"])

    assert result.exit_code == 0
    passed_presets = mock_choose.call_args.args[0]
    assert len(passed_presets) == 2
    assert passed_presets[0].name == "JetBrains Mono"


def test_choose_font_interactively_supports_resize() -> None:
    preset = FontPreset(
        name="JetBrains Mono",
        description="desc",
        settings={"font-family": '"JetBrains Mono"', "font-size": "13"},
    )
    previewed: list[str] = []

    def _preview(font_preset: FontPreset) -> tuple[bool, str]:
        previewed.append(font_preset.settings["font-size"])
        return True, "ok"

    with (
        patch("ghostty_rice.cli._read_switch_action", side_effect=["bigger", "apply"]),
        patch("ghostty_rice.cli.console.clear"),
        patch("ghostty_rice.cli._render_font_table"),
    ):
        selected = _choose_font_interactively(
            [preset],
            current_family="JetBrains Mono",
            initial_size=13.0,
            on_preview=_preview,
        )

    assert selected is not None
    assert selected.settings["font-size"] == "13.5"
    assert previewed == ["13.5"]


def test_cli_prompt_command() -> None:
    runner = CliRunner()
    selected = PromptPreset(
        name="Dev Compact",
        description="desc",
        sample="(.venv) repo »",
        script="PROMPT='test'\n",
    )

    with (
        patch("ghostty_rice.cli.zsh_available", return_value=True),
        patch("ghostty_rice.cli.detected_shell_name", return_value="zsh"),
        patch("ghostty_rice.cli.list_prompt_presets", return_value=[selected]),
        patch("ghostty_rice.cli.current_prompt_preset_name", return_value=None),
        patch("ghostty_rice.cli._choose_prompt_interactively", return_value=selected),
        patch("ghostty_rice.cli.has_prompt_bootstrap", return_value=False),
        patch("ghostty_rice.cli.prompt_runtime_active", return_value=False),
        patch(
            "ghostty_rice.cli.apply_prompt_preset",
            return_value=Path("/tmp/prompt.zsh"),
        ) as mock_apply,
    ):
        result = runner.invoke(cli, ["prompt"])

    assert result.exit_code == 0
    mock_apply.assert_called_once_with(selected)
    assert "Prompt preset:" in result.output
    assert "Dev Compact" in result.output
    assert "rice prompt --install" in result.output


def test_cli_prompt_command_install_mode() -> None:
    runner = CliRunner()
    selected = PromptPreset(
        name="Minimal Arrow",
        description="desc",
        sample="repo ›",
        script="PROMPT='test'\n",
    )

    with (
        patch("ghostty_rice.cli.zsh_available", return_value=True),
        patch("ghostty_rice.cli.detected_shell_name", return_value="zsh"),
        patch("ghostty_rice.cli.list_prompt_presets", return_value=[selected]),
        patch("ghostty_rice.cli.current_prompt_preset_name", return_value=None),
        patch("ghostty_rice.cli._choose_prompt_interactively", return_value=selected),
        patch(
            "ghostty_rice.cli.apply_prompt_preset",
            return_value=Path("/tmp/prompt.zsh"),
        ),
        patch("ghostty_rice.cli.has_prompt_bootstrap", return_value=False),
        patch("ghostty_rice.cli.prompt_runtime_active", return_value=False),
        patch("ghostty_rice.cli.ensure_prompt_bootstrap", return_value=True) as mock_install,
    ):
        result = runner.invoke(cli, ["prompt", "--install"])

    assert result.exit_code == 0
    mock_install.assert_called_once()
    assert "Installed bootstrap into ~/.zshrc." in result.output


def test_cli_prompt_command_runtime_active_applies_immediately() -> None:
    runner = CliRunner()
    selected = PromptPreset(
        name="Context Rich",
        description="desc",
        sample="[.venv] me@host repo #",
        script="PROMPT='test'\n",
    )
    with (
        patch("ghostty_rice.cli.zsh_available", return_value=True),
        patch("ghostty_rice.cli.detected_shell_name", return_value="zsh"),
        patch("ghostty_rice.cli.list_prompt_presets", return_value=[selected]),
        patch("ghostty_rice.cli.current_prompt_preset_name", return_value=None),
        patch("ghostty_rice.cli._choose_prompt_interactively", return_value=selected),
        patch("ghostty_rice.cli.has_prompt_bootstrap", return_value=True),
        patch("ghostty_rice.cli.prompt_runtime_active", return_value=True),
        patch(
            "ghostty_rice.cli.apply_prompt_preset",
            return_value=Path("/tmp/prompt.zsh"),
        ),
    ):
        result = runner.invoke(cli, ["prompt"])

    assert result.exit_code == 0
    assert "Applied immediately in current Ghostty zsh session." in result.output


def test_cli_switch_uses_full_control_mode_by_default() -> None:
    runner = CliRunner()
    with patch("ghostty_rice.cli._run_theme_studio") as mock_run:
        result = runner.invoke(cli, ["switch"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(False)


def test_cli_prompt_command_requires_zsh() -> None:
    runner = CliRunner()

    with (
        patch("ghostty_rice.cli.zsh_available", return_value=False),
        patch("ghostty_rice.cli.detected_shell_name", return_value="bash"),
    ):
        result = runner.invoke(cli, ["prompt"])

    assert result.exit_code == 1
    assert "require zsh" in result.output.lower()
