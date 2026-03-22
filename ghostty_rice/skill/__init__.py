"""AI skill installation for ghostty-rice.

Installs a theme-generation prompt into AI coding agents so users can
generate custom Ghostty color schemes through natural conversation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ghostty_rice.paths import user_profiles_dir

_SKILL_TEMPLATE = Path(__file__).parent / "ghostty-theme.md"
_SKILL_FILENAME = "ghostty-theme.md"


@dataclass(frozen=True)
class AgentTarget:
    """An AI agent that can receive the skill."""

    name: str
    display_name: str
    skill_dir: Path
    installed: bool

    @property
    def skill_path(self) -> Path:
        return self.skill_dir / _SKILL_FILENAME


def _detect_claude_code() -> AgentTarget | None:
    """Detect Claude Code (user-level commands)."""
    commands_dir = Path.home() / ".claude" / "commands"
    # Claude Code is installed if ~/.claude/ exists
    claude_dir = Path.home() / ".claude"
    if claude_dir.exists():
        installed = (commands_dir / _SKILL_FILENAME).exists()
        return AgentTarget(
            name="claude-code",
            display_name="Claude Code",
            skill_dir=commands_dir,
            installed=installed,
        )
    return None


def _detect_cursor() -> AgentTarget | None:
    """Detect Cursor (global rules)."""
    cursor_dir = Path.home() / ".cursor"
    if cursor_dir.exists():
        rules_dir = cursor_dir / "rules"
        installed = (rules_dir / _SKILL_FILENAME).exists()
        return AgentTarget(
            name="cursor",
            display_name="Cursor",
            skill_dir=rules_dir,
            installed=installed,
        )
    return None


def _detect_windsurf() -> AgentTarget | None:
    """Detect Windsurf (global rules)."""
    windsurf_dir = Path.home() / ".codeium" / "windsurf"
    if windsurf_dir.exists():
        rules_dir = windsurf_dir / "rules"
        installed = (rules_dir / _SKILL_FILENAME).exists()
        return AgentTarget(
            name="windsurf",
            display_name="Windsurf",
            skill_dir=rules_dir,
            installed=installed,
        )
    return None


_DETECTORS = [_detect_claude_code, _detect_cursor, _detect_windsurf]


def detect_agents() -> list[AgentTarget]:
    """Return all detected AI agents on this machine."""
    agents: list[AgentTarget] = []
    for detect in _DETECTORS:
        agent = detect()
        if agent is not None:
            agents.append(agent)
    return agents


def _render_template() -> str:
    """Read the skill template and fill in the profiles directory path."""
    template = _SKILL_TEMPLATE.read_text()
    profiles_dir = str(user_profiles_dir())
    return template.replace("{{PROFILES_DIR}}", profiles_dir)


def install_skill(agent: AgentTarget) -> Path:
    """Install the skill prompt for the given agent. Returns the written path."""
    content = _render_template()
    agent.skill_dir.mkdir(parents=True, exist_ok=True)
    target = agent.skill_path
    target.write_text(content)
    return target


def uninstall_skill(agent: AgentTarget) -> bool:
    """Remove the skill from the given agent. Returns True if file was removed."""
    target = agent.skill_path
    if target.exists():
        target.unlink()
        return True
    return False


def export_skill(destination: Path) -> Path:
    """Export the rendered skill template to an arbitrary path."""
    content = _render_template()
    if destination.is_dir() or str(destination).endswith("/"):
        destination = destination / _SKILL_FILENAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content)
    return destination
