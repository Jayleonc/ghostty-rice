"""Tests for profile loading and application."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

from ghostty_rice.paths import bundled_presets_dir
from ghostty_rice.profile import (
    _extract_base_config,
    _scan_profiles,
    _upsert_base_settings,
    fix_config_issues,
    reset_to_profile,
    update_base_settings,
    validate_config,
)


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
    catppuccin = (bundled_presets_dir() / "Catppuccin Mocha").read_text()
    one_dark = (bundled_presets_dir() / "One Dark Pro").read_text()
    frosted = (bundled_presets_dir() / "Frosted").read_text()
    codex = (bundled_presets_dir() / "Codex").read_text()

    assert "theme = Catppuccin Mocha" in catppuccin
    assert "theme = Atom One Dark" in one_dark
    assert "foreground = #2e3442" in frosted
    assert "background-opacity = 0.995" in frosted
    assert "minimum-contrast" not in frosted
    assert "background = #2d2d2b" in codex
    assert "palette = 8=#6f7788" in codex


def test_upsert_base_settings_replaces_existing_keys() -> None:
    base = dedent("""\
        shell-integration = detect
        font-family = "Old Font"
        font-size = 12
    """)
    updated = _upsert_base_settings(
        base,
        {"font-family": '"JetBrains Mono"', "font-size": "13"},
    )
    assert 'font-family = "Old Font"' not in updated
    assert "font-size = 12" not in updated
    assert 'font-family = "JetBrains Mono"' in updated
    assert "font-size = 13" in updated


def test_update_base_settings_preserves_active_profile(tmp_path: Path) -> None:
    config_path = tmp_path / "config"
    config_path.write_text(
        dedent("""\
            # rice-profile: Demo
            # Managed by ghostty-rice — https://github.com/jayleonc/ghostty-rice

            shell-integration = detect

            # --- Profile: Demo ---
            theme = Catppuccin Mocha
        """)
    )
    demo_profile = Path(tmp_path / "Demo")
    demo_profile.write_text("theme = Catppuccin Mocha\n")

    class _DemoProfile:
        name = "Demo"

        def config_body(self) -> str:
            return "theme = Catppuccin Mocha"

    with (
        patch("ghostty_rice.profile.ghostty_config_file", return_value=config_path),
        patch("ghostty_rice.profile.get_current_profile", return_value="Demo"),
        patch("ghostty_rice.profile.get_profile", return_value=_DemoProfile()),
    ):
        update_base_settings({"font-size": "13"})

    written = config_path.read_text()
    assert "font-size = 13" in written
    assert "# --- Profile: Demo ---" in written


def test_validate_config_detects_invalid_theme(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.write_text("theme = Tokyo Night\nbackground-opacity = 0.9\n")

    # Create a fake theme directory with valid themes
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    (themes_dir / "TokyoNight Storm").write_text("")
    (themes_dir / "Catppuccin Mocha").write_text("")

    with (
        patch("ghostty_rice.profile.ghostty_config_file", return_value=config),
        patch(
            "ghostty_rice.profile._ghostty_theme_dirs",
            return_value=[themes_dir],
        ),
    ):
        issues = validate_config()

    assert len(issues) == 1
    assert issues[0].key == "theme"
    assert issues[0].value == "Tokyo Night"


def test_validate_config_passes_valid_theme(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.write_text("theme = TokyoNight Storm\n")

    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    (themes_dir / "TokyoNight Storm").write_text("")

    with (
        patch("ghostty_rice.profile.ghostty_config_file", return_value=config),
        patch(
            "ghostty_rice.profile._ghostty_theme_dirs",
            return_value=[themes_dir],
        ),
    ):
        issues = validate_config()

    assert len(issues) == 0


def test_fix_config_issues_removes_invalid_theme(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.write_text(
        "shell-integration = detect\ntheme = Tokyo Night\nbackground-opacity = 0.9\n"
    )

    from ghostty_rice.profile import ConfigIssue

    issues = [ConfigIssue(key="theme", value="Tokyo Night", message="not found")]

    with patch("ghostty_rice.profile.ghostty_config_file", return_value=config):
        actions = fix_config_issues(issues)

    assert len(actions) == 1
    assert "Tokyo Night" in actions[0]
    content = config.read_text()
    assert "theme = Tokyo Night" not in content
    assert "shell-integration = detect" in content
    assert "background-opacity = 0.9" in content


def test_reset_to_profile_applies_profile(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.write_text("theme = BROKEN\n")

    profile_dir = tmp_path / "presets"
    profile_dir.mkdir()
    (profile_dir / "Catppuccin Mocha").write_text("theme = Catppuccin Mocha\n")
    (profile_dir / "manifest.toml").write_text(
        '[profiles."Catppuccin Mocha"]\ndescription = "test"\nauthor = "t"\n'
    )

    with (
        patch("ghostty_rice.profile.ghostty_config_file", return_value=config),
        patch("ghostty_rice.profile.bundled_presets_dir", return_value=profile_dir),
        patch("ghostty_rice.profile.user_profiles_dir", return_value=tmp_path / "empty"),
    ):
        ok, msg = reset_to_profile("Catppuccin Mocha")

    assert ok
    content = config.read_text()
    assert "rice-profile: Catppuccin Mocha" in content
    assert "theme = Catppuccin Mocha" in content


def test_reset_to_profile_fails_for_unknown() -> None:
    with (
        patch("ghostty_rice.profile.list_profiles", return_value=[]),
        patch("ghostty_rice.profile.get_profile", return_value=None),
    ):
        ok, msg = reset_to_profile("Nonexistent")

    assert not ok
    assert "not found" in msg
