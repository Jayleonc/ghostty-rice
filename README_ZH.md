<h1 align="center">🍚 ghostty-rice</h1>

<p align="center">
  <b><a href="https://ghostty.org">Ghostty</a> 终端的全方位视觉配置管理器 —— 不只是换颜色。</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/ghostty-rice/"><img src="https://img.shields.io/pypi/v/ghostty-rice?style=flat-square&color=blue&logo=pypi&logoColor=white&v=0.1.0" alt="PyPI"></a>
  <img src="https://img.shields.io/pypi/pyversions/ghostty-rice?style=flat-square&logo=python&logoColor=white&v=0.1.0" alt="Python">
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

| Catppuccin Mocha | Rose Pine | Cyber |
|:---:|:---:|:---:|
| <img src="docs/screenshots/catppuccin-mocha.png" width="280"> | <img src="docs/screenshots/rose-pine.png" width="280"> | <img src="docs/screenshots/cyber.png" width="280"> |

| Nord | Tokyo Night | Dracula |
|:---:|:---:|:---:|
| <img src="docs/screenshots/nord.png" width="280"> | <img src="docs/screenshots/tokyo-night.png" width="280"> | <img src="docs/screenshots/dracula.png" width="280"> |

| Gruvbox | Solarized | Frosted |
|:---:|:---:|:---:|
| <img src="docs/screenshots/gruvbox.png" width="280"> | <img src="docs/screenshots/solarized.png" width="280"> | <img src="docs/screenshots/frosted.png" width="280"> |

| Minimal | | |
|:---:|:---:|:---:|
| <img src="docs/screenshots/minimal.png" width="280"> | | |

</details>

---

传统主题只改 16 色调色盘。**ghostty-rice** 管理完整的视觉方案 —— 颜色、透明度、毛玻璃、标题栏、光标、边距、图标 —— 一条命令全部切换。

```bash
rice use "Catppuccin Mocha"    # 切换方案，Ghostty 自动重载
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

# 切换方案（自动重载 Ghostty）
rice use "Catppuccin Mocha"

# 预览方案（不切换）
rice preview "Cyber"

# 一键检查环境
rice doctor

# 查看当前方案
rice current
```

## 内置方案 (10)

| 方案 | 风格 |
|------|------|
| **Catppuccin Mocha** | 温暖柔和，程序员圈最火的配色 |
| **Rose Pine** | 优雅暗色，跟随系统自动切换明暗 |
| **Cyber** | 赛博朋克 —— 高透明度、隐藏标题栏、全息图标 |
| **Minimal** | 极简 —— 无标题栏、无模糊、只有代码 |
| **Frosted** | macOS 原生毛玻璃，亮色模式 |
| **Nord** | 北极冰蓝，冷静专注 |
| **Tokyo Night** | 东京夜色，现代深蓝暗色主题 |
| **Gruvbox** | 复古暖调，Vim 用户最爱 |
| **Dracula** | 经典暗色，标志性紫粉配色 |
| **Solarized** | 科学配色，支持自动明暗切换 |

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
rice use "My Theme"
```

## 环境诊断

```bash
rice doctor
```

一键检查：Ghostty 安装状态、版本号、运行状态、自动化权限、配置目录、方案加载情况。

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
