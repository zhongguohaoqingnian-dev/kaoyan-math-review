# 研数插件 · 交接笔记

> 新会话第一句可以这样说：
> 继续维护 `kaoyan-math-review/` 目录里的「研数」插件（公开仓库 zhongguohaoqingnian-dev/kaoyan-math-review），先读 `HANDOFF.md` 和 `README.md`。用户考数一，保持树形知识树 + 下方原生输入框 + 最近回复条。

## 定位

- DSH profile `desktop` 里常驻的 local bundle：`kaoyan-math-review`（本地开发用 path link，发布走 npm / Git）。
- 入口是**对话顶部的「研数」View 标签**，不是左侧独立面板：
  - `conversation.view`，id `kaoyan-math`，label `研数`，order 5。
- 页面结构：上方是知识树 / 考点详情，下方是对话壳的**原生 composer**；composer 上方有一条「最近回复」。
- 之所以做成 View：原生 composer 只存在于 conversation shell；独立 `main` 面板无法把真实输入框嵌到内容下方。

## 当前版本 1.0.1

- 面向**数一**：树根「数一」→ 高数 / 线代 / 概率 → 章节 → 板块 → 考点。
- 高数 8 章、线代 6 章、概率 8 章骨架都在树里。
- 树根下第一个子节点是**数一历年真题**：2011–2026 共 16 套、362 题；点年份进入试卷，答案默认收起。
- **常微分方程** `ready`：14 个考点、4 个板块。
- **高数 8 章全部 `ready`：常微分方程 14 个考点 + 其余七章 47 个考点、26 个板块**（极限 7、一元微分 8、一元积分 7、空间解析几何 5、多元微分 7、多元积分 7、级数 6）。
- **线性代数 6 章全部 `ready`：36 个考点、18 个板块**（行列式 6、矩阵 7、向量 6、线性方程组 5、特征值 6、二次型 6）。
- **概率论与数理统计 8 章全部 `ready`：35 个考点、25 个板块**（随机事件 5、随机变量 5、多维随机变量 4、数字特征 5、大数定律 4、数理统计基本概念 4、参数估计 4、假设检验 4）。
- 数一大纲 22 章全部 `ready`，全科共 132 个考点（14 + 47 + 36 + 35）、73 个板块。
- 内容按科目分三个对象：`CALCULUS`（高数其余七章）、`LINEAR`、`PROBABILITY`，都按章 id 分键；常微分方程仍是最早的 `SECTIONS` / `CONTENT.ode`。`SUBJECTS` 里每章用 `sections` 指向对应数组。
- `POINTS` 现在横跨「高数 → 线代 → 概率」全部已录章节，上一个 / 下一个考点可跨章连续翻。
- 树默认展开三个科目（`root`、`calculus`、`linear`、`probability`），进页面就能看到各科的章列表；章本身仍是折叠的。
- 22 章全部有内容，「待建」占位页目前不会再出现（`status: "soon"` 的判断仍保留，便于将来加章）。
- 点具体考点进入详情页：左上角「← 知识树」，底部「上一个 / 下一个考点」。
- 点年份进入试卷页：题目列表；点任意题目进入详情页，上方完整题目，下方答案 + 解析；支持「上一题 / 下一题」「返回试卷」；试卷底部「上一套 / 下一套」。
- 题目详情有 **对 / 不会 / 错** 三个状态按钮，再点取消；试卷列表显示每题标记和统计；localStorage key `dsh.kaoyan-math.question-status.v1`。
- 知识树下方是 **真题日历**：按天记录题目状态，点日期查看当天列表，组顺序固定为 不会 → 错 → 对；条目可点回题目详情。history key `dsh.kaoyan-math.question-history.v1`。
- 2026 年每题详情有默认折叠的 **「本题考点 / 方法」**，点开展示 1–2 个考点和方法速查；数据在 `data/methods-2026.json` → `PAPER_METHODS`。其他年份暂未加。
- 方法卡与知识树共用同一套 `method` 节点：每个方法有 `chapterId`，构建 `CHAPTER_METHODS` 后挂到对应章节下，带「方法」标签；方法卡上的「知识树」按钮打开 `MethodView`，方法页列出相关真题。
- 掌握状态存本机 `localStorage`：`dsh.kaoyan-math.mastery.v1`。
- 易错提示的标题现在也走 `rich()`，标题里的 `$A^{*}$` 这类公式能正常渲染（之前会原样打印美元符号）。
- 树页头有进度环、已掌握计数、重置进度。
- 输入框上方「最近回复」：
  - `useChat` selector 读取 `snapshot.order` / `snapshot.nodes`，取最后一条 `assistant-step` 的 text block。
  - `useSession` 读取 running，显示「正在回复…」。
  - `openView("chat", "")` 切到完整 Chat。

## 发布

- 公开仓库：`zhongguohaoqingnian-dev/kaoyan-math-review`（main 分支，MIT）。
- 市场索引：`https://zhongguohaoqingnian-dev.github.io/kaoyan-math-review/market.json`（GitHub Pages 直接托管仓库根目录，`.nojekyll` 关闭 Jekyll）。
- 发版：改 `package.json` 版本 → `npm run check` → `npm run market`（锁定当前 commit）→ commit & push；要发 npm 就 `npm publish` 后 `npm run market -- --source npm` 再 push。
- 本地开发安装：`plugin_manager` 的 `install_bundle` 指向本仓库目录，profile 里是 path link。

