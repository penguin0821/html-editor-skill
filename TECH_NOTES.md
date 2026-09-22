# TECH NOTES · html-editor 技术栈、方法论与维护指南

面向后续升级和维护这个 skill 的人（或 AI agent）。读完你会知道：技术选型为什么这样定、代码结构怎么划分、开发过程踩过什么坑、怎么加新功能、怎么验收。

---

## 1. 目标与设计约束

### 1.1 目标

给**不会前端的人**一个 Word 式可视化编辑器，能改**任意 AI 生成的静态 HTML**：拖区块换位、改文字、调字体字号、加粗/斜体/颜色/链接、换图片、撤销重做，改完导出**剥离了编辑器**的干净 HTML。

### 1.2 硬约束

从设计之初就锁死的四条，任何后续改动都别违反：

1. **零运行时依赖**：内核 `editor.js` 不能引任何外部库（Chart.js 是被适配对象，不是依赖）。原因：AI 生成的 HTML 通常离线打开、`file://` 双击即用，任何 CDN 引用都会在离线场景炸掉。
2. **零构建**：不能有 webpack/rollup/npm install 步骤。原因：使用者可能不会前端，`python3 inject.py xxx.html` 一条命令必须能跑通。
3. **不绑定 AI 宿主**：不能依赖 QoderWork / Claude Code / Cursor 中任何一个的私有能力。原因：skill 应该能在任何 agent 或纯手动场景下工作。
4. **导出必须完全干净**：编辑器所有痕迹（DOM、class、属性、事件、脚本）都要能在导出时被剥离。原因：产物是要**替换原文件**或**发出去**的，不能带编辑器垃圾。

### 1.3 软约束（尽量遵守）

- 内核单文件，方便内联注入
- 结构语义识别，不写死任何业务 class（`.container`、`.page` 只是候选之一）
- 撤销栈用 body 快照，不用 diff/patch（简单可靠，60 步够用）
- 所有 UI/属性带 `data-he-ui` 或 `he-*` 命名空间（导出时一刀切）

---

## 2. 技术栈

| 层 | 选型 | 为什么 |
|---|---|---|
| 内核 | 纯 ES5 JavaScript（无框架） | 兼容性最广，任何浏览器直接跑；单文件好内联 |
| 编辑 | `contenteditable` + `document.execCommand` | 浏览器原生富文本能力，零依赖；`execCommand` 虽被 deprecated 但仍是唯一无依赖方案 |
| 样式 | 内联 `style` 属性 | 原页面通常用 class 统一控制样式，编辑改动必须写成内联才能跨环境保留 |
| 拖拽 | Pointer Events + 自定义 ghost/placeholder | HTML5 drag-and-drop 在 `contenteditable` 里冲突严重，Pointer Events 更可控 |
| 撤销 | body 快照栈（`cleanBodyHTML()` → `undoStack`） | 简单可靠；文本输入按聚焦分组避免每字符一栈 |
| 图表适配 | `Chart.getChart()` 捕获 config，DOM 变动后 `resize()` / `new Chart()` 重建 | Chart.js 官方 API，不用改原页面代码 |
| 图片处理 | `FileReader.readAsDataURL()` → base64 内联 | 导出自包含，不依赖外链 |
| 保存 | 下载为主 + File System Access API 为辅 | `file://` 下浏览器禁止网页覆盖本地文件，下载是唯一通用姿势 |
| 注入器 | Python 3 标准库 | macOS/Linux 自带 python3，Windows 也易装；无 pip 依赖 |
| 打包 | zip + `.skill` 双扩展名 | `.skill` 让 QoderWork 一键安装；`.zip` 通用 |

---

## 3. 代码结构

### 3.1 文件树

```
assets/
├── editor.js   # 826 行，内核
└── inject.py   # 117 行，注入 CLI
```

### 3.2 editor.js 模块划分（按 `// ---------- xxx ----------` 分段）

