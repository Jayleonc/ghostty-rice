"""Tests for shell prompt presets."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ghostty_rice.prompt import (
    apply_prompt_preset,
    current_prompt_preset_name,
    detected_shell_name,
    ensure_prompt_bootstrap,
    get_prompt_preset,
    has_prompt_bootstrap,
    list_prompt_presets,
    prompt_bootstrap_line,
    prompt_runtime_active,
    zsh_available,
)


def test_list_prompt_presets_contains_defaults() -> None:
    presets = list_prompt_presets()
    assert len(presets) >= 3
    assert any(p.name == "Dev Compact" for p in presets)


def test_get_prompt_preset_by_name() -> None:
    preset = get_prompt_preset("Minimal Arrow")
    assert preset is not None
    assert "PROMPT=" in preset.script


def test_apply_prompt_preset_writes_config(tmp_path: Path) -> None:
    preset = get_prompt_preset("Dev Compact")
    assert preset is not None
    target = tmp_path / "prompt.zsh"

    with patch("ghostty_rice.prompt.prompt_preset_file", return_value=target):
        written = apply_prompt_preset(preset)

    assert written == target
    content = target.read_text()
    assert "rice-prompt: Dev Compact" in content
    assert "PROMPT=" in content


def test_current_prompt_preset_name_parses_header(tmp_path: Path) -> None:
    target = tmp_path / "prompt.zsh"
    target.write_text("# rice-prompt: Context Rich\nPROMPT='x'\n")

    with patch("ghostty_rice.prompt.prompt_preset_file", return_value=target):
        assert current_prompt_preset_name() == "Context Rich"


def test_prompt_bootstrap_line_uses_target_file(tmp_path: Path) -> None:
    target = tmp_path / "prompt.zsh"
    line = prompt_bootstrap_line(target)
    assert str(target) in line
    assert "${TERM_PROGRAM:-}" in line
    assert "xterm-ghostty" in line
    assert "COLORTERM" in line
    assert "add-zsh-hook precmd __rice_prompt_reload" in line


def test_has_prompt_bootstrap_detects_marker_block(tmp_path: Path) -> None:
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text(
        "# >>> ghostty-rice prompt >>>\n"
        '[[ -f "/tmp/prompt.zsh" ]] && source "/tmp/prompt.zsh"\n'
        "# <<< ghostty-rice prompt <<<\n"
    )
    assert has_prompt_bootstrap(zshrc=zshrc) is True


def test_has_prompt_bootstrap_detects_legacy_line(tmp_path: Path) -> None:
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text(
        '[[ -f "/tmp/rice/shell/prompt.zsh" ]] && source "/tmp/rice/shell/prompt.zsh"\n'
    )
    assert has_prompt_bootstrap(zshrc=zshrc) is True


def test_ensure_prompt_bootstrap_appends_block(tmp_path: Path) -> None:
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text("export PATH=$PATH\n")
    prompt_file = tmp_path / "prompt.zsh"

    changed = ensure_prompt_bootstrap(zshrc=zshrc, prompt_file=prompt_file)

    assert changed is True
    text = zshrc.read_text()
    assert "# >>> ghostty-rice prompt >>>" in text
    assert str(prompt_file) in text
    assert text.count("# >>> ghostty-rice prompt >>>") == 1


def test_ensure_prompt_bootstrap_updates_existing_block(tmp_path: Path) -> None:
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text(
        "# >>> ghostty-rice prompt >>>\n"
        '[[ -f "/old/path/prompt.zsh" ]] && source "/old/path/prompt.zsh"\n'
        "# <<< ghostty-rice prompt <<<\n"
    )
    new_prompt = tmp_path / "new-prompt.zsh"

    changed = ensure_prompt_bootstrap(zshrc=zshrc, prompt_file=new_prompt)

    assert changed is True
    text = zshrc.read_text()
    assert str(new_prompt) in text
    assert "/old/path/prompt.zsh" not in text


def test_ensure_prompt_bootstrap_upgrades_legacy_line(tmp_path: Path) -> None:
    zshrc = tmp_path / ".zshrc"
    zshrc.write_text(
        '[[ -f "/old/path/rice/shell/prompt.zsh" ]] && '
        'source "/old/path/rice/shell/prompt.zsh"\n'
    )
    new_prompt = tmp_path / "prompt.zsh"

    changed = ensure_prompt_bootstrap(zshrc=zshrc, prompt_file=new_prompt)

    assert changed is True
    text = zshrc.read_text()
    assert "# >>> ghostty-rice prompt >>>" in text
    assert str(new_prompt) in text


def test_detected_shell_name_from_env(monkeypatch) -> None:
    monkeypatch.setenv("SHELL", "/bin/zsh")
    assert detected_shell_name() == "zsh"


def test_zsh_available_false_when_not_found() -> None:
    with patch("ghostty_rice.prompt.shutil.which", return_value=None):
        assert zsh_available() is False


def test_prompt_runtime_active_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GHOSTTY_RICE_PROMPT_HOOK", "1")
    assert prompt_runtime_active() is True
