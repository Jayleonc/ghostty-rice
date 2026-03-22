"""CLI entry point for ghostty-rice."""

from __future__ import annotations

import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass

import click
from rich.console import Console
from rich.table import Table

from ghostty_rice import __version__
from ghostty_rice.colors import show_all_colors, show_profile_colors
from ghostty_rice.fonts import (
    FontPreset,
    apply_font_preset,
    build_font_candidates,
    current_font_family,
    current_font_size,
    installed_font_families,
)
from ghostty_rice.paths import ghostty_config_dir, ghostty_config_file, user_profiles_dir
from ghostty_rice.platform import (
    get_platform,
    has_xterm_ghostty_terminfo,
    install_xterm_ghostty_terminfo,
)
from ghostty_rice.preview import preview_profile
from ghostty_rice.profile import (
    Profile,
    apply_profile,
    get_current_profile,
    get_profile,
    list_profiles,
)
from ghostty_rice.prompt import (
    PromptPreset,
    apply_prompt_preset,
    current_prompt_preset_name,
    detected_shell_name,
    ensure_prompt_bootstrap,
    has_prompt_bootstrap,
    list_prompt_presets,
    prompt_bootstrap_line,
    prompt_runtime_active,
    zsh_available,
)
from ghostty_rice.reload import reload_ghostty
from ghostty_rice.studio import (
    StudioTheme,
    accent_swatches,
    background_swatches,
    build_studio_profile_body,
    default_studio_theme,
    foreground_swatches,
    list_studio_themes,
    write_studio_profile,
)

console = Console()
_PREVIEW_MIN_INTERVAL = 0.12
_STUDIO_CONTRAST_VALUES = [45, 50, 55, 60, 65, 70, 75]
_STUDIO_MIN_FONT_SIZE = 10.0
_STUDIO_MAX_FONT_SIZE = 18.0
_STUDIO_FONT_STEP = 0.5
_STUDIO_PROFILE_NAME = "Studio Live"


@dataclass
class _StudioState:
    theme_index: int
    accent_index: int
    background_index: int
    foreground_index: int
    font_index: int
    font_size: float
    contrast_index: int
    translucent: bool


@dataclass
class _SwitchUiState:
    tab: int = 0
    theme_cursor: int = 0
    control_cursor: int = 0
    font_cursor: int = 0
    theme_filter: str = ""
    font_filter: str = ""


def _render_switch_table(
    profiles: list[Profile],
    current_index: int,
    current_name: str | None,
    status_ok: bool,
    status_message: str | None,
) -> None:
    """Render interactive switcher table."""
    table = Table(
        title="Interactive Profile Switcher",
        border_style="bright_blue",
        show_lines=False,
    )
    table.add_column("", width=2)
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Description")

    for idx, profile in enumerate(profiles):
        marker = "➤" if idx == current_index else ("•" if profile.name == current_name else " ")
        table.add_row(marker, str(idx + 1), profile.name, profile.description)

    console.print(table)
    console.print(
        "[dim]Controls: ↑/↓ or j/k to move (live preview), Enter to confirm, q to cancel[/dim]"
    )
    if status_message:
        style = "green" if status_ok else "yellow"
        console.print(f"[{style}]{status_message}[/{style}]")


def _read_switch_action() -> str:
    """Read one keyboard action for interactive profile switching."""
    char = click.getchar()
    if char in ("\r", "\n"):
        return "apply"
    if char in ("q", "Q"):
        return "cancel"
    if char == "\t":
        return "toggle_focus"
    if char == "1":
        return "tab_1"
    if char == "2":
        return "tab_2"
    if char == "3":
        return "tab_3"
    if char in ("/", "\x06"):
        return "search"
    if char in ("i", "I"):
        return "install"
    if char in ("u", "U"):
        return "reset"
    if char in ("x", "X"):
        return "clear_filter"
    if char in ("k", "K"):
        return "up"
    if char in ("j", "J"):
        return "down"
    if char in ("+", "="):
        return "bigger"
    if char == "-":
        return "smaller"
    if char in ("l", "L"):
        return "bigger"
    if char in ("h", "H"):
        return "smaller"
    if char in ("\x1b[A",):
        return "up"
    if char in ("\x1b[B",):
        return "down"
    if char in ("\x1b[C",):
        return "bigger"
    if char in ("\x1b[D",):
        return "smaller"
    if char == "\x1b":
        seq1 = click.getchar()
        seq2 = click.getchar()
        if seq1 == "[" and seq2 == "A":
            return "up"
        if seq1 == "[" and seq2 == "B":
            return "down"
        if seq1 == "[" and seq2 == "C":
            return "bigger"
        if seq1 == "[" and seq2 == "D":
            return "smaller"
        return "noop"
    return "noop"


def _choose_profile_interactively(
    profiles: list[Profile],
    current_name: str | None,
    on_preview: Callable[[Profile], tuple[bool, str]] | None = None,
) -> Profile | None:
    """Return a user-selected profile via keyboard-driven interactive UI."""
    if not profiles:
        return None

    if current_name:
        current_index = next(
            (idx for idx, profile in enumerate(profiles) if profile.name == current_name),
            0,
        )
    else:
        current_index = 0

    status_ok = True
    status_message: str | None = None
    while True:
        console.clear()
        _render_switch_table(
            profiles,
            current_index,
            current_name,
            status_ok=status_ok,
            status_message=status_message,
        )
        action = _read_switch_action()
        if action == "up":
            current_index = (current_index - 1) % len(profiles)
            if on_preview:
                status_ok, status_message = on_preview(profiles[current_index])
        elif action == "down":
            current_index = (current_index + 1) % len(profiles)
            if on_preview:
                status_ok, status_message = on_preview(profiles[current_index])
        elif action == "apply":
            console.clear()
            return profiles[current_index]
        elif action == "cancel":
            console.clear()
            return None


