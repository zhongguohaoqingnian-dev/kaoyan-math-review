# 研数 · 考研数学复习（侧边栏插件）

在对话顶部注册一个「研数」视图：切过去是一棵「数一」知识树，下方仍是原生输入框。

## 安装

1. 打开 Harness 的 **Plugins** 页面 → **More**（Experimental plugins）→ 打开 **Custom plugin markets**。
2. 在 **Discover** 里添加索引地址：`https://zhongguohaoqingnian-dev.github.io/kaoyan-math-review/market.json`
3. 找到「研数 · 考研数学复习」安装，刷新页面后对话顶部会出现「研数」标签。

索引里锁定的是某个 commit，安装的是包内声明的 `dsh` bundle 与 `dsh.client`。本地开发时用 `plugin_manager` 的 `install_bundle` 指向本目录即可（profile 里存的是 path link）。

## 当前版本

- 对话顶部新增「研数」标签；切过去后**整页是知识树**，没有额外的侧边目录，树本身就是导航。
- 内容下方保留**原生对话输入框**（模型、权限、附件、排队等能力都在），可以边看边发消息让我改。
- 输入框上方有一条**「最近回复」**：实时显示我最后一条回复（流式时显示“正在回复…”），不用切回 Chat 就能看到；点“展开 Chat”看完整历史。
- 左侧仍然是 Harness 自带的会话侧边栏，不再有第二个导航栏。
- 面向**数一**，覆盖大纲全部 **21 章、132 个考点**：
  - 高数 8 章（极限、一元微分、一元积分、空间解析几何、多元微分、多元积分、级数 47 个考点 + 常微分方程 14 个）；
  - 线代 6 章 36 个考点；
  - 概率 8 章 35 个考点。
- 知识页可勾选「已掌握」，进度写入本机 `localStorage`，刷新后保留；知识树里会显示勾选状态。
- 树页头有进度环、已掌握计数、一键重置；知识页有返回知识树和上一个/下一个考点。
- 「上一个 / 下一个考点」按「高数 → 线代 → 概率」全科顺序串联，跨章也能连续翻。
- 理由做成「对话视图」而不是独立主面板：只有对话壳里才有原生输入框；独立面板无法把真实 composer 搬到下方。
- 公式由内置的小型 TeX 渲染器绘制，不依赖 CDN 或第三方数学库。

## 目录

```
kaoyan-math-review/
├── package.json          # bundle 与 dsh.client 声明
├── cordis.patch.yml      # 插入 Host 行
├── index.js              # Host 半边（空实现，负责激活 bundle）
├── client.js             # 侧边栏图标、主面板、公式渲染、全部内容
├── locale/{zh,en}.json   # 插件管理器中显示的名称与描述
├── data/papers-2011-2026.json  # 16 套数一真题的抽取结果
├── scripts/              # 真题抽取 / 嵌入 + 内容自检
└── icon.svg              # 插件图标
```

## 扩展方式

内容与渲染都在 `client.js`，按顺序分成五段：

1. `SYMBOLS` / `MathParser`：公式渲染器。
2. `SECTIONS`：常微分方程的板块与考点。每个考点包含 `id`、`title`、`lead`、`body`。
3. `CALCULUS` / `LINEAR` / `PROBABILITY`：高数其余七章、线代六章、概率八章的板块与考点，按章节 id 存成对象（高数 `limits`、`derivative`、`integral`、`vectors`、`multiderivative`、`multiintegral`、`series`；线代 `determinant`、`matrix`、`vector-space`、`linear-system`、`eigen`、`quadratic`；概率 `event`、`random-variable`、`multi-random`、`expectation`、`limit-theorem`、`statistics`、`estimation`、`hypothesis`）。
4. `CONTENT`：常微分方程的页面数据。
5. `SUBJECTS` / `TREE`：知识树的科目、章节、板块、考点层级；每章用 `sections` 指向 `CONTENT.ode.sections`、`CALCULUS[章 id]`、`LINEAR[章 id]` 或 `PROBABILITY[章 id]`。
6. `POINTS`：把高数、线代、概率的全部考点按顺序摊平，供「上一个 / 下一个考点」使用。
7. `PAPERS`：由 `data/papers-2011-2026.json` 生成并嵌入 `client.js` 顶部；源数据来自数一学习 OS-海岛版的 SQLite。
8. `CSS`：面板样式，全部使用 `--dsw-alias-*` 主题 token。
9. 组件与注册：当前注册到 `conversation.view`，id 为 `kaoyan-math`，标签为「研数」。

知识树本身就是导航；要加章节或考点，直接改 `SECTIONS` / `LINEAR` 再挂到 `SUBJECTS`，不需要再恢复左侧大纲栏。

视图内的输入框是对话壳的原生 composer，不是仿制的：消息会进入当前 Session。输入框上方读取 Chat 目标的最新 assistant 文本作为「最近回复」，所以普通回复在这里就能看到；完整历史仍可切到 Chat。

### 追加一个考点

在 `SECTIONS`（常微分方程）、`CALCULUS`（高数）、`LINEAR`（线代）或 `PROBABILITY`（概率）对应章、对应板块的 `points` 数组里追加对象即可：

