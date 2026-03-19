# Spotlight 风格论文叙事总纲

## 1. 这篇论文到底讲什么

这篇论文最应该讲的，不是“我们找到了一张 24 节点电路”，也不是“我们做了很多 patching 实验”，而是下面这句话：

> 一个极小的 instruction opening cue，会在模型内部沿着一条稀疏、可解释、带有竞争支路的 signed circuit 被读取、放大，并最终把首个生成位置从 `<tool_call>` 翻到 `no_tool`，或反过来。

如果用更具体的对象语言来说，当前最适合写进论文主文的故事是：

- 最小 cue 在早层被 `L2H14` 读入，但在这一层还只是弱的 opening-side 状态。
- `MLP11` 是第一个把它写成稳定 `file-vs-answer` 交付对象轴的节点。
- `MLP11 -> MLP16 -> MLP19` 会逐层放大这条对象轴。
- 这条状态进入晚层 tool writer 路径  
  `L20H5 -> L21H12 -> L24H6 -> MLP27`
  并最终写成 `<tool_call>` 倾向。
- 与此同时，存在一条竞争性的 suppressive route  
  `L16H4 -> MLP17 -> L23H6`
  它会把 ordinary-answer / no-tool 一侧的状态写出来，同时压低 tool route。

这就是整篇论文的主线。

---

## 2. 为什么这个故事有 spotlight 风格

和一般“机制分析”不同，这个故事天然有几个很强的传播点：

1. 干预极小  
   只改 instruction 开头一个 token / 极小 lead phrase。

2. 行为翻转很硬  
   首 token 会在 `<tool_call>` 和 `no_tool` 两侧翻转。

3. 机制链条是可叙述的  
   有 earliest reader、first stable writer、shared amplifier、late writer、suppressive route。

4. 不是只有正向链  
   还有真正的竞争性 no-tool suppression 机制。

所以这篇论文最适合的 framing 不是“某个复杂工具代理的全局解释”，而是：

> 一个最小 instruction cue 如何在 LLM 内部触发一条可解释的 signed decision mechanism。

---

## 3. 论文主 claim

### 3.1 最核心的一句话

最小 cue 不会直接在晚层被“看见”并写成 `<tool_call>`；它先被早层读入，再由 `MLP11` 稳定写成共享交付对象轴，经 `MLP16 -> MLP19` 放大后，分别进入：

- tool writer 路径：`L20H5 -> L21H12 -> L24H6 -> MLP27`
- no-tool suppressive 路径：`L16H4 -> MLP17 -> L23H6`

这两条路径共同决定首 token 是 `<tool_call>` 还是 `no_tool`。

### 3.2 主文中可以 strong write 的子命题

| 子命题 | 当前状态 |
|---|---|
| `L2H14` 是最早 retained head-level reader | 可以强写 |
| `L2H14` 不是 first stable delivery-object writer | 可以强写 |
| `MLP11` 是 first stable delivery-object writer | 可以强写 |
| `MLP11 -> MLP16 -> MLP19` 放大 shared object axis | 可以强写 |
| `L20H5 -> L21H12 -> L24H6 -> MLP27` 是主要 late tool writer bridge | 可以强写 |
| `L16H4 -> MLP17 -> L23H6` 是 suppressive no-tool route | 可以强写 |
| `MLP17` 同时抬高 `no_tool` 且压低 `<tool_call>` | 可以强写 |

### 3.3 不要作为 strongest claim 的命题

| 命题 | 原因 |
|---|---|
| `L2H14` 里最早微特征已经被唯一命名 | 还不够硬 |
| `L16H4` 里 suppressive 微特征已经被唯一命名 | 还不够硬 |
| `L21H1` 是 shared object axis 的最主要 late carrier | 现在 `L21H12` 更干净 |

---

## 4. 论文章节结构建议

## 4.1 Introduction

引言只做三件事：

1. 引出最小干预现象  
   一个极小 lead phrase 改变首 token 决策。

2. 提出 mechanistic question  
   为什么这么小的 cue 会沿网络内部逐层放大并翻转决策？

3. 给出核心贡献  
   - 一张 signed decision circuit  
   - 一条 forward writer chain  
   - 一条 suppressive no-tool chain  
   - 一组 paper-facing 因果图

不要在引言里堆太多中间实验名。

---

## 4.2 Problem Setup

这一节只需要交代：

- clean / corrupt 如何构造
- 为什么这是最小干预接口
- 为什么聚焦首 token

这里最重要的是把任务说成：

> 我们不是重新证明“第一词重要”，而是利用这个最小干预接口逆向工程模型内部的 decision mechanism。

---

## 4.3 Discovering the Signed Decision Circuit

这一节要短。

作用只是：

