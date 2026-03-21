<p align="center">
  <h1 align="center">ghostty-rice</h1>
  <p align="center">
    Full visual profile manager for <a href="https://ghostty.org">Ghostty</a> — beyond just colors.
  </p>
  <p align="center">
    <a href="https://pypi.org/project/ghostty-rice/"><img src="https://img.shields.io/pypi/v/ghostty-rice?style=flat-square&color=blue" alt="PyPI"></a>
    <a href="https://github.com/jayleonc/ghostty-rice/blob/main/LICENSE"><img src="https://img.shields.io/github/license/jayleonc/ghostty-rice?style=flat-square" alt="License"></a>
    <a href="https://github.com/jayleonc/ghostty-rice/actions"><img src="https://img.shields.io/github/actions/workflow/status/jayleonc/ghostty-rice/ci.yml?style=flat-square&label=CI" alt="CI"></a>
    <img src="https://img.shields.io/pypi/pyversions/ghostty-rice?style=flat-square" alt="Python">
    <a href="./README_CN.md"><img src="https://img.shields.io/badge/lang-简体中文-red?style=flat-square" alt="中文"></a>
  </p>
</p>

---

Color themes only change 16 ANSI colors. **ghostty-rice** manages complete visual profiles — colors, opacity, blur, titlebar, cursor, padding, icons — and switches them with a single command.

```bash
rice use "Catppuccin Mocha"    # Switch profile, auto-reloads Ghostty
```

## Why ghostty-rice?

Projects like [catppuccin/ghostty](https://github.com/catppuccin/ghostty) and [iTerm2-Color-Schemes](https://github.com/mbadolato/iTerm2-Color-Schemes) are color palettes. A terminal's look is more than 16 colors:

| What they manage | What ghostty-rice manages |
|------------------|--------------------------|
| Foreground/background | Everything they do, plus: |
| 16 ANSI palette colors | Window opacity & blur effects |
| | Titlebar style (tabs, transparent, hidden) |
| | Cursor shape, color, animation |
| | Window padding & spacing |
| | App icon variant |

## Install

```bash
pipx install ghostty-rice
```

<details>
<summary>Other methods</summary>

```bash
# With pip
pip install ghostty-rice

# From source
git clone https://github.com/jayleonc/ghostty-rice.git
cd ghostty-rice
pip install -e .
```

</details>

## Quick Start

```bash
# List available profiles
rice list

# Switch profile (auto-reloads Ghostty)
rice use "Catppuccin Mocha"

# Preview without switching
rice preview "Cyber"

# Check setup
rice doctor

# See current profile
rice current
```

## Built-in Profiles

| Profile | Style |
|---------|-------|
| **Catppuccin Mocha** | Warm, cozy, the most popular dev palette |
| **Rose Pine** | Elegant dark with automatic light/dark switching |
| **Cyber** | High transparency, hidden chrome, holographic icon |
| **Minimal** | No titlebar, no blur, just code |
| **Frosted** | macOS native frosted glass, light mode |

## Custom Profiles

Profile files follow Ghostty's own format — plain `key = value`, no file extension, filename is the profile name.

**1. Create from an existing profile:**

```bash
rice create "My Theme" --from "Catppuccin Mocha"
```

**2. Or write one from scratch:**

Create a file in your Ghostty config directory under `rice-profiles/`:

| Platform | Path |
|----------|------|
| macOS | `~/Library/Application Support/com.mitchellh.ghostty/rice-profiles/` |
| Linux | `~/.config/ghostty/rice-profiles/` |

```ini
theme = Catppuccin Mocha
background-opacity = 0.90
background-blur = macos-glass-regular
macos-titlebar-style = transparent
window-padding-x = 12
window-padding-y = 8
cursor-style = block
cursor-style-blink = true
```

**3. Add metadata** (optional) in `manifest.toml` alongside your profiles:

```toml
[profiles."My Theme"]
description = "My custom visual profile"
author = "me"
tags = ["dark", "custom"]
```

**4. Use it:**

```bash
rice use "My Theme"
```

## Diagnostics

```bash
rice doctor
```

Checks Ghostty installation, version, running state, automation permissions, config directory, and profile status in one command.

## How It Works

ghostty-rice preserves your base Ghostty config (shell, fonts, keybinds) and only manages the visual profile section. When you switch profiles:

1. Your base config stays untouched
2. The profile section is replaced
3. Ghostty is auto-reloaded (macOS: native AppleScript API, Linux: xdotool)

## Platform Support

| Platform | Profile switching | Auto-reload |
|----------|------------------|-------------|
| macOS | Full | Native AppleScript API |
| Linux | Full | Via xdotool (optional) |

## Contributing

Contributions welcome — especially new profiles, platform support, and shader management.

```bash
git clone https://github.com/jayleonc/ghostty-rice.git
cd ghostty-rice
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

## License

[MIT](LICENSE)
