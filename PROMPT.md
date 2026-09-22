# PROMPT.md · 通用粘贴式提示词（任意聊天 agent 都能用）

有些 agent 没有「技能」机制，或者是纯云端办公助手（千问办公、豆包办公、kimi work、
workbuddy、deepseek、GLM 等），不一定能读 `SKILL.md`。这时用本文件：
把下面对应场景的整段文字**复制粘贴**进你和 agent 的对话即可。

---

## 场景 A：agent 能访问你电脑的终端 / 文件（本地 CLI 类）

> 适用：Claude Code、Codex、Cursor、QoderWork、a1、Gemini CLI、OpenClaw，
> 以及任何能执行 shell 命令的 agent。

复制这段发给 agent（把路径换成你的 HTML）：

```
我要用 html-editor 这个工具把一份静态 HTML 变成可在浏览器里可视化编辑的页面。
工具就在当前目录（含 assets/inject.py 和 assets/editor.js）。请执行：

1. 生成可编辑副本并打开：
   python3 assets/inject.py "/绝对路径/你的.html"
   然后按系统打开它：macOS 用 open，Linux 用 xdg-open，Windows 用 start ""。
   （若本机已 pipx install 过，直接跑：html-editor "/绝对路径/你的.html" 更省事）

2. 告诉我：在浏览器里像 Word 一样改文字、拖区块、调字体，改完点顶栏「⬇ 导出 HTML」
   下载一份剥离了编辑器的干净文件。

3. 如果我希望你把改动写回原文件：在页面里调用
   window.__htmlEditor.exportCleanHTML() 取干净 HTML 字符串，先备份原文件再覆盖。

注意：这份 HTML 必须是静态页面；如果是 React/Vue 运行时渲染的就不适用。
```

---

## 场景 B：agent 是纯云端办公助手，碰不到你的电脑文件

> 适用：千问办公、豆包办公、kimi work、workbuddy 等没有本地 shell / 文件权限的助手。

这类 agent **没法替你跑脚本**，但能给你讲清楚怎么做。复制这段发给它：

```
我有一个叫 html-editor 的本地小工具（一个文件夹，里面有 assets/inject.py）。
请教我在自己电脑上用它，把一份 HTML 变成可视化可编辑的页面。步骤我大概知道，
你帮我确认并补全：

1. 先把 html-editor 文件夹放到电脑某处，确保装了 Python 3。
2. 打开终端，cd 进那个文件夹。
3. 运行：python3 assets/inject.py "/我的/报告.html"
   —— 会在同目录生成 报告.editable.html（不改原文件）。
4. 双击打开 报告.editable.html，浏览器里就能拖区块、改文字、调字体、换图、撤销重做。
5. 改完点顶栏「⬇ 导出 HTML」，下载的就是剥离了编辑器的干净 HTML。

如果哪一步在 Windows / Mac 上命令不一样，请告诉我对应写法。
```

---

## 一行速查（给你自己，不用发给 agent）

```bash
# 不装任何东西，最省事的用法：
python3 assets/inject.py 你的.html && open 你的.editable.html      # macOS
python3 assets/inject.py 你的.html && xdg-open 你的.editable.html  # Linux

# 想要全局命令（任意目录可用）：
pipx install .            # 在本文件夹里执行一次
html-editor 你的.html      # 之后随时随地

# 想接进支持 MCP 的 agent：
pipx install '.[mcp]'                 # 需要 Python 3.10+
python -m html_editor.mcp_server      # 在宿主的 MCP 配置里登记这条命令
```

---

## 各宿主「技能目录」速查（想让它像原生技能一样被自动发现）

把整个 html-editor 文件夹复制进对应目录，重开会话即可：

| 宿主 | 技能目录 |
|---|---|
| QoderWork | `~/.qoderwork/skills/` |
| Claude Code | `~/.claude/skills/` |
| Codex CLI | `~/.codex/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| Cursor | `~/.cursor/skills/`（装完需重载窗口） |
| GitHub Copilot（agent） | `~/.config/github-copilot/skills/` |
| OpenClaw | `~/.openclaw/skills/` |
| a1 / 通用 | `~/.agents/skills/` |

懒得挑？在本文件夹里跑 `bash install.sh`，它会自动探测已装的宿主并复制过去。
