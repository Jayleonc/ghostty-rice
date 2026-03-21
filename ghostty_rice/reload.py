"""Ghostty config reload — delegates to platform layer."""

from __future__ import annotations

from ghostty_rice.platform import get_platform


def reload_ghostty() -> tuple[bool, str]:
    """Attempt to reload Ghostty config. Returns (success, message)."""
    result = get_platform().reload_config()
    return result.success, result.message
