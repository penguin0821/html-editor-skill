#!/usr/bin/env bash
# html-editor 一键安装（macOS / Linux）—— 跨 agent 宿主
#
# 自动探测本机已装的 agent 宿主技能目录，把 html-editor 复制进去。
# 支持 QoderWork / Claude Code / Codex / Gemini CLI / Cursor / GitHub Copilot /
# OpenClaw / a1，也可用 --dest 指定任意目录。
#
# 用法：
#   bash install.sh                 # 自动探测；探测到多个则交互让你选
#   bash install.sh --host claude   # 指定宿主（见下方 host_dir_of 全名单）
#   bash install.sh --dest <dir>    # 装到指定目录（其下会建 html-editor/）
#   bash install.sh --all           # 装到所有探测到的宿主
#   bash install.sh --list          # 只列出探测结果，不安装
#   bash install.sh --help
#
# 不想用 AI？根本不用装，直接：
#   python3 assets/inject.py 你的.html && open 你的.editable.html
# 或装成命令行工具（推荐，全局可用 html-editor 命令）：
#   pipx install .        # 之后：html-editor 你的.html
#
# 宿主可选值：qoderwork | claude | codex | gemini | cursor | copilot | openclaw | a1

set -euo pipefail

SKILL_NAME="html-editor"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 已知宿主的技能目录（按优先级；探测以「宿主根目录是否存在」为准）
HOST_QODERWORK="$HOME/.qoderwork/skills"
HOST_CLAUDE="$HOME/.claude/skills"
HOST_CODEX="$HOME/.codex/skills"
HOST_GEMINI="$HOME/.gemini/skills"
HOST_CURSOR="$HOME/.cursor/skills"
HOST_COPILOT="$HOME/.config/github-copilot/skills"
HOST_OPENCLAW="$HOME/.openclaw/skills"
HOST_A1="$HOME/.agents/skills"

# 探测顺序（越常用越靠前）
ALL_HOSTS="qoderwork claude codex gemini cursor copilot openclaw a1"

MODE="auto"
FORCE_DEST=""
CHOSEN_HOST=""

usage() { awk 'NR==1{next} /^#/{sub(/^# ?/,"");print;next} {exit}' "${BASH_SOURCE[0]}"; exit 0; }

# 解析参数
while [ $# -gt 0 ]; do
  case "$1" in
    --host)   MODE="host"; CHOSEN_HOST="${2:-}"; shift 2 ;;
    --host=*) MODE="host"; CHOSEN_HOST="${1#*=}"; shift ;;
    --dest)   MODE="dest"; FORCE_DEST="${2:-}"; shift 2 ;;
    --dest=*) MODE="dest"; FORCE_DEST="${1#*=}"; shift ;;
    --all)    MODE="all"; shift ;;
    --list)   MODE="list"; shift ;;
    -h|--help) usage ;;
    *) echo "✗ 未知参数：$1（用 --help 看用法）" >&2; exit 2 ;;
  esac
done

host_dir_of() {
  case "$1" in
    qoderwork) echo "$HOST_QODERWORK" ;;
    claude)    echo "$HOST_CLAUDE" ;;
    codex)     echo "$HOST_CODEX" ;;
    gemini)    echo "$HOST_GEMINI" ;;
    cursor)    echo "$HOST_CURSOR" ;;
    copilot)   echo "$HOST_COPILOT" ;;
    openclaw)  echo "$HOST_OPENCLAW" ;;
    a1)        echo "$HOST_A1" ;;
    *) echo "" ;;
  esac
}

# 探测：哪些宿主目录"已存在"（说明对方装了那个 agent）
detect_hosts() {
  local found=()
  for h in $ALL_HOSTS; do
    local d; d="$(host_dir_of "$h")"
    # 宿主根目录存在（如 ~/.claude、~/.codex、~/.cursor）即认为装了该 agent
    if [ -d "$(dirname "$d")" ]; then found+=("$h"); fi
  done
  echo "${found[@]:-}"
}

# 前置检查
[ -f "$SRC_DIR/SKILL.md" ] || { echo "✗ 源目录里没有 SKILL.md，请在解压后的 html-editor/ 目录里运行" >&2; exit 1; }
[ -f "$SRC_DIR/assets/editor.js" ] && [ -f "$SRC_DIR/assets/inject.py" ] || { echo "✗ assets/ 下缺 editor.js 或 inject.py" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "✗ 未找到 python3，请先安装" >&2; exit 1; }

DETECTED="$(detect_hosts)"

# --list：只报告
if [ "$MODE" = "list" ]; then
  echo "==> 探测到的 agent 宿主："
  if [ -z "$DETECTED" ]; then
    echo "    （无）没探测到已知 agent 宿主的技能目录。"
    echo "    你仍可不装直接用：python3 $SRC_DIR/assets/inject.py 你的.html && open 你的.editable.html"
    echo "    或装成命令行工具：pipx install $SRC_DIR    # 之后全局可用 html-editor 命令"
  else
    for h in $DETECTED; do echo "    · $h → $(host_dir_of "$h")"; done
  fi
  exit 0
fi

