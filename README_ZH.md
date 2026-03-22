<h1 align="center">🍚 ghostty-rice</h1>

<p align="center">
  <b><a href="https://ghostty.org">Ghostty</a> 终端的全方位视觉配置管理器 —— 不只是换颜色。</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/ghostty-rice/"><img src="https://img.shields.io/pypi/v/ghostty-rice?style=flat-square&color=blue&logo=pypi&logoColor=white&v=0.2.2" alt="PyPI"></a>
  <img src="https://img.shields.io/pypi/pyversions/ghostty-rice?style=flat-square&logo=python&logoColor=white&v=0.2.2" alt="Python">
  <a href="https://github.com/jayleonc/ghostty-rice/actions"><img src="https://img.shields.io/github/actions/workflow/status/jayleonc/ghostty-rice/ci.yml?style=flat-square&label=CI&logo=github" alt="CI"></a>
  <a href="https://github.com/jayleonc/ghostty-rice/blob/main/LICENSE"><img src="https://img.shields.io/github/license/jayleonc/ghostty-rice?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="./README.md">English</a> • <b>简体中文</b>
</p>

---

> **不只是换颜色 —— 完全掌控 Ghostty 终端的视觉体验。**

<!-- 🎬 展示区 — 录好 GIF/截图后替换下方占位图 -->
<p align="center">
  <img src="docs/demo.gif" alt="ghostty-rice 演示 — 实时切换视觉方案" width="720">
</p>

<p align="center">
  <i>一条命令，整体变身，Ghostty 瞬间重载。</i>
</p>

<!-- 📸 方案画廊 — 在此放置各方案截图 -->
<details>
<summary><b>方案画廊</b>（点击展开）</summary>
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

传统主题只改 16 色调色盘。**ghostty-rice** 管理完整的视觉方案 —— 颜色、透明度、毛玻璃、标题栏、光标、边距、图标 —— 一条命令全部切换。

```bash
rice switch    # 交互式实时切换 + 自动重载
```

## 为什么需要 ghostty-rice？

