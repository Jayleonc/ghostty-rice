"""Tests for profile loading and application."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from ghostty_rice.paths import bundled_presets_dir
from ghostty_rice.profile import _extract_base_config, _scan_profiles


def test_scan_profiles_from_directory(tmp_path: Path) -> None:
    # Create profile files (no extension, Ghostty-style)
    (tmp_path / "My Theme").write_text("theme = Catppuccin Mocha\nbackground-opacity = 0.9\n")
    (tmp_path / "Other").write_text("theme = Rose Pine\n")

    # Create manifest
    (tmp_path / "manifest.toml").write_text(
        dedent("""\
        [profiles."My Theme"]
        description = "A test profile"
        author = "tester"
        tags = ["dark", "test"]

        [profiles."Other"]
        description = "Another profile"
        author = "tester"
        tags = ["dark"]
    """)
    )

    profiles = _scan_profiles(tmp_path, source="builtin")
    assert len(profiles) == 2

    my_theme = next(p for p in profiles if p.name == "My Theme")
    assert my_theme.description == "A test profile"
    assert my_theme.author == "tester"
    assert my_theme.tags == ["dark", "test"]
    assert "theme = Catppuccin Mocha" in my_theme.config_body()


def test_scan_profiles_without_manifest(tmp_path: Path) -> None:
    (tmp_path / "Bare Theme").write_text("theme = Catppuccin Mocha\n")

    profiles = _scan_profiles(tmp_path, source="user")
    assert len(profiles) == 1
    assert profiles[0].name == "Bare Theme"
    assert profiles[0].description == ""


def test_scan_profiles_skips_dotfiles_and_extensions(tmp_path: Path) -> None:
    (tmp_path / "Valid Theme").write_text("theme = Rose Pine\n")
    (tmp_path / ".hidden").write_text("should skip\n")
    (tmp_path / "manifest.toml").write_text("[profiles]\n")
    (tmp_path / "__pycache__").mkdir()

    profiles = _scan_profiles(tmp_path, source="builtin")
    assert len(profiles) == 1
    assert profiles[0].name == "Valid Theme"


def test_extract_base_config() -> None:
    text = dedent("""\
        # rice-profile: test
        # Managed by ghostty-rice

        shell-integration = detect
        font-family = "JetBrains Mono"

        # --- Profile: test ---
        theme = Catppuccin Mocha
        background-opacity = 0.9
    """)
    base = _extract_base_config(text)
    assert "shell-integration = detect" in base
    assert "font-family" in base
    assert "theme = Catppuccin" not in base
    assert "Profile: test" not in base


def test_critical_builtin_theme_names_match_ghostty() -> None:
    tokyo = (bundled_presets_dir() / "Tokyo Night").read_text()
    solarized = (bundled_presets_dir() / "Solarized").read_text()

    assert "theme = TokyoNight" in tokyo
    assert "theme = light:iTerm2 Solarized Light,dark:iTerm2 Solarized Dark" in solarized
