#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
html-editor · inject.py

把 assets/editor.js 内联注入到目标 HTML，生成一份「自包含、可直接双击打开」的
可编辑工作副本。注入内容全部带 data-he-ui 标记，编辑器"导出"时会被整段剥离，
因此导出的 HTML 与原件结构一致（只多用户真实改动）。

用法：
    python3 inject.py <输入.html> [输出.html]
    python3 inject.py <输入.html> [输出.html] --no-autostart   # 打开后停在预览，不自动进编辑
    python3 inject.py <输入.html> [输出.html] --filename "xxx.html"  # 指定导出文件名

不传输出路径时，默认写到  <输入名>.editable.html （与输入同目录）。
本脚本不修改输入文件，只读。
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR_JS = os.path.join(HERE, "editor.js")


def read_editor_js():
    with open(EDITOR_JS, "r", encoding="utf-8") as f:
        return f.read()


def build_snippet(js_code, filename, autostart):
    cfg = {"filename": filename, "autoStart": autostart}
    cfg_json = json.dumps(cfg, ensure_ascii=False)
    # 防止页面里出现 </script> 提前闭合（editor.js 内不含，但保险起见转义）
    js_safe = js_code.replace("</script>", "<\\/script>")
    return (
        '\n<!-- ===== html-editor 注入层（导出时自动剥离） ===== -->\n'
        '<script id="__he_config__" data-he-ui>window.__HE__ = ' + cfg_json + ';</script>\n'
        '<script id="__he_script__" data-he-ui>\n' + js_safe + '\n</script>\n'
        '<!-- ===== /html-editor 注入层 ===== -->\n'
    )


def inject(html, snippet):
    lower = html.lower()
    idx = lower.rfind("</body>")
    if idx != -1:
        return html[:idx] + snippet + html[idx:]
    # 没有 </body>：直接追加到末尾
    return html + snippet


def main(argv):
    rest = argv[1:]
    args = []
    autostart = True
    filename = None
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--no-autostart":
            autostart = False
            i += 1
        elif a == "--filename":
            # 值单独成参：吃掉它，绝不落入 positionals（否则与输入同名时会误删输入）
            if i + 1 >= len(rest):
                print("✗ --filename 缺少取值")
                return 2
            filename = rest[i + 1]
            i += 2
        elif a.startswith("--filename="):
            filename = a.split("=", 1)[1]
            i += 1
        elif a.startswith("--"):
            print("✗ 未知参数：", a)
            return 2
        else:
            args.append(a)
            i += 1

    if not args:
        print(__doc__)
        return 2

    src = args[0]
    if not os.path.isfile(src):
        print("✗ 输入文件不存在：", src)
        return 1

    if len(args) >= 2:
        dst = args[1]
    else:
        base, ext = os.path.splitext(src)
        dst = base + ".editable" + (ext or ".html")

    if not filename:
        filename = os.path.basename(os.path.splitext(dst)[0]).replace(".editable", "") + ".html"

    with open(src, "r", encoding="utf-8") as f:
        html = f.read()

    js_code = read_editor_js()
    snippet = build_snippet(js_code, filename, autostart)
    out = inject(html, snippet)

    with open(dst, "w", encoding="utf-8") as f:
        f.write(out)

    print("✓ 已生成可编辑副本：", dst)
    print("  · 双击用浏览器打开即可编辑；改完点顶栏「⬇ 导出 HTML」得到干净文件")
    print("  · 导出文件名：", filename)
    print("  · 自动进入编辑模式：", autostart)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
