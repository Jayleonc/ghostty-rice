"""Ghostty config reload — platform-specific strategies."""

from __future__ import annotations

import platform
import shutil
import subprocess


def reload_ghostty() -> tuple[bool, str]:
    """Attempt to reload Ghostty config. Returns (success, message)."""
    system = platform.system()
    if system == "Darwin":
        return _reload_macos()
    elif system == "Linux":
        return _reload_linux()
    return False, f"Unsupported platform: {system}"


def _is_ghostty_running_macos() -> bool:
    """Check if Ghostty is running on macOS."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "Ghostty.app/Contents/MacOS/ghostty"],
            capture_output=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _reload_macos() -> tuple[bool, str]:
    """Reload Ghostty config on macOS via menu bar click."""
    if not _is_ghostty_running_macos():
        return False, "Ghostty is not running. Changes will apply on next launch."

    script = """
        tell application "Ghostty" to activate
        delay 0.3
        tell application "System Events"
            tell process "Ghostty"
                click menu item "Reload Configuration" of menu "Ghostty" of menu bar 1
            end tell
        end tell
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, "Config reloaded."
        return False, (
            "Auto-reload failed. Press Cmd+Shift+, to reload manually.\n"
            f"  Hint: {result.stderr.strip()}"
        )
    except subprocess.TimeoutExpired:
        return False, "Auto-reload timed out. Press Cmd+Shift+, to reload manually."


def _reload_linux() -> tuple[bool, str]:
    """Reload Ghostty config on Linux via SIGUSR2 or xdotool."""
    # Try xdotool approach
    if shutil.which("xdotool"):
        try:
            subprocess.run(
                [
                    "xdotool",
                    "key",
                    "--window",
                    "$(xdotool search --name ghostty | head -1)",
                    "ctrl+shift+comma",
                ],
                capture_output=True,
                shell=True,
                timeout=5,
            )
            return True, "Config reloaded via xdotool."
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return False, "Auto-reload not available. Press Ctrl+Shift+, to reload manually."
