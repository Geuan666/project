# 项目机制总览（2026-03-25）

## 1. 先看总答案

当前最可信、也最适合直接写进论文主线的总机制是：

> 模型先把开头要求、函数体、文件名和后续说明整合成一份可写的指令状态；然后在中层把这份状态压成一个稳定的输出路线偏好；如果偏向工具路线，后面的节点会逐步把 `<tool_call>` 组装出来；如果偏向直接回答路线，另一条抑制链会把 no-tool 写强，并主动压住工具链。

整条主线可以压成下面四段：

1. `Instruction Integration`: `L2H14 + L11H5 -> MLP11`
2. `Output-Route Decision`: `MLP11 -> MLP16 -> MLP19`
3. `Tool-Call Construction`: `MLP19 -> L20H5 -> (L21H1 / L21H12) -> L24H6 -> MLP27`
4. `Tool-Call Suppression`: `MLP16 -> MLP17` 分叉进入 `L16H4 -> MLP17 -> L23H6`

如果你只记一句话，就记这句：

> 工具调用不是一个孤立的 yes/no 开关，而是“先整合任务，再决定输出路线，最后由两条竞争分支把首词推向 `<tool_call>` 或普通回答”的结果。

## 2. 当前已经冻结的全局事实

| 项目 | 当前正式结论 |
| --- | --- |
| 模型 | `Qwen3-1.7B` |
| 数据 | `1722` 对 clean/corrupt 样本，Python `555` / Java `584` / C++ `583` |
| 划分 | 按 `lang × clean_candidate` 分层，`seed=42`，train `1223` / test `499` |
| 总电路 | train 集上重新发现后仍为 `24` 节点、`64` 条边 |
| 全局泛化 | `R_module` AUC：train `0.9946`，test `0.9943` |
| Construction 终点 | `+MLP27` `<tool_call>` top-1：train `97.9%`，test `97.2%` |
| Suppression 终点 | `+L23H6` no-tool top-1：train `79.0%`，test `78.2%` |

结论很明确：当前主叙事已经不是“在训练样本上看起来合理”，而是“在 held-out test 上也稳定成立”。

## 3. 四模块总表

| 模块 | 最稳主链 | 它在做什么 | 最硬数字 | 当前可信度 |
| --- | --- | --- | --- | --- |
| `Instruction Integration` | `L2H14 + L11H5 -> MLP11` | 把分散输入先整成一份可交给 decision spine 的状态 | `L11H5 -> MLP11` local rescue `0.196`；`L2H14 + L11H5` route rescue `0.060`；test `MLP11` AUC `0.9677` | 中高 |
| `Output-Route Decision` | `MLP11 -> MLP16 -> MLP19` | 把整合状态压成稳定的输出路线偏好 | `R_module` AUC train/test `0.9946/0.9943`；三条关键边均为 strong | 高 |
| `Tool-Call Construction` | `MLP19 -> L20H5 -> (L21H1 / L21H12) -> L24H6 -> MLP27` | 将工具路线逐步落实成 `<tool_call>` 首词 | train `0.0 -> 97.9%`；test `0.0 -> 97.2%`；`L21H12_only` `67.3%` vs `L21H1_only` `48.9%` | 高 |
| `Tool-Call Suppression` | `L16H4 -> MLP17 -> L23H6` | 写强 no-tool，并主动压制 construction 链 | train no-tool `1.0 -> 79.0%`；test `1.4 -> 78.2%`；`MLP17` inject: `<tool_call>` `-0.625` / no-tool `+1.125` | 高 |

这里的“可信度”指的是：这条说法现在是否已经足够稳定，能直接作为论文主文叙事，而不是还停留在探索口径。

## 4. 模块 1：Instruction Integration

### 4.1 它在做什么

模块 1 不负责决定“要不要调工具”，它负责先把输入读成一份统一的交付要求。也就是说，它回答的是：

> 这次用户到底在要求什么样的输出方式？

### 4.2 当前最稳结论

- `L2H14` 是更早的 ingress 头，不是全能整合头
- `L11H5` 是更明确的 `MLP11` same-block handoff 头
- `MLP11` 是模块 1 的出口，也是模块 2 的入口

