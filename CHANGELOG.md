# CHANGELOG

版本节奏遵循 [SemVer](https://semver.org/lang/zh-CN/)：MAJOR 破坏性改动 / MINOR 新功能 / PATCH bug 修复。

版本号现需四处同步：内核 `window.__htmlEditor.version`（editor.js）、`SKILL.md` frontmatter、`pyproject.toml`、`html_editor/__init__.py`。打包前跑 `bash smoke_test.sh` 会硬断言四处一致并做注入/CLI 演练，不一致直接失败。

---

## [1.3.0] — 2026-09-22

### Added
- **pipx/pip 可安装 CLI**：新增 `html_editor` Python 包与 `pyproject.toml`，`pipx install .` 后全局可用 `html-editor 你的.html`（默认注入 + 自动开系统浏览器）。参数 `--no-open` / `--no-autostart` / `--filename` / `--which-js` / `--version`。
- **MCP server 封装**（可选 extra）：`pipx install '.[mcp]'` 后 `python -m html_editor.mcp_server` 以 stdio 启动，暴露 `make_editable` / `export_note` / `locate_editor_js` / `version`。`mcp` 依赖用环境标记约束到 Python 3.10+，不影响 CLI/skill 在 3.8+ 使用。
- **跨 agent 入口文件**：`AGENTS.md`（Codex/Cursor/Zed 等读 AGENTS.md 的宿主）、`CLAUDE.md`（Claude Code 指针）、`PROMPT.md`（无技能机制/云端办公 agent 的粘贴式提示词，含"有本地 shell"与"无本地 shell"两种场景）。
- **`smoke_test.sh`**：打包前冒烟自检——四处版本一致性硬断言、Python/JS/shell 语法自检、inject.py 注入演练（含"原文件不被改动"断言）、CLI 演练、`editor.js` 单一真源 `cmp` 校验。
- `README.md` 新增诚实版跨 agent 兼容矩阵（区分"已确认/有前提/未逐一实测/不适用"），覆盖 QoderWork/Claude Code/Codex/Cursor/Gemini/Copilot/OpenClaw/a1/GLM/Kimi/千问办公/豆包办公/workbuddy/deepseek。

### Changed
- `install.sh` 宿主探测从 3 类（qoderwork/claude/a1）扩到 8 类，新增 codex/gemini/cursor/copilot/openclaw；安装时一并复制 AGENTS.md/PROMPT.md/CLAUDE.md/html_editor/pyproject.toml。
- **单一真源**：`editor.js` 仍只在 `assets/` 存一份；`pyproject.toml` 用 setuptools `package-dir` 把 `assets/` 映射为 `html_editor.assets` 包，安装时复制进 site-packages，仓库内不产生第二份、无 drift。
- `html_editor/core.py` 是 `inject.py` 的可导入版，二者共用同一注入逻辑与同一 editor.js。

### Verified
- 干净 venv（pip 26 / setuptools 82）实测 `pip install .`：`html-editor --version` = 1.3.0，`--which-js` 指向 site-packages 内 editor.js 且与源 `cmp` 完全一致，CLI 注入成功。
- MCP 模块 lazy-import 通过、无 mcp 时优雅报错；因本机仅 Python 3.9，MCP server 未做运行时端到端实测（需 3.10+）。
- `bash smoke_test.sh` 六步全绿。

---

## [1.2.0] — 2026-09-22

### Added
- **默认工作流升级**：agent 收到"编辑这份 HTML / 让这份 HTML 可编辑 / 打开让我改"等指令后，一步到位执行 `inject.py` + 系统 `open` 命令，自动弹出用户默认浏览器，无需再问。
- `SKILL.md` 新增"一句话触发流程"章节，写明跨平台 open 命令（macOS `open` / Linux `xdg-open` / Windows `start`）。
- `description` 触发短语扩展：编辑这份 HTML / 让这份 HTML 可编辑 / 打开这份 HTML 让我改 / 像 Word 一样改网页 / 把 HTML 变成可拖拽可编辑的。
- 分发包结构：README.md、USER_GUIDE.md、TECH_NOTES.md、CHANGELOG.md、LICENSE (MIT)、install.sh、examples/demo.html。

### Changed
- `SKILL.md` Step 1 重写：系统默认浏览器为默认路径，内嵌 Chrome + http.server 降级为"仅当用户明说在对话里打开"的备选。

---

## [1.1.1] — 2026-09-22

### Fixed
- **inject.py 参数解析炸掉**：旧逻辑把 `--filename` 的值当位置参数收集，再用"值等于就删"的方式剔除——当 `--filename` 恰好等于输入文件名时，会把输入路径一起删掉，报"输入文件不存在"。改成从左到右扫描，`--filename`/`--filename=` 的值被吃掉不落入 positionals。
- **导出泄漏 `he_canvas_XXXX` 合成 id**：`captureCharts` 给无 id 的 `<canvas>` 赋合成 id 供快照重建，旧 `exportCleanHTML` 未清理。修复方式：在导出克隆里单独剥掉 `canvas[id^="he_canvas_"]` 的 id；**不动 `stripMarkers`**（撤销快照仍需该 id 让 `restoreCharts` 找回画布）。

### Verified
- 跨 4 类真实文件回归：`.container` 静态 DOM（GDPR 汇报）、无外壳 body 根（detection_dashboard）、单 `.page` 外壳 + tab 按钮 + 相对路径 Chart.js（pii_dashboard small/big）、无 id canvas fixture。全部通过：根识别正确、区块/可编辑元素数符合预期、图表全捕获、编辑+撤销+拖拽+图表存活、导出零残留。

---

## [1.1.0] — 2026-09-21

### Fixed
- **导出泄漏 `he-bodypad`**：`stripMarkers` 只清了 `contenteditable`/`data-he-text`/`data-he-spell`，漏了编辑器 class。修复：显式列出所有 `he-*` class 并从匹配元素和 root 上都移除；末尾扫一遍 `class=""` 空属性删掉。
- **撤销后拖拽失效**：`restoreBody` 用 `insertAdjacentHTML` 替换 body 内容，boot 时缓存的 `rootContainer` 已脱离文档。修复：`restoreBody` 末尾重新 `detectRoot()`，并 `applyEditable()` 重挂、`restoreCharts()` 重建。
- **无 `.container` 页面区块识别过窄**：旧 `detectRoot` 兜底"取子元素最多的那层"，在无外壳看板上误把 `.kpi-row` 当根，表格单元格全部不可编辑。修复：改成三条规则（明确 wrapper ≥2 子块 → body 下唯一 wrapper → 否则 body）。

### Added
- **`resync()` 异步渲染兜底**：`window.load` + 400ms + 1500ms 各跑一次，重探根、重挂 contenteditable、重捕图表。覆盖 pako 解压、setTimeout、fetch 后填充等异步渲染场景。
- `SKILL.md` 踩坑清单新增 5 条（resync、detectRoot、inject.py 参数、he_canvas 泄漏、内嵌浏览器 file:// 限制）。

---

## [1.0.0] — 2026-09-20

### Added
- 首版发布。核心功能：
  - **拖区块换位**：Pointer Events + `⠿` 手柄 + ghost/placeholder，不干扰文字选择；Alt+点选中区块。
  - **改文字**：`contenteditable`，结构语义识别可编辑元素（子节点全是行内标签 + 有非空文本）。
  - **字体 / 字号 / 颜色**：写成元素内联 `style`，导出后跨环境保留。
  - **行内富文本**：加粗 / 斜体 / 下划线 / 链接，`document.execCommand` + `styleWithCSS`。
  - **区块增 / 删 / 复制**：选中区块后顶栏按钮。
  - **图片替换 / 上传**：`FileReader.readAsDataURL()` 转 base64 内联，导出自包含。
  - **撤销 / 重做**：body 快照栈，深 60 步；文本输入按聚焦分组（1400ms 去抖）。
  - **Chart.js 适配**：`Chart.getChart()` 捕获 config，DOM 变动后 `resize()` / `new Chart()` 重建。
  - **导出干净 HTML**：剥离所有 `data-he-ui` 元素、`he-*` class、`contenteditable`、编辑器 UI DOM、注入脚本。
  - **保存**：下载为主（`file://` 通用）+ File System Access API 为辅（仅 https/localhost）。
- 内核零依赖、零构建、单文件 `editor.js`（~826 行）。
- `inject.py` 注入 CLI（~117 行，纯 Python3 标准库）。
- `SKILL.md` agent 手册：触发短语、两步流程、API、踩坑清单、设计原则。

### Design decisions（v1 锁死的硬约束）
1. 零运行时依赖（不能引外部库）
2. 零构建（不能有 webpack/npm install）
3. 不绑定 AI 宿主（QoderWork/Claude Code/Cursor 都能跑，也能纯手动）
4. 导出必须完全干净（所有编辑器痕迹可剥离）

### Known limitations（v1 故意不做）
- 不支持 React/Vue/Svelte 等框架运行时渲染的页面
- 选区级样式（只改选中文字而非整个元素）坑多，v1 作用域是"整个 activeEditable"
- 自动保存（localStorage）未做，崩溃即丢撤销栈
- 仅适配 Chart.js，其他图表库（ECharts/D3）需自行加 capture/restore