def _render_font_table(
    presets: list[FontPreset],
    current_index: int,
    current_family: str | None,
    current_size: float,
    status_ok: bool,
    status_message: str | None,
) -> None:
    """Render interactive font switcher table."""
    table = Table(
        title="Interactive Font Switcher",
        border_style="bright_blue",
        show_lines=False,
    )
    table.add_column("", width=2)
    table.add_column("#", style="dim", width=4)
    table.add_column("Preset", style="bold")
    table.add_column("Font Family")
    table.add_column("Size", width=6)
    table.add_column("Description")

    for idx, preset in enumerate(presets):
        family = preset.settings.get("font-family", "").strip('"')
        marker = "➤" if idx == current_index else ("•" if family == current_family else " ")
        size_value = (
            _format_font_size(current_size)
            if idx == current_index
            else preset.settings.get("font-size", "-")
        )
        table.add_row(
            marker,
            str(idx + 1),
            preset.name,
            family,
            size_value,
            preset.description,
        )

    console.print(table)
    console.print(
        "[dim]Controls: ↑/↓ or j/k move, +/- or ←/→ resize, "
        "Enter confirm, q cancel[/dim]"
    )
    if status_message:
        style = "green" if status_ok else "yellow"
        console.print(f"[{style}]{status_message}[/{style}]")


def _choose_font_interactively(
    presets: list[FontPreset],
    current_family: str | None,
    initial_size: float | None = None,
    on_preview: Callable[[FontPreset], tuple[bool, str]] | None = None,
) -> FontPreset | None:
    """Return a user-selected font preset via keyboard-driven interactive UI."""
    if not presets:
        return None

    if current_family:
        current_index = next(
            (
                idx
                for idx, preset in enumerate(presets)
                if preset.settings.get("font-family", "").strip('"') == current_family
            ),
            0,
        )
    else:
        current_index = 0
    current_size = initial_size or _preset_font_size(presets[current_index]) or 13.0

    status_ok = True
    status_message: str | None = None
    while True:
        console.clear()
        _render_font_table(
            presets,
            current_index,
            current_family,
            current_size,
            status_ok=status_ok,
            status_message=status_message,
        )
        action = _read_switch_action()
        if action == "up":
            current_index = (current_index - 1) % len(presets)
            if on_preview:
                status_ok, status_message = on_preview(
                    _preset_with_size(presets[current_index], current_size)
                )
        elif action == "down":
            current_index = (current_index + 1) % len(presets)
            if on_preview:
                status_ok, status_message = on_preview(
                    _preset_with_size(presets[current_index], current_size)
                )
        elif action == "bigger":
            current_size = min(current_size + 0.5, 24.0)
            if on_preview:
                status_ok, status_message = on_preview(
                    _preset_with_size(presets[current_index], current_size)
                )
        elif action == "smaller":
            current_size = max(current_size - 0.5, 9.0)
            if on_preview:
                status_ok, status_message = on_preview(
                    _preset_with_size(presets[current_index], current_size)
                )
        elif action == "apply":
            console.clear()
            return _preset_with_size(presets[current_index], current_size)
        elif action == "cancel":
            console.clear()
            return None


def _render_prompt_table(
    presets: list[PromptPreset],
    current_index: int,
    current_name: str | None,
) -> None:
    """Render interactive shell prompt preset table."""
    table = Table(
        title="Interactive Prompt Picker (zsh)",
        border_style="bright_blue",
        show_lines=False,
    )
    table.add_column("", width=2)
    table.add_column("#", style="dim", width=4)
    table.add_column("Preset", style="bold")
    table.add_column("Description")
    table.add_column("Sample", style="dim")

    for idx, preset in enumerate(presets):
        marker = "➤" if idx == current_index else ("•" if preset.name == current_name else " ")
        table.add_row(marker, str(idx + 1), preset.name, preset.description, preset.sample)

    console.print(table)
    console.print("[dim]Controls: ↑/↓ or j/k to move, Enter to confirm, q to cancel[/dim]")


def _choose_prompt_interactively(
    presets: list[PromptPreset],
    current_name: str | None,
) -> PromptPreset | None:
    """Return selected prompt preset via keyboard-driven UI."""
    if not presets:
        return None

    if current_name:
        current_index = next(
            (idx for idx, preset in enumerate(presets) if preset.name == current_name),
            0,
        )
    else:
        current_index = 0

    while True:
        console.clear()
        _render_prompt_table(
            presets,
            current_index,
            current_name,
        )
        action = _read_switch_action()
        if action == "up":
            current_index = (current_index - 1) % len(presets)
        elif action == "down":
            current_index = (current_index + 1) % len(presets)
        elif action == "apply":
            console.clear()
            return presets[current_index]
        elif action == "cancel":
            console.clear()
            return None


def _preset_font_size(preset: FontPreset) -> float | None:
    raw = preset.settings.get("font-size")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _format_font_size(size: float) -> str:
    text = f"{size:.1f}"
    return text.rstrip("0").rstrip(".")


def _preset_with_size(preset: FontPreset, size: float) -> FontPreset:
    settings = dict(preset.settings)
    settings["font-size"] = _format_font_size(size)
    return FontPreset(
        name=preset.name,
        description=preset.description,
        settings=settings,
    )


def _capture_config_snapshot() -> tuple[bool, str]:
    """Capture current config content for cancel/rollback flows."""
    config_path = ghostty_config_file()
    if config_path.exists():
        return True, config_path.read_text()
    return False, ""