### 4.3 最硬证据

- `L11H5 -> MLP11` local rescue = `0.196`
- `L2H14 + L11H5` route rescue = `0.060`
- held-out test：
  - `MLP11` route AUC = `0.9677`
  - `R_module` AUC = `0.9943`
- span masking 显示：
  - `L11H5` 稳定依赖 `tool_schema / lead_phrase / function_body / file_target / instruction_suffix`
  - `L2H14` 主要依赖 `lead_phrase / file_target / instruction_suffix`，对 `function_body / task_body` 也有较弱但同号依赖

### 4.4 现在可以怎么写

最稳的说法是：

> 模块 1 是一个两段式入口组。`L2H14` 提供更早的开头读入，`L11H5` 把整合后的状态交给 `MLP11`，从而为后续 route decision 提供输入边界。

### 4.5 现在不能写太满的地方

- 不要把 `L2H14` 和 `L11H5` 写成两个对称的“全能整合头”
- 不要把模块 1 写成已经有和模块 2 同等级别显式公式化的单一标量对象

## 5. 模块 2：Output-Route Decision

### 5.1 它在做什么

模块 2 把模块 1 交来的指令状态，压成一个更高层的内部选择：

> 接下来应该走工具协议输出，还是走普通回答输出？

### 5.2 当前最稳结论

- 决策主干是 `MLP11 -> MLP16 -> MLP19`
- 这里形成的是逐层重编码的 `route score`
- `MLP16 -> MLP17` 是 direct-answer / suppressive 一侧的强分叉边

### 5.3 最硬证据

| 节点 | Train route AUC | Test route AUC |
| --- | ---: | ---: |
| `MLP11` | `0.9661` | `0.9677` |
| `MLP16` | `0.9960` | `0.9956` |
| `MLP19` | `0.9947` | `0.9934` |
| `R_module` | `0.9946` | `0.9943` |

三条关键边的 promote mediation：

- `MLP11 -> MLP16` = `0.156`
- `MLP16 -> MLP19` = `0.095`
- `MLP16 -> MLP17` = `0.149`

三对局部方向余弦都接近 `0`：

- `cos(MLP11, MLP16) = 0.040`
- `cos(MLP16, MLP19) = -0.006`
- `cos(MLP11, MLP19) = 0.052`

### 5.4 现在可以怎么写

最稳的说法是：

> 模块 2 不是在直接写某个 token，而是在写“输出路线状态”。这个状态在 `MLP11 -> MLP16 -> MLP19` 上持续存在，但每一层都被重新编码，因此它是稳定的决策对象，而不是被原样搬运的固定方向。

### 5.5 现在不能写太满的地方

- 不要把 `route score` 写成某一层唯一拥有的对象
- 不要把三层说成“共享同一方向”，因为几何上它们更像逐层重编码

## 6. 模块 3：Tool-Call Construction

### 6.1 它在做什么

模块 3 负责把已经偏向工具路线的状态，真正落实成 `<tool_call>` 这个首词。

### 6.2 当前最稳结论

- 主链：`MLP19 -> L20H5 -> (L21H1 / L21H12) -> L24H6 -> MLP27`
- 这是渐进构造链，不是单节点瞬时控制
- `L21H12` 明显强于 `L21H1`
- `MLP27` 是最终主 writer

### 6.3 最硬证据

stagewise `<tool_call>` top-1：

- train：`0.0% -> 4.3% -> 14.6% -> 48.9% -> 85.9% -> 92.8% -> 97.9%`
- test：`0.0% -> 4.8% -> 16.0% -> 53.7% -> 86.2% -> 91.2% -> 97.2%`

branch 对比：

- `L21H12_only` = `67.3%`
- `L21H1_only` = `48.9%`
- `L21H12 + L24H6` = `83.9%`
- `L21H1 + L24H6` = `73.2%`

writer 证据：

- `L24H6` delta margin = `0.257`
- `MLP27` delta margin = `1.609`

### 6.4 现在可以怎么写

最稳的说法是：

