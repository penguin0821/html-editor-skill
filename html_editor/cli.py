#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""html-editor · 命令行入口。

默认行为：注入编辑器生成可编辑副本，并用系统默认浏览器自动打开（一步到位）。

    html-editor 报告.html                 # 生成 报告.editable.html 并打开
    html-editor 报告.html 副本.html        # 指定输出路径
    html-editor 报告.html --no-open        # 只注入不打开
    html-editor 报告.html --no-autostart   # 打开后停在预览，不自动进编辑模式
    html-editor 报告.html --filename 成品.html  # 指定「导出 HTML」时的下载文件名
    html-editor --version
    html-editor --which-js                 # 打印实际使用的 editor.js 路径（排障用）
"""
import sys
import argparse

from . import __version__
from .core import inject_file, open_in_browser, find_editor_js


def build_parser():
    p = argparse.ArgumentParser(
        prog="html-editor",
        description="把静态 HTML 变成可在浏览器里可视化编辑的副本，改完导出干净 HTML。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input", nargs="?", help="输入的 HTML 文件（不会被修改）")
    p.add_argument("output", nargs="?", help="输出的可编辑副本路径（默认 <输入名>.editable.html）")
    p.add_argument("--out", dest="out_opt", metavar="PATH", help="等价于位置参数 output")
    p.add_argument("--filename", metavar="NAME", help="编辑器「导出 HTML」时使用的下载文件名")
    p.add_argument("--no-autostart", action="store_true", help="打开后停在预览，不自动进入编辑模式")
    p.add_argument("--no-open", action="store_true", help="只生成副本，不自动用浏览器打开")
    p.add_argument("--which-js", action="store_true", help="打印实际使用的 editor.js 路径后退出")
    p.add_argument("--version", action="version", version="html-editor %s" % __version__)
    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)

    if args.which_js:
        print(find_editor_js())
        return 0

    if not args.input:
        build_parser().print_help()
        return 2

    dst = args.output or args.out_opt
    try:
        out_path, export_name = inject_file(
            args.input,
            dst=dst,
            filename=args.filename,
            autostart=not args.no_autostart,
        )
    except FileNotFoundError as e:
        print("✗", e)
        return 1
    except RuntimeError as e:
        print("✗", e)
        return 1

    print("✓ 已生成可编辑副本：", out_path)
    print("  · 导出文件名：", export_name)
    print("  · 自动进入编辑模式：", not args.no_autostart)

    if not args.no_open:
        if open_in_browser(out_path):
            print("  · 已用系统默认浏览器打开")
        else:
            print("  · 自动打开失败，请手动双击上面的副本文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