def _restore_config_snapshot(existed: bool, content: str) -> None:
    """Restore config content from snapshot."""
    config_path = ghostty_config_file()
    if existed:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(content)
        return
    if config_path.exists():
        config_path.unlink()


def _studio_rows(
    state: _StudioState,
    themes: list[StudioTheme],
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
    fonts: list[FontPreset],
) -> list[tuple[str, str]]:
    font_family = fonts[state.font_index].settings.get("font-family", "").strip('"')
    return [
        ("Accent", _color_chip(accents[state.accent_index])),
        ("Background", _color_chip(backgrounds[state.background_index])),
        ("Foreground", _color_chip(foregrounds[state.foreground_index])),
        ("Code font", font_family),
        ("Code font size", _format_font_size(state.font_size)),
        ("Translucent glass", "On" if state.translucent else "Off"),
        ("Contrast", str(_STUDIO_CONTRAST_VALUES[state.contrast_index])),
    ]


def _color_chip(color: str) -> str:
    normalized = color.upper()
    return f"[on {normalized}]  [/on {normalized}] {normalized}"


def _filter_indices_by_name(names: list[str], query: str) -> list[int]:
    q = query.strip().casefold()
    if not q:
        return list(range(len(names)))
    return [idx for idx, name in enumerate(names) if q in name.casefold()]


def _render_studio_table(
    state: _StudioState,
    ui: _SwitchUiState,
    themes: list[StudioTheme],
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
    fonts: list[FontPreset],
    theme_indices: list[int],
    font_indices: list[int],
    status_ok: bool,
    status_message: str | None,
) -> None:
    active_theme = themes[state.theme_index].name
    active_font = _font_family_from_preset(fonts[state.font_index])
    tabs = (
        "[bold green]1 Themes[/bold green] | "
        "[bold green]2 Controls[/bold green] | "
        "[bold green]3 Fonts[/bold green]"
    )
    if ui.tab == 0:
        tabs = "[reverse] 1 Themes [/reverse] | 2 Controls | 3 Fonts"
    elif ui.tab == 1:
        tabs = "1 Themes | [reverse] 2 Controls [/reverse] | 3 Fonts"
    else:
        tabs = "1 Themes | 2 Controls | [reverse] 3 Fonts [/reverse]"

    header = (
        f"[bold]Rice Switch[/bold]  {tabs}\n"
        f"[dim]Theme:[/dim] {active_theme}    "
        f"[dim]Font:[/dim] {active_font} {_format_font_size(state.font_size)}"
    )
    console.print(header)

    if ui.tab == 0:
        table = Table(border_style="bright_blue", show_lines=False, title="Themes")
        table.add_column("", width=2)
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="bold")
        table.add_column("Description")
        if not theme_indices:
            table.add_row("", "-", "[dim]No match[/dim]", "[dim]Try another /search[/dim]")
        for pos, real_idx in enumerate(theme_indices):
            theme = themes[real_idx]
            marker = "➤" if pos == ui.theme_cursor else ("•" if real_idx == state.theme_index else " ")
            name = f"[bold]{theme.name}[/bold]" if real_idx == state.theme_index else theme.name
            table.add_row(marker, str(pos + 1), name, theme.description)
        if ui.theme_filter:
            table.caption = f"filter: {ui.theme_filter}"
        console.print(table)
    elif ui.tab == 1:
        table = Table(border_style="bright_blue", show_lines=False, title="Controls")
        table.add_column("", width=2)
        table.add_column("Setting", style="bold", width=20)
        table.add_column("Value")
        rows = _studio_rows(state, themes, accents, backgrounds, foregrounds, fonts)
        for idx, (label, value) in enumerate(rows):
            marker = "➤" if idx == ui.control_cursor else " "
            style = "bold" if idx == ui.control_cursor else "none"
            table.add_row(marker, label, f"[{style}]{value}[/{style}]")
        console.print(table)
    else:
        table = Table(border_style="bright_blue", show_lines=False, title="Fonts")
        table.add_column("", width=2)
        table.add_column("#", style="dim", width=4)
        table.add_column("Preset", style="bold")
        table.add_column("Family")
        if not font_indices:
            table.add_row("", "-", "[dim]No match[/dim]", "[dim]Try another /search[/dim]")
        for pos, real_idx in enumerate(font_indices):
            preset = fonts[real_idx]
            family = _font_family_from_preset(preset)
            marker = "➤" if pos == ui.font_cursor else ("•" if real_idx == state.font_index else " ")
            title = f"[bold]{preset.name}[/bold]" if real_idx == state.font_index else preset.name
            table.add_row(marker, str(pos + 1), title, family)
        if ui.font_filter:
            table.caption = f"filter: {ui.font_filter}"
        console.print(table)

    console.print(
        "[dim]Keys: 1/2/3 tab, j/k move, h/l or ←/→ adjust, / search, "
        "i apply now, u reset theme defaults, Enter confirm, q cancel[/dim]"
    )
    if status_message:
        style = "green" if status_ok else "yellow"
        console.print(f"[{style}]{status_message}[/{style}]")


def _row_cycle_index(current: int, delta: int, size: int) -> int:
    return (current + delta) % size


def _index_of_color(options: list[str], value: str) -> int:
    try:
        return options.index(value.upper())
    except ValueError:
        return 0


def _font_family_from_preset(preset: FontPreset) -> str:
    return preset.settings.get("font-family", "").strip('"')


def _closest_contrast_index(value: int) -> int:
    return min(
        range(len(_STUDIO_CONTRAST_VALUES)),
        key=lambda idx: abs(_STUDIO_CONTRAST_VALUES[idx] - value),
    )


