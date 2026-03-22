"""Tests for studio theme builders."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ghostty_rice.studio import (
    build_studio_profile_body,
    default_studio_theme,
    list_studio_themes,
    write_studio_profile,
)


def test_list_studio_themes_contains_expected_names() -> None:
    names = [theme.name for theme in list_studio_themes()]
    assert "Absolutely" in names
    assert "Codex" in names
    assert "Tokyo Night" in names
    assert len(names) >= 12


def test_build_studio_profile_body_contains_expected_fields() -> None:
    theme = default_studio_theme()
    body = build_studio_profile_body(
        theme=theme,
        accent="#CC7D5E",
        background="#2D2D2B",
        foreground="#F9F9F7",
        translucent=True,
    )
    assert "background = #2D2D2B" in body
    assert "foreground = #F9F9F7" in body
    assert "cursor-color = #CC7D5E" in body
    assert "minimum-contrast" not in body
    assert "background-opacity = 0.96" in body
    assert "background-blur = macos-glass-regular" in body


def test_build_studio_profile_body_disables_blur_when_not_translucent() -> None:
    theme = default_studio_theme()
    body = build_studio_profile_body(
        theme=theme,
        accent="#CC7D5E",
        background="#2D2D2B",
        foreground="#F9F9F7",
        translucent=False,
    )
    assert "background-opacity = 1.0" in body
    assert "background-blur = macos-glass-regular" not in body
    assert "minimum-contrast" not in body


def test_write_studio_profile_writes_under_user_profiles(tmp_path: Path) -> None:
    target_dir = tmp_path / "profiles"
    body = "background = #2D2D2B\n"

    with patch("ghostty_rice.studio.user_profiles_dir", return_value=target_dir):
        path = write_studio_profile(body, profile_name="Studio Live")

    assert path == target_dir / "Studio Live"
    assert path.read_text() == body
