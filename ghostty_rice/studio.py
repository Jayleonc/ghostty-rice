"""Theme studio data and profile builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ghostty_rice.paths import user_profiles_dir


@dataclass(frozen=True)
class StudioTheme:
    """A dark-theme preset for studio mode."""

    name: str
    description: str
    ghostty_theme: str | None
    accent: str
    background: str
    foreground: str
    contrast: int = 60  # legacy, no longer used in generated profiles
    translucent: bool = True


_STUDIO_THEMES: list[StudioTheme] = [
    StudioTheme(
        name="Absolutely",
        description="Graphite + copper accent",
        ghostty_theme=None,
        accent="#CC7D5E",
        background="#2D2D2B",
        foreground="#F9F9F7",
        contrast=60,
        translucent=True,
    ),
    StudioTheme(
        name="Ayu",
        description="Ayu Mirage base with warm yellow accent",
        ghostty_theme="Ayu Mirage",
        accent="#E7C664",
        background="#1F2430",
        foreground="#D9D7CE",
        contrast=58,
        translucent=False,
    ),
    StudioTheme(
        name="Catppuccin",
        description="Mocha base with muted mauve accent",
        ghostty_theme="Catppuccin Mocha",
        accent="#CBA6F7",
        background="#1E1E2E",
        foreground="#CDD6F4",
        contrast=58,
        translucent=False,
    ),
    StudioTheme(
        name="Codex",
        description="Dark neutral with electric blue accent",
        ghostty_theme="Atom One Dark",
        accent="#2998FF",
        background="#22252B",
        foreground="#E8EDF7",
        contrast=60,
        translucent=True,
    ),
    StudioTheme(
        name="Dracula",
        description="Theatrical purple dark with neon pink accent",
        ghostty_theme="Dracula",
        accent="#FF79C6",
        background="#282A36",
        foreground="#F8F8F2",
        contrast=58,
        translucent=False,
    ),
    StudioTheme(
        name="Everforest",
        description="Soft woodland dark for low eye fatigue",
        ghostty_theme="Everforest Dark Hard",
        accent="#A7C080",
        background="#272E33",
        foreground="#D3C6AA",
        contrast=55,
        translucent=False,
    ),
    StudioTheme(
        name="GitHub",
        description="GitHub dark dimmed style with cool blue accent",
        ghostty_theme="GitHub Dark Dimmed",
        accent="#58A6FF",
        background="#22272E",
        foreground="#C9D1D9",
        contrast=58,
        translucent=False,
    ),
    StudioTheme(
        name="Gruvbox",
        description="Earth-tone retro dark with olive accent",
        ghostty_theme="Gruvbox Dark Hard",
        accent="#8EC07C",
        background="#1D2021",
        foreground="#EBDBB2",
        contrast=56,
        translucent=False,
    ),
    StudioTheme(
        name="Linear",
        description="Minimal graphite with quiet blue highlight",
        ghostty_theme=None,
        accent="#7AA2F7",
        background="#1E2025",
        foreground="#D7DBE4",
        contrast=60,
        translucent=True,
    ),
    StudioTheme(
        name="Sentry",
        description="Deep indigo with observability red accent",
        ghostty_theme=None,
        accent="#7C4DFF",
        background="#161A24",
        foreground="#D6DEEB",
        contrast=62,
        translucent=True,
    ),
    StudioTheme(
        name="Solarized",
        description="Solarized dark with restrained contrast",
        ghostty_theme="Solarized Dark Higher Contrast",
        accent="#268BD2",
        background="#002B36",
        foreground="#93A1A1",
        contrast=54,
        translucent=False,
    ),
    StudioTheme(
        name="Temple",
        description="Dark shrine green with ember orange accent",
        ghostty_theme=None,
        accent="#C8A95A",
        background="#101B18",
        foreground="#C8D4CC",
        contrast=57,
        translucent=True,
    ),
    StudioTheme(
        name="Tokyo Night",
        description="TokyoNight Storm with blue-violet accent",
        ghostty_theme="TokyoNight Storm",
        accent="#7AA2F7",
        background="#24283B",
        foreground="#C0CAF5",
        contrast=58,
        translucent=False,
    ),
    StudioTheme(
        name="VS Code Plus",
        description="One Dark-like baseline with stronger blue accent",
        ghostty_theme="Atom One Dark",
        accent="#61AFEF",
        background="#282C34",
        foreground="#ABB2BF",
        contrast=58,
        translucent=False,
    ),
]


def list_studio_themes() -> list[StudioTheme]:
    """Return all studio themes."""
    return _STUDIO_THEMES[:]


def get_studio_theme(name: str) -> StudioTheme | None:
    """Get a studio theme by exact name."""
    for theme in _STUDIO_THEMES:
        if theme.name == name:
            return theme
    return None


def default_studio_theme() -> StudioTheme:
    """Return default theme for studio mode."""
    return _STUDIO_THEMES[0]


def accent_swatches() -> list[str]:
    """Return unique accent swatches from studio themes."""
    seen: set[str] = set()
    colors: list[str] = []
    for theme in _STUDIO_THEMES:
        key = theme.accent.upper()
        if key in seen:
            continue
        seen.add(key)
        colors.append(key)
    return colors


def background_swatches() -> list[str]:
    """Return unique background swatches from studio themes."""
    seen: set[str] = set()
    colors: list[str] = []
    for theme in _STUDIO_THEMES:
        key = theme.background.upper()
        if key in seen:
            continue
        seen.add(key)
        colors.append(key)
    return colors


def foreground_swatches() -> list[str]:
    """Return unique foreground swatches from studio themes."""
    seen: set[str] = set()
    colors: list[str] = []
    for theme in _STUDIO_THEMES:
        key = theme.foreground.upper()
        if key in seen:
            continue
        seen.add(key)
        colors.append(key)
    return colors


def build_studio_profile_body(
    *,
    theme: StudioTheme,
    accent: str,
    background: str,
    foreground: str,
    translucent: bool,
) -> str:
    """Build Ghostty config body for studio selections."""
    accent_hex = _normalize_hex(accent)
    background_hex = _normalize_hex(background)
    foreground_hex = _normalize_hex(foreground)
    selection_background = _blend_hex(accent_hex, background_hex, 0.35)
    opacity = "0.96" if translucent else "1.0"

    lines: list[str] = []
    if theme.ghostty_theme:
        lines.append(f"theme = {theme.ghostty_theme}")
    lines.extend(
        [
            f"background = {background_hex}",
            f"foreground = {foreground_hex}",
            f"cursor-color = {accent_hex}",
            f"selection-background = {selection_background}",
            f"selection-foreground = {foreground_hex}",
            f"background-opacity = {opacity}",
            "window-padding-x = 14",
            "window-padding-y = 10",
            "window-padding-color = extend",
            "macos-titlebar-style = transparent",
            "macos-icon = glass",
            "cursor-style = block",
            "cursor-style-blink = false",
            "unfocused-split-opacity = 0.80",
        ]
    )
    if translucent:
        lines.append("background-blur = macos-glass-regular")

    return "\n".join(lines).strip() + "\n"


def write_studio_profile(body: str, *, profile_name: str = "Studio Live") -> Path:
    """Write studio profile under user profiles directory and return path."""
    target = user_profiles_dir() / profile_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.strip() + "\n")
    return target


def _normalize_hex(value: str) -> str:
    text = value.strip()
    if not text.startswith("#"):
        text = f"#{text}"
    if len(text) != 7:
        raise ValueError(f"Invalid hex color: {value}")
    return text.upper()


def _blend_hex(foreground: str, background: str, ratio: float) -> str:
    fr, fg, fb = _hex_to_rgb(foreground)
    br, bg, bb = _hex_to_rgb(background)
    alpha = max(0.0, min(1.0, ratio))
    red = int(round(fr * alpha + br * (1 - alpha)))
    green = int(round(fg * alpha + bg * (1 - alpha)))
    blue = int(round(fb * alpha + bb * (1 - alpha)))
    return f"#{red:02X}{green:02X}{blue:02X}"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    normalized = _normalize_hex(value)
    return (
        int(normalized[1:3], 16),
        int(normalized[3:5], 16),
        int(normalized[5:7], 16),
    )
