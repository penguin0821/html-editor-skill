#!/usr/bin/env bash
# html-editor · 打包前冒烟自检
#
# 固化「版本号多处不同步」这类复发问题的自动预防：四处版本必须一致，否则硬失败。
# 另做语法自检、注入演练、CLI 演练、editor.js 单一真源一致性校验。
#
# 用法： bash smoke_test.sh    （在 html-editor/ 目录里跑；退出码 0 = 全绿）
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

fail() { echo "✗ FAIL: $*" >&2; exit 1; }
ok()   { echo "  ✓ $*"; }

echo "==> 1/6 版本号四处同步"
V_JS=$(grep -oE "version: '[0-9]+\.[0-9]+\.[0-9]+'" assets/editor.js | head -1 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+")
V_SKILL=$(grep -E "^version:" SKILL.md | head -1 | awk '{print $2}')
V_PYPROJECT=$(grep -E "^version = " pyproject.toml | head -1 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+")
V_INIT=$(grep -E "__version__" html_editor/__init__.py | head -1 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+")
echo "    editor.js=$V_JS  SKILL.md=$V_SKILL  pyproject=$V_PYPROJECT  __init__=$V_INIT"
[ -n "$V_JS" ] || fail "editor.js 未解析出版本号"
[ "$V_JS" = "$V_SKILL" ] && [ "$V_JS" = "$V_PYPROJECT" ] && [ "$V_JS" = "$V_INIT" ] \
  || fail "四处版本号不一致（editor.js/SKILL.md/pyproject.toml/__init__.py）"
ok "四处版本一致：$V_JS"

echo "==> 2/6 Python 语法自检"
python3 -m py_compile assets/inject.py html_editor/__init__.py html_editor/core.py html_editor/cli.py html_editor/mcp_server.py \
  || fail "有 .py 文件语法错误"
ok "inject.py + html_editor/*.py 全部 py_compile 通过"

echo "==> 3/6 editor.js 语法自检"
if command -v node >/dev/null 2>&1; then
  node --check assets/editor.js || fail "editor.js 语法错误"
  ok "node --check editor.js 通过"
else
  echo "    · 未找到 node，跳过（不影响使用）"
fi

echo "==> 4/6 install.sh 语法自检"
bash -n install.sh || fail "install.sh 语法错误"
ok "bash -n install.sh 通过"

echo "==> 5/6 注入演练（inject.py，不改原文件）"
TMP=$(mktemp -d)
BEFORE=$(wc -c < examples/demo.html)
python3 assets/inject.py examples/demo.html "$TMP/demo.editable.html" --no-autostart >/dev/null \
  || fail "inject.py 注入失败"
[ -f "$TMP/demo.editable.html" ] || fail "未生成可编辑副本"
grep -q "data-he-ui" "$TMP/demo.editable.html" || fail "副本里没有注入标记 data-he-ui"
grep -q "__he_config__" "$TMP/demo.editable.html" || fail "副本里没有 __he_config__"
AFTER=$(wc -c < examples/demo.html)
[ "$BEFORE" = "$AFTER" ] || fail "原文件被修改了（inject.py 应只读输入）"
ok "注入生成副本、含编辑标记、原文件未被改动"

echo "==> 6/6 CLI 演练 + editor.js 单一真源一致性"
CLI_V=$(python3 -m html_editor.cli --version 2>/dev/null | grep -oE "[0-9]+\.[0-9]+\.[0-9]+")
[ "$CLI_V" = "$V_JS" ] || fail "CLI 版本($CLI_V) 与内核($V_JS) 不一致"
WHICH=$(python3 -m html_editor.cli --which-js 2>/dev/null)
[ -f "$WHICH" ] || fail "--which-js 指向的文件不存在：$WHICH"
# 仓库态下 --which-js 应回落到同级 assets/editor.js，且与真源逐字节一致
cmp "$WHICH" assets/editor.js || fail "--which-js 指向的 editor.js 与 assets/editor.js 不一致（有 drift）"
python3 -m html_editor.cli examples/demo.html "$TMP/cli.editable.html" --no-open >/dev/null \
  || fail "CLI 注入失败"
[ -f "$TMP/cli.editable.html" ] || fail "CLI 未生成副本"
ok "CLI 版本一致、editor.js 单一真源(cmp 一致)、CLI 注入成功"

rm -rf "$TMP"
echo ""
echo "✓ 冒烟自检全绿：html-editor v$V_JS 可以打包发布"
