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
rice use catppuccin-mocha

# Preview before switching
rice preview rosepine

# Create your own
rice create my-theme --from catppuccin-mocha
# Edit ~/.config/ghostty/rice-profiles/my-theme.conf, then:
rice use my-theme
```

## Built-in Profiles

| Profile | Description |
|---------|-------------|
| `catppuccin-mocha` | Warm and cozy — the most popular dev palette |
| `rosepine` | Elegant dark with auto light/dark switching |
| `cyber` | Cyberpunk vibes — high transparency, holographic icon |
| `minimal` | Distraction-free — no titlebar, no blur, just code |
| `frosted` | macOS native frosted glass (light mode) |

## Custom Profiles

Create a `.conf` file in `~/.config/ghostty/rice-profiles/` (Linux) or `~/Library/Application Support/com.mitchellh.ghostty/rice-profiles/` (macOS):

```ini
# @name: My Theme
# @description: My custom visual profile
# @author: me
# @tags: dark, custom

theme = Catppuccin Mocha
background-opacity = 0.90
background-blur = macos-glass-regular
macos-titlebar-style = transparent
window-padding-x = 12
window-padding-y = 8
cursor-style = block
cursor-style-blink = true
```

Then `rice use my-theme` — that's it.

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
