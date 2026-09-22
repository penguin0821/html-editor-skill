---
name: html-editor
version: 1.3.0
description: 把任意静态 HTML 变成可在浏览器里「拖拽区块、改文字、换字体字号、加粗/颜色/链接、换图、撤销重做」的可视化编辑器，改完导出剥离编辑器的干净 HTML。面向不会前端的人，也供 agent 自动化注入/写回。**默认工作流：agent 收到指令后一步到位——注入生成 `*.editable.html`，再用系统命令自动打开到用户默认浏览器，用户直接开编**。当用户说"用 html-editor 编辑 xxx.html / 可视化编辑 HTML / 像 Word 一样改网页 / 让这份 HTML 可编辑 / 打开这份 HTML 让我改 / 拖模块改字体 / 编辑生成的 HTML 报告 / 把 HTML 变成可拖拽可编辑的"时使用。不依赖 QoderWork，任意浏览器可跑。
---

# html-editor · 可视化 HTML 编辑闭环

给任意**静态** HTML 注入一段自包含编辑器（`assets/editor.js`），让人在真实浏览器里
拖区块、改文字、调字体字号、加粗/颜色/链接、换图、撤销重做，改完一键导出
**剥离了编辑器**的干净 HTML。编辑器不绑定任何 AI 宿主，`file://` 双击即可用。

两条使用路径，共用同一内核：

- **手动路径**（无 AI）：跑一次 `inject.py` 生成可编辑副本 → 双击打开 → 编辑 → 点「⬇ 导出 HTML」。
- **agent 路径**（QoderWork / Claude Code / a1 / Cursor 等）：agent 注入 → 打开 → 用户编辑 →
  导出 → agent 把导出的干净 HTML 写回原文件（**写回前备份原件**）。

> 除了本文件（读 `SKILL.md` 的宿主），本包还提供三种等价接入，内核同一份 `editor.js`：
> `AGENTS.md`（Codex/Cursor/Zed 等读 AGENTS.md 的宿主）、`html-editor` 命令行
> （`pipx install .` 后全局可用，注入即自动开浏览器）、MCP server
> （`pipx install '.[mcp]'` 后 `python -m html_editor.mcp_server`，需 Python 3.10+）。
> 无本地 shell 的云端办公 agent 见 `PROMPT.md`。兼容矩阵见 `README.md`。

## 适用边界（先读，避免误用）

- 适用：单文件静态 HTML（AI 生成的报告、文档、落地页等），可含少量原生 JS / Chart.js。
- **不适用**：React/Vue/Svelte 等框架运行时渲染的页面——它们会重渲染 DOM，手动改动会被冲掉。
- 已知 v1 局限：`<pre>`/等宽架构图里的每个 `<span>` 会被单独识别为可编辑文本（粒度偏细）；
  字体/字号作用于"点选的整个文本元素或选中的文字"，不是任意像素区域。

## 一句话触发流程（agent 默认按这个跑）

用户在对话里说「用 html-editor 编辑 xxx.html / 打开这份 HTML 让我改 / 让这份 HTML 可编辑」等，
agent 一步到位执行下面两步，无需再问：

```bash
# 1) 注入生成副本（不动原文件）
python3 ~/.qoderwork/skills/html-editor/assets/inject.py <用户给的.html>

# 2) 用系统默认浏览器打开副本（跨平台）
#    macOS:   open       <path>.editable.html
#    Linux:   xdg-open   <path>.editable.html
#    Windows: start ""   <path>.editable.html
```

- 副本默认与原文件同目录（保留相对路径 `js/`、`css/`、图片引用）；名字为 `<原名>.editable.html`。
- 打开后浏览器自动进入编辑模式；改完点顶栏「⬇ 导出 HTML」或 `⌘/Ctrl+S` 下载干净版本。
- 若用户想「覆盖原文件」，agent 收到导出文件后**先备份原件**再覆盖，不要把 editable 副本当成品。
- 若用户明说「在对话里/QoderWork 内嵌浏览器打开」，才改走"内嵌 Chrome + 本地 http.server"路径（见 Step 1 备选）。

## Step 0 · 注入，生成可编辑副本

```bash
python3 assets/inject.py <输入.html> [输出.html] [--filename 导出名.html] [--no-autostart]
```

- 不传输出路径时默认生成 `<输入名>.editable.html`，**不修改输入文件**。
- 注入层全部带 `data-he-ui` 标记；编辑器"导出"时整段剥离，原文件结构不受污染。
- 注入是**内联** editor.js（不引 CDN），所以副本离线 / `file://` 也能跑。

## Step 1 · 打开并编辑

**默认（推荐）：系统默认浏览器打开**

```bash
open       /path/to/xxx.editable.html   # macOS
xdg-open   /path/to/xxx.editable.html   # Linux
start ""   "C:\path\to\xxx.editable.html"  # Windows
```

- 走 `file://`，无需起本地服务；相对路径的 `js/`、`css/`、图片天然可用。
- 用你日常浏览器（书签、密码、扩展都在）。
- 打开即自动进入编辑模式；`--no-autostart` 则停在预览。
- 副作用：`file://` 下顶栏「💾 保存」（FSA 覆盖保存）不出现，`⌘/Ctrl+S` 会降级为下载——
  这是浏览器安全模型，不是 bug；下载完再覆盖原文件即可（agent 写回路径也是这么走的）。

**备选：QoderWork 内嵌 Chrome 打开**（仅当用户明确说"在对话里打开 / 让我在这看到 tab"）

- `builtin_browser` 的 `navigate` 不接受 `file://`，agent 需先起本地服务：
  ```bash
  cd <editable.html 所在目录> && python3 -m http.server 8971 &
  ```
  然后 `navigate` 到 `http://localhost:8971/<name>.editable.html`。
