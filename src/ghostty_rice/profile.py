"""Profile loading, listing, and application."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ghostty_rice.paths import bundled_presets_dir, ghostty_config_file, user_profiles_dir

_HEADER_RE = re.compile(r"^#\s*@(\w+):\s*(.+)$")
_CURRENT_RE = re.compile(r"^#\s*rice-profile:\s*(\S+)")


@dataclass
class Profile:
    """A Ghostty visual profile."""

    name: str
    description: str
    author: str
    source: str  # "builtin" or "user"
    path: Path
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path, source: str) -> Profile:
        """Parse a profile from a .conf file with header metadata."""
        description = ""
        author = ""
        tags: list[str] = []

        with open(path) as f:
            for line in f:
                m = _HEADER_RE.match(line.strip())
                if not m:
                    break
                key, val = m.group(1).lower(), m.group(2).strip()
                if key == "description":
                    description = val
                elif key == "author":
                    author = val
                elif key == "tags":
                    tags = [t.strip() for t in val.split(",")]

        return cls(
            name=path.stem,
            description=description,
            author=author,
            source=source,
            path=path,
            tags=tags,
        )

    def config_body(self) -> str:
        """Return the config content (excluding header comments)."""
        lines = self.path.read_text().splitlines()
        body_lines = []
        past_header = False
        for line in lines:
            if not past_header and _HEADER_RE.match(line.strip()):
                continue
            past_header = True
            body_lines.append(line)
        return "\n".join(body_lines).strip()


def list_profiles() -> list[Profile]:
    """List all available profiles (builtin + user), user profiles override builtin."""
    profiles: dict[str, Profile] = {}

    # Load builtin presets
    presets_dir = bundled_presets_dir()
    if presets_dir.exists():
        for f in sorted(presets_dir.glob("*.conf")):
            p = Profile.from_file(f, source="builtin")
            profiles[p.name] = p

    # Load user profiles (override builtin with same name)
    user_dir = user_profiles_dir()
    if user_dir.exists():
        for f in sorted(user_dir.glob("*.conf")):
            p = Profile.from_file(f, source="user")
            profiles[p.name] = p

    return sorted(profiles.values(), key=lambda p: p.name)


def get_profile(name: str) -> Profile | None:
    """Get a profile by name."""
    for p in list_profiles():
        if p.name == name:
            return p
    return None


def get_current_profile() -> str | None:
    """Read the currently active profile name from the config file."""
    config = ghostty_config_file()
    if not config.exists():
        return None
    for line in config.read_text().splitlines()[:5]:
        m = _CURRENT_RE.match(line)
        if m:
            return m.group(1)
    return None


_BASE_CONFIG = """\
# rice-profile: {name}
# Managed by ghostty-rice — https://github.com/jayleonc/ghostty-rice
# Do not edit the profile section below manually; use `rice use <profile>`.

"""


def apply_profile(profile: Profile, base_lines: list[str] | None = None) -> None:
    """Write a profile to the Ghostty config file.

    Preserves user's base config (shell, font, keybinds, etc.) and replaces
    only the profile section.
    """
    config_path = ghostty_config_file()

    if base_lines is not None:
        base = "\n".join(base_lines)
    elif config_path.exists():
        base = _extract_base_config(config_path.read_text())
    else:
        base = ""

    content = _BASE_CONFIG.format(name=profile.name)
    if base.strip():
        content += base.strip() + "\n\n"
    content += f"# --- Profile: {profile.name} ---\n"
    content += profile.config_body() + "\n"

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content)


_PROFILE_SECTION_RE = re.compile(r"^#\s*---\s*Profile:.*---\s*$")


def _extract_base_config(text: str) -> str:
    """Extract the base config (everything before the profile section)."""
    lines = text.splitlines()
    base_lines = []
    for line in lines:
        # Skip rice header lines
        if (
            _CURRENT_RE.match(line)
            or "Managed by ghostty-rice" in line
            or ("Do not edit the profile section" in line)
        ):
            continue
        # Stop at profile section
        if _PROFILE_SECTION_RE.match(line):
            break
        base_lines.append(line)
    return "\n".join(base_lines)
