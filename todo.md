# TODO: `/root/autodl-tmp/project`

## 背景

### 我们当前工作的基本思路

当前这项工作的目标，不是再去证明“某个 cue 会不会让模型调用工具”，而是：

- 先用 **双向电路发现** 的方式，在模型内部找到一张真实参与首 token 决策的 circuit。
- 再在这张已经找到的 circuit 里，反向解释：
  - 哪些节点在读信息
  - 哪些节点在路由信息
  - 哪些节点在放大信息
  - 哪些节点最终把状态写成 `<tool_call>` 或 `no_tool`
- 最终把这些节点和边串成一条 **人类可理解、对象语言化、带证据的 mechanistic chain**

换句话说，方法顺序必须是：

1. 先找 circuit
2. 再解释 circuit 的语义
3. 不在全模型里漫无目的搜头
4. 而是在已发现的 circuit 中定位：到底是谁实现了我们关心的语义与决策

### 当前工作的真实状态

当前工作的核心其实已经很明确：

- 我们已经通过双向方法 **计算出了 circuit**
- 也已经通过 faithful 性验证 **证明了 circuit 是对的**
- 当前真正缺的，不再是“这张电路存不存在”
- 当前真正缺的是：**这张电路到底如何实现机制**

也就是说，当前工作的短板不是 circuit correctness，而是 mechanistic evidence。

从现在开始，后续讨论要从：

- “哪些节点和边重要”
- “这张电路能不能恢复行为”

推进到：

- “这些节点分别读什么”
- “这些节点分别写什么”
- “这些边到底在传递什么状态”
- “这个最小 cue 为什么会沿着电路被放大并最终翻转首 token 决策”

### 当前已有结果在哪里

当前主结果已经整理到：

- [results/final](/root/autodl-tmp/project/results/final)

其中最重要的文件是：

- 总文档：[FINAL_PACKAGE.md](/root/autodl-tmp/project/results/final/FINAL_PACKAGE.md)
- 图像目录：[figures](/root/autodl-tmp/project/results/final/figures)
- 数据目录：[data](/root/autodl-tmp/project/results/final/data)
- 旧 run 归档：[archive/raw_runs](/root/autodl-tmp/project/results/final/archive/raw_runs)

主线已有结果包括：

- 最终 signed circuit：`24` 个节点，`64` 条边
- 最终机制主链候选：
  - tool 路：`L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27`
  - no-tool 路：`L16H4 -> MLP17 -> L23H6`
- 反向发现与 no-tool 语义线的高重合
- attention head 的 span / QKV 审计
- `MLP27` 的 late writer 证据

### 当前必须始终记住的前提

这不是研究结果，而是**数据构造前提**：

- clean 和 corrupt 的关键差异，是用户 instruction 最前面的极小 token / lead phrase
- clean 会走 `<tool_call>`
- corrupt 不会走 `<tool_call>`

因此，下面这些问题**不是**当前研究目标：

- “第一句 instruction 重不重要？”
- “lead phrase 会不会翻转行为？”

因为这些是数据设计里已经写死的。

真正要解释的是：

**为什么只改这一个 token / 极小短语，模型内部就会发生级联变化，最后在首个生成位置从 `<tool_call>` 翻到 `no_tool`，或者反过来。**

### 当前必须区分的两类证据

后续讨论里，必须明确区分：

#### 1. 定位证据

这些证据回答的是：

- 这个节点是不是在这条链上
- 这条边是不是重要
- 动这个节点之后，行为会不会变

目前已经有很多这类证据，例如：

- reverse overlap
- patch rescue
- stepwise rescue
- edge mediation
- sufficiency / necessity

这些证据很重要，但它们本质上回答的是：

**“它在不在这条电路里，以及动它会不会影响行为。”**

#### 2. 机制证据

这些证据回答的是：

- 它读了什么对象
- 它把 residual 往哪个方向推
- 它到底是在抬高 `no_tool`，还是在压低 `<tool_call>`，还是两者同时发生
- 它怎样具体影响下游节点

这类证据才是真正的 mechanistic evidence。

所以从现在开始，必须避免把：

- reverse overlap
- patch 后恢复 no-tool
- clean 上逐步 patch 后越来越像 no-tool

直接当作“机制已经解释完了”。

这些结果只能说明：

**我们定位到了 suppressive branch。**

但还不能单独说明：

**这个 suppressive branch 到底是如何实现抑制的。**

---

## 第一点：解释“最小 cue 如何在已发现的 circuit 中引发级联决策翻转”

### 这一点到底要解决什么问题

当前第一核心问题是：

**在已经发现的 24 节点 circuit 里面，找出这个已知最小 cue 是如何被某个具体节点读取、经具体边传播、被具体 MLP/heads 放大，并最终写成 `<tool_call>` / `no_tool` 决策的。**

更具体地说，我们接下来真正要拆清楚的是：

1. 这个首 token / 极小 lead phrase，先被 circuit 里的哪个 head 读到。
2. 这个 head 读到的到底是什么：
   - 这个词的词面身份
   - 这个位置
   - 它和 `solve.py / solve.cpp / solve.java / function body` 的组合对象
   - 还是更抽象的“交付承诺”语义