- 相对路径依赖要求服务根目录选对；关闭前记得 kill 掉 http.server。

编辑操作速查：

| 想做的事 | 操作 |
|---|---|
| 改文字 | 直接点进文字输入（contenteditable） |
| 选中区块 | 点区块左上角 `⠿` 手柄，或 Alt+点击区块 |
| 拖拽排序 | 按住 `⠿` 手柄拖动，出现蓝色虚线占位即松手 |
| 上/下移、复制、新增、删除、换图 | 选中区块后出现的悬浮工具条 |
| 字体 / 字号 / 颜色 / 加粗斜体下划线 / 链接 | 顶部工具栏（先点选文字或选中文字） |
| 撤销 / 重做 | 顶栏按钮，或 Ctrl+Z / Ctrl+Shift+Z |
| 预览（隐藏编辑框） | 顶栏「👁 预览」 |

## Step 2 · 保存 / 导出

- **默认：顶栏「⬇ 导出 HTML」** → 浏览器下载一份已剥离编辑器的干净 HTML。
  这是唯一在 `file://`、任意浏览器都成立的落盘方式（浏览器安全策略禁止网页静默覆盖本地文件）。
- **可选：顶栏「💾 保存」** → 仅当运行在 `https://` 或 `localhost`（安全上下文）时出现，
  用 File System Access API 覆盖保存。`file://` 下没有此按钮。
- agent 写回：拿到导出文件后，**先备份原文件**，再覆盖原文件；不要直接编辑注入副本当成品。

## agent 自动化 API（`window.__htmlEditor`）

注入后页面暴露该对象，供自动化与验收：

```js
__htmlEditor.exportCleanHTML()      // -> 剥离后的完整 HTML 字符串（含 <!DOCTYPE html>）
__htmlEditor.download()             // 触发下载
__htmlEditor.saveInPlace()          // 安全上下文下覆盖保存
__htmlEditor.enterEdit()/exitEdit()
__htmlEditor.getRoot()              // 识别出的根容器（.container/main/body 之一）
__htmlEditor.getBlocks()            // 顶层可拖拽区块
__htmlEditor.setText(el, txt)
__htmlEditor.applyTextStyle(prop, v)// 如 ('fontSize','40px') / ('fontFamily',"'Songti SC',serif")
__htmlEditor.moveBlock(el, beforeEl)
__htmlEditor.duplicateBlock()/deleteBlock()
__htmlEditor.undo()/redo()
```

验收断言（改完必查）：导出字符串里 `data-he-ui`、`contenteditable`、`__he_`、
`he-bodypad`、`he-topbar` 计数全为 0；原有 `<script>`/`<canvas>`/`<style>` 保留。

## 踩坑清单

| 现象 | 原因 | 处置 |
|---|---|---|
| 内嵌浏览器打不开 `file://` | navigate 只支持 http(s) | 起本地 http 服务，或让用户真实 Chrome 双击 |
| 自动化里 `download()` 无文件落地 | 程序化 `a.click()` 缺用户手势被拦 | 真人点击正常；自动化改用 `exportCleanHTML()` 取串自行落盘 |
| 撤销/重做后拖拽失效 | 快照替换使缓存根容器脱离文档 | 已修：`restoreBody` 内重新 `detectRoot()`；若复现先重载 |
| 图表拖动/撤销后空白 | canvas 被移动或重建 | 已内置：捕获 Chart 配置，DOM 变动后 `resize()`/重建；自定义图表需自行重绘 |
| 导出后字体/字号丢失 | 原页样式是 class 统一控制 | 编辑器把字体/字号写成元素**内联 style**，导出即保留 |
| 换图后导出丢图 | 用了外链 src | 编辑器把上传图转 **base64 内联**，导出自包含 |
| 编辑框盖住内容 | 顶栏占位 | 编辑模式给 body 加 `he-bodypad`，导出时自动剥离 |
| 可编辑/可拖拽挂不上 JS 渲染的内容 | 页面在 load 或异步（解压内嵌数据、setTimeout）才渲染 | 已内置 `resync`（window.load + 400ms + 1500ms）重探根、重挂 contenteditable、重捕图表；更慢的渲染可重载页面 |
| 无 `.container` 的页面区块识别过窄 | 旧兜底误选"子元素最多的那层"（如 kpi-row） | 已修：无单一 wrapper 时根 = `body`，所有顶层块可拖、全部文本可编辑（实测 282 单元格表格全可编辑） |
| `inject.py --filename X` 报"输入文件不存在" | 旧参数解析把 `--filename` 的值当位置参数，值与输入同名时把输入一起过滤掉 | 已修：改成从左到右扫描，`--filename`/`--filename=` 的值被吃掉不落入 positionals；`--filename` 现可安全等于输入名 |
| 导出残留 `id="he_canvas_xxx"` | `captureCharts` 给无 id 的 `<canvas>` 赋合成 id 供快照重建，旧 `exportCleanHTML` 未清理 | 已修：导出克隆里剥掉 `canvas[id^="he_canvas_"]` 的 id；**不动** `stripMarkers`（撤销快照仍需该 id 让 `restoreCharts` 找回画布） |

## 设计原则（改动内核时遵守）

1. 所有编辑器 UI/属性必须带 `data-he-ui` 或 `he-*` 命名空间，导出时能被 `stripMarkers` 干净剥离。
2. 不写死任何业务 class；靠结构语义识别（顶层区块 = 容器/flex/grid/ul/ol 的直接子元素；
   可编辑文本 = 仅含行内子节点的文本元素）。
3. 无外部依赖、无构建；单文件 `editor.js`，可内联进任意 HTML。
4. 撤销用 body 快照栈；每次离散操作前 `pushState()`，文本输入按聚焦分组。
