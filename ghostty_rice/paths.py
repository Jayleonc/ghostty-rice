"""Platform-specific path resolution for Ghostty config."""

from __future__ import annotations

import os
import platform
from pathlib import Path

_BUNDLED_PRESETS = Path(__file__).parent / "presets"


def _existing_config_file(directory: Path) -> Path | None:
    """Return the existing Ghostty config file in a directory, if any."""
    for filename in ("config", "config.ghostty"):
        candidate = directory / filename
        if candidate.exists():
            return candidate
    return None


def ghostty_config_dir() -> Path:
    """Return the Ghostty configuration directory for the current platform.

    On macOS, prefer the active Ghostty config location:
    - ~/Library/Application Support/com.mitchellh.ghostty (default)
    - ~/.config/ghostty (XDG fallback)
    On Linux, use XDG_CONFIG_HOME/ghostty (or ~/.config/ghostty).
    """
    system = platform.system()
    if system == "Darwin":
        home = Path.home()
        app_support_dir = home / "Library" / "Application Support" / "com.mitchellh.ghostty"
        xdg = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config")))
        xdg_dir = xdg / "ghostty"

        if _existing_config_file(app_support_dir):
            return app_support_dir
        if _existing_config_file(xdg_dir):
            return xdg_dir
        return app_support_dir
    elif system == "Linux":
        xdg = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        return xdg / "ghostty"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def ghostty_config_file() -> Path:
    """Return the main Ghostty config file path."""
    config_dir = ghostty_config_dir()
    existing = _existing_config_file(config_dir)
    if existing:
        return existing
    return config_dir / "config"


def rice_dir() -> Path:
    """Return the rice data directory (~/.config/ghostty/rice/).

    This is the root for all rice-managed data, with subdirectories for
    profiles, backups, and future extensions.
    """
    d = ghostty_config_dir() / "rice"
    d.mkdir(parents=True, exist_ok=True)
    return d


def user_profiles_dir() -> Path:
    """Return the directory where user profiles are stored."""
    config_dir = ghostty_config_dir()
    legacy = config_dir / "rice-profiles"
    if legacy.exists():
        return legacy

    d = rice_dir() / "profiles"
    d.mkdir(parents=True, exist_ok=True)
    return d


def prompt_preset_file() -> Path:
    """Return the zsh prompt preset file managed by rice."""
    shell_dir = rice_dir() / "shell"
    shell_dir.mkdir(parents=True, exist_ok=True)
    return shell_dir / "prompt.zsh"


def bundled_presets_dir() -> Path:
    """Return the directory containing bundled preset profiles."""
    return _BUNDLED_PRESETS