- 说明最终 signed circuit 是怎样得到的
- 简要证明它是 faithful 的
- 让读者接受后面只解释这张电路，而不是全模型乱搜

主文只放：

- circuit 总览图
- 一张紧凑 validation 图

剩下的 sufficiency / necessity / overlap / reverse-selective 细节放附录。

---

## 4.4 Forward Mechanism: From Minimal Cue to `<tool_call>`

这是第一核心结果节。

建议分成四小段：

1. `L2H14` 是 earliest reader，但不是 stable writer
2. `MLP11` 写出第一条稳定 `file-vs-answer` 轴
3. `MLP11 -> MLP16 -> MLP19` 放大 shared object axis
4. `L20H5 -> L21H12 -> L24H6 -> MLP27` 完成最终写出

---

## 4.5 Suppression Mechanism: How the No-Tool Route Wins

这是第二核心结果节。

建议分成四小段：

1. `L16H4` 读入 ordinary-answer evidence
2. `MLP17` 是 suppressive writer
3. `MLP17` 同时抬高 `no_tool` 并压低 `<tool_call>`
4. `L23H6` 将 suppressive state 送到输出附近

这一节一定要比现在更“机制化”，不要只说“这是 competing branch”。

---

## 4.6 Discussion / Limitations

这里只保留两个 limitation：

1. `L2H14` 的最窄微特征命名还没完全锁死
2. `L16H4` 的最窄 suppressive 微特征命名还没完全锁死

这两个 limitation 不应反过来削弱主机制链。

---

## 5. 论文主图顺序

下面这套图顺序比现在的 package 顺序更接近论文主文叙事。

## 图 1：总机制图

这一张最重要，目前最值得补。

它应该把下面这些放到一张图里：

- 最小 cue
- signed circuit 的 forward / suppressive 双路径
- forward 链关键节点
- suppressive 链关键节点
- 最终 `<tool_call>` / `no_tool` 决策

如果这张图做得好，整篇论文的“记忆点”就有了。

---

## 图 2：最终 signed circuit

直接用现有 final circuit 图。

作用：

- 说明这不是零散节点，而是一张稀疏有向电路
- 给后续 reader / writer / suppressor 分工提供结构底图

---

## 图 3：`L2H14` vs `MLP11`

建议使用现有：

![图18 L2H14 与 MLP11 对照图](../figures/figure_18_earliest_reader_vs_mlp11.png)

这张图的任务不是解释一切，而是回答一个关键问题：

> earliest reader 和 first stable writer 不是同一个节点。

这点是我们论文叙事非常重要的辨别点。

---

## 图 4：shared object axis 的逐层放大

建议使用现有：

![图19 Shared Object Axis 的逐层放大](../figures/figure_19_stagewise_object_axis_accumulation.png)

这张图应当服务于一句话：

> 最小 cue 在早层只有弱差异；真正稳定的对象轴在 `MLP11` 被写出，并由 `MLP16 -> MLP19` 明显放大。

---

## 图 5：`MLP11` 的因果写出效应

建议把下面两张一起讲：

![图20 MLP11 编辑后的下游投影轨迹热图](../figures/figure_20_mlp11_projection_trajectory_heatmap.png)

![图21 MLP11 对最终 Writer 的影响](../figures/figure_21_mlp11_final_writer_effect.png)

这组图是 forward 机制最强的因果证据。

它们应当支撑的结论是：

> 只改 `MLP11` 的 shared `file-vs-answer` direction，就足以把同一条对象轴推进到 `MLP16`、`MLP19`、`L20H5`、`L21H12`、`L24H6`、`MLP27`，并最终改变 `<tool_call>` / `no_tool` 的写出。

---

## 图 6：suppressive projection 图

建议使用：

![图22 Suppressive Residual Projection](../figures/figure_22_suppressive_residual_projection.png)

这张图应当回答：

> no-tool 链到底是在抬高 `no_tool`、压低 `<tool_call>`，还是两者同时发生？

---

## 图 7：tool ingress disturbance 图

建议使用：

![图23 Tool Ingress Disturbance](../figures/figure_23_tool_ingress_disturbance.png)

这张图应当回答：

> `MLP17` 的 suppressive direction 是否真的在扰动 tool route，而不是只在末端另起炉灶。

---

## 图 8：suppression heatmap + stagewise trajectory

建议一起讲：

![图24 Downstream Suppression Heatmap](../figures/figure_24_downstream_suppression_heatmap.png)

![图25 Suppression Stagewise Trajectory](../figures/figure_25_suppression_stagewise_trajectory.png)

这组图应当支撑：

> `L16H4 -> MLP17 -> L23H6` 是逐层积累的 suppressive chain，而不是单节点瞬时效应。

---

## 6. 指标公式说明