3. 它通过哪条 Q/K/V 路径，把这个局部差异送到下游。
4. 下游哪些节点把这个微小差异放大成：
   - `L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27` 这类 tool 链优势
   - 或者 `L16H4 -> MLP17 -> L23H6` 这类 no-tool 链优势
5. 为什么这个差异最后会被写成几乎二值化的首 token 翻转。

### 这一点的边界

这一点当前**不是**在问：

- “哪个 cue 会导致翻转？”
- “哪个词和 `<tool_call>` 相关？”

而是在问：

**这个已知 cue，为什么能通过我们已经找到的 circuit，造成最终决策的级联翻转。**

所以接下来所有提问、分析、实验，都应该受这个边界约束：

- 必须在当前已发现的 circuit 里寻找解释
- 必须优先解释当前电路中的节点与边
- 不要把“数据构造事实”误当成“机制发现”
- 不要把“定位证据”误当成“机制证据”

### 当前第一问题最缺的机制证据类型

当前这一步最缺的不是更多 patch，而是更接近经典 mech interp 的机制证据：

#### A. Attention Heatmap / Readout 可视化

目标：

- 展示某个 head 到底读了哪个对象

重点问题：

- 它读的是首词本身？
- 还是首词和 `solve.py / solve.cpp / solve.java / function body` 的组合？
- 还是句首位置 / instruction 边界？

这类证据主要服务于：

- 找最早 cue-reader head
- 解释 `L16H4 / L16H8 / L17H2 / L17H8 / L20H5`

#### B. Logit Lens / Residual Direction 可视化

目标：

- 展示某个节点把 residual 往什么方向推

重点问题：

- 它是在抬高 `<tool_call>`？
- 还是在抬高 `no_tool`？
- 还是主要在压低对侧方向？

这类证据主要服务于：

- 解释 `MLP17`
- 解释 `L23H6`
- 解释 `MLP27`

#### C. Downstream Suppression Visualization

目标：

- 展示 no-tool 链如何具体压制 tool ingress

重点问题：

- `MLP17` 之后，`L20H5 / L21H1 / L21H12` 的 tool-biased state 是否被削弱？
- 去掉 `MLP17` 之后，这些节点的状态是否回升？

这类证据主要服务于：

- 解释 no-tool 链不只是“自己写 no_tool”
- 而是真的在 **压制 tool 路**

### 当前最值得重点追问的节点范围

接下来第一问题的分析，应优先围绕以下节点展开。

#### 可能的最早 cue-reader 候选

- `L2H14`
- `L16H8`
- `L17H2`
- `L17H8`
- `L20H5`

#### tool 路由 / 放大 / 写出候选

- `L21H1`
- `L21H12`
- `L24H6`
- `MLP27`

#### no-tool 竞争 / 抑制候选

- `L16H4`
- `MLP17`
- `L23H6`
- 以及 reverse-aligned 支路上的：
  - `MLP12`
  - `L15H5`
  - `L16H13`
  - `L16H9`

### 当前 no-tool 链的专门机制问题

对于：

- `L16H4 -> MLP17 -> L23H6`

当前已经有很多“定位证据”，但真正要补的是“机制证据”。

接下来要围绕这条链明确回答：

1. `L16H4` 到底读了什么，才把状态送进 suppressive route？
2. `MLP17` 到底是在写 `no_tool`，还是在压 `<tool_call>`，还是两者都有？
3. `L23H6` 是不是把这个 suppressive state 送到了输出附近？
4. `MLP17` 到底如何让 `L20H5 / L21H1 / L21H12` 这些 tool ingress 节点变弱？

这 4 个问题，才是 no-tool 链后续真正的 mechanistic target。

### 当前这一步真正想要的最终答案形式

这一点最终不是要得到一句泛泛的话，而是要得到一条可以写进主文的 mechanistic chain：

1. `Head A` 最先读取这个最小 cue
2. `Head A` 读到的是 `X`，不是 `Y`
3. 它主要通过 `Q / K / V / Z` 的哪一部分起作用
4. 它把这个差异传给 `Node B`
5. `Node B / C / D` 如何继续放大
6. `MLP27` 或 `MLP17` 如何把这个差异写成最终首 token 偏置

### 当前这一步的验收标准

这一点只有在下面这些问题都能回答时，才算真正完成：

- 哪个节点最先读取了最小 cue？
- 它读到的是词面、位置、对象组合，还是更抽象的语义？
- 它的主要作用成分是 `Q`、`K`、`V` 还是 `Z`？
- 它通过哪条边影响了哪个下游节点？
- 哪些节点负责放大？
- 哪个节点最终完成了 `<tool_call>` / `no_tool` 的写出？

---

## 备注

从现在开始，后续围绕 [results/final](/root/autodl-tmp/project/results/final) 的提问，默认都应服务于上面“第一点”的任务推进。

也就是说，后续问题应该优先帮助我们回答：

**这个已知最小 cue，究竟如何在当前已发现的 circuit 中被读取、传播、放大并最终写成决策。**
