"""Tests for font presets and helpers."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from ghostty_rice.fonts import (
    apply_font_preset,
    current_font_family,
    get_font_preset,
    installed_font_families,
    list_font_presets,
)


def test_list_font_presets_contains_defaults() -> None:
    presets = list_font_presets()
    assert len(presets) >= 3
    assert any(p.name == "JetBrains Mono" for p in presets)


def test_get_font_preset_by_name() -> None:
    preset = get_font_preset("JetBrains Mono")
    assert preset is not None
    assert preset.settings["font-family"] == '"JetBrains Mono"'


def test_current_font_family_parses_quoted_value(tmp_path) -> None:
    config = tmp_path / "config"
    config.write_text('font-family = "Maple Mono"\nfont-size = 13\n')

    with patch("ghostty_rice.fonts.ghostty_config_file", return_value=config):
        assert current_font_family() == "Maple Mono"


def test_apply_font_preset_updates_base_settings() -> None:
    preset = get_font_preset("JetBrains Mono")
    assert preset is not None

    with patch("ghostty_rice.fonts.update_base_settings") as mock_update:
        apply_font_preset(preset)

    mock_update.assert_called_once_with(preset.settings)


def test_installed_font_families_parses_ghostty_output() -> None:
    output = (
        "error: SentryInitFailed\n"
        "JetBrains Mono\n"
        "  JetBrains Mono Regular\n"
        "\n"
        "Menlo\n"
        "  Menlo Regular\n"
    )
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=output, stderr="")

    with (
        patch("ghostty_rice.fonts._ghostty_binary", return_value="/tmp/ghostty"),
        patch("ghostty_rice.fonts.subprocess.run", return_value=completed),
    ):
        families = installed_font_families()

    assert families == {"JetBrains Mono", "Menlo"}