## 文件

- `client.js`：全部内容与 UI。顺序大致是：
  1. 内置 TeX-ish 公式渲染器（`SYMBOLS` / `MathParser` / `renderMathNode`）。
  2. 内容 `SECTIONS`、`CONTENT.ode`。
  3. 树数据 `SUBJECTS`、`TREE`、`PAPERS_NODE`、`POINT_INDEX`、`CHAPTER_INDEX`。
  3b. `PAPERS` 是生成块，在文件顶部 `PAPERS_DATA_START/END` 之间；由 `scripts/embed_papers.py` 生成。
  4. CSS。
  5. 组件：`MathText`、`Block`、`PointCard`、`Chevron`、`TreeNode`、`Breadcrumb`、`Panel`。
  6. 注册：`conversation.view`。
- `package.json`：`dsh.client.inject` 含 `@deepseek-ai/dsh-client-ui-conversation` 和 `@deepseek-ai/dsh-client-ui-layout`。
- `locale/zh.json`、`locale/en.json`：插件管理器显示用。
- `icon.svg`：插件图标。
- `data/papers-2011-2026.json`：16 套真题的抽取结果。
- `market.json`：插件市场索引（format 1），发布到 npm 后配合 HTTPS 静态托管给 Discover 用。
- `data/methods-2026.json`：2026 年 22 题的考点/方法速查。
- `scripts/extract_papers.py`：从海岛版 SQLite 只读抽取、清洗 LaTeX、提取答案/图片。
- `scripts/embed_papers.py`：把 JSON 嵌入 `client.js` 的 `PAPERS`。
- `scripts/check-content.mjs`：内容自检。用桩 React 载入 factory，遍历 `SECTIONS` + `LINEAR` + `PROBABILITY`，把每个公式交给真实渲染器解析，检查 `$` / 花括号 / `\left` `\right` / `\begin` `\end` 是否配对、命令是否受支持，并统计章节/板块/考点数。
- `README.md`：给用户看的说明与扩展方式。
- `HANDOFF.md`：本文件。

## 开发流程

1. 改 `client.js`。
2. 校验：
   - `node --check client.js`
   - `node scripts/check-content.mjs`（公式与结构自检，必须 `OK`）
   - `node -e "for (const f of ['package.json','locale/zh.json','locale/en.json']) JSON.parse(require('fs').readFileSync(f,'utf8'))"`
3. bump `package.json` version（当前 1.0.0）。
4. 用 `plugin_manager` 重装（Client JS 有缓存，直接 install 会 `already-installed`）：
   - `action: "remove_bundle"`, `target: "kaoyan-math-review"`
   - `action: "install_bundle"`, `target: "<本仓库目录的绝对路径>"`
5. 用 `cordis_inspect_query` 查 `conversation.view`，确认 `kaoyan-math` occupant active。
6. 告诉用户刷新页面 / 重新点「研数」标签。

## 用户偏好

- 考**数一**；不要数三差分、不要数一/二/三筛选。
- 要**树形逐层展开**：数一 → 高数/线代/概率 → 章节 → 考点 → 知识。
- 内容上方、原生输入框下方；不要额外侧边栏。
- 要在页面里直接看到我的回复（最近回复条），不用切 Chat。
- 中文界面；喜欢边看边用对话改。
- 之前明确说过：不要“全部内容平铺”的页面，也不要独立主面板。

## 已知问题 / 可继续做

- 「研数」View 不是默认选中；用户需要点一下标签。可以研究 persisted view selection / pin，或加一个轻量入口。
- 离开 View 再回来，当前考点和展开状态会重置（只在组件 state 里）；可以持久化到 localStorage。
- 「最近回复」只显示最后一条 assistant 文本；完整历史在 Chat。
- 题目详情页的答案默认直接显示（这是用户明确要求的）；如果以后要“先做后看”，可加隐藏/展开开关。
- 对/不会/错记录按「年份-题号」存；日历按「日期 → 年份-题号」存；重置进度会同时清空掌握、题目状态和日历。
- 日历在知识树页面，位于树卡片下面；默认显示当前月/今天，可切换月份和「今天」。
- 树的默认展开是 `{ root: true, calculus: true }`；用户可能想默认只展开 root。
- 「假设检验」只在数一大纲内，内容里已标注；命题以填选为主。
- 公式量已达 1559 条，`client.js` 约 1.5MB（其中真题 JSON 占 1.2MB）；若继续加内容，可考虑把真题改成年份懒加载。
- 线代内容偏「考点 + 例题」，每章最后没有单独的「章末题型清单」；如需可再加一个汇总考点。
- 公式渲染器支持 `\frac`、`\sqrt`、上下标、积分/求和、希腊字母、`\left/\right`、`\text`、`\mathrm`、`cases`、`aligned`、`pmatrix/bmatrix/vmatrix`、`array`、`gathered`、`overline/hat/vec` 等；极复杂的排版仍可能退化。
- 真题数据较大（`client.js` ~1.3MB）；如果要更快加载，可把 `PAPERS` 改为按年份懒加载/宿主 RPC。

## 约束

- 用 `cordis-plugin-development` skill 的规范；不要 iframe、不要 CDN、不要 import Harness Client 包。
- UI 文本中文；主题只用 `--dsw-alias-*` token。
- 插件装在 profile 里，所有会话可见；文件在 workspace，跨会话保留。
