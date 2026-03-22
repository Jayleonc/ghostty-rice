"""Platform abstraction layer for Ghostty operations.

Each platform implements GhosttyPlatform to handle:
- Config reload
- Ghostty detection (installed, running, version)
- Platform-specific diagnostics

To add a new platform, subclass GhosttyPlatform and register it in get_platform().
"""

from __future__ import annotations

import abc
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

_GHOSTTY_TERMINFO_NAME = "xterm-ghostty"
_MACOS_BUNDLED_TERMINFO = Path(
    "/Applications/Ghostty.app/Contents/Resources/terminfo/78/xterm-ghostty"
)


@dataclass
class ReloadResult:
    """Result of a config reload attempt."""

    success: bool
    message: str


@dataclass
class DiagnosticCheck:
    """A single diagnostic check result."""

    name: str
    passed: bool
    message: str
    hint: str = ""


def has_xterm_ghostty_terminfo() -> bool:
    """Return whether `xterm-ghostty` terminfo entry is available."""
    try:
        result = subprocess.run(
            ["infocmp", _GHOSTTY_TERMINFO_NAME],
            capture_output=True,
            timeout=3,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    return result.returncode == 0


def install_xterm_ghostty_terminfo() -> tuple[bool, str]:
    """Install Ghostty bundled terminfo into user terminfo dir on macOS."""
    if platform.system() != "Darwin":
        return False, "Terminfo installer is currently macOS-only."

    if has_xterm_ghostty_terminfo():
        return True, "xterm-ghostty terminfo already installed."

    if not _MACOS_BUNDLED_TERMINFO.exists():
        return False, f"Bundled terminfo not found: {_MACOS_BUNDLED_TERMINFO}"

    target = Path.home() / ".terminfo" / "78" / _GHOSTTY_TERMINFO_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(_MACOS_BUNDLED_TERMINFO, target)
    except OSError as exc:
        return False, f"Failed to install terminfo: {exc}"

    if has_xterm_ghostty_terminfo():
        return True, "Installed xterm-ghostty terminfo (improves Vim/Neovim rendering)."
    return False, "Terminfo copy succeeded but `infocmp xterm-ghostty` still fails."


class GhosttyPlatform(abc.ABC):
    """Abstract base for platform-specific Ghostty operations."""

    @abc.abstractmethod
    def reload_config(self) -> ReloadResult:
        """Reload Ghostty configuration."""

    @abc.abstractmethod
    def is_ghostty_installed(self) -> bool:
        """Check if Ghostty is installed."""

    @abc.abstractmethod
    def is_ghostty_running(self) -> bool:
        """Check if Ghostty is currently running."""

    @abc.abstractmethod
    def ghostty_version(self) -> str | None:
        """Return Ghostty version string, or None if not found."""

    @abc.abstractmethod
    def run_diagnostics(self) -> list[DiagnosticCheck]:
        """Run platform-specific diagnostic checks."""


class MacOSPlatform(GhosttyPlatform):
    """macOS-specific Ghostty operations."""

    _GHOSTTY_APP = "/Applications/Ghostty.app"
    _GHOSTTY_BIN = f"{_GHOSTTY_APP}/Contents/MacOS/ghostty"

    def reload_config(self) -> ReloadResult:
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
                return ReloadResult(True, "Config reloaded.")
            stderr = result.stderr.strip()
            if "1001" in stderr or "ghostty_not_running" in stderr:
                return ReloadResult(
                    False, "Ghostty is not running. Changes will apply on next launch."
                )
            return ReloadResult(
                False,
                f"Auto-reload failed. Press Cmd+Shift+, to reload manually.\n  Hint: {stderr}",
            )
        except subprocess.TimeoutExpired:
            return ReloadResult(
                False, "Auto-reload timed out. Press Cmd+Shift+, to reload manually."
            )

    def is_ghostty_installed(self) -> bool:
        from pathlib import Path

        return Path(self._GHOSTTY_APP).exists()

    def is_ghostty_running(self) -> bool:
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
            if ghostty_running then
                return "true"
            else
                return "false"
            end if
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0:
                return result.stdout.strip().lower() == "true"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        probes = [
            ["pgrep", "-x", "ghostty"],
            ["pgrep", "-x", "Ghostty"],
            ["pgrep", "-f", "Ghostty.app/Contents/MacOS/ghostty"],
            ["pgrep", "-f", "Ghostty.app/Contents/MacOS/Ghostty"],
        ]
        for probe in probes:
            try:
                result = subprocess.run(probe, capture_output=True)
            except FileNotFoundError:
                return False
            if result.returncode == 0:
                return True
        return False

    def ghostty_version(self) -> str | None:
        try:
            result = subprocess.run(
                [self._GHOSTTY_BIN, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                if line.startswith("Ghostty "):
                    return line.split(" ", 1)[1]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def run_diagnostics(self) -> list[DiagnosticCheck]:
        checks: list[DiagnosticCheck] = []

        # Check Ghostty installed
        installed = self.is_ghostty_installed()
        checks.append(
            DiagnosticCheck(
                name="Ghostty installed",
                passed=installed,
                message=self._GHOSTTY_APP if installed else "Not found",
                hint="Download from https://ghostty.org" if not installed else "",
            )
        )

        # Check version
        if installed:
            version = self.ghostty_version()
            checks.append(
                DiagnosticCheck(
                    name="Ghostty version",
                    passed=version is not None,
                    message=version or "Unknown",
                )
            )

        # Check running
        running = self.is_ghostty_running()
        checks.append(
            DiagnosticCheck(
                name="Ghostty running",
                passed=running,
                message="Yes" if running else "No",
                hint="Start Ghostty to test auto-reload" if not running else "",
            )
        )

        # Check AppleScript automation permission
        checks.append(self._check_automation_permission())

        # Check xterm-ghostty terminfo for better TUI compatibility (Vim/Neovim/FZF)
        terminfo_ok = has_xterm_ghostty_terminfo()
        checks.append(
            DiagnosticCheck(
                name="xterm-ghostty terminfo",
                passed=terminfo_ok,
                message="Installed" if terminfo_ok else "Missing",
                hint=(
                    "Run `rice doctor --fix` to install bundled terminfo "
                    "for better Vim/Neovim colors and key behavior"
                    if not terminfo_ok
                    else ""
                ),
            )
        )

        return checks

    def _check_automation_permission(self) -> DiagnosticCheck:
        """Check if the current terminal has macOS Automation permission for Ghostty."""
        test_script = """
            try
                tell application id "com.mitchellh.ghostty" to get name
                return "ok"
            on error errMsg number errNum
                return "error:" & errNum & ":" & errMsg
            end try
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", test_script],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = result.stdout.strip()
            if output == "ok":
                return DiagnosticCheck(
                    name="Automation permission",
                    passed=True,
                    message="Granted",
                )
            if output.startswith("error:"):
                return DiagnosticCheck(
                    name="Automation permission",
                    passed=False,
                    message="Not granted",
                    hint="Allow in System Settings > Privacy & Security > Automation",
                )
            return DiagnosticCheck(
                name="Automation permission",
                passed=False,
                message="Could not verify",
                hint="Run `rice switch` once to trigger the permission prompt",
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return DiagnosticCheck(
                name="Automation permission",
                passed=False,
                message="Could not check",
                hint="Try running: rice switch to trigger the permission prompt",
            )


class LinuxPlatform(GhosttyPlatform):
    """Linux-specific Ghostty operations."""

    def reload_config(self) -> ReloadResult:
        if shutil.which("xdotool"):
            try:
                # Find Ghostty window
                find_result = subprocess.run(
                    ["xdotool", "search", "--name", "ghostty"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                window_ids = find_result.stdout.strip().splitlines()
                if window_ids:
                    subprocess.run(
                        ["xdotool", "key", "--window", window_ids[0], "ctrl+shift+comma"],
                        capture_output=True,
                        timeout=5,
                    )
                    return ReloadResult(True, "Config reloaded via xdotool.")
                return ReloadResult(False, "No Ghostty window found.")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return ReloadResult(
            False, "Auto-reload not available. Press Ctrl+Shift+, to reload manually."
        )

    def is_ghostty_installed(self) -> bool:
        return shutil.which("ghostty") is not None

    def is_ghostty_running(self) -> bool:
        try:
            result = subprocess.run(["pgrep", "-x", "ghostty"], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def ghostty_version(self) -> str | None:
        try:
            result = subprocess.run(
                ["ghostty", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                if line.startswith("Ghostty "):
                    return line.split(" ", 1)[1]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def run_diagnostics(self) -> list[DiagnosticCheck]:
        checks: list[DiagnosticCheck] = []

        installed = self.is_ghostty_installed()
        ghostty_path = shutil.which("ghostty") or "Not found"
        checks.append(
            DiagnosticCheck(
                name="Ghostty installed",
                passed=installed,
                message=ghostty_path,
                hint="Install from https://ghostty.org" if not installed else "",
            )
        )

        if installed:
            version = self.ghostty_version()
            checks.append(
                DiagnosticCheck(
                    name="Ghostty version",
                    passed=version is not None,
                    message=version or "Unknown",
                )
            )

        running = self.is_ghostty_running()
        checks.append(
            DiagnosticCheck(
                name="Ghostty running",
                passed=running,
                message="Yes" if running else "No",
                hint="Start Ghostty to test auto-reload" if not running else "",
            )
        )

        # Check xdotool for auto-reload
        has_xdotool = shutil.which("xdotool") is not None
        checks.append(
            DiagnosticCheck(
                name="xdotool (for auto-reload)",
                passed=has_xdotool,
                message="Installed" if has_xdotool else "Not found",
                hint="Install xdotool for auto-reload support" if not has_xdotool else "",
            )
        )

        return checks


def get_platform() -> GhosttyPlatform:
    """Return the platform handler for the current OS."""
    system = platform.system()
    if system == "Darwin":
        return MacOSPlatform()
    elif system == "Linux":
        return LinuxPlatform()
    raise RuntimeError(
        f"Unsupported platform: {system}. "
        "Contributions welcome: https://github.com/jayleonc/ghostty-rice/issues"
    )
