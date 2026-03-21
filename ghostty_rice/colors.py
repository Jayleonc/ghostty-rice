"""Color palette display for profiles."""

from __future__ import annotations

import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ghostty_rice.profile import Profile

# Known theme palettes — representative colors for popular Ghostty themes.
# Each entry maps a theme name to (bg, fg, accent, 8 sample colors).
_THEME_PALETTES: dict[str, dict[str, str]] = {
    "Catppuccin Mocha": {
        "bg": "#1e1e2e",
        "fg": "#cdd6f4",
        "red": "#f38ba8",
        "green": "#a6e3a1",
        "yellow": "#f9e2af",
        "blue": "#89b4fa",
        "magenta": "#cba6f7",
        "cyan": "#94e2d5",
        "accent": "#b4befe",
    },
    "Catppuccin Macchiato": {
        "bg": "#24273a",
        "fg": "#cad3f5",
        "red": "#ed8796",
        "green": "#a6da95",
        "yellow": "#eed49f",
        "blue": "#8aadf4",
        "magenta": "#c6a0f6",
        "cyan": "#8bd5ca",
        "accent": "#b7bdf8",
    },
    "Catppuccin Latte": {
        "bg": "#eff1f5",
        "fg": "#4c4f69",
        "red": "#d20f39",
        "green": "#40a02b",
        "yellow": "#df8e1d",
        "blue": "#1e66f5",
        "magenta": "#8839ef",
        "cyan": "#179299",
        "accent": "#7287fd",
    },
    "Builtin Tango Dark": {
        "bg": "#2e3436",
        "fg": "#d3d7cf",
        "red": "#cc0000",
        "green": "#4e9a06",
        "yellow": "#c4a000",
        "blue": "#3465a4",
        "magenta": "#75507b",
        "cyan": "#06989a",
        "accent": "#729fcf",
    },
    "Nord": {
        "bg": "#2e3440",
        "fg": "#d8dee9",
        "red": "#bf616a",
        "green": "#a3be8c",
        "yellow": "#ebcb8b",
        "blue": "#81a1c1",
        "magenta": "#b48ead",
        "cyan": "#88c0d0",
        "accent": "#5e81ac",
    },
    "Atom One Dark": {
        "bg": "#282c34",
        "fg": "#abb2bf",
        "red": "#e06c75",
        "green": "#98c379",
        "yellow": "#e5c07b",
        "blue": "#61afef",
        "magenta": "#c678dd",
        "cyan": "#56b6c2",
        "accent": "#61afef",
    },
    "TokyoNight": {
        "bg": "#1a1b26",
        "fg": "#c0caf5",
        "red": "#f7768e",
        "green": "#9ece6a",
        "yellow": "#e0af68",
        "blue": "#7aa2f7",
        "magenta": "#bb9af7",
        "cyan": "#7dcfff",
        "accent": "#7aa2f7",
    },
    "Gruvbox Dark Hard": {
        "bg": "#1d2021",
        "fg": "#ebdbb2",
        "red": "#fb4934",
        "green": "#b8bb26",
        "yellow": "#fabd2f",
        "blue": "#83a598",
        "magenta": "#d3869b",
        "cyan": "#8ec07c",
        "accent": "#fe8019",
    },
    "Dracula": {
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "red": "#ff5555",
        "green": "#50fa7b",
        "yellow": "#f1fa8c",
        "blue": "#6272a4",
        "magenta": "#ff79c6",
        "cyan": "#8be9fd",
        "accent": "#bd93f9",
    },
}


def _parse_config(config_body: str) -> dict[str, str]:
    """Extract key visual settings from a profile config."""
    result: dict[str, str] = {}
    palette: dict[int, str] = {}

    for line in config_body.splitlines():
        line = line.strip()
        if line.startswith("#") or not line or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()

        if key in ("theme", "background", "foreground", "background-opacity"):
            result[key] = val
        elif key.startswith("palette"):
            m = re.match(r"palette\s*=\s*(\d+)=(#[0-9a-fA-F]{6})", line)
            if m:
                palette[int(m.group(1))] = m.group(2)

    if palette:
        result["_has_palette"] = "true"
        for idx, color in palette.items():
            result[f"_palette_{idx}"] = color

    return result


def _get_theme_colors(theme_name: str) -> dict[str, str] | None:
    """Look up known colors for a theme name."""
    # Handle light:X,dark:Y format — use the dark variant
    if "," in theme_name:
        for part in theme_name.split(","):
            part = part.strip()
            if part.startswith("dark:"):
                theme_name = part[5:]
                break
            elif not part.startswith("light:"):
                theme_name = part
                break

    return _THEME_PALETTES.get(theme_name)


def _render_swatch(color: str) -> Text:
    """Render a small color swatch."""
    return Text(" \u2588\u2588 ", style=color)


def show_profile_colors(profile: Profile, console: Console) -> None:
    """Display color palette for a single profile."""
    config = _parse_config(profile.config_body())
    theme_name = config.get("theme", "")
    theme_colors = _get_theme_colors(theme_name) if theme_name else None

    grid = Table.grid(padding=(0, 1))
    grid.add_column(style="bold cyan", min_width=12)
    grid.add_column()

    grid.add_row("Theme", theme_name or "(custom)")
    if config.get("background"):
        grid.add_row("Background", config["background"])
    if config.get("foreground"):
        grid.add_row("Foreground", config["foreground"])
    if config.get("background-opacity"):
        grid.add_row("Opacity", config["background-opacity"])

    # Color strip
    if theme_colors:
        strip = Text()
        bg_swatch = Text("  \u2588\u2588  ", style=f"on {theme_colors['bg']}")
        fg_swatch = Text("  Aa  ", style=f"{theme_colors['fg']} on {theme_colors['bg']}")
        strip.append_text(bg_swatch)
        strip.append(" ")
        strip.append_text(fg_swatch)
        strip.append("  ")
        for key in ("red", "green", "yellow", "blue", "magenta", "cyan"):
            strip.append_text(Text(" \u2588\u2588 ", style=theme_colors[key]))
        grid.add_row("", Text())
        grid.add_row("Palette", strip)

    subtitle = profile.description if profile.description else None
    console.print(
        Panel(
            grid,
            title=f"[bold]{profile.name}[/bold]",
            subtitle=subtitle,
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def show_all_colors(profiles: list[Profile], console: Console) -> None:
    """Display a comparison table of all profiles' color palettes."""
    table = Table(
        title="Profile Color Comparison",
        border_style="bright_blue",
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("Profile", style="bold", min_width=18)
    table.add_column("Theme", min_width=20)
    table.add_column("Opacity", justify="center", min_width=7)
    table.add_column("Palette", min_width=42)

    for profile in profiles:
        config = _parse_config(profile.config_body())
        theme_name = config.get("theme", "(custom)")
        opacity = config.get("background-opacity", "-")
        theme_colors = _get_theme_colors(theme_name) if theme_name else None

        strip = Text()
        if theme_colors:
            strip.append_text(Text(" \u2588\u2588 ", style=f"on {theme_colors['bg']}"))
            strip.append_text(Text(" Aa ", style=f"{theme_colors['fg']} on {theme_colors['bg']}"))
            for key in ("red", "green", "yellow", "blue", "magenta", "cyan"):
                strip.append_text(Text(" \u2588\u2588 ", style=theme_colors[key]))
        else:
            strip.append("(theme colors not indexed)", style="dim")

        table.add_row(profile.name, theme_name, opacity, strip)

    console.print(table)