| 行号 | 模块 | 职责 |
|---|---|---|
| 25–47 | 常量 | `UI_ATTR`、`ROOT_ID`、`INLINE_TAGS`、`CONTAINER_TAGS`、`TEXT_SELECTOR`、`FONT_OPTIONS` |
| 49–59 | 全局状态 | `rootContainer`、`editMode`、`activeEditable`、`selectedBlock`、`undoStack`、`redoStack`、`charts` |
| 61–129 | 结构识别工具 | `$/$all/isUI/meaningfulKids/detectRoot/isContainer/findBlock/siblingsOf/isTextEditable` |
| 131–164 | 图表捕获/重绘 | `captureCharts/restoreCharts/resizeCharts` |
| 166–223 | 撤销/重做 | `stripMarkers/cleanBodyHTML/pushState/restoreBody/undo/redo/updateUndoButtons` |
| 225–248 | 可编辑文本 | `applyEditable/clearEditable` |
| 250–282 | 导出 | `exportCleanHTML/download/saveInPlace` |
| 284–341 | 文本样式 | `getActiveTextEl/applyTextStyle/execInline/makeLink` |
| 343–434 | 区块操作 | `selectBlock/duplicateBlock/blankText/deleteBlock/addBlockBelow/replaceImage/moveBlock` |
| 436–489 | 拖拽排序 | `startDrag/moveGhost/onDragMove/endDrag`（Pointer Events） |
| 491–659 | UI 构建 | `injectStyle/buildUI/wireUI/bumpSize/nudgeBlock/syncSizeFont` |
| 661–689 | 悬浮定位 + toast | `positionBlockUI/hideBlockBar/showBlockBar/toast` |
| 691–756 | 全局事件委托 | `wireEvents`（click/focusin/input/keydown/scroll/resize） |
| 758–777 | 进入/退出编辑 | `enterEdit/exitEdit` |
| 779–801 | 启动 | `boot/resync`（含 window.load + 400ms + 1500ms 三次 resync 兜底异步渲染） |
| 803–826 | 对外 API | `window.__htmlEditor = {...}` |

### 3.3 对外 API（agent 自动化用）

```js
window.__htmlEditor = {
  version: '1.2.0',
  exportCleanHTML(): string,       // 剥离后的完整 HTML（含 <!DOCTYPE html>）
  download(): void,                // 触发下载
  saveInPlace(): void,             // 安全上下文下覆盖保存
  enterEdit(): void, exitEdit(): void,
  selectBlock(el): void,
  getBlocks(): Element[],          // 顶层可拖拽区块
  getRoot(): Element,              // 识别出的根容器
  applyTextStyle(prop, value),     // 如 ('fontSize', '40px')
  setText(el, txt),
  moveBlock(el, beforeEl),
  duplicateBlock(), deleteBlock(),
  undo(), redo(),
  findBlock(el): Element,
  _charts(): [{id, config}]        // getter 函数，须调用取数组
};
```

### 3.4 inject.py 契约

```
python3 inject.py <in.html> [out.html] [--filename X] [--no-autostart]
```

- **不修改输入文件**（只读）
- 默认输出 `<name>.editable.html`，与输入同目录（保留相对路径 `js/`、`css/`）
- 注入位置：`</body>` 前；无 `</body>` 则追加到末尾
- 注入内容两段，都带 `data-he-ui`：
  - `<script id="__he_config__">window.__HE__ = {filename, autoStart}</script>`
  - `<script id="__he_script__">/* editor.js 全文，</script> 转义为 <\/script> */</script>`
- 参数解析：**从左到右扫描**（不要用"按前缀分组"，v1.1.1 修过这个坑，见 §5）

---

## 4. 关键算法

### 4.1 detectRoot（根容器识别）

三条规则，按优先级：

```
1) 明确的单一 wrapper（.container/main/#main/.wrapper/#app/#root/.page/.content）
   且该 wrapper 有 ≥2 个"有意义子块"（非 UI、非 script/style）
2) body 下恰好一个有意义的子 wrapper，且它自己也有 ≥2 个有意义子块
3) 否则 → 根 = body
```

**为什么不选"子元素最多的那层"**：v1.0 用过这个启发式，在无 `.container` 的看板上误把 `.kpi-row`（一堆 KPI 卡片的父容器）当根，导致表格单元格全部不可编辑。v1.1 改成上面三条规则，跨 4 类真实文件验证通过。

### 4.2 findBlock（拖拽粒度）

从鼠标位置向上找，直到"父节点是容器"的那层。容器 = 根、`display: flex/grid`、`UL/OL/TABLE/TBODY/TR/DL/FIGURE` 之一。这样表格里的 `<td>` 不会被单独当区块拖，而是整个 `<tr>` 或整个 `<table>` 被拖——符合直觉。

### 4.3 isTextEditable（可编辑文本识别）

一个元素可编辑当且仅当：
- 它的所有 element 子节点都是**行内标签**（`INLINE_TAGS` 白名单：B/STRONG/I/EM/U/S/STRIKE/SPAN/A/CODE/KBD/MARK/SMALL/SUB/SUP/BR/IMG）
- 且它自己有非空文本