[catppuccin/ghostty](https://github.com/catppuccin/ghostty) 和 [iTerm2-Color-Schemes](https://github.com/mbadolato/iTerm2-Color-Schemes) 是优秀的调色盘项目。但终端的视觉体验远不止 16 个颜色：

| 传统调色盘项目 | 🍚 `ghostty-rice` |
|---------------|-------------------|
| ✅ 前景色与背景色 | ✅ **涵盖左侧所有内容，外加：** |
| ✅ 16 色 ANSI 调色盘 | ✅ 窗口透明度与毛玻璃效果 |
| ❌ 标题栏样式 | ✅ 标题栏样式（标签页 / 透明 / 隐藏） |
| ❌ 光标定制 | ✅ 光标形状、颜色与动画 |
| ❌ 窗口内外边距 | ✅ 窗口内边距定制 |
| ❌ App 图标 | ✅ App 图标一键切换 |

**一句话：它们是调色盘，我们是整套视觉方案。**

## 安装

```bash
pipx install ghostty-rice
```

<details>
<summary>其他安装方式</summary>

```bash
# pip 安装
pip install ghostty-rice

# 从源码安装
git clone https://github.com/jayleonc/ghostty-rice.git
cd ghostty-rice
pip install -e .
```

</details>

## 快速上手

```bash
# 查看所有可用方案
rice list

# 交互式 switch（主题 / 外观 / 字体 / Prompt — 4 标签页实时预览）
rice switch

# 交互式字体工作台（高质量字体筛选，+/- 可实时调字号）
rice font

# 交互式 zsh Prompt 选择器，并自动写入 ~/.zshrc
rice prompt --install

# 预览方案（不切换）
rice preview "Cyber"

# 一键检查环境（验证配置、检测无效主题引用）
rice doctor
# 自动修复（terminfo、无效主题行等）
rice doctor --fix

# 配置损坏时一键恢复到安全方案
rice reset "Catppuccin Mocha"

# 查看当前方案
rice current
```

## 内置方案 (10)

| 方案 | 风格 |
|------|------|
| **Catppuccin Mocha** | 深夜咖啡馆 —— 全不透明、稳定光标、温暖舒适 |
| **One Dark Pro** | 工作基线 —— 高采用率 One Dark 系列、稳定对比度 |
| **Codex** | 石墨专注 —— Codex 风暗色、暖色强调、低眩光文字 |
| **Everforest** | 柔和森林 —— 低对比度暗色，长时间编码更舒适 |
| **Cyber** | 银翼杀手 —— 半透明毛玻璃、隐藏标题栏、全息图标 |
| **Minimal** | 打字机 —— 零装饰、宽边距、Dieter Rams 式极简 |
| **Frosted** | 清晨工作台 —— 毛玻璃亮色模式、深墨色文字 |
| **Nord** | 北欧清冽 —— 全不透明冷色调、《降临》级冷静 |
| **Gruvbox** | 模拟暖调 —— 全不透明、大地色系、韦斯·安德森调色盘 |
| **Dracula** | 哥特影院 —— 全不透明紫灰、醒目强调、蒂姆·伯顿戏剧感 |

## Rice Switch

`rice switch` 打开完整工作台 —— Mason/Lazy 风格的边框面板，4 个标签页：

| 标签 | 功能 |
|------|------|
| **1 Themes** | 浏览 14 个暗色主题族，实时预览 + 色块展示 |
| **2 Appearance** | 强调色 / 背景色 / 前景色 / 对比度 / 毛玻璃开关 |
| **3 Fonts** | 字体选择器 + 字号调节 |
| **4 Prompt** | Shell Prompt 预设，带样例预览（确认后应用） |

键位风格（Mason/Lazy）：
- `1/2/3/4`：切换标签
- `j/k` 或 `↑/↓`：移动选择
- `h/l` 或 `←/→` 或 `+/-`：调整参数 / 字号
- `/`：在当前列表标签内搜索
- `i`：立即应用当前项
- `u`：重置到当前主题默认值
- `Enter`：确认并应用全部
- `q`：取消并回滚

## Shell Prompt 预设（zsh）

8 个内置 Prompt 预设 —— 从极简到双行 git 分支：

| 预设 | 样例 | 风格 |
|------|------|------|
| **Zen** | `❯` | 仅状态箭头 |
| **Minimal Arrow** | `ghostty-rice ›` | 目录名 + 箭头 |
| **Lambda** | `λ ghostty-rice ›` | Lambda 符号 |
| **Dev Compact** | `(.venv) repo/subdir »` | 虚拟环境 + 短路径 |
| **Starship** | `~/project main` ⏎ `❯` | 双行 + git 分支 |
| **Boxed** | `┌ ~/project (main)` ⏎ `└ ❯` | 框线 + git 分支 |
| **Deep Path** | `(.venv) ~/Dev/project ❯` | 完整路径 |
| **Context Rich** | `[.venv] jay@mbp project #` | 用户@主机 + 路径 |

可以在 `rice switch`（标签 4）中选择，也可以单独使用：

```bash
rice prompt --install
```

首次安装需要执行一次：

```bash
source ~/.zshrc
```

之后再执行 `rice prompt` 或 `rice switch`，在 Ghostty 的 zsh 会话里会在下一次提示符自动生效。
同时会给 `zsh-autosuggestions` 设置更柔和的灰色（`fg=#555555`，不受主题调色盘影响），并导出 `COLORTERM=truecolor`。

如果你用了 Oh My Zsh / Starship / Powerlevel10k，请把 rice 的 bootstrap 放在 `~/.zshrc` 靠后位置，确保在其它 Prompt 初始化之后生效。

## 自定义方案

方案文件完全遵循 Ghostty 原生格式 —— 纯 `key = value`，无文件扩展名，文件名即方案名。

**1. 从已有方案创建：**

```bash
rice create "My Theme" --from "Catppuccin Mocha"
```

**2. 或者从零开始：**

在 rice 配置目录下创建文件：

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

**3. 添加元数据**（可选），在同目录下的 `manifest.toml` 中：

```toml
[profiles."My Theme"]
description = "我的自定义方案"
author = "me"
tags = ["dark", "custom"]
```

**4. 使用：**

```bash
rice switch    # 然后选中 "My Theme"
```

## 环境诊断与修复

```bash
rice doctor          # 全面检查：安装状态、配置文件、无效主题引用
rice doctor --fix    # 自动修复：terminfo、无效主题行等
rice reset "Codex"   # 配置损坏时一键恢复到安全方案
```

`rice doctor` 一键检查：Ghostty 安装状态、版本号、运行状态、自动化权限、`xterm-ghostty` terminfo、配置目录、方案加载情况，以及**验证配置中的主题引用是否有效**。

如果配置损坏（如 Ghostty 弹出 "theme not found"），`rice doctor --fix` 会移除无效行，`rice reset` 可以一键切换到正常的内置方案。

## 工作原理

ghostty-rice 会保留你的基础配置（Shell、字体、快捷键等），只管理视觉方案部分。切换时：

1. 基础配置原封不动
2. 视觉方案部分被替换
3. Ghostty 自动重载（macOS 通过原生 AppleScript API，Linux 通过 xdotool）

## 平台支持

| 平台 | 方案切换 | 自动重载 |
|------|---------|---------|
| macOS | 完整支持 | 原生 AppleScript API |
| Linux | 完整支持 | xdotool（可选） |

## 征集主题

我们正在打造一个 Ghostty 视觉方案合集 —— **期待你的作品加入**。

如果你调出了满意的终端风格，欢迎提交 PR：

1. 将方案文件放入 `ghostty_rice/presets/`
2. 在 `ghostty_rice/presets/manifest.toml` 中添加元数据
3. （加分项）在 `docs/screenshots/` 中附上截图

所有贡献者都会在 manifest 中署名。开发环境搭建见下方[参与贡献](#参与贡献)。

## 参与贡献

欢迎贡献 —— 特别是新的视觉方案、平台支持、Shader 管理。

```bash
git clone https://github.com/jayleonc/ghostty-rice.git
cd ghostty-rice
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

## 开源协议

[MIT](LICENSE)
