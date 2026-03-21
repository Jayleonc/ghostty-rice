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


def _reload_macos() -> tuple[bool, str]:
    """Reload Ghostty config on macOS via Ghostty's AppleScript API."""
    script = """
        set ghostty_running to false
        try
            set ghostty_running to application id "com.mitchellh.ghostty" is running
        end try
        if not ghostty_running then
            try
                set ghostty_running to application "Ghostty" is running
            end try
        end if

        if not ghostty_running then
            error "ghostty_not_running" number 1001
        end if

        try
            tell application id "com.mitchellh.ghostty"
                activate
                set t to focused terminal of selected tab of front window
                perform action "reload_config" on t
            end tell
        on error
            tell application "Ghostty"
                activate
                set t to focused terminal of selected tab of front window
                perform action "reload_config" on t
            end tell
        end try
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
        stderr = result.stderr.strip()
        if "1001" in stderr or "ghostty_not_running" in stderr:
            return False, "Ghostty is not running. Changes will apply on next launch."
        return False, (
            "Auto-reload failed. Press Cmd+Shift+, to reload manually.\n"
            f"  Hint: {stderr}"
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
