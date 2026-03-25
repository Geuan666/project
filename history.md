# 项目历史

## 1. 问题设定与数据起点

这个项目研究的不是一般意义上的“工具调用好不好用”，而是一个更具体的问题：

> 为什么只改用户提示开头的一个动词或很短的词组，模型首个输出词就会在 `<tool_call>` 和普通回答之间翻转？

数据入口在 `experiment/datasets/`。当前冻结的设定是：

- 模型：`/root/autodl-tmp/Qwen/Qwen3-1.7B`
- 数据：`1722` 对 clean/corrupt 样本
- 语言分布：Python `555` / Java `584` / C++ `583`
- 格式：Qwen 原生工具调用模板，关闭 thinking
- 控制变量：每对样本除开头要求词外尽量保持一致

这批数据的价值在于，它提供了一个非常干净的最小干预接口：只改一句开头要求，就能让首个输出词翻转。因此后续电路分析有明确的因果对象，而不是在追整段提示词风格差异。

## 2. 从整体电路到双向机制

在数据构造完成后，项目的第二阶段是定位负责这类翻转的真实电路。这里并不是单靠一种方法，而是结合了电路聚合、patching、边级中介量和节点级干预。

这一步最重要的方法升级是双向反转：

- 正向：把 `<tool_call>` 一侧当作目标，找促进工具调用的链
- 反向：把 `<tool_call>` 一侧当作反例，找压制工具调用、推动 no-tool 的链

双向做法的结果是，项目最后得到的不是一条单边促进链，而是一条共享 backbone 加两条竞争分支的机制结构。当前在 train 集上重新发现后的正式总电路仍为：

- `24` 个节点
- `64` 条边

对应正式结果入口：

- `experiment/results/split/pipeline/final_signed_circuit/`
- `experiment/results/split/pipeline/bidirectional/`
- `experiment/results/split/pipeline/signed_validate/`

## 3. 正式范式升级：Discovery / Validation 分离

早期实验曾经在全量 `1722` 对样本上完成一轮完整发现，但当前正式口径已经统一切换为 split 范式：

- 按 `lang × clean_candidate` 分层抽样
- `seed=42`
- train `1223` / test `499`

从这一步开始，所有正式结论都要求：

1. 在 train 集上发现方向、节点、边和模块主链
2. 在 test 集上只用 train 学到的结构做泛化验证

当前最关键的全局验证结果见 `experiment/results/split/split_comparison_summary.md`：

| 指标 | Train | Test | 结论 |
| --- | ---: | ---: | --- |
| `R_module` AUC | `0.9946` | `0.9943` | 几乎无下降 |
| Construction `+MLP27` top-1 | `97.9%` | `97.2%` | 渐进构造链稳定 |
| Suppression `+L23H6` no-tool top-1 | `79.0%` | `78.2%` | 抑制链稳定 |
| Signed circuit 规模 | `24 / 64` | 复用 train 结构 | 结构未塌缩 |

这意味着当前主叙事不是对特定样本的过拟合，而是模型内部更稳定的计算模式。

## 4. 模块 1：Instruction Integration

正式结果入口：

- `experiment/results/split/instruction_integration/instruction_integration_module1_report.md`

当前最稳结论是：

- `L2H14` 不是全能整合头，而是更早的 ingress 头
- `L11H5` 是更明确的 `MLP11` same-block handoff 头
- `MLP11` 是模块 1 的出口，也是模块 2 的入口

当前最硬的数字有三类：

- `L11H5 -> MLP11` local rescue = `0.196`
- `L2H14 + L11H5` route rescue = `0.060`
- held-out test：
  - `MLP11` route AUC = `0.9677`
  - `R_module` AUC = `0.9943`

模块 1 当前最可信的写法，不是“两个头对称地整合所有输入”，而是“一个较早入口头加一个较晚交接头，把分散的开头要求、函数体、文件名和说明整成一份可交给 `MLP11` 的状态”。

## 5. 模块 2：Output-Route Decision

正式结果入口：

- `experiment/results/split/output_route_decision/output_route_decision_paper_assets.md`

这一模块是当前整条机制线上最稳定的中枢。正式结论是：

