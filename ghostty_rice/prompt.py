"""Zsh prompt presets managed by ghostty-rice."""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from ghostty_rice.paths import prompt_preset_file

_PROMPT_NAME_RE = re.compile(r"^#\s*rice-prompt:\s*(.+)$")
_BOOTSTRAP_START = "# >>> ghostty-rice prompt >>>"
_BOOTSTRAP_END = "# <<< ghostty-rice prompt <<<"
_LEGACY_SOURCE_RE = re.compile(
    r'^\s*\[\[\s+-f\s+"[^"]*/rice/shell/prompt\.zsh"\s*\]\]\s*&&\s*source\s+"[^"]*/rice/shell/prompt\.zsh"\s*$',
    re.MULTILINE,
)


@dataclass(frozen=True)
class PromptPreset:
    """A curated zsh prompt preset."""

    name: str
    description: str
    sample: str
    script: str


_PROMPT_PRESETS: list[PromptPreset] = [
    PromptPreset(
        name="Zen",
        description="Ultra-minimal — colored status arrow only",
        sample="❯",
        script="PROMPT='%(?.%F{green}.%F{red})❯%f '\n",
    ),
    PromptPreset(
        name="Minimal Arrow",
        description="Repo name with subtle arrow",
        sample="ghostty-rice ›",
        script="PROMPT='%F{blue}%1~%f %F{242}›%f '\n",
    ),
    PromptPreset(
        name="Lambda",
        description="Sleek lambda accent with path",
        sample="λ ghostty-rice ›",
        script="PROMPT='%F{yellow}λ%f %F{blue}%1~%f %F{242}›%f '\n",
    ),
    PromptPreset(
        name="Dev Compact",
        description="Virtualenv + short path, single line",
        sample="(.venv) repo/subdir »",
        script=(
            "setopt PROMPT_SUBST\n"
            "PROMPT='${VIRTUAL_ENV:+(%F{green}${VIRTUAL_ENV:t}%f) }"
            "%F{blue}%2~%f %F{242}»%f '\n"
        ),
    ),
    PromptPreset(
        name="Starship",
        description="Two-line with git branch — modern and spacious",
        sample="~/project main\n❯",
        script=(
            "setopt PROMPT_SUBST\n"
            "__rice_git_prompt() {\n"
            "  local b=$(git symbolic-ref --short HEAD 2>/dev/null)\n"
            '  [[ -n "$b" ]] && echo " %F{magenta}$b%f"\n'
            "}\n"
            "PROMPT='\n"
            "%F{blue}%~%f$(__rice_git_prompt)\n"
            "%(?.%F{green}.%F{red})❯%f '\n"
        ),
    ),
    PromptPreset(
        name="Boxed",
        description="Two-line box-drawn frame with git branch",
        sample="┌ ~/project (main)\n└ ❯",
        script=(
            "setopt PROMPT_SUBST\n"
            "__rice_git_prompt() {\n"
            "  local b=$(git symbolic-ref --short HEAD 2>/dev/null)\n"
            '  [[ -n "$b" ]] && echo " %F{242}($b)%f"\n'
            "}\n"
            "PROMPT='%F{242}┌%f %F{blue}%~%f$(__rice_git_prompt)\n"
            "%F{242}└%f %(?.%F{green}.%F{red})❯%f '\n"
        ),
    ),
    PromptPreset(
        name="Deep Path",
        description="Full working path for deep directory trees",
        sample="(.venv) ~/Developer/python/project ❯",
        script=(
            "setopt PROMPT_SUBST\n"
            "PROMPT='${VIRTUAL_ENV:+(%F{green}${VIRTUAL_ENV:t}%f) }"
            "%F{blue}%~%f %F{242}❯%f '\n"
        ),
    ),
    PromptPreset(
        name="Context Rich",
        description="Full context — user@host, path, privileges",
        sample="[.venv] jay@mbp ghostty-rice #",
        script=(
            "setopt PROMPT_SUBST\n"
            "PROMPT='${VIRTUAL_ENV:+[%F{green}${VIRTUAL_ENV:t}%f] }"
            "%F{blue}%n@%m%f %F{blue}%1~%f %F{242}%#%f '\n"
        ),
    ),
]


def list_prompt_presets() -> list[PromptPreset]:
    """Return all prompt presets."""
    return _PROMPT_PRESETS[:]


def get_prompt_preset(name: str) -> PromptPreset | None:
    """Return preset by exact name."""
    for preset in _PROMPT_PRESETS:
        if preset.name == name:
            return preset
    return None