def _apply_theme_defaults(
    state: _StudioState,
    *,
    themes: list[StudioTheme],
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
) -> None:
    theme = themes[state.theme_index]
    state.accent_index = _index_of_color(accents, theme.accent)
    state.background_index = _index_of_color(backgrounds, theme.background)
    state.foreground_index = _index_of_color(foregrounds, theme.foreground)
    state.translucent = theme.translucent
    state.contrast_index = _closest_contrast_index(theme.contrast)


def _adjust_studio_state(
    state: _StudioState,
    *,
    row: int,
    delta: int,
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
    fonts: list[FontPreset],
) -> bool:
    if row == 0:
        state.accent_index = _row_cycle_index(state.accent_index, delta, len(accents))
        return True
    if row == 1:
        state.background_index = _row_cycle_index(state.background_index, delta, len(backgrounds))
        return True
    if row == 2:
        state.foreground_index = _row_cycle_index(state.foreground_index, delta, len(foregrounds))
        return True
    if row == 3:
        state.font_index = _row_cycle_index(state.font_index, delta, len(fonts))
        return True
    if row == 4:
        updated = state.font_size + (_STUDIO_FONT_STEP * delta)
        clamped = max(_STUDIO_MIN_FONT_SIZE, min(_STUDIO_MAX_FONT_SIZE, updated))
        if clamped == state.font_size:
            return False
        state.font_size = clamped
        return True
    if row == 5:
        state.translucent = not state.translucent
        return True
    if row == 6:
        state.contrast_index = _row_cycle_index(
            state.contrast_index, delta, len(_STUDIO_CONTRAST_VALUES)
        )
        return True
    return False


def _studio_profile_signature(
    state: _StudioState,
    *,
    themes: list[StudioTheme],
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
    fonts: list[FontPreset],
) -> tuple[str, str, str, str, str, str, int, bool]:
    return (
        themes[state.theme_index].name,
        accents[state.accent_index],
        backgrounds[state.background_index],
        foregrounds[state.foreground_index],
        _font_family_from_preset(fonts[state.font_index]),
        _format_font_size(state.font_size),
        _STUDIO_CONTRAST_VALUES[state.contrast_index],
        state.translucent,
    )


def _build_studio_profile_body_from_state(
    state: _StudioState,
    *,
    themes: list[StudioTheme],
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
) -> str:
    theme = themes[state.theme_index]
    return build_studio_profile_body(
        theme=theme,
        accent=accents[state.accent_index],
        background=backgrounds[state.background_index],
        foreground=foregrounds[state.foreground_index],
        translucent=state.translucent,
        contrast=_STUDIO_CONTRAST_VALUES[state.contrast_index],
    )


def _run_studio_interactively(
    state: _StudioState,
    *,
    themes: list[StudioTheme],
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
    fonts: list[FontPreset],
    on_preview: Callable[[_StudioState], tuple[bool, str]] | None = None,
) -> bool:
    ui = _SwitchUiState()
    status_ok = True
    status_message: str | None = None
    row_count = len(_studio_rows(state, themes, accents, backgrounds, foregrounds, fonts))

    while True:
        theme_indices = _filter_indices_by_name([theme.name for theme in themes], ui.theme_filter)
        if theme_indices:
            ui.theme_cursor = max(0, min(ui.theme_cursor, len(theme_indices) - 1))
        else:
            ui.theme_cursor = 0
        font_name_list = [f"{preset.name} {_font_family_from_preset(preset)}" for preset in fonts]
        font_indices = _filter_indices_by_name(font_name_list, ui.font_filter)
        if font_indices:
            ui.font_cursor = max(0, min(ui.font_cursor, len(font_indices) - 1))
        else:
            ui.font_cursor = 0
        ui.control_cursor = max(0, min(ui.control_cursor, row_count - 1))

        console.clear()
        _render_studio_table(
            state,
            ui,
            themes,
            accents,
            backgrounds,
            foregrounds,
            fonts,
            theme_indices,
            font_indices,
            status_ok,
            status_message,
        )
        action = _read_switch_action()
        if action == "tab_1":
            ui.tab = 0
            continue
        if action == "tab_2":
            ui.tab = 1
            continue
        if action == "tab_3":
            ui.tab = 2
            continue
        if action == "toggle_focus":
            ui.tab = (ui.tab + 1) % 3
            continue
        if action == "search":
            query = click.prompt("Search", default="", show_default=False)
            if ui.tab == 0:
                ui.theme_filter = query
            elif ui.tab == 2:
                ui.font_filter = query
            continue
        if action == "clear_filter":
            if ui.tab == 0:
                ui.theme_filter = ""
            elif ui.tab == 2:
                ui.font_filter = ""
            continue
        if action == "reset":
            if ui.tab in {0, 1} and themes:
                if ui.tab == 0 and theme_indices:
                    state.theme_index = theme_indices[ui.theme_cursor]
                _apply_theme_defaults(
                    state,
                    themes=themes,
                    accents=accents,
                    backgrounds=backgrounds,
                    foregrounds=foregrounds,
                )
                if on_preview:
                    status_ok, status_message = on_preview(state)
            continue
        if action == "install":
            if ui.tab == 0 and theme_indices:
                state.theme_index = theme_indices[ui.theme_cursor]
                _apply_theme_defaults(
                    state,
                    themes=themes,
                    accents=accents,
                    backgrounds=backgrounds,
                    foregrounds=foregrounds,
                )
                if on_preview:
                    status_ok, status_message = on_preview(state)
            elif ui.tab == 2 and font_indices:
                state.font_index = font_indices[ui.font_cursor]
                if on_preview:
                    status_ok, status_message = on_preview(state)
            continue
        elif action == "up":
            if ui.tab == 0:
                if theme_indices:
                    ui.theme_cursor = (ui.theme_cursor - 1) % len(theme_indices)
                    state.theme_index = theme_indices[ui.theme_cursor]
                    _apply_theme_defaults(
                        state,
                        themes=themes,
                        accents=accents,
                        backgrounds=backgrounds,
                        foregrounds=foregrounds,
                    )
                    if on_preview:
                        status_ok, status_message = on_preview(state)
            elif ui.tab == 2:
                if font_indices:
                    ui.font_cursor = (ui.font_cursor - 1) % len(font_indices)
                    state.font_index = font_indices[ui.font_cursor]
                    if on_preview:
                        status_ok, status_message = on_preview(state)
            else:
                ui.control_cursor = (ui.control_cursor - 1) % row_count
        elif action == "down":
            if ui.tab == 0:
                if theme_indices:
                    ui.theme_cursor = (ui.theme_cursor + 1) % len(theme_indices)
                    state.theme_index = theme_indices[ui.theme_cursor]
                    _apply_theme_defaults(
                        state,
                        themes=themes,
                        accents=accents,
                        backgrounds=backgrounds,
                        foregrounds=foregrounds,
                    )
                    if on_preview:
                        status_ok, status_message = on_preview(state)
            elif ui.tab == 2:
                if font_indices:
                    ui.font_cursor = (ui.font_cursor + 1) % len(font_indices)
                    state.font_index = font_indices[ui.font_cursor]
                    if on_preview:
                        status_ok, status_message = on_preview(state)
            else:
                ui.control_cursor = (ui.control_cursor + 1) % row_count
        elif action in {"bigger", "smaller"}:
            if ui.tab == 1:
                changed = _adjust_studio_state(
                    state,
                    row=ui.control_cursor,
                    delta=1 if action == "bigger" else -1,
                    accents=accents,
                    backgrounds=backgrounds,
                    foregrounds=foregrounds,
                    fonts=fonts,
                )
                if changed and on_preview:
                    status_ok, status_message = on_preview(state)
            elif ui.tab == 0:
                if theme_indices:
                    delta = 1 if action == "bigger" else -1
                    ui.theme_cursor = (ui.theme_cursor + delta) % len(theme_indices)
                    state.theme_index = theme_indices[ui.theme_cursor]
                    _apply_theme_defaults(
                        state,
                        themes=themes,
                        accents=accents,
                        backgrounds=backgrounds,
                        foregrounds=foregrounds,
                    )
                    if on_preview:
                        status_ok, status_message = on_preview(state)
            else:
                if font_indices:
                    delta = 1 if action == "bigger" else -1
                    ui.font_cursor = (ui.font_cursor + delta) % len(font_indices)
                    state.font_index = font_indices[ui.font_cursor]
                    if on_preview:
                        status_ok, status_message = on_preview(state)
        elif action == "apply":
            console.clear()
            return True
        elif action == "cancel":
            console.clear()
            return False


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="ghostty-rice")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ghostty-rice — Full visual profile manager for Ghostty."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_cmd)