这样 `<p>正文<strong>加粗</strong>正文</p>` 整个 `<p>` 可编辑（含内嵌 `<strong>`），而 `<div><h1>标题</h1><p>段落</p></div>` 的 `<div>` 不可编辑（子节点是块级），但里面的 `<h1>` 和 `<p>` 各自可编辑。

### 4.4 撤销栈策略

- **快照粒度**：整个 body 的 cleanHTML（剥掉编辑器标记后的 innerHTML）
- **触发时机**：每次离散操作前 `pushState()`（移动、删除、复制、换图、字体样式应用）
- **文本输入分组**：`focusin` 时记 `pendingSnapshot`，第一次 `input` 时把 pendingSnapshot 入栈，之后 1400ms 内的连续输入算同一组
- **栈深**：60 步，超出丢弃最早
- **快照里的合成 id**：`he_canvas_XXXX` 必须保留（`restoreCharts` 靠它找回画布重建），**只在 `exportCleanHTML` 的克隆里剥掉**（见 §5 坑 6）

### 4.5 图表适配

```
boot/resync 时：
  captureCharts() → 遍历所有 <canvas>，Chart.getChart(cv) 取实例，
                    无 id 则赋 he_canvas_XXXX，push {id, config} 到 charts[]

DOM 变动后（restoreBody/moveBlock）：
  restoreCharts() → 遍历 charts[]，getElementById(c.id)：
                    - 若该 canvas 已有 Chart 实例 → resize()
                    - 若没有（快照重建后是空 canvas） → new Chart(cv, c.config)
```

**为什么不用 Chart.js 的 update()**：update 要求 data 变了，我们的场景是 canvas DOM 被替换但 config 不变，re-instantiate 更直接。

### 4.6 异步渲染兜底（resync）

很多 AI 生成的看板页面在 `DOMContentLoaded` 之后才异步渲染内容（pako 解压内嵌数据、setTimeout、fetch 后填充）。`boot()` 里加了三次 resync：

```js
window.addEventListener('load', resync);
setTimeout(resync, 400);
setTimeout(resync, 1500);
```

`resync()` 重探根、重挂 contenteditable、重捕图表。更慢的渲染（>1.5s）用户可以手动重载页面。

---

## 5. 踩坑史（按发现顺序）

每条都是真实 bug，都已在内核里修掉，写在这里防止后续维护者重蹈覆辙。

### 坑 1：导出泄漏 `he-bodypad`（v1.0 → v1.1）

**现象**：`exportCleanHTML()` 产物里残留 `class="he-bodypad"`（编辑模式给 body 加的顶栏占位 padding）。
**根因**：`stripMarkers` 只清了 `contenteditable`、`data-he-text`、`data-he-spell`，漏了编辑器 class。
**修法**：`stripMarkers` 里显式列出所有 `he-*` class 并从匹配元素和 root 上都移除；末尾扫一遍 `class=""` 空属性删掉。
**教训**：所有编辑器命名空间的东西，必须在 `stripMarkers` 里有对应清理；新增任何 `he-*` class 都要同步加进去。

### 坑 2：撤销后拖拽失效（v1.0 → v1.1）

**现象**：编辑 → 撤销 → 再想拖区块，拖不动。
**根因**：`restoreBody` 用 `insertAdjacentHTML` 替换 body 内容，boot 时缓存的 `rootContainer` 已脱离文档，`findBlock` 在死节点上跑。
**修法**：`restoreBody` 末尾重新 `rootContainer = detectRoot()`，并 `applyEditable()` 重挂、`restoreCharts()` 重建。
**教训**：任何"整体替换 DOM"的操作之后，所有缓存的元素引用都要重探。

### 坑 3：无 `.container` 页面区块识别过窄（v1.0 → v1.1）

**现象**：在一个无外壳的监控看板上，只识别出 5 个区块（应该是 7 个），表格 282 个单元格一个都不可编辑。
**根因**：旧 `detectRoot` 兜底逻辑是"取子元素最多的那层"，误把 `.kpi-row`（KPI 卡片父容器）当根，导致根之外的内容都不在编辑范围。
**修法**：改成三条规则（见 §4.1），无单一 wrapper 时根 = body。
**教训**：结构启发式必须**保守**——宁可根选大（body）也不要选小，选小了会漏内容；选大了顶多多几个可拖区块，无害。