论文里需要把几个核心指标写清楚，不然图表会显得只是经验统计。

### 6.1 Rescue Ratio

定义：

`RescueRatio = (Score_patched - Score_base) / (Score_anchor - Score_base)`

解释：

- `Score_base`：基础条件下的分数
- `Score_anchor`：目标 anchor 条件下的分数
- `Score_patched`：做 intervention 后的分数

含义：

- `1` 表示完全恢复到 anchor
- `0` 表示没有恢复
- 小于 `0` 表示方向反了

---

### 6.2 Edge Mediation

定义：

`Mediation(A -> B) = Rescue(source-only) - Rescue(source-with-B-blocked)`

含义：

- 如果只 patch `A` 时有明显恢复
- 但把 `B` 挡住后恢复明显下降
- 说明 `A` 的一部分效应是经由 `B` 实现的

---

### 6.3 Object Score Delta

在 `file-vs-answer` 方向下，定义：

`ObjectScore = Score_file - Score_answer`

direction-level intervention 后：

`ObjectScoreDelta = ObjectScore_after - ObjectScore_before`

含义：

- 大于 `0`：往 file-delivery 一侧推
- 小于 `0`：往 answer-delivery / no-tool 一侧推

---

### 6.4 Residual Projection Delta

对某个节点 `X` 和某条方向 `d`，定义：

`ProjectionDelta(X, d) = <h_after - h_before, d_unit>`

其中：

- `h_before`：干预前该节点的 residual / head output
- `h_after`：干预后该节点的 residual / head output
- `d_unit`：单位化后的目标方向

含义：

- 大于 `0`：沿该方向正向移动
- 小于 `0`：沿该方向反向移动

---

### 6.5 Decision Score Delta

定义：

`DecisionScore = Score_tool - Score_no_tool`

干预后：

`DecisionScoreDelta = DecisionScore_after - DecisionScore_before`

含义：

- 大于 `0`：更偏向 `<tool_call>`
- 小于 `0`：更偏向 `no_tool`

---

## 7. 我们和那篇 propositional logic 论文的对照

如果和 `/root/autodl-tmp/prop-logic-transformer-circuit/paper` 那篇比较，我觉得：

### 我们的优势

1. 任务更真实  
   它是 synthetic logic reasoning；我们是 tool / no-tool 决策。

2. signed 竞争结构更强  
   它主要是 reasoning families；我们这里 forward route 和 suppression route 对立得更明确。

3. suppression 机制更有故事性  
   `MLP17` 同时抬高 `no_tool` 和压低 `<tool_call>`，这一点很有机制论文味道。

### 我们的劣势

1. 模块命名不如它整齐  
   它有 queried-rule locating / mover / fact-processing / decision 四个 family，传播性非常强。

2. 正式 package 历史版本多  
   我们需要更小心只保留 paper-facing 主线。

3. 缺一张真正的总 teaser 图  
   它有很强的总图；我们现在还缺一个把全篇锁住的“总机制图”。

### 所以我们最该补的不是更多 patch，而是

> 做出一张整合 forward route 与 suppression route 的总机制图，并把整篇论文压成一条主线叙事。

---

## 8. 还值不值得补实验

如果只为了论文更强，我建议只补 **高 ROI** 的东西。

### 高 ROI

1. 一张总机制图  
   这是最该补的。

2. 一个更紧凑的 forward 对比图  
   把 `L2H14` 和 `MLP11` 在
   - object score
   - tool logit
   - `MLP27` projection
   上的量级差距直接并排画出来。

3. 一个 suppressive chain comparison 图  
   把 `L16H4`、`MLP17`、`L23H6` 对
   - `<tool_call>` delta
   - `no_tool` delta
   - decision score delta
   的影响放到一张图里。

### 低 ROI

1. 再做更多全模型搜索
2. 再堆更多 raw patch rescue
3. 再追 `L2H14` 或 `L16H4` 的最窄微特征命名

这些不会明显提升 spotlight 叙事强度。

---

## 9. 最终建议

如果现在开始写论文，我建议采用下面这条单线叙事：

1. 最小 cue 会翻转首 token 决策
2. signed circuit 定位出两条竞争路线
3. `L2H14` 是 earliest reader，但 `MLP11` 才是 first stable writer
4. `MLP11 -> MLP16 -> MLP19` 放大 shared object axis
5. `L20H5 -> L21H12 -> L24H6 -> MLP27` 完成 `<tool_call>` 写出
6. `L16H4 -> MLP17 -> L23H6` 实现 no-tool suppression
7. 决策来自两条竞争性机制，而不是单路触发

一句话总结：

> 这篇论文应该写成“一个最小 cue 如何触发一条 signed、可解释、可逆向工程的首 token 决策机制”，而不是“我们做了很多机制分析实验”。
