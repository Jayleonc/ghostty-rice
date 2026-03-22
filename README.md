<h1 align="center">🍚 ghostty-rice</h1>

<p align="center">
  <b>Full visual profile manager for <a href="https://ghostty.org">Ghostty</a> — beyond just colors.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/ghostty-rice/"><img src="https://img.shields.io/pypi/v/ghostty-rice?style=flat-square&color=blue&logo=pypi&logoColor=white&v=0.1.0" alt="PyPI"></a>
  <img src="https://img.shields.io/pypi/pyversions/ghostty-rice?style=flat-square&logo=python&logoColor=white&v=0.1.0" alt="Python">
  <a href="https://github.com/jayleonc/ghostty-rice/actions"><img src="https://img.shields.io/github/actions/workflow/status/jayleonc/ghostty-rice/ci.yml?style=flat-square&label=CI&logo=github" alt="CI"></a>
  <a href="https://github.com/jayleonc/ghostty-rice/blob/main/LICENSE"><img src="https://img.shields.io/github/license/jayleonc/ghostty-rice?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <b>English</b> • <a href="./README_ZH.md">简体中文</a>
</p>

---

> **Beyond just colors — total visual control for your Ghostty terminal.**

<!-- 🎬 SHOWCASE — replace the placeholder below with your own GIF/screenshots -->
<p align="center">
  <img src="docs/demo.gif" alt="ghostty-rice demo — switching profiles in real time" width="720">
</p>

<p align="center">
  <i>One command. Entire visual transformation. Ghostty reloads instantly.</i>
</p>

<!-- 📸 PROFILE GALLERY — add screenshots of each profile here -->
<details>
<summary><b>Profile Gallery</b> (click to expand)</summary>
<br>

| Catppuccin Mocha | One Dark Pro | Cyber |
|:---:|:---:|:---:|
| <img src="docs/screenshots/catppuccin-mocha.png" width="280"> | <img src="docs/screenshots/one-dark-pro.png" width="280"> | <img src="docs/screenshots/cyber.png" width="280"> |

| Nord | Dracula | Frosted |
|:---:|:---:|:---:|
| <img src="docs/screenshots/nord.png" width="280"> | <img src="docs/screenshots/dracula.png" width="280"> | <img src="docs/screenshots/frosted.png" width="280"> |

| Gruvbox | | |
|:---:|:---:|:---:|
| <img src="docs/screenshots/gruvbox.png" width="280"> | | |

| Minimal | | |
|:---:|:---:|:---:|
| <img src="docs/screenshots/minimal.png" width="280"> | | |

</details>

---

Color themes only change 16 ANSI colors. **ghostty-rice** manages complete visual profiles — colors, opacity, blur, titlebar, cursor, padding, icons — and switches them with a single command.

```bash
rice switch    # Interactive live switch with instant preview + reload
```

## Why ghostty-rice?

Projects like [catppuccin/ghostty](https://github.com/catppuccin/ghostty) and [iTerm2-Color-Schemes](https://github.com/mbadolato/iTerm2-Color-Schemes) are color palettes. A terminal's look is more than 16 colors:

| Other Color Schemes | 🍚 `ghostty-rice` |
|---------------------|-------------------|
| ✅ Foreground & Background | ✅ **Everything they do, plus:** |
| ✅ 16 ANSI Palette Colors | ✅ Window Opacity & Blur Effects |
| ❌ Titlebar Style | ✅ Titlebar Style (tabs, transparent, hidden) |
| ❌ Cursor Customization | ✅ Cursor Shape, Color & Animation |
| ❌ Window Spacing | ✅ Window Padding & Spacing |
| ❌ App Icon | ✅ App Icon Variant |

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

# Full switcher (themes + controls, live preview; Tab / hjkl / arrows)
rice switch

# Interactive font studio (quality fonts only, +/- to resize live)
rice font

# Interactive zsh prompt picker + one-shot install to ~/.zshrc
rice prompt --install

# Preview without switching
rice preview "Cyber"

# Check setup
rice doctor
# Install safe fixes (recommended once, macOS terminfo for Vim/Neovim)
rice doctor --fix

# See current profile
rice current
```

## Built-in Profiles (10)

| Profile | Style |
|---------|-------|
| **Catppuccin Mocha** | Warm, cozy, the most popular dev palette |
| **One Dark Pro** | High-adoption baseline with balanced contrast |
| **Codex** | Graphite dark, warm accent, muted low-glare text |
| **Everforest** | Soft woodland palette for long low-fatigue sessions |
| **Cyber** | High transparency, hidden chrome, holographic icon |
| **Minimal** | No chrome, no blur, just code |
| **Frosted** | macOS native frosted glass, light mode |
| **Nord** | Arctic, north-bluish palette — calm and focused |
| **Gruvbox** | Retro groove with warm, earthy tones |
| **Dracula** | Iconic dark theme with vibrant purple and pink |

## Switch Controls

`rice switch` now includes the full control panel with live preview:

- Dark theme family (Absolutely / Ayu / Catppuccin / Codex / Dracula / Everforest / GitHub / Gruvbox / Linear / Sentry / Solarized / Temple / Tokyo Night / VS Code Plus)
- Accent color
- Background / foreground
- Code font + size
- Translucent glass toggle
- Contrast

Mason/Lazy-style keyboard flow:
- `1/2/3`: switch tabs (Themes / Controls / Fonts)
- `j/k` or `↑/↓`: move selection
- `h/l` or `←/→` or `+/-`: adjust
- `/`: search in current list tab
- `i`: apply current selected item immediately
- `u`: reset to selected theme defaults
- `q`: cancel and rollback

## Shell Prompt Presets (zsh)

The line like `(.venv) jayleonc/ghostty-rice »` is your **shell prompt** (zsh), not the Ghostty theme.
If `zsh` is missing, `rice prompt` will warn and stop.
By default, rice prompt is applied only in Ghostty sessions, so iTerm2 can keep your existing prompt.

```bash
rice prompt --install
```

First install requires one reload:

```bash
source ~/.zshrc
```

After that, changing preset via `rice prompt` is applied on the next prompt automatically in Ghostty zsh.
The bootstrap also sets a muted default for `zsh-autosuggestions` and exports `COLORTERM=truecolor`.

If you use Oh My Zsh / Starship / Powerlevel10k, keep the rice bootstrap near the end of `~/.zshrc` so it takes effect after other prompt initializers.

## Custom Profiles

Profile files follow Ghostty's own format — plain `key = value`, no file extension, filename is the profile name.

**1. Create from an existing profile:**

```bash
rice create "My Theme" --from "Catppuccin Mocha"
```

**2. Or write one from scratch:**

Create a file in the rice profiles directory:

```
~/.config/ghostty/rice/profiles/
```

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
rice switch    # then pick "My Theme"
```

## Diagnostics

```bash
rice doctor
```

Checks Ghostty installation, version, running state, automation permissions, `xterm-ghostty` terminfo, config directory, and profile status in one command.
If Vim/Neovim colors or key behavior look wrong, run `rice doctor --fix` once.

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

## Call for Themes

We're building a collection of stunning Ghostty visual profiles — and **your profile could be next**.

If you've crafted a look you love, submit it as a PR:

1. Add your profile file to `ghostty_rice/presets/`
2. Add metadata in `ghostty_rice/presets/manifest.toml`
3. (Bonus) Include a screenshot in `docs/screenshots/`

All contributors are credited in the manifest. See [Contributing](#contributing) below for dev setup.

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