@cli.command("list")
def list_cmd() -> None:
    """List all available profiles."""
    profiles = list_profiles()
    if not profiles:
        console.print("[yellow]No profiles found.[/yellow]")
        return

    current = get_current_profile()

    table = Table(title="Available Profiles", border_style="bright_blue", show_lines=False)
    table.add_column("", width=2)
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Source", style="dim")

    for p in profiles:
        marker = "[green]*[/green]" if p.name == current else " "
        table.add_row(marker, p.name, p.description, p.source)

    console.print(table)
    console.print(f"\n[dim]Current: {current or 'none'}  |  Run: rice switch[/dim]")


def _switch_profiles_classic(no_reload: bool) -> None:
    """Legacy profile list switcher with live preview."""
    if not has_xterm_ghostty_terminfo():
        ok, msg = install_xterm_ghostty_terminfo()
        style = "green" if ok else "yellow"
        console.print(f"[{style}]{msg}[/{style}]")

    profiles = list_profiles()
    if not profiles:
        console.print("[yellow]No profiles found.[/yellow]")
        return

    snapshot_existed, snapshot_content = _capture_config_snapshot()
    current = get_current_profile()
    previewed_name = current
    preview_reload_pending = False
    last_preview_reload = 0.0

    def _preview(profile: Profile) -> tuple[bool, str]:
        nonlocal previewed_name, preview_reload_pending, last_preview_reload
        if previewed_name == profile.name:
            return True, f"Previewing: {profile.name}"

        apply_profile(profile)
        previewed_name = profile.name
        if no_reload:
            return True, f"Previewing: {profile.name}"
        now = time.monotonic()
        if now - last_preview_reload < _PREVIEW_MIN_INTERVAL:
            preview_reload_pending = True
            return True, f"Previewing {profile.name}: queued for fast apply"
        ok, msg = reload_ghostty()
        last_preview_reload = now
        preview_reload_pending = False
        return ok, f"Previewing {profile.name}: {msg}"

    selected = _choose_profile_interactively(
        profiles,
        current_name=current,
        on_preview=_preview,
    )
    if not selected:
        if previewed_name != current:
            _restore_config_snapshot(snapshot_existed, snapshot_content)
            console.print("[yellow]Cancelled.[/yellow] Restored previous config.")
            if not no_reload:
                ok, msg = reload_ghostty()
                style = "green" if ok else "yellow"
                console.print(f"[{style}]{msg}[/{style}]")
            return
        console.print("[yellow]Cancelled.[/yellow]")
        return

    if previewed_name != selected.name:
        apply_profile(selected)
    console.print(f"[green]Switched to:[/green] [bold]{selected.name}[/bold]")

    if not no_reload:
        if previewed_name == selected.name and not preview_reload_pending:
            console.print("[green]Preview already active.[/green]")
        else:
            ok, msg = reload_ghostty()
            style = "green" if ok else "yellow"
            console.print(f"[{style}]{msg}[/{style}]")


