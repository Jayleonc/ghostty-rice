"""CLI entry point for ghostty-rice."""

from __future__ import annotations

import shutil
import time
from collections.abc import Callable

import click
from rich.console import Console
from rich.table import Table

from ghostty_rice import __version__
from ghostty_rice.colors import show_all_colors, show_profile_colors
from ghostty_rice.fonts import (
    FontPreset,
    apply_font_preset,
    current_font_family,
    installed_font_families,
    list_font_presets,
)
from ghostty_rice.paths import ghostty_config_dir, ghostty_config_file, user_profiles_dir
from ghostty_rice.platform import get_platform
from ghostty_rice.preview import preview_profile
from ghostty_rice.profile import (
    Profile,
    apply_profile,
    get_current_profile,
    get_profile,
    list_profiles,
)
from ghostty_rice.reload import reload_ghostty

console = Console()
_PREVIEW_MIN_INTERVAL = 0.12


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
    if char in ("k", "K"):
        return "up"
    if char in ("j", "J"):
        return "down"
    if char in ("\x1b[A",):
        return "up"
    if char in ("\x1b[B",):
        return "down"
    if char == "\x1b":
        seq1 = click.getchar()
        seq2 = click.getchar()
        if seq1 == "[" and seq2 == "A":
            return "up"
        if seq1 == "[" and seq2 == "B":
            return "down"
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
        table.add_row(
            marker,
            str(idx + 1),
            preset.name,
            family,
            preset.settings.get("font-size", "-"),
            preset.description,
        )

    console.print(table)
    console.print(
        "[dim]Controls: ↑/↓ or j/k to move (live preview), Enter to confirm, q to cancel[/dim]"
    )
    if status_message:
        style = "green" if status_ok else "yellow"
        console.print(f"[{style}]{status_message}[/{style}]")


def _choose_font_interactively(
    presets: list[FontPreset],
    current_family: str | None,
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

    status_ok = True
    status_message: str | None = None
    while True:
        console.clear()
        _render_font_table(
            presets,
            current_index,
            current_family,
            status_ok=status_ok,
            status_message=status_message,
        )
        action = _read_switch_action()
        if action == "up":
            current_index = (current_index - 1) % len(presets)
            if on_preview:
                status_ok, status_message = on_preview(presets[current_index])
        elif action == "down":
            current_index = (current_index + 1) % len(presets)
            if on_preview:
                status_ok, status_message = on_preview(presets[current_index])
        elif action == "apply":
            console.clear()
            return presets[current_index]
        elif action == "cancel":
            console.clear()
            return None


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
    console.print(f"\n[dim]Current: {current or 'none'}  |  Use: rice use <name>[/dim]")


@cli.command("use")
@click.argument("name")
@click.option("--no-reload", is_flag=True, help="Don't auto-reload Ghostty config.")
def use_cmd(name: str, no_reload: bool) -> None:
    """Switch to a profile."""
    profile = get_profile(name)
    if not profile:
        console.print(f"[red]Profile '{name}' not found.[/red]")
        console.print("[dim]Run `rice list` to see available profiles.[/dim]")
        raise SystemExit(1)

    apply_profile(profile)
    console.print(f"[green]Switched to:[/green] [bold]{name}[/bold]")

    if not no_reload:
        ok, msg = reload_ghostty()
        style = "green" if ok else "yellow"
        console.print(f"[{style}]{msg}[/{style}]")


@cli.command("switch")
@click.option("--no-reload", is_flag=True, help="Don't auto-reload Ghostty config.")
def switch_cmd(no_reload: bool) -> None:
    """Interactive profile picker with immediate apply."""
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


@cli.command("font")
@click.option("--no-reload", is_flag=True, help="Don't auto-reload Ghostty config.")
def font_cmd(no_reload: bool) -> None:
    """Interactive font preset picker with immediate preview."""
    all_presets = list_font_presets()
    installed = installed_font_families()
    if installed:
        presets = [
            preset
            for preset in all_presets
            if preset.settings.get("font-family", "").strip('"') in installed
        ]
    else:
        presets = all_presets
    if not presets:
        console.print("[yellow]No font presets available.[/yellow]")
        return

    if installed and len(presets) < len(all_presets):
        console.print(
            f"[dim]Using {len(presets)}/{len(all_presets)} presets based on installed fonts.[/dim]"
        )

    snapshot_existed, snapshot_content = _capture_config_snapshot()
    current_family = current_font_family()
    previewed_name: str | None = None
    preview_reload_pending = False
    last_preview_reload = 0.0

    def _preview(preset: FontPreset) -> tuple[bool, str]:
        nonlocal previewed_name, preview_reload_pending, last_preview_reload
        if previewed_name == preset.name:
            return True, f"Previewing font: {preset.name}"

        apply_font_preset(preset)
        previewed_name = preset.name
        if no_reload:
            return True, f"Previewing font: {preset.name}"
        now = time.monotonic()
        if now - last_preview_reload < _PREVIEW_MIN_INTERVAL:
            preview_reload_pending = True
            return True, f"Previewing {preset.name}: queued for fast apply"
        ok, msg = reload_ghostty()
        last_preview_reload = now
        preview_reload_pending = False
        return ok, f"Previewing {preset.name}: {msg}"

    selected = _choose_font_interactively(
        presets,
        current_family=current_family,
        on_preview=_preview,
    )
    if not selected:
        if previewed_name is not None:
            _restore_config_snapshot(snapshot_existed, snapshot_content)
            console.print("[yellow]Cancelled.[/yellow] Restored previous font config.")
            if not no_reload:
                ok, msg = reload_ghostty()
                style = "green" if ok else "yellow"
                console.print(f"[{style}]{msg}[/{style}]")
            return
        console.print("[yellow]Cancelled.[/yellow]")
        return

    if previewed_name != selected.name:
        apply_font_preset(selected)

    console.print(f"[green]Font preset:[/green] [bold]{selected.name}[/bold]")
    if not no_reload:
        if previewed_name == selected.name and not preview_reload_pending:
            console.print("[green]Preview already active.[/green]")
        else:
            ok, msg = reload_ghostty()
            style = "green" if ok else "yellow"
            console.print(f"[{style}]{msg}[/{style}]")


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
    console.print(f"[dim]Edit it, then run: rice use {name}[/dim]")


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
def doctor_cmd() -> None:
    """Check Ghostty installation, permissions, and runtime status."""
    from ghostty_rice.profile import list_profiles as _list_profiles

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
            hint="Run `rice use <profile>` to create one" if not config_file.exists() else "",
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
            hint="Run `rice use <profile>` to activate one" if not current else "",
        )
    )

    # Render
    console.print()
    console.print("[bold]ghostty-rice doctor[/bold]")
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
