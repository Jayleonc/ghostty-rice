"""Font presets and helpers."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ghostty_rice.paths import ghostty_config_file
from ghostty_rice.profile import update_base_settings

_FONT_FAMILY_RE = re.compile(r"^\s*font-family\s*=\s*(.+?)\s*$")


@dataclass(frozen=True)
class FontPreset:
    """A curated font configuration preset."""

    name: str
    description: str
    settings: dict[str, str]


_FONT_PRESETS: list[FontPreset] = [
    FontPreset(
        name="JetBrains Mono",
        description="Balanced default — excellent readability and code density",
        settings={
            "font-family": '"JetBrains Mono"',
            "font-size": "13",
            "adjust-cell-height": "8%",
            "font-thicken": "true",
        },
    ),
    FontPreset(
        name="SF Mono",
        description="macOS native classic — crisp system-level rendering",
        settings={
            "font-family": '"SF Mono"',
            "font-size": "13",
            "adjust-cell-height": "8%",
            "font-thicken": "true",
        },
    ),
    FontPreset(
        name="Menlo",
        description="macOS built-in fallback — stable and universally available",
        settings={
            "font-family": '"Menlo"',
            "font-size": "13",
            "adjust-cell-height": "8%",
            "font-thicken": "true",
        },
    ),
    FontPreset(
        name="Maple Mono",
        description="Sharper geometry — compact look with clear symbols",
        settings={
            "font-family": '"Maple Mono"',
            "font-size": "13",
            "adjust-cell-height": "8%",
            "font-thicken": "true",
        },
    ),
    FontPreset(
        name="Berkeley Mono",
        description="Editorial style — smooth text color for long sessions",
        settings={
            "font-family": '"Berkeley Mono"',
            "font-size": "13",
            "adjust-cell-height": "10%",
            "font-thicken": "true",
        },
    ),
    FontPreset(
        name="Monaspace Neon",
        description="Modern engineering vibe — high legibility at small sizes",
        settings={
            "font-family": '"Monaspace Neon"',
            "font-size": "13",
            "adjust-cell-height": "9%",
            "font-thicken": "true",
        },
    ),
    FontPreset(
        name="Iosevka Term",
        description="Density mode — maximal information per column",
        settings={
            "font-family": '"Iosevka Term"',
            "font-size": "12.5",
            "adjust-cell-height": "6%",
            "font-thicken": "true",
        },
    ),
    FontPreset(
        name="Fira Code",
        description="Ligature-friendly developer classic",
        settings={
            "font-family": '"Fira Code"',
            "font-size": "13",
            "adjust-cell-height": "8%",
            "font-thicken": "true",
        },
    ),
]


def list_font_presets() -> list[FontPreset]:
    """Return all curated font presets."""
    return _FONT_PRESETS[:]


def get_font_preset(name: str) -> FontPreset | None:
    """Return a font preset by exact name."""
    for preset in _FONT_PRESETS:
        if preset.name == name:
            return preset
    return None


def apply_font_preset(preset: FontPreset) -> None:
    """Apply a font preset into base config."""
    update_base_settings(preset.settings)


def current_font_family() -> str | None:
    """Return current `font-family` from config, if present."""
    config = ghostty_config_file()
    if not config.exists():
        return None

    for line in config.read_text().splitlines():
        m = _FONT_FAMILY_RE.match(line)
        if not m:
            continue
        value = m.group(1).strip()
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        return value
    return None


def installed_font_families() -> set[str]:
    """Return installed font families discoverable by Ghostty."""
    binary = _ghostty_binary()
    if not binary:
        return set()

    try:
        result = subprocess.run(
            [binary, "+list-fonts"],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return set()

    output = result.stdout
    families: set[str] = set()
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.lower().startswith("error:"):
            continue
        if raw.startswith(" ") or raw.startswith("\t"):
            continue
        families.add(line)
    return families


def _ghostty_binary() -> str | None:
    """Return path to Ghostty binary for helper actions."""
    if platform.system() == "Darwin":
        mac_binary = Path("/Applications/Ghostty.app/Contents/MacOS/ghostty")
        if mac_binary.exists():
            return str(mac_binary)
    return shutil.which("ghostty")
