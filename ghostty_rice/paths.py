"""Platform-specific path resolution for Ghostty config."""

from __future__ import annotations

import platform
from pathlib import Path

_BUNDLED_PRESETS = Path(__file__).parent / "presets"


def ghostty_config_dir() -> Path:
    """Return the Ghostty configuration directory for the current platform."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "com.mitchellh.ghostty"
    elif system == "Linux":
        xdg = Path(__import__("os").environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        return xdg / "ghostty"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def ghostty_config_file() -> Path:
    """Return the main Ghostty config file path."""
    return ghostty_config_dir() / "config"


def user_profiles_dir() -> Path:
    """Return the directory where user profiles are stored."""
    d = ghostty_config_dir() / "rice-profiles"
    d.mkdir(parents=True, exist_ok=True)
    return d


def bundled_presets_dir() -> Path:
    """Return the directory containing bundled preset profiles."""
    return _BUNDLED_PRESETS
