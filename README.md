# html-editor

**把任意静态 HTML 变成 Word 式可视化编辑器**——浏览器里直接拖区块、改文字、换字体字号、加粗/斜体/颜色/链接、换图片、撤销重做，改完一键导出剥离了编辑器的干净 HTML。

- 零依赖、零构建、单文件内核（~37KB 的 `editor.js`）
- 不绑定任何 AI 宿主，`file://` 双击即用
- 结构语义识别，不写死任何业务 class，适配任意 AI 生成的报告 / 监控看板 / 落地页
- 面向不会前端的人；也提供 `window.__htmlEditor` API 供 agent 自动化改 HTML
- **三种接入方式**：agent 技能（SKILL.md）、命令行工具（pipx）、MCP server——覆盖从本地 CLI agent 到云端办公助手

当前版本：**v1.3.0**（editor.js / SKILL.md / pyproject.toml / CLI 四处版本一致，`smoke_test.sh` 会硬断言）

---

## 30 秒快速试

```bash
# 无需安装，最省事：
python3 assets/inject.py examples/demo.html
open examples/demo.editable.html      # macOS
# xdg-open examples/demo.editable.html  # Linux
# start "" examples\demo.editable.html  # Windows
```

浏览器弹出后：点文字直接改；鼠标悬到区块上出 `⠿` 手柄，按住拖拽换位；顶栏改字体/字号/颜色；`⌘/Ctrl+Z` 撤销；改完点顶栏「⬇ 导出 HTML」得到干净文件。

---

## 三种接入方式（按你的 agent 选一种）

### 方式一：作为 agent 技能（会被自动发现，说一句话就开）

适用于有「技能」机制、且能读本地文件的宿主（QoderWork / Claude Code / Codex / Cursor 等）。

```bash
bash install.sh                 # 自动探测本机装了哪些宿主，多个则让你选
bash install.sh --list          # 只看探测结果，不安装
bash install.sh --host claude   # 指定宿主（见下方兼容矩阵的可选值）
bash install.sh --dest <目录>   # 装到任意自定义技能目录
bash install.sh --all           # 装到所有探测到的宿主
```

QoderWork 用户也可直接把 `html-editor.skill`（就是本压缩包换扩展名）拖进对话，点「Save skill」。
装完在对话里说「用 html-editor 编辑 xxx.html / 让这份 HTML 可编辑」，agent 会自动注入并打开浏览器。

> 读 `SKILL.md` 的宿主（QoderWork/Claude/a1）和读 `AGENTS.md` 的宿主（Codex/Cursor/Zed 等）都被覆盖——两份内容等价。Claude Code 另有 `CLAUDE.md` 指针。

### 方式二：作为命令行工具（全局 `html-editor` 命令，推荐）

只要本机有 Python 3，装一次就到处能用，和 agent 无关：

```bash
pipx install .            # 在本文件夹里执行一次（没有 pipx 就 pip install --user .）
html-editor 你的.html      # 生成 你的.editable.html 并自动用系统浏览器打开
```

常用参数：

```bash
html-editor 报告.html --no-open            # 只注入不打开
html-editor 报告.html --no-autostart       # 打开后停在预览
html-editor 报告.html --filename 成品.html  # 指定「导出 HTML」的下载名
html-editor --which-js                     # 打印实际用的 editor.js 路径（排障）
```

这条路对**云端办公 agent**（碰不到你电脑文件的助手）尤其有用：让 agent 把命令告诉你，你在自己终端跑一下即可（见 `PROMPT.md` 场景 B）。

### 方式三：作为 MCP server（接进支持 MCP 的 agent）

```bash
pipx install '.[mcp]'                 # 需要 Python 3.10+（mcp 官方 SDK 的要求）
python -m html_editor.mcp_server      # 以 stdio 启动
```

在宿主的 MCP 配置里登记：

```json
{ "mcpServers": { "html-editor": { "command": "python", "args": ["-m", "html_editor.mcp_server"] } } }
```

暴露工具：`make_editable`（注入生成可编辑副本）、`export_note`（导出机制说明）、`locate_editor_js`、`version`。

### 方式零：完全不用 AI，纯手动（任何电脑都行）

```bash
python3 assets/inject.py 报告.html
open 报告.editable.html        # 或直接双击生成的文件
```

零依赖、零宿主，全功能可用。

---

## 跨 agent 兼容矩阵（诚实版）

图例：✅ 已确认可用　⚠️ 可用但有前提　❓ 未逐一实测（按公开机制推断）　— 不适用

