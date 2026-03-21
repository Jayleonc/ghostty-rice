"""Tests for platform abstraction."""

from __future__ import annotations

from ghostty_rice.platform import DiagnosticCheck, get_platform


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