# 计算要装到哪些目录
TARGETS=()
case "$MODE" in
  dest)
    [ -n "$FORCE_DEST" ] || { echo "✗ --dest 需要给目录" >&2; exit 2; }
    TARGETS+=("$FORCE_DEST")
    ;;
  host)
    d="$(host_dir_of "$CHOSEN_HOST")"
    [ -n "$d" ] || { echo "✗ 未知宿主：$CHOSEN_HOST（可选：$ALL_HOSTS，或用 --dest 指定目录）" >&2; exit 2; }
    TARGETS+=("$d")
    ;;
  all)
    [ -n "$DETECTED" ] || { echo "✗ 没探测到任何宿主，用 --dest 指定目录" >&2; exit 2; }
    for h in $DETECTED; do TARGETS+=("$(host_dir_of "$h")"); done
    ;;
  auto)
    if [ -z "$DETECTED" ]; then
      echo "==> 没探测到已知 agent 宿主（QoderWork/Claude/Codex/Gemini/Cursor/Copilot/OpenClaw/a1）。"
      echo "    内核零依赖，不装也能用："
      echo "      python3 $SRC_DIR/assets/inject.py 你的.html && open 你的.editable.html"
      echo "    装成全局命令行工具（推荐）： pipx install $SRC_DIR"
      echo "    要装到指定目录： bash install.sh --dest <你的技能目录>"
      exit 0
    fi
    # 探测到 1 个：直接装
    count=$(echo $DETECTED | wc -w | tr -d ' ')
    if [ "$count" = "1" ]; then
      TARGETS+=("$(host_dir_of "$DETECTED")")
    else
      # 多个：交互选择（非交互终端则装到全部）
      echo "==> 探测到多个宿主："
      i=1; arr=()
      for h in $DETECTED; do echo "    [$i] $h → $(host_dir_of "$h")"; arr+=("$h"); i=$((i+1)); done
      echo "    [a] 全部安装"
      if [ -t 0 ]; then
        printf "选哪个？(默认 a) " ; read -r pick
        if [ "$pick" = "a" ] || [ -z "$pick" ]; then
          for h in $DETECTED; do TARGETS+=("$(host_dir_of "$h")"); done
        else
          sel="${arr[$((pick-1))]:-}"
          [ -n "$sel" ] && TARGETS+=("$(host_dir_of "$sel")") || { echo "✗ 无效选择" >&2; exit 2; }
        fi
      else
        for h in $DETECTED; do TARGETS+=("$(host_dir_of "$h")"); done
      fi
    fi
    ;;
esac

install_to() {
  local DEST_ROOT="$1"
  local DEST_DIR="$DEST_ROOT/$SKILL_NAME"
  echo ""
  echo "==> 安装到：$DEST_DIR"
  mkdir -p "$DEST_ROOT"
  if [ -d "$DEST_DIR" ]; then
    local BACKUP="$DEST_DIR.bak.$(date +%Y%m%d-%H%M%S)"
    echo "    已存在旧版本，备份到：$BACKUP"
    mv "$DEST_DIR" "$BACKUP"
  fi
  mkdir -p "$DEST_DIR"
  cp -R "$SRC_DIR/SKILL.md" "$DEST_DIR/"
  cp -R "$SRC_DIR/assets"   "$DEST_DIR/"
  # 文档 + 跨 agent 入口 + Python 包（存在才复制）
  for opt in README.md USER_GUIDE.md TECH_NOTES.md CHANGELOG.md LICENSE \
             AGENTS.md PROMPT.md CLAUDE.md examples html_editor pyproject.toml; do
    [ -e "$SRC_DIR/$opt" ] && cp -R "$SRC_DIR/$opt" "$DEST_DIR/"
  done
  echo "    ✓ 文件已复制"
}

for t in "${TARGETS[@]}"; do install_to "$t"; done

# 语法自检（对第一个目标做一次即可）
FIRST="${TARGETS[0]}/$SKILL_NAME"
echo ""
echo "==> 自检..."
python3 -m py_compile "$FIRST/assets/inject.py" && echo "    ✓ inject.py 语法 OK"
if command -v node >/dev/null 2>&1; then
  node --check "$FIRST/assets/editor.js" && echo "    ✓ editor.js 语法 OK"
else
  echo "    · 未找到 node，跳过 editor.js 语法检查（不影响使用）"
fi

VERSION=$(grep -E "^version:" "$FIRST/SKILL.md" | head -1 | awk '{print $2}')
echo ""
echo "✓ 安装完成：html-editor v$VERSION"
for t in "${TARGETS[@]}"; do echo "  · $t/$SKILL_NAME"; done
echo ""
echo "下一步："
echo "  · 重启 / 新开你 agent 的会话，技能列表里应出现 html-editor"
echo "  · 说一句话试试：「用 html-editor 编辑 ~/Desktop/某份.html」"
echo "  · 或完全手动：python3 $FIRST/assets/inject.py 你的.html && open 你的.editable.html"
echo "  · 想要全局命令：pipx install $SRC_DIR    # 之后任意目录敲 html-editor 你的.html"
echo "  · Cursor 用户：技能装到 ~/.cursor/skills 后需重载窗口；也可用 pipx 命令或 .cursor/rules 触发"
echo "  · 云端办公 agent（千问办公/豆包办公/kimi work 等无本地 shell）：见 PROMPT.md 的手动/CLI 方案"
