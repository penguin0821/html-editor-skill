# -*- coding: utf-8 -*-
"""html-editor · 把任意静态 HTML 变成浏览器里的可视化编辑器。

CLI：安装后提供 `html-editor` 命令。
MCP：可选，`pip install html-editor[mcp]` 后 `python -m html_editor.mcp_server`。
"""
from .core import (  # noqa: F401
    find_editor_js,
    read_editor_js,
    build_snippet,
    inject,
    inject_file,
    open_in_browser,
    default_output_path,
    default_export_filename,
)

__version__ = "1.3.0"

__all__ = [
    "__version__",
    "find_editor_js",
    "read_editor_js",
    "build_snippet",
    "inject",
    "inject_file",
    "open_in_browser",
    "default_output_path",
    "default_export_filename",
]