### 坑 4：异步渲染内容挂不上编辑（v1.1 预防性加固）

**现象**：pako 解压内嵌数据后 setTimeout 渲染的 KPI 卡片，boot 时 DOM 还是空的，`applyEditable` 没东西可挂。
**修法**：加 `resync()`（window.load + 400ms + 1500ms 各一次）重探根、重挂 editable、重捕图表。
**教训**：AI 生成的页面经常异步渲染，boot 不能只跑一次；三次 resync 覆盖 99% 场景，更慢的用户手动重载。

### 坑 5：inject.py `--filename` 参数解析炸掉（v1.1.0 → v1.1.1）

**现象**：`python3 inject.py in.html out.html --filename in.html` 报"输入文件不存在：out.html"。
**根因**：旧解析用 `args = [a for a in argv[1:] if not a.startswith("--")]` 收集位置参数，`--filename` 的值 `in.html` 也被收进去；然后用 `args = [a for a in args if a != filename]` 剔除——把**所有**等于 `in.html` 的位置参数都删了，包括真正的输入路径。
**修法**：改成从左到右扫描，遇到 `--filename` 直接吃掉下一个 argv 作为值，绝不落入 positionals；同时支持 `--filename=X` 写法。
**教训**：CLI 参数解析不要用"按前缀分组"的偷懒写法，规规矩矩顺序扫描；写单元测试覆盖"值与位置参数同名"的边界。

### 坑 6：导出泄漏 `he_canvas_XXXX` 合成 id（v1.1.0 → v1.1.1）

**现象**：无 id 的 `<canvas>` 页面，导出 HTML 里残留 `id="he_canvas_a3f9k2"`。
**根因**：`captureCharts` 给无 id canvas 赋合成 id 供 `restoreCharts` 用，但 `stripMarkers` 不清理它（**也不能清理**——撤销快照需要这个 id 让 restore 找回画布）。
**修法**：在 `exportCleanHTML` 的克隆里单独剥掉 `canvas[id^="he_canvas_"]` 的 id 属性。**不动 `stripMarkers`**，否则撤销后图表全丢。
**教训**：编辑器内部状态和导出产物是两个世界，清理逻辑要分清楚哪些是"全局清理"（stripMarkers，用于快照和导出）哪些是"仅导出清理"（exportCleanHTML 里额外一步）。

### 坑 7：内嵌浏览器打不开 `file://`（环境限制）

**现象**：用 `builtin_browser` 的 `navigate` 打开 `file:///...editable.html` 被拒。
**根因**：`navigate` 只支持 http(s) 协议。
**修法**：自动化验收时起 `python3 -m http.server` 走 localhost；真人用户走 `open` 命令直接 `file://`。
**教训**：这是环境限制不是 bug，SKILL.md 默认走系统 `open` 命令绕开它。

### 坑 8：自动化标签里 `a.click()` 下载不落地（环境限制）

**现象**：MCP 标签组里跑 `download()`，浏览器没弹下载，`~/Downloads` 也没文件。
**根因**：程序化 `a.click()` 缺用户手势，被浏览器拦截 blob 下载。
**修法**：自动化验收改用 `exportCleanHTML()` 拿字符串，自己 POST 到本地 sink 服务落盘；真人用户点顶栏按钮正常。
**教训**：所有"需要用户手势"的浏览器能力（下载、剪贴板写、FSA），自动化场景都要有 fallback。

### 坑 9：`_charts` 是 getter 函数不是数组（API 设计小坑）

**现象**：验收脚本 `(E._charts || []).length` 永远返回 0，误以为图表没捕获。
**根因**：`_charts: function () { return charts; }` 是 getter 函数，`.length` 拿到的是函数元数（arity = 0）。
**修法**：验收脚本必须 `E._charts()` 调用取数组。SKILL.md 里加注释说明。
**教训**：暴露内部状态的 API 要么直接给数组（快照），要么命名成 `getCharts()` 让人一眼看出是函数。`_charts` 这种暧昧命名是坑。

---

## 6. 验收清单（每次改内核必跑）

### 6.1 语法自检

```bash
node --check assets/editor.js
python3 -m py_compile assets/inject.py
```

### 6.2 跨文件类型回归（至少覆盖 4 类）

