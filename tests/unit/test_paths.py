"""Tests for path resolution logic."""

from __future__ import annotations

from pathlib import Path

from ghostty_rice import paths


def _set_macos_env(monkeypatch, home: Path) -> None:
    monkeypatch.setattr(paths.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(paths.Path, "home", lambda: home)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".xdg"))


def test_macos_prefers_app_support_when_config_exists(monkeypatch, tmp_path: Path) -> None:
    _set_macos_env(monkeypatch, tmp_path)

    app_dir = tmp_path / "Library" / "Application Support" / "com.mitchellh.ghostty"
    xdg_dir = tmp_path / ".xdg" / "ghostty"
    app_dir.mkdir(parents=True)
    xdg_dir.mkdir(parents=True)
    (app_dir / "config").write_text("# app config\n")
    (xdg_dir / "config").write_text("# xdg config\n")

    assert paths.ghostty_config_dir() == app_dir
    assert paths.ghostty_config_file() == app_dir / "config"


def test_macos_uses_xdg_when_app_support_has_no_config(monkeypatch, tmp_path: Path) -> None:
    _set_macos_env(monkeypatch, tmp_path)

    app_dir = tmp_path / "Library" / "Application Support" / "com.mitchellh.ghostty"
    xdg_dir = tmp_path / ".xdg" / "ghostty"
    app_dir.mkdir(parents=True)
    xdg_dir.mkdir(parents=True)
    (xdg_dir / "config").write_text("# xdg config\n")

    assert paths.ghostty_config_dir() == xdg_dir
    assert paths.ghostty_config_file() == xdg_dir / "config"


def test_macos_defaults_to_app_support_when_no_config_exists(
    monkeypatch, tmp_path: Path
) -> None:
    _set_macos_env(monkeypatch, tmp_path)

    expected = tmp_path / "Library" / "Application Support" / "com.mitchellh.ghostty"
    assert paths.ghostty_config_dir() == expected
    assert paths.ghostty_config_file() == expected / "config"


def test_ghostty_config_file_supports_config_ghostty(monkeypatch, tmp_path: Path) -> None:
    _set_macos_env(monkeypatch, tmp_path)

    app_dir = tmp_path / "Library" / "Application Support" / "com.mitchellh.ghostty"
    app_dir.mkdir(parents=True)
    (app_dir / "config.ghostty").write_text("# legacy filename\n")

    assert paths.ghostty_config_file() == app_dir / "config.ghostty"


def test_user_profiles_dir_prefers_legacy_folder(monkeypatch, tmp_path: Path) -> None:
    _set_macos_env(monkeypatch, tmp_path)

    app_dir = tmp_path / "Library" / "Application Support" / "com.mitchellh.ghostty"
    app_dir.mkdir(parents=True)
    (app_dir / "config").write_text("# app config\n")
    legacy = app_dir / "rice-profiles"
    legacy.mkdir()

    assert paths.user_profiles_dir() == legacy
