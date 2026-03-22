"""CLI entry point for ghostty-rice."""

from __future__ import annotations

import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass

import click
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
    fix_config_issues,
    get_current_profile,
    get_profile,
    list_profiles,
    reset_to_profile,
    validate_config,
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
_STUDIO_MIN_FONT_SIZE = 10.0
_STUDIO_MAX_FONT_SIZE = 18.0
_STUDIO_FONT_STEP = 0.5
_STUDIO_PROFILE_NAME = "Switch Live"


@dataclass
class _StudioState:
    theme_index: int
    accent_index: int
    background_index: int
    foreground_index: int
    font_index: int
    font_size: float
    translucent: bool
    prompt_index: int = 0


@dataclass
class _SwitchUiState:
    tab: int = 0  # 0=Themes, 1=Appearance, 2=Fonts, 3=Prompt
    theme_cursor: int = 0
    appearance_cursor: int = 0
    font_cursor: int = 0
    prompt_cursor: int = 0
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
    if char == "4":
        return "tab_4"
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


_APPEARANCE_ROW_COUNT = 4


def _filter_indices_by_name(names: list[str], query: str) -> list[int]:
    q = query.strip().casefold()
    if not q:
        return list(range(len(names)))
    return [idx for idx, name in enumerate(names) if q in name.casefold()]


def _render_studio_panel(
    state: _StudioState,
    ui: _SwitchUiState,
    themes: list[StudioTheme],
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
    fonts: list[FontPreset],
    prompts: list[PromptPreset],
    theme_indices: list[int],
    font_indices: list[int],
    status_ok: bool,
    status_message: str | None,
) -> None:
    active_theme = themes[state.theme_index].name
    active_font = _font_family_from_preset(fonts[state.font_index])

    # ── Tab bar ──
    tab_labels = ["Themes", "Appearance", "Fonts", "Prompt"]
    tab_bar = Text("  ")
    for i, label in enumerate(tab_labels):
        num = str(i + 1)
        if i == ui.tab:
            tab_bar.append(f" {num} {label} ", style="bold reverse")
        else:
            tab_bar.append(f" {num} ", style="dim bold")
            tab_bar.append(f"{label} ", style="dim")
        tab_bar.append("   ")

    # ── Status line ──
    status_line = Text("  ")
    status_line.append("Theme ", style="dim")
    status_line.append(active_theme, style="bold")
    status_line.append("    ")
    status_line.append("Font ", style="dim")
    status_line.append(f"{active_font} {_format_font_size(state.font_size)}", style="bold")

    # ── Tab content ──
    content_lines: list[Text] = []

    if ui.tab == 0:
        if ui.theme_filter:
            content_lines.append(Text(f"  filter: {ui.theme_filter}", style="yellow"))
        if not theme_indices:
            content_lines.append(Text("  No match — try another /search", style="dim"))
        for pos, real_idx in enumerate(theme_indices):
            theme = themes[real_idx]
            line = Text("  ")
            if pos == ui.theme_cursor:
                line.append("➤ ", style="green bold")
                line.append(f"{theme.name:<20}", style="bold")
            elif real_idx == state.theme_index:
                line.append("• ", style="bright_blue")
                line.append(f"{theme.name:<20}", style="bright_blue")
            else:
                line.append("  ")
                line.append(f"{theme.name:<20}")
            line.append(theme.description, style="dim")
            line.append("  ")
            line.append("██", style=theme.accent)
            content_lines.append(line)

    elif ui.tab == 1:
        appearance_data: list[tuple[str, str | None, bool | None]] = [
            ("Accent", accents[state.accent_index], None),
            ("Background", backgrounds[state.background_index], None),
            ("Foreground", foregrounds[state.foreground_index], None),
            ("Translucent", None, state.translucent),
        ]
        for i, (label, color_hex, toggle_val) in enumerate(appearance_data):
            line = Text("  ")
            if i == ui.appearance_cursor:
                line.append("➤ ", style="green bold")
                line.append(f"{label:<20}", style="bold")
            else:
                line.append("  ")
                line.append(f"{label:<20}")
            if color_hex is not None:
                line.append("██", style=color_hex)
                line.append(f"  {color_hex}", style="dim")
                line.append("    ◀ ▶", style="dim")
            elif toggle_val is not None:
                if toggle_val:
                    line.append("● On", style="green")
                else:
                    line.append("○ Off", style="dim")
            content_lines.append(line)

    elif ui.tab == 2:
        if ui.font_filter:
            content_lines.append(Text(f"  filter: {ui.font_filter}", style="yellow"))
        size_line = Text("  ")
        size_line.append("Size ", style="dim")
        size_line.append(_format_font_size(state.font_size), style="bold")
        size_line.append("    +/- to adjust", style="dim")
        content_lines.append(size_line)
        content_lines.append(Text(""))
        if not font_indices:
            content_lines.append(Text("  No match — try another /search", style="dim"))
        for pos, real_idx in enumerate(font_indices):
            preset = fonts[real_idx]
            line = Text("  ")
            if pos == ui.font_cursor:
                line.append("➤ ", style="green bold")
                line.append(f"{preset.name:<22}", style="bold")
            elif real_idx == state.font_index:
                line.append("• ", style="bright_blue")
                line.append(f"{preset.name:<22}", style="bright_blue")
            else:
                line.append("  ")
                line.append(f"{preset.name:<22}")
            line.append(preset.description, style="dim")
            content_lines.append(line)

    else:
        for pos, preset in enumerate(prompts):
            line = Text("  ")
            if pos == ui.prompt_cursor:
                line.append("➤ ", style="green bold")
                line.append(f"{preset.name:<20}", style="bold")
            elif pos == state.prompt_index:
                line.append("• ", style="bright_blue")
                line.append(f"{preset.name:<20}", style="bright_blue")
            else:
                line.append("  ")
                line.append(f"{preset.name:<20}")
            line.append(preset.description, style="dim")
            content_lines.append(line)
        selected_prompt = prompts[ui.prompt_cursor] if prompts else None
        if selected_prompt:
            content_lines.append(Text(""))
            content_lines.append(Text("  Preview:", style="dim"))
            for sample_line in selected_prompt.sample.split("\n"):
                preview_line = Text("    ")
                preview_line.append(sample_line, style="bold green")
                content_lines.append(preview_line)

    # ── Help + status ──
    help_line = Text(
        "  j/k navigate   ←→ adjust   / search   "
        "i install   u reset   Enter apply   q quit",
        style="dim",
    )
    status_text: Text | None = None
    if status_message:
        s = "green" if status_ok else "yellow"
        status_text = Text(f"  {status_message}", style=s)

    # ── Assemble panel ──
    parts: list[Text] = [tab_bar, Text(""), status_line, Text("")]
    parts.extend(content_lines)
    parts.append(Text(""))
    parts.append(help_line)
    if status_text:
        parts.append(status_text)

    panel = Panel(
        Group(*parts),
        title="[bold]Rice Switch[/bold]",
        border_style="bright_blue",
        expand=True,
        padding=(1, 1),
    )
    console.print(panel)


