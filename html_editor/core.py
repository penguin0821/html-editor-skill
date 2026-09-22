#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
html-editor · CLI 内核

把 assets/editor.js 内联注入到目标 HTML，生成一份「自包含、可直接双击打开」的
可编辑工作副本。注入内容全部带 data-he-ui 标记，编辑器「导出」时会被整段剥离，
因此导出的 HTML 与原件结构一致（只多用户真实改动）。

这个模块是 inject.py 的可导入版本，二者共用同一份注入逻辑与同一份 editor.js
（editor.js 是磁盘上唯一的真源，CLI 安装时通过 setuptools package-dir 映射进包，
不产生第二份拷贝）。

对外函数：
    find_editor_js()                -> editor.js 的绝对路径
    read_editor_js()                -> editor.js 源码字符串
    build_snippet(js, filename, autostart) -> 注入片段字符串
    inject(html, snippet)           -> 注入后的完整 HTML 字符串
    inject_file(src, dst=None, filename=None, autostart=True) -> (输出路径, 导出文件名)
    open_in_browser(path)           -> 用系统默认程序打开（跨平台）
"""
import os
import sys
import json
import subprocess

__all__ = [
    "find_editor_js",
    "read_editor_js",
    "build_snippet",
    "inject",
    "inject_file",
    "open_in_browser",
    "default_output_path",
    "default_export_filename",
]


def find_editor_js():
    """定位 editor.js。优先环境变量，其次安装态包内路径，最后仓库态同级 assets。"""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.environ.get("HTML_EDITOR_JS"),
        os.path.join(here, "assets", "editor.js"),        # 安装态：html_editor/assets/editor.js
        os.path.join(here, "..", "assets", "editor.js"),  # 仓库态：与 html_editor/ 同级的 assets/
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    # importlib.resources 兜底（zip 安装等边缘情形）
    try:
        from importlib import resources
        ref = resources.files("html_editor.assets").joinpath("editor.js")  # py3.9+
        p = str(ref)
        if os.path.isfile(p):
            return p
    except Exception:
        pass
    raise RuntimeError(
        "找不到 editor.js。请确认它位于 assets/editor.js，"
        "或用环境变量 HTML_EDITOR_JS 指定其绝对路径。"
    )


def read_editor_js():
    with open(find_editor_js(), "r", encoding="utf-8") as f:
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


def default_output_path(src):
    base, ext = os.path.splitext(src)
    return base + ".editable" + (ext or ".html")


def default_export_filename(dst):
    return os.path.basename(os.path.splitext(dst)[0]).replace(".editable", "") + ".html"


def inject_file(src, dst=None, filename=None, autostart=True):
    """读入 src，注入编辑器，写到 dst（默认 <src>.editable.html）。不修改 src。

    返回 (dst, filename)。
    """
    if not os.path.isfile(src):
        raise FileNotFoundError("输入文件不存在：%s" % src)
    if not dst:
        dst = default_output_path(src)
    if not filename:
        filename = default_export_filename(dst)

    with open(src, "r", encoding="utf-8") as f:
        html = f.read()

    snippet = build_snippet(read_editor_js(), filename, autostart)
    out = inject(html, snippet)

    with open(dst, "w", encoding="utf-8") as f:
        f.write(out)
    return dst, filename


def open_in_browser(path):
    """用系统默认程序（通常是浏览器）打开本地文件。跨平台，失败不抛异常只返回 False。"""
    path = os.path.abspath(path)
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", path])
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        # 再退一步用 webbrowser（会尊重 BROWSER 环境变量）
        try:
            import webbrowser
            return webbrowser.open("file://" + path)
        except Exception:
            return False