@cli.command("switch")
@click.option("--no-reload", is_flag=True, help="Don't auto-reload Ghostty config.")
def switch_cmd(no_reload: bool) -> None:
    """Interactive switcher with live preview (theme + controls)."""
    _run_theme_studio(no_reload)


@cli.command("font")
@click.option("--no-reload", is_flag=True, help="Don't auto-reload Ghostty config.")
def font_cmd(no_reload: bool) -> None:
    """Interactive font preset picker with immediate preview."""
    installed = installed_font_families()
    presets = build_font_candidates(installed=installed)
    if not presets:
        if installed:
            console.print(
                "[yellow]No coding-friendly fonts detected from installed families.[/yellow]"
            )
            console.print(
                "[dim]Install fonts like JetBrains Mono / Iosevka / Fira Code "
                "for better choices.[/dim]"
            )
        else:
            console.print("[yellow]No font presets available.[/yellow]")
        return

    if installed:
        console.print(
            f"[dim]Detected {len(installed)} installed font families; "
            f"showing {len(presets)} high-quality candidates.[/dim]"
        )

    snapshot_existed, snapshot_content = _capture_config_snapshot()
    current_family = current_font_family()
    current_size = current_font_size()
    previewed_signature: tuple[str, str] | None = None
    preview_reload_pending = False
    last_preview_reload = 0.0

    def _preview(preset: FontPreset) -> tuple[bool, str]:
        nonlocal previewed_signature, preview_reload_pending, last_preview_reload
        size_text = preset.settings.get("font-size", "?")
        signature = (preset.name, size_text)
        if previewed_signature == signature:
            return True, f"Previewing font: {preset.name} ({size_text})"

        apply_font_preset(preset)
        previewed_signature = signature
        if no_reload:
            return True, f"Previewing font: {preset.name} ({size_text})"
        now = time.monotonic()
        if now - last_preview_reload < _PREVIEW_MIN_INTERVAL:
            preview_reload_pending = True
            return True, f"Previewing {preset.name} ({size_text}): queued for fast apply"
        ok, msg = reload_ghostty()
        last_preview_reload = now
        preview_reload_pending = False
        return ok, f"Previewing {preset.name} ({size_text}): {msg}"

    selected = _choose_font_interactively(
        presets,
        current_family=current_family,
        initial_size=current_size,
        on_preview=_preview,
    )
    if not selected:
        if previewed_signature is not None:
            _restore_config_snapshot(snapshot_existed, snapshot_content)
            console.print("[yellow]Cancelled.[/yellow] Restored previous font config.")
            if not no_reload:
                ok, msg = reload_ghostty()
                style = "green" if ok else "yellow"
                console.print(f"[{style}]{msg}[/{style}]")
            return
        console.print("[yellow]Cancelled.[/yellow]")
        return

    selected_signature = (selected.name, selected.settings.get("font-size", "?"))
    if previewed_signature != selected_signature:
        apply_font_preset(selected)

    size_text = selected.settings.get("font-size", "?")
    console.print(
        f"[green]Font preset:[/green] [bold]{selected.name}[/bold]  "
        f"[dim]({size_text})[/dim]"
    )
    if not no_reload:
        if previewed_signature == selected_signature and not preview_reload_pending:
            console.print("[green]Preview already active.[/green]")
        else:
            ok, msg = reload_ghostty()
            style = "green" if ok else "yellow"
            console.print(f"[{style}]{msg}[/{style}]")


