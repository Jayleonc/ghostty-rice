"""Tests for platform abstraction."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from ghostty_rice.platform import DiagnosticCheck, MacOSPlatform, get_platform


def test_get_platform_returns_instance() -> None:
    plat = get_platform()
    assert plat is not None


def test_diagnostics_returns_checks() -> None:
    plat = get_platform()
    checks = plat.run_diagnostics()
    assert len(checks) > 0
    assert all(isinstance(c, DiagnosticCheck) for c in checks)


def test_diagnostic_check_fields() -> None:
    check = DiagnosticCheck(
        name="Test",
        passed=True,
        message="OK",
        hint="",
    )
    assert check.name == "Test"
    assert check.passed is True


def _completed(
    returncode: int, *, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_macos_is_ghostty_running_uses_applescript() -> None:
    plat = MacOSPlatform()
    with patch(
        "ghostty_rice.platform.subprocess.run",
        return_value=_completed(0, stdout="true\n"),
    ) as mock_run:
        assert plat.is_ghostty_running() is True
    assert mock_run.call_count == 1
    assert mock_run.call_args.args[0][:2] == ["osascript", "-e"]


def test_macos_is_ghostty_running_falls_back_to_pgrep() -> None:
    plat = MacOSPlatform()
    with patch("ghostty_rice.platform.subprocess.run") as mock_run:
        mock_run.side_effect = [
            _completed(1, stdout="", stderr="osascript failed"),
            _completed(1),
            _completed(0),
        ]
        assert plat.is_ghostty_running() is True
    assert mock_run.call_args_list[1].args[0] == ["pgrep", "-x", "ghostty"]
    assert mock_run.call_args_list[2].args[0] == ["pgrep", "-x", "Ghostty"]


def test_macos_check_automation_permission_parses_error_output() -> None:
    plat = MacOSPlatform()
    with patch(
        "ghostty_rice.platform.subprocess.run",
        return_value=_completed(0, stdout="error:-1743:not permitted\n"),
    ):
        check = plat._check_automation_permission()

    assert check.passed is False
    assert check.message == "Not granted"