def current_prompt_preset_name() -> str | None:
    """Return currently active prompt preset name."""
    config = prompt_preset_file()
    if not config.exists():
        return None

    for line in config.read_text().splitlines()[:5]:
        match = _PROMPT_NAME_RE.match(line.strip())
        if match:
            return match.group(1)
    return None


def apply_prompt_preset(preset: PromptPreset) -> Path:
    """Write selected prompt preset into rice-managed shell file."""
    path = prompt_preset_file()
    content = (
        f"# rice-prompt: {preset.name}\n"
        "# Managed by ghostty-rice\n\n"
        f"{preset.script}"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def detected_shell_name() -> str:
    """Return current user shell name from `$SHELL`."""
    shell_path = os.environ.get("SHELL", "").strip()
    if not shell_path:
        return "unknown"
    return Path(shell_path).name or shell_path


def zsh_available() -> bool:
    """Return whether `zsh` is installed and available in PATH."""
    return shutil.which("zsh") is not None


def prompt_runtime_active() -> bool:
    """Return whether current shell session already loaded rice prompt hook."""
    return os.environ.get("GHOSTTY_RICE_PROMPT_HOOK") == "1"


def prompt_bootstrap_line(prompt_file: Path | None = None) -> str:
    """Return zsh bootstrap script to load prompt presets in Ghostty sessions."""
    target = prompt_file or prompt_preset_file()
    return (
        'if [[ "${TERM_PROGRAM:-}" == "ghostty" || "${TERM:-}" == xterm-ghostty* '
        '|| -n "${GHOSTTY_RESOURCES_DIR:-}" ]]; then\n'
        "  export GHOSTTY_RICE_PROMPT_HOOK=1\n"
        "  export COLORTERM=${COLORTERM:-truecolor}\n"
        "  if [[ -z \"${ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE:-}\" "
        "|| \"${ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE}\" == \"fg=8\" "
        "|| ${ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE} == fg=#* ]]; then\n"
        "    export ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=238'\n"
        "  fi\n"
        "  if typeset -p ZSH_HIGHLIGHT_STYLES >/dev/null 2>&1; then\n"
        "    [[ -n \"${ZSH_HIGHLIGHT_STYLES[comment]:-}\" ]] || "
        "ZSH_HIGHLIGHT_STYLES[comment]='fg=238'\n"
        "  fi\n"
        f'  _RICE_PROMPT_FILE="{target}"\n'
        "  __rice_prompt_reload() {\n"
        '    [[ -f "$_RICE_PROMPT_FILE" ]] || return\n'
        '    source "$_RICE_PROMPT_FILE"\n'
        "  }\n"
        "  autoload -Uz add-zsh-hook\n"
        "  add-zsh-hook -d precmd __rice_prompt_reload >/dev/null 2>&1\n"
        "  add-zsh-hook precmd __rice_prompt_reload\n"
        "  __rice_prompt_reload\n"
        "fi"
    )


def has_prompt_bootstrap(zshrc: Path | None = None) -> bool:
    """Check whether `~/.zshrc` already sources rice prompt file."""
    target = zshrc or Path.home() / ".zshrc"
    if not target.exists():
        return False

    text = target.read_text()
    if _BOOTSTRAP_START in text and _BOOTSTRAP_END in text:
        return True

    line = prompt_bootstrap_line()
    if line in text:
        return True
    return bool(_LEGACY_SOURCE_RE.search(text))


def ensure_prompt_bootstrap(zshrc: Path | None = None, prompt_file: Path | None = None) -> bool:
    """Ensure `~/.zshrc` sources rice prompt preset; returns True if changed."""
    target = zshrc or Path.home() / ".zshrc"
    line = prompt_bootstrap_line(prompt_file)
    block = f"{_BOOTSTRAP_START}\n{line}\n{_BOOTSTRAP_END}"

    if target.exists():
        text = target.read_text()
    else:
        text = ""

    marker_start_idx = text.find(_BOOTSTRAP_START)
    marker_end_idx = text.find(_BOOTSTRAP_END)
    if marker_start_idx != -1 and marker_end_idx != -1 and marker_end_idx > marker_start_idx:
        marker_end_idx += len(_BOOTSTRAP_END)
        updated = f"{text[:marker_start_idx]}{block}{text[marker_end_idx:]}"
        if updated != text:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(updated.rstrip() + "\n")
            return True
        return False

    if line in text:
        return False
    if _LEGACY_SOURCE_RE.search(text):
        updated = _LEGACY_SOURCE_RE.sub(block, text)
        if updated != text:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(updated.rstrip() + "\n")
            return True
        return False

    text = text.rstrip()
    if text:
        text += "\n\n"
    text += block + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    return True