def _run_theme_studio(no_reload: bool) -> None:
    """Run full switcher with live controls."""
    if not has_xterm_ghostty_terminfo():
        ok, msg = install_xterm_ghostty_terminfo()
        style = "green" if ok else "yellow"
        console.print(f"[{style}]{msg}[/{style}]")

    themes = list_studio_themes()
    if not themes:
        console.print("[yellow]No switch themes available.[/yellow]")
        return

    fonts = build_font_candidates(installed=installed_font_families())
    if not fonts:
        console.print("[yellow]No font presets available for full switcher.[/yellow]")
        return

    accents = accent_swatches()
    backgrounds = background_swatches()
    foregrounds = foreground_swatches()
    if not accents or not backgrounds or not foregrounds:
        console.print("[yellow]Theme swatches are not available.[/yellow]")
        return

    snapshot_existed, snapshot_content = _capture_config_snapshot()
    current_profile = get_current_profile()
    theme_index = next(
        (idx for idx, theme in enumerate(themes) if theme.name == current_profile),
        0,
    )
    if current_profile == _STUDIO_PROFILE_NAME:
        theme_index = next(
            (idx for idx, theme in enumerate(themes) if theme.name == default_studio_theme().name),
            0,
        )

    initial_font_family = current_font_family()
    font_index = 0
    if initial_font_family:
        font_index = next(
            (
                idx
                for idx, preset in enumerate(fonts)
                if _font_family_from_preset(preset) == initial_font_family
            ),
            0,
        )

    initial_size = current_font_size() or 13.0
    state = _StudioState(
        theme_index=theme_index,
        accent_index=0,
        background_index=0,
        foreground_index=0,
        font_index=font_index,
        font_size=max(_STUDIO_MIN_FONT_SIZE, min(_STUDIO_MAX_FONT_SIZE, initial_size)),
        contrast_index=0,
        translucent=False,
    )
    _apply_theme_defaults(
        state,
        themes=themes,
        accents=accents,
        backgrounds=backgrounds,
        foregrounds=foregrounds,
    )

    preview_signature: tuple[str, str, str, str, str, str, int, bool] | None = None
    preview_reload_pending = False
    last_preview_reload = 0.0

    def _preview(current_state: _StudioState) -> tuple[bool, str]:
        nonlocal preview_signature, preview_reload_pending, last_preview_reload
        signature = _studio_profile_signature(
            current_state,
            themes=themes,
            accents=accents,
            backgrounds=backgrounds,
            foregrounds=foregrounds,
            fonts=fonts,
        )
        if preview_signature == signature:
            return True, f"Previewing: {signature[0]}"

        body = _build_studio_profile_body_from_state(
            current_state,
            themes=themes,
            accents=accents,
            backgrounds=backgrounds,
            foregrounds=foregrounds,
        )
        path = write_studio_profile(body, profile_name=_STUDIO_PROFILE_NAME)
        profile = Profile(
            name=_STUDIO_PROFILE_NAME,
            description=f"Switch profile based on {signature[0]}",
            author="ghostty-rice",
            source="user",
            path=path,
        )
        apply_font_preset(_preset_with_size(fonts[current_state.font_index], current_state.font_size))
        apply_profile(profile)
        preview_signature = signature
        if no_reload:
            return True, f"Previewing: {signature[0]}"

        now = time.monotonic()
        if now - last_preview_reload < _PREVIEW_MIN_INTERVAL:
            preview_reload_pending = True
            return True, f"Previewing {signature[0]}: queued for fast apply"
        ok, msg = reload_ghostty()
        last_preview_reload = now
        preview_reload_pending = False
        return ok, f"Previewing {signature[0]}: {msg}"

    applied = _run_studio_interactively(
        state,
        themes=themes,
        accents=accents,
        backgrounds=backgrounds,
        foregrounds=foregrounds,
        fonts=fonts,
        on_preview=_preview,
    )
    if not applied:
        if preview_signature is not None:
            _restore_config_snapshot(snapshot_existed, snapshot_content)
            console.print("[yellow]Cancelled.[/yellow] Restored previous config.")
            if not no_reload:
                ok, msg = reload_ghostty()
                style = "green" if ok else "yellow"
                console.print(f"[{style}]{msg}[/{style}]")
            return
        console.print("[yellow]Cancelled.[/yellow]")
        return

    final_signature = _studio_profile_signature(
        state,
        themes=themes,
        accents=accents,
        backgrounds=backgrounds,
        foregrounds=foregrounds,
        fonts=fonts,
    )
    if preview_signature != final_signature:
        body = _build_studio_profile_body_from_state(
            state,
            themes=themes,
            accents=accents,
            backgrounds=backgrounds,
            foregrounds=foregrounds,
        )
        path = write_studio_profile(body, profile_name=_STUDIO_PROFILE_NAME)
        profile = Profile(
            name=_STUDIO_PROFILE_NAME,
            description=f"Switch profile based on {final_signature[0]}",
            author="ghostty-rice",
            source="user",
            path=path,
        )
        apply_font_preset(_preset_with_size(fonts[state.font_index], state.font_size))
        apply_profile(profile)

    console.print(
        "[green]Switch applied:[/green] "
        f"[bold]{final_signature[0]}[/bold] "
        f"[dim]font={final_signature[4]} size={final_signature[5]} "
        f"contrast={final_signature[6]}[/dim]"
    )
    if not no_reload:
        if preview_signature == final_signature and not preview_reload_pending:
            console.print("[green]Preview already active.[/green]")
        else:
            ok, msg = reload_ghostty()
            style = "green" if ok else "yellow"
            console.print(f"[{style}]{msg}[/{style}]")


@cli.command("prompt")
@click.option(
    "--install",
    is_flag=True,
    help="Install or update auto-load block in ~/.zshrc.",
)
def prompt_cmd(install: bool) -> None:
    """Interactive zsh prompt preset picker."""
    shell_name = detected_shell_name()
    if not zsh_available():
        console.print("[red]Prompt presets require zsh, but zsh was not found.[/red]")
        console.print("[dim]Install zsh first, then run `rice prompt --install`.[/dim]")
        raise SystemExit(1)

    if shell_name != "zsh":
        console.print(
            f"[yellow]Current shell is {shell_name}. "
            "Preset will be installed for zsh and takes effect in zsh sessions.[/yellow]"
        )

    presets = list_prompt_presets()
    if not presets:
        console.print("[yellow]No prompt presets available.[/yellow]")
        return

    selected = _choose_prompt_interactively(
        presets,
        current_name=current_prompt_preset_name(),
    )
    if not selected:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    config_path = apply_prompt_preset(selected)
    bootstrap = prompt_bootstrap_line(config_path)
    already_installed = has_prompt_bootstrap()
    runtime_active = prompt_runtime_active()
    installed_now = False
    if install:
        installed_now = ensure_prompt_bootstrap(prompt_file=config_path)

    console.print(f"[green]Prompt preset:[/green] [bold]{selected.name}[/bold]")
    console.print(f"[dim]Saved:[/dim] {config_path}")
    if install:
        if installed_now:
            console.print("[green]Installed bootstrap into ~/.zshrc.[/green]")
        else:
            console.print("[dim]Bootstrap already present in ~/.zshrc.[/dim]")
        if runtime_active:
            console.print("[green]Applied immediately in current Ghostty zsh session.[/green]")
        else:
            console.print("[dim]First-time install (or non-zsh shell): source ~/.zshrc once.[/dim]")
    else:
        if runtime_active:
            console.print("[green]Applied immediately in current Ghostty zsh session.[/green]")
            return
        if already_installed:
            console.print("[dim]Bootstrap already present in ~/.zshrc.[/dim]")
            console.print("[dim]Apply now:[/dim] source ~/.zshrc")
        else:
            console.print("[dim]Run once:[/dim] rice prompt --install")
            console.print("[dim]Or add this to ~/.zshrc:[/dim]")
            console.print(f"[bold]{bootstrap}[/bold]")
            console.print(f"[dim]Apply now:[/dim] source \"{config_path}\"")


