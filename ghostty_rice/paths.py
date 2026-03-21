"""Platform-specific path resolution for Ghostty config."""

from __future__ import annotations

import os
import platform
from pathlib import Path

_BUNDLED_PRESETS = Path(__file__).parent / "presets"


def ghostty_config_dir() -> Path:
    """Return the Ghostty configuration directory for the current platform.

    Always uses ~/.config/ghostty regardless of platform, following the
    XDG convention for a consistent and accessible path.
    """
    system = platform.system()
    if system == "Darwin":
        return Path.home() / ".config" / "ghostty"
    elif system == "Linux":
        xdg = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        return xdg / "ghostty"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def ghostty_config_file() -> Path:
    """Return the main Ghostty config file path."""
    return ghostty_config_dir() / "config"


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
    d = rice_dir() / "profiles"
    d.mkdir(parents=True, exist_ok=True)
    return d


def bundled_presets_dir() -> Path:
    """Return the directory containing bundled preset profiles."""
    return _BUNDLED_PRESETS