```js
{
  id: "my-point",                 // 全局唯一，用于掌握记录
  title: "考点标题",
  lead: "一句话概括。",
  body: [
    p("段落，行内公式写成 $y'=f(x)$。"),
    f("\\frac{\\mathrm{d}y}{\\mathrm{d}x}=f(x)"),
    note("warn", "易错", "提醒内容。"),
    ex("例题题干。", "解答过程。"),
  ],
}
```

支持的 `body` 块：`p`、`f`、`ul`、`note`、`table`、`steps`、`ex`、`cue`。

### 追加一章

知识树由 `SUBJECTS` 驱动。给某一章加内容时，把该章 `status` 改成 `"ready"`，并让 `sections` 指向内容数组；树会自动出现该章的板块和考点，点击即可复习。

数一大纲的 21 章已全部 `ready`，新章内容写在 `CALCULUS`、`LINEAR`、`PROBABILITY` 里，例如：

```js
CALCULUS.series = [ /* 板块数组，结构同 SECTIONS */ ];
LINEAR.matrix = [ /* 同上 */ ];
PROBABILITY.estimation = [ /* 同上 */ ];
```

只写在对象里不会显示，必须在 `SUBJECTS` 里被引用。加新章时照此新增一个键并挂到 `SUBJECTS` 即可。

### 历年真题

真题数据由 `scripts/extract_papers.py` 从本机 `数一学习 OS-海岛版/data/mathos.sqlite` 只读抽取，经 LaTeX 清洗后写入 `data/papers-2011-2026.json`（数一）和 `data/papers-math2-2011-2026.json`（数二）；`client.js` 顶部的 `PAPERS` / `PAPERS_MATH2` 是生成块。重新生成：

```bash
python3 scripts/extract_papers.py
python3 scripts/extract_papers.py --subject 数学二 --tag 数二 --out data/papers-math2-2011-2026.json
python3 scripts/embed_papers.py          # 数一
python3 scripts/embed_math2.py           # 数二（新增脚本）
node --check client.js
```

题目按「一、选择题 / 二、填空题 / 三、解答题」分组；点题目进入详情，上方是题目，下方是答案与解析。当前嵌入了 2015 年第 1 题的配图，其余题目的图片如果源库里有，会按同样方式加入。

2026 年每题的考点/方法速查放在 `data/methods-2026.json`，嵌入 `client.js` 的 `PAPER_METHODS`；默认折叠，点标题展开。其他年份暂时没有这层方法卡。

### 公式语法

`$...$` 是行内公式，`f("...")` 是独立公式块。支持：

- `\frac{}{}`、`\sqrt{}`、`^{}`、`_{}`
- `\int`、`\sum`、`\prod`、`\lim`
- 希腊字母、`\to`、`\infty`、`\partial`、`\ne`、`\le`、`\Rightarrow`
- `\left( ... \right)`、`\text{}`、`\mathrm{}`
- `\begin{cases} ... \end{cases}`、`\begin{aligned} ... \end{aligned}`
- 矩阵：`\begin{pmatrix} ... \end{pmatrix}`、`bmatrix`、`vmatrix`、`array`

## 修改后如何生效

在对话里说明要改的章节或考点即可。内容改动会写回 `client.js`，先跑自检，再重新安装 bundle：

```bash
node --check client.js
node scripts/check-content.mjs   # 解析全部公式，查 $、花括号、环境与未知命令
```

`check-content.mjs` 会用内置渲染器把每个公式真正解析一遍，输出章节 / 板块 / 考点计数；改完内容一定要跑。之后重装 bundle，刷新页面（或按提示重启）后可见。

## 进度数据

`localStorage` key：`dsh.kaoyan-math.mastery.v1`。清除它或点章节页头的「重置进度」即可归零。

## 发布到插件市场

仓库：<https://github.com/zhongguohaoqingnian-dev/kaoyan-math-review>
市场索引：<https://zhongguohaoqingnian-dev.github.io/kaoyan-math-review/market.json>

DSH 没有官方商店：所谓「市场」是一份你托管的 **index JSON**，用户在 Plugins → Discover 里添加它的 URL 后即可搜索、安装。

1. 改成可发布的身份（`@local/` 作用域和 `private: true` 都不能发布）：把 `package.json` 的 `name` 改成 `kaoyan-math-review`（npm 上目前未被占用），删掉 `private`，补上 `license`、`repository`、`engines.dsh`。
2. 发布包：`npm publish --access public`（私有 registry 则加 `--registry`）。
3. 托管索引：仓库根目录的 `market.json` 就是格式 1 的索引，已通过 GitHub Pages 托管（不能 302 跳转）。发版时用 `npm run market` 重新生成：默认把源码锁定到当前 commit（`source: git`），`npm publish` 之后改用 `npm run market -- --source npm`。
4. 用户侧开启市场：Plugins → More（Experimental plugins）→ 打开 **Custom plugin markets**，再到 Discover 添加你的索引 URL 安装。


注意 `engines.dsh` 的预发布语义：`^0.2.0` **不会**匹配 `0.2.1-rc.5`，要在当前 rc 上装得通，写 `>=0.2.1-rc.0 <0.3.0`。
