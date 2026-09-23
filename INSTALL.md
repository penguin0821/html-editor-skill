# INSTALL.md · 换台电脑，从 GitHub 下载即用

三步就能用：**下载 → 注入 → 浏览器里改**。核心只依赖 Python 3 和一个浏览器。

---

## 你需要什么

- **一个现代浏览器**（Chrome / Edge / Safari / Firefox 都行）
- **Python 3**：跑注入脚本用。macOS / 多数 Linux 自带；Windows 去 [python.org](https://www.python.org/downloads/) 装，安装时勾选 “Add Python to PATH”。
- **git**（可选）：只有用 `git clone` 下载时才需要。

编辑器内核 `editor.js` 零依赖、离线可用——**不需要 Node，不需要联网**。

---

## 第 1 步：下载

任选一种，下载后得到一个目录（下文统称 `<目录>`）：

- **方式 A（最简单，无需任何工具）**：浏览器打开
  <https://github.com/penguin0821/html-editor-skill/archive/refs/heads/main.zip>
  下载并解压，得到 `html-editor-skill-main/`。
- **方式 B（装了 git）**：`git clone https://github.com/penguin0821/html-editor-skill.git`
- **方式 C（装了 gh）**：`gh repo clone penguin0821/html-editor-skill`

---

## 第 2 步：编辑你的 HTML（核心用法）

```bash
cd <目录>
python3 assets/inject.py 你的.html        # Windows 若 python3 无效，改用 python
```

同目录会生成 `你的.editable.html`（**不修改原文件**）。打开它：

```bash
open 你的.editable.html          # macOS
xdg-open 你的.editable.html      # Linux
start "" 你的.editable.html      # Windows（注意中间那对空引号）
```

或者直接双击 `你的.editable.html`。浏览器里：点文字直接改；鼠标悬到区块上出 `⠿` 手柄，按住拖拽换位；顶栏调字体/字号/颜色/加粗/链接；`⌘/Ctrl+Z` 撤销；改完点顶栏「⬇ 导出 HTML」得到剥离了编辑器的干净文件。

---

## 第 3 步（可选）：装成 agent 技能，一句话触发

- **macOS / Linux**：在 `<目录>` 里跑 `bash install.sh`——自动探测本机装了哪些 agent（QoderWork / Claude Code / Codex / Cursor 等）并复制进去。
  - `bash install.sh --list` 只看探测结果；`--dest <目录>` 装到指定位置。
- **Windows**：没有 bash，手动把整个文件夹拷进对应技能目录，例如：
  - QoderWork：`%USERPROFILE%\.qoderwork\skills\html-editor\`
  - Claude Code：`%USERPROFILE%\.claude\skills\html-editor\`
  - 其他宿主目录见 [README.md](README.md) 的兼容矩阵。

装完重开 agent 会话，说「用 html-editor 编辑 xxx.html」即可。

---

## 第 4 步（可选）：装成全局命令行工具

```bash
pipx install .          # 没有 pipx 就： pip install --user .
html-editor 你的.html    # 之后任意目录都能用，注入并自动开浏览器
```

---

## 第 5 步（可选）：接进支持 MCP 的 agent

需要 **Python 3.10+**：

```bash
pipx install '.[mcp]'
python -m html_editor.mcp_server      # 以 stdio 启动
```

在宿主的 MCP 配置里登记这条命令，示例见 [README.md](README.md)。

---

## 验证装好了

```bash
bash smoke_test.sh      # 六步全绿即 OK（Windows 用 Git Bash 或 WSL 跑）
```

或打开在线 Demo 对照效果：<https://penguin0821.github.io/html-editor-skill/demo/>

---

## 常见情况

- **只想看效果、不想下载**：直接开[在线 Demo](https://penguin0821.github.io/html-editor-skill/demo/)。
- **打开后不能编辑**：多半是打开了原文件而不是 `*.editable.html`；确认文件名带 `.editable`。
- **图表不显示**：那是被编辑的 HTML 自己引用了 CDN（如 Chart.js），需要联网加载，与编辑器无关。
- **Windows `open` 报错**：Windows 没有 `open`，用 `start "" "你的.editable.html"`。

---

## 更多文档

[README](README.md)（总览 + 跨 agent 兼容矩阵）· [USER_GUIDE](USER_GUIDE.md)（人读使用手册）· [SKILL](SKILL.md) / [AGENTS](AGENTS.md)（给 agent 的指令）· [PROMPT](PROMPT.md)（云端办公 agent 的粘贴提示词）· [TECH_NOTES](TECH_NOTES.md)（技术栈与维护）· [CHANGELOG](CHANGELOG.md)
