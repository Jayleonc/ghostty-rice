"""Profile loading, listing, and application."""

from __future__ import annotations

import platform as _platform
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ghostty_rice.paths import bundled_presets_dir, ghostty_config_file, user_profiles_dir

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]

_CURRENT_RE = re.compile(r"^#\s*rice-profile:\s*(.+)$")
_PROFILE_SECTION_RE = re.compile(r"^#\s*---\s*Profile:.*---\s*$")
_SETTING_KEY_RE = re.compile(r"^\s*([a-zA-Z0-9-]+)\s*=")


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


def _upsert_base_settings(base_text: str, settings: dict[str, str]) -> str:
    """Return base config text with setting keys replaced by `settings`."""
    keys = set(settings.keys())
    lines: list[str] = []
    for line in base_text.splitlines():
        m = _SETTING_KEY_RE.match(line)
        if m and m.group(1) in keys:
            continue
        lines.append(line)

    while lines and not lines[-1].strip():
        lines.pop()
    if lines:
        lines.append("")

    for key, value in settings.items():
        lines.append(f"{key} = {value}")

    return "\n".join(lines)


def update_base_settings(settings: dict[str, str]) -> None:
    """Update base (non-profile) config settings and preserve active profile."""
    config_path = ghostty_config_file()
    existing = config_path.read_text() if config_path.exists() else ""
    base = _extract_base_config(existing) if existing else ""
    updated_base = _upsert_base_settings(base, settings)

    current_name = get_current_profile()
    current_profile = get_profile(current_name) if current_name else None

    if current_profile:
        content = _HEADER.format(name=current_profile.name)
        if updated_base.strip():
            content += updated_base.strip() + "\n\n"
        content += f"# --- Profile: {current_profile.name} ---\n"
        content += current_profile.config_body() + "\n"
    else:
        content = updated_base.strip() + ("\n" if updated_base.strip() else "")

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content)


# ---------------------------------------------------------------------------
# Config validation & repair
# ---------------------------------------------------------------------------

_THEME_RE = re.compile(r"^\s*theme\s*=\s*(.+)$", re.MULTILINE)


def _ghostty_theme_dirs() -> list[Path]:
    """Return directories where Ghostty themes can be found."""
    dirs: list[Path] = []
    if _platform.system() == "Darwin":
        bundled = Path(
            "/Applications/Ghostty.app/Contents/Resources/ghostty/themes"
        )
        if bundled.is_dir():
            dirs.append(bundled)
    from ghostty_rice.paths import ghostty_config_dir as _config_dir

    user_themes = _config_dir() / "themes"
    if user_themes.is_dir():
        dirs.append(user_themes)
    return dirs


def _available_ghostty_themes() -> set[str]:
    """Return the set of theme names Ghostty can resolve."""
    names: set[str] = set()
    for d in _ghostty_theme_dirs():
        for f in d.iterdir():
            if f.is_file() and not f.name.startswith("."):
                names.add(f.name)
    return names


@dataclass
class ConfigIssue:
    """A single config validation issue."""

    key: str
    value: str
    message: str
    fixable: bool = True


def validate_config() -> list[ConfigIssue]:
    """Check the current Ghostty config for common issues."""
    config_path = ghostty_config_file()
    if not config_path.exists():
        return []

    text = config_path.read_text()
    issues: list[ConfigIssue] = []

    # Check theme references
    available = _available_ghostty_themes()
    if available:
        for m in _THEME_RE.finditer(text):
            theme_name = m.group(1).strip()
            if theme_name not in available:
                issues.append(
                    ConfigIssue(
                        key="theme",
                        value=theme_name,
                        message=(
                            f'theme "{theme_name}" not found in Ghostty'
                        ),
                    )
                )

    return issues


def fix_config_issues(issues: list[ConfigIssue]) -> list[str]:
    """Attempt to fix config issues. Returns list of actions taken."""
    config_path = ghostty_config_file()
    if not config_path.exists() or not issues:
        return []

    text = config_path.read_text()
    actions: list[str] = []

    for issue in issues:
        if not issue.fixable:
            continue
        if issue.key == "theme":
            # Remove the invalid theme line — Ghostty will use defaults
            pattern = re.compile(
                rf"^\s*theme\s*=\s*{re.escape(issue.value)}\s*$",
                re.MULTILINE,
            )
            new_text = pattern.sub("", text)
            if new_text != text:
                text = new_text
                actions.append(
                    f'Removed invalid theme = {issue.value}'
                )

    if actions:
        # Clean up consecutive blank lines left by removals
        text = re.sub(r"\n{3,}", "\n\n", text)
        config_path.write_text(text)

    return actions


def reset_to_profile(name: str) -> tuple[bool, str]:
    """Reset config to a known-good builtin profile, preserving base settings.

    Returns (success, message).
    """
    profile = get_profile(name)
    if profile is None:
        available = [p.name for p in list_profiles()]
        return False, (
            f'Profile "{name}" not found. '
            f"Available: {', '.join(available)}"
        )
    apply_profile(profile)
    return True, f'Config reset to "{name}"'