- `MLP11 -> MLP16 -> MLP19` 形成决策主干
- 这里写出来的不是具体 token，而是更上层的输出路线状态
- 这个状态更适合写成逐层重编码的 `route score`

最关键的数字：

| 节点 | Train route AUC | Test route AUC |
| --- | ---: | ---: |
| `MLP11` | `0.9661` | `0.9677` |
| `MLP16` | `0.9960` | `0.9956` |
| `MLP19` | `0.9947` | `0.9934` |
| `R_module` | `0.9946` | `0.9943` |

三条关键边的中介量都稳定为 strong：

- `MLP11 -> MLP16`: promote `0.156`
- `MLP16 -> MLP19`: promote `0.095`
- `MLP16 -> MLP17`: promote `0.149`

同时，三对局部方向余弦都接近 `0`，说明模块 2 更像逐层重编码，而不是把同一条方向原封不动搬运到后层。

## 6. 模块 3：Tool-Call Construction

正式结果入口：

- `experiment/results/split/tool_call_construction/tool_call_construction_paper_report.md`

这一模块回答的是：当 route state 已经偏向工具路线时，模型怎样把 `<tool_call>` 真正构造出来。

当前冻结主链：

`MLP19 -> L20H5 -> (L21H1 / L21H12) -> L24H6 -> MLP27`

最关键的 stagewise 结果：

- train：`0.0% -> 4.3% -> 14.6% -> 48.9% -> 85.9% -> 92.8% -> 97.9%`
- test：`0.0% -> 4.8% -> 16.0% -> 53.7% -> 86.2% -> 91.2% -> 97.2%`

这说明模块 3 的核心不是某一个节点瞬间决定 `<tool_call>`，而是一条渐进组装链。

当前还明确冻结了两点：

- `MLP19` 是 route-state relay / late fanout，不是 construction initiator
- `L21H12` 明显强于 `L21H1`
  - `L21H12_only` `<tool_call>` top-1 = `67.3%`
  - `L21H1_only` `<tool_call>` top-1 = `48.9%`

late writer 证据集中在：

- `L24H6` delta margin = `0.257`
- `MLP27` delta margin = `1.609`

因此模块 3 当前最稳的论文写法是：先 relay route state，再由 late heads 分工完成 payload binding、protocol routing、format commitment，最后由 `MLP27` 把 `<tool_call>` 写强。

## 7. 模块 4：Tool-Call Suppression

正式结果入口：

- `experiment/results/split/tool_call_suppression/tool_call_suppression_report.md`

这一模块说明，普通回答路线并不是工具链缺席后的被动结果，而是一条主动 suppress `<tool_call>` 的 competing line。

当前冻结主链：

- 边界分叉：`MLP16 -> MLP17`
- 模块主体：`L16H4 -> MLP17 -> L23H6`

最关键的数字：

- stagewise train no-tool top-1：`1.0% -> 29.9% -> 79.0%`
- stagewise test no-tool top-1：`1.4% -> 27.1% -> 78.2%`
- `MLP17` inject no-tool direction into clean：
  - `<tool_call>` `-0.625`
  - no-tool `+1.125`
  - decision score `-1.586`

`MLP17` 不只是在输出边界改 token，它还会把 construction 链的关键节点整体往 no-tool 方向推：

- `L20H5` `+3.549`
- `L21H1` `+6.391`
- `L21H12` `+7.125`
- `L24H6` `+12.309`
- `MLP27` `+110.862`

因此模块 4 的当前最稳说法是：

- `L16H4` 是 suppressive ingress / reader
- `MLP17` 是主 suppressive writer
- `L23H6` 更像 late relay，而不是对称意义上的最终 writer

## 8. 2026-03-25 的整理结论

到 `2026-03-25` 为止，项目已经完成两件关键收束工作：

1. 四模块正式结果全部统一到 `project/experiment/results/split/`
2. 高层文档只保留一套单仓库口径：
   - `AGENTS.md`
   - `CLAUDE.md`
   - `history.md`
   - `final/PROJECT_MECHANISM_GUIDE_ZH.md`

这意味着后续如果只保留一个文件夹，只需要保留：

- `/root/autodl-tmp/project`

后续工作应优先围绕论文主文、图表重排和少量边界补强展开，而不是再把结果分散回四个模块仓库。
