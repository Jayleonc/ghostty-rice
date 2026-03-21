"""CLI entry point for ghostty-rice."""

from __future__ import annotations

import shutil

import click
from rich.console import Console
from rich.table import Table

from ghostty_rice import __version__
from ghostty_rice.paths import ghostty_config_dir, ghostty_config_file, user_profiles_dir
from ghostty_rice.platform import get_platform
from ghostty_rice.preview import preview_profile
from ghostty_rice.profile import apply_profile, get_current_profile, get_profile, list_profiles
from ghostty_rice.reload import reload_ghostty

console = Console()


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
        dest.write_text("theme = Catppuccin Mocha\nbackground-opacity = 0.95\n")

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
