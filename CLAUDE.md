# CLAUDE.md

本目录是 **html-editor** 技能包。Claude Code 的操作说明与内核手册都在
[`SKILL.md`](./SKILL.md)，请直接读它——触发短语、两步流程（注入 → 编辑 → 导出）、
`window.__htmlEditor` API、踩坑清单、验收断言全在里面。

跨宿主的等价指令见 [`AGENTS.md`](./AGENTS.md)；人读的使用手册见
[`USER_GUIDE.md`](./USER_GUIDE.md)；技术栈与维护指南见
[`TECH_NOTES.md`](./TECH_NOTES.md)。

一句话用法（Claude Code 有本地 shell，可直接跑）：

```bash
python3 assets/inject.py 你的.html && open 你的.editable.html
# 或若已 pipx install . ：
html-editor 你的.html
```