def _row_cycle_index(current: int, delta: int, size: int) -> int:
    return (current + delta) % size


def _index_of_color(options: list[str], value: str) -> int:
    try:
        return options.index(value.upper())
    except ValueError:
        return 0


def _font_family_from_preset(preset: FontPreset) -> str:
    return preset.settings.get("font-family", "").strip('"')




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


def _adjust_appearance_state(
    state: _StudioState,
    *,
    row: int,
    delta: int,
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
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
        state.translucent = not state.translucent
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
) -> tuple[str, str, str, str, str, str, bool]:
    return (
        themes[state.theme_index].name,
        accents[state.accent_index],
        backgrounds[state.background_index],
        foregrounds[state.foreground_index],
        _font_family_from_preset(fonts[state.font_index]),
        _format_font_size(state.font_size),
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
    )


def _run_studio_interactively(
    state: _StudioState,
    *,
    themes: list[StudioTheme],
    accents: list[str],
    backgrounds: list[str],
    foregrounds: list[str],
    fonts: list[FontPreset],
    prompts: list[PromptPreset],
    on_preview: Callable[[_StudioState], tuple[bool, str]] | None = None,
) -> bool:
    ui = _SwitchUiState()
    status_ok = True
    status_message: str | None = None

    def _theme_navigate(delta: int) -> None:
        nonlocal status_ok, status_message
        if not theme_indices:
            return
        ui.theme_cursor = (ui.theme_cursor + delta) % len(theme_indices)
        state.theme_index = theme_indices[ui.theme_cursor]
        _apply_theme_defaults(
            state, themes=themes, accents=accents,
            backgrounds=backgrounds, foregrounds=foregrounds,
        )
        if on_preview:
            status_ok, status_message = on_preview(state)

    def _font_navigate(delta: int) -> None:
        nonlocal status_ok, status_message
        if not font_indices:
            return
        ui.font_cursor = (ui.font_cursor + delta) % len(font_indices)
        state.font_index = font_indices[ui.font_cursor]
        if on_preview:
            status_ok, status_message = on_preview(state)

    while True:
        theme_indices = _filter_indices_by_name(
            [theme.name for theme in themes], ui.theme_filter,
        )
        if theme_indices:
            ui.theme_cursor = min(ui.theme_cursor, len(theme_indices) - 1)
        else:
            ui.theme_cursor = 0
        font_name_list = [f"{p.name} {_font_family_from_preset(p)}" for p in fonts]
        font_indices = _filter_indices_by_name(font_name_list, ui.font_filter)
        ui.font_cursor = max(0, min(ui.font_cursor, len(font_indices) - 1)) if font_indices else 0
        ui.appearance_cursor = max(0, min(ui.appearance_cursor, _APPEARANCE_ROW_COUNT - 1))
        if prompts:
            ui.prompt_cursor = max(0, min(ui.prompt_cursor, len(prompts) - 1))

        console.clear()
        _render_studio_panel(
            state, ui, themes, accents, backgrounds, foregrounds,
            fonts, prompts, theme_indices, font_indices,
            status_ok, status_message,
        )
        action = _read_switch_action()

        if action == "tab_1":
            ui.tab = 0
        elif action == "tab_2":
            ui.tab = 1
        elif action == "tab_3":
            ui.tab = 2
        elif action == "tab_4":
            ui.tab = 3
        elif action == "toggle_focus":
            ui.tab = (ui.tab + 1) % 4
        elif action == "search":
            query = click.prompt("Search", default="", show_default=False)
            if ui.tab == 0:
                ui.theme_filter = query
            elif ui.tab == 2:
                ui.font_filter = query
        elif action == "clear_filter":
            if ui.tab == 0:
                ui.theme_filter = ""
            elif ui.tab == 2:
                ui.font_filter = ""
        elif action == "reset":
            if ui.tab in {0, 1} and themes:
                if ui.tab == 0 and theme_indices:
                    state.theme_index = theme_indices[ui.theme_cursor]
                _apply_theme_defaults(
                    state, themes=themes, accents=accents,
                    backgrounds=backgrounds, foregrounds=foregrounds,
                )
                if on_preview:
                    status_ok, status_message = on_preview(state)
        elif action == "install":
            if ui.tab == 0 and theme_indices:
                state.theme_index = theme_indices[ui.theme_cursor]
                _apply_theme_defaults(
                    state, themes=themes, accents=accents,
                    backgrounds=backgrounds, foregrounds=foregrounds,
                )
                if on_preview:
                    status_ok, status_message = on_preview(state)
            elif ui.tab == 2 and font_indices:
                state.font_index = font_indices[ui.font_cursor]
                if on_preview:
                    status_ok, status_message = on_preview(state)
            elif ui.tab == 3 and prompts:
                state.prompt_index = ui.prompt_cursor
        elif action == "up":
            if ui.tab == 0:
                _theme_navigate(-1)
            elif ui.tab == 1:
                ui.appearance_cursor = (ui.appearance_cursor - 1) % _APPEARANCE_ROW_COUNT
            elif ui.tab == 2:
                _font_navigate(-1)
            elif ui.tab == 3 and prompts:
                ui.prompt_cursor = (ui.prompt_cursor - 1) % len(prompts)
        elif action == "down":
            if ui.tab == 0:
                _theme_navigate(1)
            elif ui.tab == 1:
                ui.appearance_cursor = (ui.appearance_cursor + 1) % _APPEARANCE_ROW_COUNT
            elif ui.tab == 2:
                _font_navigate(1)
            elif ui.tab == 3 and prompts:
                ui.prompt_cursor = (ui.prompt_cursor + 1) % len(prompts)
        elif action in {"bigger", "smaller"}:
            delta = 1 if action == "bigger" else -1
            if ui.tab == 0:
                _theme_navigate(delta)
            elif ui.tab == 1:
                changed = _adjust_appearance_state(
                    state, row=ui.appearance_cursor, delta=delta,
                    accents=accents, backgrounds=backgrounds,
                    foregrounds=foregrounds,
                )
                if changed and on_preview:
                    status_ok, status_message = on_preview(state)
            elif ui.tab == 2:
                # ←/→ adjusts font size on font tab
                updated = state.font_size + (_STUDIO_FONT_STEP * delta)
                clamped = max(_STUDIO_MIN_FONT_SIZE, min(_STUDIO_MAX_FONT_SIZE, updated))
                if clamped != state.font_size:
                    state.font_size = clamped
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

    prompts = list_prompt_presets()
    current_prompt = current_prompt_preset_name()
    prompt_index = 0
    if current_prompt:
        prompt_index = next(
            (i for i, p in enumerate(prompts) if p.name == current_prompt), 0,
        )

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
        translucent=False,
        prompt_index=prompt_index,
    )
    _apply_theme_defaults(
        state,
        themes=themes,
        accents=accents,
        backgrounds=backgrounds,
        foregrounds=foregrounds,
    )

    preview_signature: tuple[str, str, str, str, str, str, bool] | None = None
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
        font = _preset_with_size(fonts[current_state.font_index], current_state.font_size)
        apply_font_preset(font)
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
        prompts=prompts,
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

    # Apply prompt preset if changed
    if prompts and state.prompt_index < len(prompts):
        selected_prompt = prompts[state.prompt_index]
        apply_prompt_preset(selected_prompt)
        if zsh_available():
            ensure_prompt_bootstrap()

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

    prompt_name = prompts[state.prompt_index].name if prompts else "—"
    console.print(
        "[green]Switch applied:[/green] "
        f"[bold]{final_signature[0]}[/bold] "
        f"[dim]font={final_signature[4]} size={final_signature[5]} "
        f"translucent={'on' if final_signature[6] else 'off'} prompt={prompt_name}[/dim]"
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


@cli.command("reset")
@click.argument("name", required=False)
@click.option(
    "--no-reload",
    is_flag=True,
    help="Skip Ghostty reload after reset.",
)
def reset_cmd(name: str | None, no_reload: bool) -> None:
    """Reset config to a known-good builtin profile.

    If NAME is omitted, lists available profiles and prompts you to pick one.
    Preserves base settings (shell, keybinds) and replaces the visual profile.
    """
    profiles = list_profiles()
    if not profiles:
        console.print("[red]No profiles found.[/red]")
        raise SystemExit(1)

    if name is None:
        console.print("[bold]Available profiles:[/bold]")
        for p in profiles:
            tag = " [dim](current)[/dim]" if p.name == get_current_profile() else ""
            console.print(f"  {p.name}{tag}")
        console.print()
        name = click.prompt("Reset to", type=str)

    ok, msg = reset_to_profile(name)
    if not ok:
        console.print(f"[red]{msg}[/red]")
        raise SystemExit(1)

    console.print(f"[green]{msg}[/green]")
    if not no_reload:
        ok_reload, reload_msg = reload_ghostty()
        console.print(reload_msg)


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
    help="Apply safe fixes (terminfo, invalid theme references, etc.).",
)
def doctor_cmd(fix: bool) -> None:
    """Check Ghostty installation, permissions, and runtime status."""
    from ghostty_rice.platform import DiagnosticCheck
    from ghostty_rice.profile import list_profiles as _list_profiles

    fix_actions: list[str] = []

    # Terminfo fix
    if fix and not has_xterm_ghostty_terminfo():
        ok, msg = install_xterm_ghostty_terminfo()
        fix_actions.append(msg)

    plat = get_platform()
    checks = plat.run_diagnostics()

    # Add rice-specific checks
    config_dir = ghostty_config_dir()
    config_file = ghostty_config_file()
    profiles = _list_profiles()
    current = get_current_profile()

    checks.append(
        DiagnosticCheck(
            name="Config directory",
            passed=config_dir.exists(),
            message=str(config_dir),
            hint=f"Create it: mkdir -p '{config_dir}'" if not config_dir.exists() else "",
        )
    )
    checks.append(
        DiagnosticCheck(
            name="Config file",
            passed=config_file.exists(),
            message=str(config_file) if config_file.exists() else "Not found",
            hint="Run `rice switch` to create one" if not config_file.exists() else "",
        )
    )
    checks.append(
        DiagnosticCheck(
            name="Profiles available",
            passed=len(profiles) > 0,
            message=str(len(profiles)),
        )
    )
    checks.append(
        DiagnosticCheck(
            name="Active profile",
            passed=current is not None,
            message=current or "None",
            hint="Run `rice switch` to activate one" if not current else "",
        )
    )

    # Config validation — check for invalid theme references
    config_issues = validate_config()
    if config_issues:
        for issue in config_issues:
            checks.append(
                DiagnosticCheck(
                    name="Config validation",
                    passed=False,
                    message=issue.message,
                    hint=(
                        "Run `rice doctor --fix` to remove invalid lines, "
                        "or `rice reset` to switch to a safe profile"
                    ),
                )
            )
        if fix:
            actions = fix_config_issues(config_issues)
            fix_actions.extend(actions)
    else:
        checks.append(
            DiagnosticCheck(
                name="Config validation",
                passed=True,
                message="No issues found",
            )
        )

    shell_name = detected_shell_name()
    zsh_ok = zsh_available()
    checks.append(
        DiagnosticCheck(
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

    if fix_actions:
        for action in fix_actions:
            console.print(f"  [green]fix[/green]  {action}")
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
    if fix_actions:
        console.print(
            "[green]Fixes applied.[/green] "
            "Run `rice reset \"Catppuccin Mocha\"` to switch to a safe profile."
        )
    elif all_passed:
        console.print("[green]All checks passed.[/green]")
    else:
        console.print("[yellow]Some checks need attention.[/yellow]")