@cli.command("preview")
@click.argument("name")
def preview_cmd(name: str) -> None:
    """Preview a profile without applying it."""
    profile = get_profile(name)
    if not profile:
        console.print(f"[red]Profile '{name}' not found.[/red]")
        raise SystemExit(1)

    preview_profile(
        name=profile.name,
        config_body=profile.config_body(),
        description=profile.description,
        console=console,
    )


@cli.command("create")
@click.argument("name")
@click.option("--from", "from_profile", default=None, help="Base on an existing profile.")
def create_cmd(name: str, from_profile: str | None) -> None:
    """Create a new profile."""
    dest = user_profiles_dir() / name
    if dest.exists():
        console.print(f"[red]Profile '{name}' already exists at {dest}[/red]")
        raise SystemExit(1)

    if from_profile:
        source = get_profile(from_profile)
        if not source:
            console.print(f"[red]Source profile '{from_profile}' not found.[/red]")
            raise SystemExit(1)
        shutil.copy2(source.path, dest)
    else:
        dest.write_text("theme = Catppuccin Mocha\nbackground-opacity = 1.0\n")

    console.print(f"[green]Created:[/green] {dest}")
    console.print("[dim]Edit it, then run: rice switch[/dim]")


@cli.command("current")
def current_cmd() -> None:
    """Show the current active profile."""
    current = get_current_profile()
    if current:
        console.print(f"[bold]{current}[/bold]")
    else:
        console.print("[yellow]No profile active.[/yellow]")


@cli.command("colors")
@click.argument("name", required=False)
@click.option("--all", "show_all", is_flag=True, help="Compare colors across all profiles.")
def colors_cmd(name: str | None, show_all: bool) -> None:
    """Show color palette for a profile (or compare all)."""
    if show_all:
        profiles = list_profiles()
        if not profiles:
            console.print("[yellow]No profiles found.[/yellow]")
            return
        show_all_colors(profiles, console)
        return

    if name:
        profile = get_profile(name)
        if not profile:
            console.print(f"[red]Profile '{name}' not found.[/red]")
            raise SystemExit(1)
    else:
        current = get_current_profile()
        if not current:
            console.print("[yellow]No active profile. Specify a name or use --all.[/yellow]")
            raise SystemExit(1)
        profile = get_profile(current)
        if not profile:
            console.print(f"[red]Active profile '{current}' not found.[/red]")
            raise SystemExit(1)

    show_profile_colors(profile, console)


@cli.command("doctor")
@click.option(
    "--fix",
    is_flag=True,
    help="Apply safe fixes (currently installs xterm-ghostty terminfo on macOS).",
)
def doctor_cmd(fix: bool) -> None:
    """Check Ghostty installation, permissions, and runtime status."""
    from ghostty_rice.profile import list_profiles as _list_profiles

    fix_note: tuple[bool, str] | None = None
    if fix and not has_xterm_ghostty_terminfo():
        fix_note = install_xterm_ghostty_terminfo()

    plat = get_platform()
    checks = plat.run_diagnostics()

    # Add rice-specific checks
    config_dir = ghostty_config_dir()
    config_file = ghostty_config_file()
    profiles = _list_profiles()
    current = get_current_profile()

    checks.append(
        type(checks[0])(
            name="Config directory",
            passed=config_dir.exists(),
            message=str(config_dir),
            hint=f"Create it: mkdir -p '{config_dir}'" if not config_dir.exists() else "",
        )
    )
    checks.append(
        type(checks[0])(
            name="Config file",
            passed=config_file.exists(),
            message=str(config_file) if config_file.exists() else "Not found",
            hint="Run `rice switch` to create one" if not config_file.exists() else "",
        )
    )
    checks.append(
        type(checks[0])(
            name="Profiles available",
            passed=len(profiles) > 0,
            message=str(len(profiles)),
        )
    )
    checks.append(
        type(checks[0])(
            name="Active profile",
            passed=current is not None,
            message=current or "None",
            hint="Run `rice switch` to activate one" if not current else "",
        )
    )
    shell_name = detected_shell_name()
    zsh_ok = zsh_available()
    checks.append(
        type(checks[0])(
            name="Prompt shell support",
            passed=zsh_ok,
            message=f"Current shell: {shell_name}",
            hint=(
                "Install zsh to use `rice prompt`"
                if not zsh_ok
                else "Prompt presets target zsh; run in zsh for immediate effect"
                if shell_name != "zsh"
                else ""
            ),
        )
    )

    # Render
    console.print()
    console.print("[bold]ghostty-rice doctor[/bold]")
    console.print()

    if fix_note:
        ok, msg = fix_note
        style = "green" if ok else "yellow"
        console.print(f"  [{style}]fix[/{style}]  {msg}")
        console.print()

    all_passed = True
    for check in checks:
        if check.passed:
            icon = "[green]OK[/green]"
        else:
            icon = "[red]!![/red]"
            all_passed = False

        console.print(f"  {icon}  [bold]{check.name}[/bold]: {check.message}")
        if check.hint:
            console.print(f"       [dim]{check.hint}[/dim]")

    console.print()
    if all_passed:
        console.print("[green]All checks passed.[/green]")
    else:
        console.print("[yellow]Some checks need attention.[/yellow]")