| 类型 | 特征 | 代表文件 |
|---|---|---|
| A | `.container` 外壳 + 静态 DOM + CDN Chart.js | GDPR 汇报 |
| B | 无外壳 + body 根 + JS 运行时渲染 + pako 内嵌数据 | detection_dashboard |
| C | 单 `.page` 外壳 + tab 切换按钮 + 相对路径 Chart.js + 大表格 | pii_dashboard |
| D | 无 id canvas fixture（合成 id 路径） | 自制最小 fixture |

每份文件跑：

```js
// 1) 根识别
E.getRoot()  // 期望：A=DIV.container, B=BODY, C=DIV.page, D=DIV.page

// 2) 区块数 > 0，可编辑元素数 > 0
E.getBlocks().length
document.querySelectorAll('[contenteditable="true"]').length

// 3) 图表捕获
E._charts().length  // 期望等于页面 canvas 数（有 Chart 实例的）

// 4) 编辑+撤销
E.setText(h1, 'X'); E.undo();  // h1.textContent 回到原值

// 5) 拖拽+撤销+图表存活
E.moveBlock(footer, blocks[0]);
// 所有 canvas 仍有 Chart.getChart(cv) 实例
E.undo();  // 顺序恢复

// 6) 导出零残留
const html = E.exportCleanHTML();
(html.match(/data-he-ui|he_canvas_|contenteditable|__he_|he-(selected|hover|dragging|bodypad|ghost|placeholder)/g) || []).length === 0

// 7) 导出保留 doctype、canvas、script src
html.startsWith('<!DOCTYPE html>')
html.includes('<canvas')
html.includes('chart.umd.min.js')  // 或原页面的 CDN
```

### 6.3 交互验收（真人浏览器）

- tab 按钮点击仍能切页（编辑模式下）
- 拖区块后 Chart.js 图表不变形
- 撤销后图表不空白
- 换图后导出文件里图是 base64 内联
- 下载按钮在真人点击时正常落地

### 6.4 验收脚本模板

`examples/` 里可以放一个 `validate.js`，在浏览器 Console 里粘贴跑，返回 pass/fail 表。

---

## 7. 怎么加新功能

### 7.1 加一个文本样式（比如"高亮背景"）

1. `applyTextStyle(prop, value)` 已支持任意 CSS 属性，直接调用 `applyTextStyle('backgroundColor', '#ff0')` 即可
2. 在 `buildUI()` 的格式化条里加按钮，`wireUI()` 里绑事件
3. 按钮和容器都带 `data-he-ui`，导出自动剥离
4. 跑 §6 验收

### 7.2 加一种区块操作（比如"合并两个区块"）

1. 在 `// ---------- 区块操作 ----------` 段加函数 `mergeBlocks(a, b)`
2. 操作前 `pushState()`，操作后 `restoreCharts()`
3. 暴露到 `window.__htmlEditor`
4. 在区块工具条加按钮
5. 跑 §6 验收，特别是撤销路径

### 7.3 适配新的图表库（ECharts / D3）

1. 在 `captureCharts()` 旁边加 `captureECharts()`：遍历 `[_echarts_instance_]` 属性的 div，`echarts.getInstanceByDom(el)` 取实例，`getOption()` 存 config
2. 在 `restoreCharts()` 旁边加 `restoreECharts()`：`echarts.init(el).setOption(config)`
3. `boot/resync/restoreBody/moveBlock` 里都调一遍
4. 合成 id 同样用 `he_echarts_XXXX`，`exportCleanHTML` 里剥掉
5. 跑 §6 验收

### 7.4 加自动保存（localStorage）

1. `pushState()` 后异步写 `localStorage.setItem('he_autosave_' + FILENAME, cleanBodyHTML())`
2. `boot()` 时检查 localStorage 有没有比当前 body 更新的快照，弹 toast 问用户"检测到未保存的编辑，恢复吗？"
3. `exportCleanHTML()` 后清掉 localStorage
4. 注意：`file://` 下 localStorage 是按 origin 隔离的，所有 `file://` 页面共享一个 origin，key 必须带 FILENAME 区分

### 7.5 加"选区级别"的样式（不是整个元素）

现在 `applyTextStyle` 作用于整个 `activeEditable`。要支持"只改选中文字"，需要：

1. `window.getSelection()` 拿 Range
2. `document.execCommand('styleWithCSS', false, true)` 打开 CSS 模式
3. `document.execCommand('fontSize', false, '5')` 这类只支持 1–7 的旧 API，要自定义需用 `Range.surroundContents(<span style="...">)`
4. 注意 `surroundContents` 在跨元素选区会抛错，要先 `Range.extractContents()` 再包

