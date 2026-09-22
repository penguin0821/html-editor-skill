#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""html-editor · MCP server（可选）。

把 html-editor 的注入/导出能力封装成 MCP 工具，供任意支持 MCP 的 agent 宿主
（Claude Code、Codex、Cursor、QoderWork、GLM Coding、通义灵码、Kimi Code 等）调用。

安装可选依赖后运行：
    pip install 'html-editor[mcp]'      # 或 pipx install 'html-editor[mcp]'
    python -m html_editor.mcp_server     # 以 stdio 传输启动

在宿主的 MCP 配置里登记（示例）：
    {
      "mcpServers": {
        "html-editor": {
          "command": "python",
          "args": ["-m", "html_editor.mcp_server"]
        }
      }
    }

暴露的工具：
    make_editable(input_path, output_path=None, filename=None, autostart=True, open_browser=False)
        注入编辑器，返回生成的可编辑副本绝对路径。
    export_note()  -> 关于「导出干净 HTML」的说明（导出发生在浏览器里，非本进程）。
    locate_editor_js() -> 打印实际使用的 editor.js 路径（排障）。
    version()      -> 版本号。
"""
from typing import Optional

from . import __version__
from .core import inject_file, find_editor_js, open_in_browser


def _require_mcp():
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
        return FastMCP
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "未安装 MCP 依赖。请先执行：pip install 'html-editor[mcp]'"
        ) from e


def build_server():
    FastMCP = _require_mcp()
    mcp = FastMCP("html-editor")

    @mcp.tool()
    def make_editable(
        input_path: str,
        output_path: Optional[str] = None,
        filename: Optional[str] = None,
        autostart: bool = True,
        open_browser: bool = False,
    ) -> str:
        """给静态 HTML 注入可视化编辑器，生成可编辑副本（不修改原文件）。

        参数：
            input_path:   输入 HTML 的路径。
            output_path:  输出副本路径；缺省为 <输入名>.editable.html。
            filename:     编辑器「导出 HTML」时的下载文件名；缺省据输出名推断。
            autostart:    打开后是否直接进入编辑模式（默认 True）。
            open_browser: 是否立即用系统默认浏览器打开副本（默认 False，
                          云端/无图形环境应保持 False）。
        返回：生成的副本绝对路径，以及一行下一步提示。
        """
        dst, export_name = inject_file(
            input_path, dst=output_path, filename=filename, autostart=autostart
        )
        opened = ""
        if open_browser:
            opened = "（已尝试用系统浏览器打开）" if open_in_browser(dst) else "（自动打开失败，请手动打开）"
        return (
            "可编辑副本已生成：%s%s\n"
            "下一步：在浏览器里打开它进行可视化编辑，改完点顶栏「⬇ 导出 HTML」得到"
            "剥离了编辑器的干净文件（导出名：%s）。" % (dst, opened, export_name)
        )

    @mcp.tool()
    def export_note() -> str:
        """说明「导出/保存」的机制与边界。"""
        return (
            "导出发生在浏览器页面内，不在本 MCP 进程：\n"
            "1) 顶栏「⬇ 导出 HTML」下载一份剥离编辑器的干净 HTML（file:// 与任意浏览器都可用）。\n"
            "2) 顶栏「💾 保存」仅在 https:// 或 localhost 安全上下文出现，用 File System Access API 覆盖保存。\n"
            "agent 若要自动写回原文件：调用页面里的 window.__htmlEditor.exportCleanHTML() 取干净字符串，"
            "先备份原文件再覆盖。"
        )

    @mcp.tool()
    def locate_editor_js() -> str:
        """打印实际使用的 editor.js 绝对路径（排障用）。"""
        return find_editor_js()

    @mcp.tool()
    def version() -> str:
        """返回 html-editor 版本号。"""
        return __version__

    return mcp


def main():
    mcp = build_server()
    mcp.run()  # 默认 stdio 传输


if __name__ == "__main__":
    main()
