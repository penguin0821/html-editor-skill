# AGENTS.md · html-editor 给 AI agent 的操作说明

> 这是一份**跨宿主**的 agent 指令文件。凡是读取 `AGENTS.md` 作为项目/工作指令的
> agent（Codex、Cursor、Zed、Jules、Factory、Sourcegraph Amp 等），照此执行即可，
> 无需理解内部实现。QoderWork / Claude Code 等读 `SKILL.md` 的宿主，`SKILL.md`
> 与本文件等价，二选一即可。

## 这个工具是什么

给任意**静态 HTML** 注入一段自包含的可视化编辑器，让人在浏览器里像用 Word 一样
拖区块、改文字、调字体字号、加粗/颜色/链接、换图、撤销重做；改完一键导出
**剥离了编辑器**的干净 HTML。零外部依赖、零构建、离线可用（`file://` 双击即可）。

## 何时触发

用户说以下任意一类意图时使用本工具：
「可视化编辑 HTML」「像 Word 一样改网页」「让这份 HTML 可以拖拽/改字体」
「编辑生成的 HTML 报告」「用 html-editor 打开 xxx.html」。

## 适用边界（先判断，避免误用）

- 适用：单文件静态 HTML（AI 生成的报告、文档、落地页等），可含少量原生 JS / Chart.js。
- **不适用**：React/Vue/Svelte 等框架运行时渲染的页面——它们会重渲染 DOM，手改会被冲掉。

## 标准工作流（agent 一步到位）

**首选：装好的命令行（若宿主能跑 shell 且已 `pipx install`）**

```bash
html-editor <输入.html>            # 生成 <输入名>.editable.html 并自动用系统浏览器打开
```

**次选：直接跑仓库里的注入脚本（无需安装）**

```bash
python3 assets/inject.py <输入.html>     # 生成 <输入名>.editable.html，不修改原文件
# 再用系统命令打开：
open <输入名>.editable.html              # macOS
xdg-open <输入名>.editable.html          # Linux
start "" <输入名>.editable.html          # Windows
```

然后告诉用户：在浏览器里编辑，改完点顶栏「⬇ 导出 HTML」得到干净文件。

## 可选参数

```bash
html-editor 报告.html --no-open            # 只注入不打开
html-editor 报告.html --no-autostart       # 打开后停在预览，不自动进编辑模式
html-editor 报告.html --filename 成品.html  # 指定「导出 HTML」的下载文件名
html-editor --which-js                     # 打印实际使用的 editor.js 路径（排障）
```

## agent 写回原文件（用户导出后）

浏览器安全策略禁止网页静默覆盖本地文件，所以「导出」是下载一份干净 HTML。
若用户希望 agent 直接把改动写回原文件：

1. 在页面里取干净字符串：`window.__htmlEditor.exportCleanHTML()`（返回含 `<!DOCTYPE html>` 的完整 HTML）。
2. **先备份原文件**，再用该字符串覆盖原文件。
3. 不要拿注入副本（`*.editable.html`）当成品交付——它内含编辑器代码。

自动化里 `download()` 常因缺用户手势被浏览器拦截；需要落盘时用 `exportCleanHTML()` 取串自行写文件。

## 验收断言（改完/导出后必查）

导出的干净 HTML 里，这些标记的计数应全为 **0**：
`data-he-ui`、`contenteditable`、`__he_`、`he-bodypad`、`he-topbar`；
同时原有 `<script>` / `<canvas>` / `<style>` 应保留。

## 云端办公 agent（无本地 shell）怎么办

千问办公 / 豆包办公 / kimi work 等如果没有本地文件系统或命令执行能力，
无法替你跑注入脚本。此时把 `PROMPT.md` 里的说明发给用户，让 TA 在自己电脑上
执行那一行 `html-editor` 或 `python3 assets/inject.py` 命令即可。详见 `PROMPT.md`。

## 更多

- 完整内核手册、API、踩坑清单：`SKILL.md`
- 人读的使用手册：`USER_GUIDE.md`
- 技术栈 / 设计原则 / 维护指南：`TECH_NOTES.md`
- 通用聊天 agent 的粘贴式提示词：`PROMPT.md`