| 宿主 | 技能自动发现 | 命令行 (pipx) | MCP server | 推荐接入 | 备注 |
|---|---|---|---|---|---|
| **QoderWork** | ✅ `~/.qoderwork/skills/` | ✅ | ✅ | 技能 / CLI | 本机已实测注入+编辑+导出闭环 |
| **Claude Code** | ✅ `~/.claude/skills/` | ✅ | ✅ | 技能 / CLI | SKILL.md 即其原生技能格式 |
| **Codex CLI** | ✅ `~/.codex/skills/` | ✅ | ✅ | 技能(AGENTS.md) / CLI | 读 AGENTS.md |
| **Cursor** | ⚠️ `~/.cursor/skills/` | ✅ | ✅ | CLI | 装完需重载窗口才被发现 |
| **Gemini CLI** | ✅ `~/.gemini/skills/` | ✅ | ⚠️ | 技能 / CLI | |
| **GitHub Copilot（agent）** | ✅ `~/.config/github-copilot/skills/` | ✅ | ✅ | 技能 / CLI | |
| **OpenClaw** | ✅ `~/.openclaw/skills/` | ✅ | ✅ | 技能 / CLI | |
| **a1 / 通用 agents** | ✅ `~/.agents/skills/` | ✅ | ✅ | 技能 / CLI | |
| **GLM（Coding/agent）** | ❓ 视版本 | ✅ | ✅ | CLI / MCP | 支持 MCP，走 MCP 最稳 |
| **Kimi（Code/work）** | ❓ Code 支持 MCP | ✅ | ✅ | CLI / MCP | |
| **千问办公** | — 无本地技能机制 | ⚠️ 需你自己跑 | — | 手动 / CLI | 云端助手，见 PROMPT.md 场景 B |
| **豆包办公** | — 无本地技能机制 | ⚠️ 需你自己跑 | — | 手动 / CLI | 同上；其自定义智能体能力已下线 |
| **workbuddy** | ❓ 未知 | ❓ | ❓ | 手动 | 扩展机制未公开，走 PROMPT.md 最保险 |
| **deepseek（harness/网页）** | — | ⚠️ 需你自己跑 | — | 手动 | 无本地执行环境时只能给你命令 |

**一句话结论**：内核与宿主完全无关。凡是能跑 `python3` 的电脑，「方式零/方式二」永远成立；
「技能自动发现」取决于宿主是否读 `SKILL.md`/`AGENTS.md`；「MCP」取决于宿主是否支持 MCP。
拿不准的宿主，一律退到 `PROMPT.md`——把命令交到你手上，自己在终端跑。

---

## 包内容

```
html-editor/
├── README.md              # 你在看的这份
├── SKILL.md               # agent 内核手册（触发短语、两步流程、API、踩坑清单）
├── AGENTS.md              # 跨宿主 agent 指令（Codex/Cursor/Zed 等读这个）
├── CLAUDE.md              # Claude Code 指针，指向 SKILL.md
├── PROMPT.md              # 通用粘贴式提示词（云端办公 agent / 无技能机制的宿主）
├── USER_GUIDE.md          # 使用手册（人读的，含所有编辑操作和快捷键）
├── TECH_NOTES.md          # 技术栈 + 设计原则 + 模块划分 + 踩坑史 + 维护指南
├── CHANGELOG.md           # 版本历史
├── LICENSE                # MIT
├── install.sh             # 一键安装（自动探测 8 类宿主，macOS / Linux）
├── pyproject.toml         # 打包配置：pipx/pip 安装 + html-editor 命令 + [mcp] extra
├── html_editor/           # Python 包（CLI + MCP server 的源码）
│   ├── __init__.py
│   ├── core.py            # 注入/打开内核（inject.py 的可导入版，共用同一 editor.js）
│   ├── cli.py             # 命令行入口 html-editor
│   └── mcp_server.py      # 可选 MCP server（FastMCP）
├── assets/
│   ├── editor.js          # 内核，~826 行，零依赖（磁盘上唯一真源）
│   └── inject.py          # 独立注入 CLI，~117 行，纯标准库
└── examples/
    └── demo.html          # 小样本，装完立即试
```

> 单一真源说明：`editor.js` 只在 `assets/` 存一份。`pyproject.toml` 用 setuptools 的
> `package-dir` 把 `assets/` 映射进 `html_editor.assets` 包，安装时复制进 site-packages，
> 仓库里不会出现第二份、也不会与源文件产生偏差（drift）。已用干净 venv 实测：安装后 `html-editor --which-js`
> 指向的 editor.js 与源文件 `cmp` 完全一致。

---

## 适用边界

**适用**：单文件静态 HTML（AI 生成的报告、文档、落地页、监控看板等），可含少量原生 JS 或 Chart.js。

**不适用**：React / Vue / Svelte 等框架运行时渲染的页面——它们会重渲染 DOM，手动改动会被冲掉。

**已知局限**：
- `<pre>` / 等宽架构图里每个 `<span>` 会被单独识别为可编辑文本（粒度偏细）
- 字体/字号作用于「点选的整个文本元素或选中的文字」，不是任意像素区域
- `file://` 下浏览器安全策略禁止网页覆盖本地文件，所以保存靠**下载**再替换原文件
- MCP server 依赖 `mcp` 官方 SDK，需 Python 3.10+；CLI 与手动路径仅需 Python 3.8+

---

## 深入阅读

- 想学会怎么用：读 [USER_GUIDE.md](USER_GUIDE.md)
- 想搞清楚怎么实现的、后续怎么维护：读 [TECH_NOTES.md](TECH_NOTES.md)
- 想让 agent 自动化：读 [SKILL.md](SKILL.md) 或 [AGENTS.md](AGENTS.md)
- 宿主不认识技能 / 云端助手：读 [PROMPT.md](PROMPT.md)
- 想看版本演进：读 [CHANGELOG.md](CHANGELOG.md)

## License

MIT — 随便用、随便改、随便分发，保留版权声明即可。
