"""Profile loading, listing, and application."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ghostty_rice.paths import bundled_presets_dir, ghostty_config_file, user_profiles_dir

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

_CURRENT_RE = re.compile(r"^#\s*rice-profile:\s*(.+)$")
_PROFILE_SECTION_RE = re.compile(r"^#\s*---\s*Profile:.*---\s*$")


@dataclass
class Profile:
    """A Ghostty visual profile."""

    name: str
    description: str
    author: str
    source: str  # "builtin" or "user"
    path: Path
    tags: list[str] = field(default_factory=list)

    def config_body(self) -> str:
        """Return the raw Ghostty config content."""
        return self.path.read_text().strip()


def _load_manifest(directory: Path) -> dict[str, dict[str, object]]:
    """Load manifest.toml from a directory, returning profile metadata."""
    manifest_path = directory / "manifest.toml"
    if not manifest_path.exists():
        return {}
    with open(manifest_path, "rb") as f:
        data = tomllib.load(f)
    profiles: dict[str, dict[str, object]] = data.get("profiles", {})
    return profiles


def _scan_profiles(directory: Path, source: str) -> list[Profile]:
    """Scan a directory for profile files (no extension, like Ghostty themes)."""
    if not directory.exists():
        return []

    manifest = _load_manifest(directory)
    profiles = []

    for f in sorted(directory.iterdir()):
        # Skip files with extensions (manifest.toml, __init__.py, etc.)
        if f.suffix or f.name.startswith((".", "_")):
            continue
        if not f.is_file():
            continue

        meta = manifest.get(f.name, {})
        profiles.append(
            Profile(
                name=f.name,
                description=str(meta.get("description", "")),
                author=str(meta.get("author", "")),
                source=source,
                path=f,
                tags=[str(t) for t in (meta.get("tags") or [])],  # type: ignore[attr-defined]
            )
        )

    return profiles


def list_profiles() -> list[Profile]:
    """List all available profiles (builtin + user), user profiles override builtin."""
    profiles: dict[str, Profile] = {}

    for p in _scan_profiles(bundled_presets_dir(), source="builtin"):
        profiles[p.name] = p

    for p in _scan_profiles(user_profiles_dir(), source="user"):
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


_HEADER = """\
# rice-profile: {name}
# Managed by ghostty-rice — https://github.com/jayleonc/ghostty-rice

"""


def apply_profile(profile: Profile) -> None:
    """Write a profile to the Ghostty config file.

    Preserves user's base config (shell, font, keybinds, etc.) and replaces
    only the profile section.
    """
    config_path = ghostty_config_file()

    if config_path.exists():
        base = _extract_base_config(config_path.read_text())
    else:
        base = ""

    content = _HEADER.format(name=profile.name)
    if base.strip():
        content += base.strip() + "\n\n"
    content += f"# --- Profile: {profile.name} ---\n"
    content += profile.config_body() + "\n"

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content)


def _extract_base_config(text: str) -> str:
    """Extract the base config (everything before the profile section)."""
    lines = text.splitlines()
    base_lines = []
    for line in lines:
        if _CURRENT_RE.match(line) or "Managed by ghostty-rice" in line:
            continue
        if _PROFILE_SECTION_RE.match(line):
            break
        base_lines.append(line)
    return "\n".join(base_lines)
