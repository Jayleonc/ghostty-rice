# ghostty-rice

Full visual profile manager for [Ghostty](https://ghostty.org) terminal — beyond just colors.

Unlike color-only theme repos, **ghostty-rice** manages complete visual profiles: colors, opacity, blur, titlebar, cursor, padding, icons, and more. Switch your entire terminal aesthetic with a single command.

## Install

```bash
pipx install ghostty-rice
```

## Quick Start

```bash
# List available profiles
rice list

# Switch profile (auto-reloads Ghostty)
rice use "Catppuccin Mocha"

# Preview before switching
rice preview "Rose Pine"

# Create your own
rice create "My Theme" --from "Catppuccin Mocha"
# Edit the profile file, then:
rice use "My Theme"
```

## Built-in Profiles

| Profile | Description |
|---------|-------------|
| `Catppuccin Mocha` | Warm and cozy — the most popular dev palette |
| `Rose Pine` | Elegant dark with auto light/dark switching |
| `Cyber` | Cyberpunk vibes — high transparency, holographic icon |
| `Minimal` | Distraction-free — no titlebar, no blur, just code |
| `Frosted` | macOS native frosted glass (light mode) |

## Custom Profiles

Profile files follow the same format as Ghostty's built-in themes — plain key=value config with no extension. Create a file in `rice-profiles/` under your Ghostty config directory:

**macOS:** `~/Library/Application Support/com.mitchellh.ghostty/rice-profiles/`
**Linux:** `~/.config/ghostty/rice-profiles/`

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

Optionally add metadata in `manifest.toml` alongside your profiles:

```toml
[profiles."My Theme"]
description = "My custom visual profile"
author = "me"
tags = ["dark", "custom"]
```

Then `rice use "My Theme"` — that's it.

## Why not just use a color theme?

Color themes (like [catppuccin/ghostty](https://github.com/catppuccin/ghostty) or [iTerm2-Color-Schemes](https://github.com/mbadolato/iTerm2-Color-Schemes)) only change the 16 ANSI colors. A Ghostty profile is much more than that:

- Window opacity and blur effects
- Titlebar style (tabs, transparent, hidden)
- Cursor shape, color, and animation
- Window padding and spacing
- App icon variant
- Custom shaders (planned)

**ghostty-rice** manages the full visual experience, not just the palette.

## License

MIT