> `MLP19` 负责把 route state relay 到 construction 区，`L20H5` 负责更早的 payload binding，`L21H1 / L21H12` 负责 late routing，`L24H6` 负责 format commitment，最后由 `MLP27` 把 `<tool_call>` 明确写成首词。

### 6.5 现在不能写太满的地方

- 不要把 `MLP19` 写成 construction initiator
- 不要把 `L21H1` 和 `L21H12` 写成简单冗余头
- 不要把 `MLP19 -> MLP27` shortcut 写成独立主路

## 7. 模块 4：Tool-Call Suppression

### 7.1 它在做什么

模块 4 说明的是：

> 当 decision spine 偏向直接回答路线时，模型不是简单地“不去写 `<tool_call>`”，而是在主动写强 no-tool，并反过来压制 construction 链。

### 7.2 当前最稳结论

- 边界分叉：`MLP16 -> MLP17`
- 模块主体：`L16H4 -> MLP17 -> L23H6`
- `L16H4` 是 suppressive ingress / reader
- `MLP17` 是主 suppressive writer
- `L23H6` 是 late relay

### 7.3 最硬证据

stagewise no-tool top-1：

- train：`1.0% -> 29.9% -> 79.0%`
- test：`1.4% -> 27.1% -> 78.2%`

`MLP17` inject no-tool direction into clean：

- `<tool_call>` `-0.625`
- no-tool `+1.125`
- decision score `-1.586`

`MLP17` 对 construction 链的下游干扰：

- `L20H5` `+3.549`
- `L21H1` `+6.391`
- `L21H12` `+7.125`
- `L24H6` `+12.309`
- `MLP27` `+110.862`

补充证据：

- `<tool_call>` 的 logit lens 在 `17_pre` 到 `25_pre` 始终维持负值
- held-out corrupt set 首词并不发散，而是高度集中：`I` `495/499`、`To` `3/499`、`The` `1/499`

### 7.4 现在可以怎么写

最稳的说法是：

> suppression 不是 construction 的空缺，而是一条主动 competing line。`L16H4` 把 ordinary-answer 证据读进来，`MLP17` 同时抬高 no-tool、压低 `<tool_call>`，`L23H6` 再把这份 suppressive state 送到输出附近。

### 7.5 现在不能写太满的地方

- 不要把 `L23H6` 写成和 `MLP27` 对称的 universal final writer
- 不要把 suppressive route 写成“只是在顶一个替代 token”
- `L16H4` 的精确 microfeature 还没有被命名到足够窄

## 8. 当前最可信的整体叙事

如果把四个模块连成一句完整的话，当前最稳的叙事是：

> 开头要求的细小差异，先在模块 1 被读成一份统一的交付要求，再在模块 2 被压成一个稳定的输出路线状态；随后模型并不是立刻生成某个词，而是进入两条竞争后路之一。若路线偏向工具协议，模块 3 会渐进地把 `<tool_call>` 组装出来；若路线偏向直接回答，模块 4 会主动写强 no-tool，并同时压住工具构造链。

这个叙事现在已经有足够强的 train/test 支撑，可以作为当前项目的正式总口径。

## 9. 目前项目进展到哪一步

当前项目已经完成的是：

- 数据、总电路、四模块主链都已冻结
- 四模块正式结果都已统一迁入 `project/experiment/results/split/`
- 总文档、总历史、总指南都已经统一到 `project`

当前项目还没有完全做完的是：

- 论文主文的最终排版和图序重构
- 少量“边界不能写太满”的补强实验
- 模块 2 更细的 feature-level 讲述

但就“是否已经形成一套稳定、可信、可继续展开后续工作的总机制”这个问题而言，答案是：

> 是，已经形成。

## 10. 建议下一步阅读

1. `experiment/results/split/split_comparison_summary.md`
2. `experiment/results/split/instruction_integration/instruction_integration_module1_report.md`
3. `experiment/results/split/output_route_decision/output_route_decision_paper_assets.md`
4. `experiment/results/split/tool_call_construction/tool_call_construction_paper_report.md`
5. `experiment/results/split/tool_call_suppression/tool_call_suppression_report.md`
6. `paper/PAPER_OUTLINE.md`
7. `final/FIGURE_INDEX.csv`