这条路坑多，v1 故意没做。要做的话建议先写一个 `wrapSelectionWithStyle(prop, value)` 工具函数，覆盖 90% 单元素内选区场景。

---

## 8. 版本演进

见 [CHANGELOG.md](CHANGELOG.md)。

大版本节奏：

- **v1.x**：核心 4 功能（拖区块、字体、字号、文字）+ 撤销重做 + 区块增删复制 + 行内富文本 + 图片替换。已稳定。
- **v2.x（规划）**：自动保存、选区级样式、ECharts/D3 适配、多人协作后端、AI 辅助改写（"把这段改得更正式"）。
- **v3.x（远期）**：从"编辑现有 HTML"扩展到"用自然语言生成 + 编辑"的闭环。

---

## 9. 维护者备忘

- **改内核前先跑一遍 §6 验收**，记录基线；改完再跑，对比差异。
- **新增任何 `he-*` class 或 `data-he-*` 属性，必须同步加到 `stripMarkers`**（或明确注释为什么不需要）。
- **新增任何合成 id（如 `he_canvas_`），必须同步加到 `exportCleanHTML` 的剥离逻辑**。
- **不要在 `stripMarkers` 里剥合成 id**——撤销快照需要它们。
- **`detectRoot` 的三条规则顺序不能乱**：明确 wrapper → body 下唯一 wrapper → body 兜底。
- **`resync` 的三次时机（load + 400 + 1500ms）是经验值**，覆盖大多数异步渲染；改之前先确认新页面真的需要更晚的时机。
- **inject.py 的参数解析必须从左到右扫描**，不要回退到"按前缀分组"的写法。
- **版本号四处同步**：`editor.js` 的 `window.__htmlEditor.version`、`SKILL.md` frontmatter、`pyproject.toml` 的 `version`、`html_editor/__init__.py` 的 `__version__`（`CHANGELOG.md` 记录历史）。改一处就得改四处——别靠记忆，**跑 `bash smoke_test.sh`**，它第一步就硬断言四处一致，不一致直接 fail。
- **editor.js 单一真源**：只在 `assets/editor.js` 存一份。`pyproject.toml` 用 `[tool.setuptools.package-dir] "html_editor.assets" = "assets"` 把它映射进包，安装时复制进 site-packages，不要手动往 `html_editor/` 里再拷一份（会 drift）。`smoke_test.sh` 第 6 步用 `cmp` 校验 `--which-js` 指向的文件与 `assets/editor.js` 逐字节一致。
- **`html_editor/core.py` 与 `assets/inject.py` 共用同一注入逻辑**：改注入行为（`build_snippet`/`inject`/输出命名）时两处都要改，或考虑让 inject.py 直接 import core。
- **MCP server 需 Python 3.10+**（`mcp` SDK 要求），已用环境标记 `; python_version>='3.10'` 约束在 `[mcp]` extra 里；CLI 与手动路径保持 3.8+ 可用。`mcp_server.py` 对 `mcp` 做 lazy import，未装时 `build_server()` 抛友好错误而非 import 崩。
- **发布前**：跑 `bash smoke_test.sh`（六步全绿）→ 跑 §6 全部浏览器验收 → 更新 CHANGELOG → 清 `__pycache__`/`*.editable.html` 等临时产物 → 打 zip 和 .skill → 在 QoderWork 里用 .skill 装一遍确认能跑。

---

## 10. 参考资料

- `SKILL.md`：agent 读的内核手册（触发短语、两步流程、API、踩坑清单）
- `AGENTS.md` / `CLAUDE.md` / `PROMPT.md`：跨宿主 agent 入口（读 AGENTS.md 的宿主 / Claude Code 指针 / 无技能机制宿主的粘贴提示词）
- `USER_GUIDE.md`：人读的使用手册
- `README.md`：三种接入方式 + 跨 agent 兼容矩阵
- `CHANGELOG.md`：版本历史
- `smoke_test.sh`：打包前冒烟自检（版本同步/语法/注入/CLI/单一真源）
- [MDN: contenteditable](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/contenteditable)
- [MDN: document.execCommand](https://developer.mozilla.org/en-US/docs/Web/API/Document/execCommand)（deprecated 但仍是唯一无依赖富文本方案）
- [Chart.js API: getChart](https://www.chartjs.org/docs/latest/developers/api.html#chart-getchart-item)
- [File System Access API](https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API)（仅 https/localhost）
