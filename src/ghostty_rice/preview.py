"""Terminal color preview for profiles."""

from __future__ import annotations

import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Standard ANSI color names
_ANSI_NAMES = [
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "bright black",
    "bright red",
    "bright green",
    "bright yellow",
    "bright blue",
    "bright magenta",
    "bright cyan",
    "bright white",
]


def preview_profile(name: str, config_body: str, description: str, console: Console) -> None:
    """Render a color preview of a profile in the terminal."""
    # Parse palette and key visual settings from config
    palette: dict[int, str] = {}
    bg = None
    fg = None
    theme_name = None
    opacity = None
    blur = None
    titlebar = None
    cursor = None
    padding_x = None
    padding_y = None

    for line in config_body.splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue

        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()

        if key == "theme":
            theme_name = val
        elif key == "background":
            bg = val
        elif key == "foreground":
            fg = val
        elif key == "background-opacity":
            opacity = val
        elif key == "background-blur":
            blur = val
        elif key == "macos-titlebar-style":
            titlebar = val
        elif key == "cursor-style":
            cursor = val
        elif key == "window-padding-x":
            padding_x = val
        elif key == "window-padding-y":
            padding_y = val
        elif key.startswith("palette"):
            m = re.match(r"palette\s*=\s*(\d+)=(#[0-9a-fA-F]{6})", line)
            if m:
                palette[int(m.group(1))] = m.group(2)

    # Build info table
    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold cyan")
    info.add_column()

    if theme_name:
        info.add_row("Theme", theme_name)
    if bg:
        info.add_row("Background", bg)
    if fg:
        info.add_row("Foreground", fg)
    if opacity:
        info.add_row("Opacity", opacity)
    if blur:
        info.add_row("Blur", blur)
    if titlebar:
        info.add_row("Titlebar", titlebar)
    if cursor:
        info.add_row("Cursor", cursor)
    if padding_x or padding_y:
        info.add_row("Padding", f"x={padding_x or '?'}  y={padding_y or '?'}")

    # Build color swatches if palette available
    color_text = Text()
    if palette:
        for i in range(16):
            color = palette.get(i)
            if color:
                color_text.append("  \u2588\u2588  ", style=color)
            else:
                color_text.append("  ??  ", style="dim")
            if i == 7:
                color_text.append("\n")

    # Compose panel
    content = Text()
    if description:
        content.append(description + "\n\n", style="italic")

    panel_content = info
    if palette:
        combined = Table.grid()
        combined.add_row(info)
        combined.add_row(Text(""))
        combined.add_row(Text("Palette:", style="bold"))
        combined.add_row(color_text)
        panel_content = combined

    console.print(
        Panel(
            panel_content,
            title=f"[bold]{name}[/bold]",
            subtitle=description if description else None,
            border_style="bright_blue",
            padding=(1, 2),
        )
    )
