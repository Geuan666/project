# Tool-Call Suppression 主报告

## 模块定义

本报告把 Tool-Call Suppression 定义为：在上游 `Output-Route Decision` 已经偏向 direct-response route 之后，一条 competing no-tool 线路把 ordinary-answer 侧的状态写强，并同时把 `<tool_call>` 路线压低。对当前数据最可信的最小主链是 `L16H4 -> MLP17 -> L23H6`；其中 `MLP16 -> MLP17` 是从 Decision 模块进入 suppressive line 的边界 fork，而不算 suppression 模块主体。

## 样本与结果范围

- 全部结论基于 `1722` 个有效样本的 full-run suppression 结果。
- 这次不重跑大模型；直接复用 legacy full-run 的 per-sample 与 summary 结果，并按当前模块标准重组。
- attention 可视化同时复用 `experiment/results/attentionhead/20260319-121000-attention-head-full/`。

## 节点分层

- anchor nodes: `L16H4, MLP17, L23H6`
- support nodes: `MLP16`
- candidate nodes: `MLP12, L16H8, L15H5, L16H13, L16H9, L17H2`

### 分层理由

- `L16H4` 是最稳的 suppressive reader / ingress：它主要读 task-body / tail-suffix 一带的 ordinary-answer evidence，而不是 tool schema。
- `MLP17` 是主 suppressive writer：它既抬高 no-tool，也压低 `<tool_call>`，并直接扰动 tool-side ingress 与 late writer。
- `L23H6` 更像 late suppressive relay，而不是新的 reader 或主要 writer。
- `MLP16` 是 support，因为 `MLP16->MLP17` 是强 fork edge，但 `MLP16` 更适合被写成 Decision 到 Suppression 的边界节点。
- 其余候选节点虽然带有 no-tool bias 或 no-tool tail 痕迹，但当前 patch / writeout / stagewise 证据不足以升格。

## 核心结论

### 1. 旧主线是否仍成立

成立。当前最稳的 suppressive 主链仍是 `L16H4 -> MLP17 -> L23H6`，上游通过 `MLP16->MLP17` 从 `Output-Route Decision` 分叉进来。

### 2. 这个模块到底在做什么

它不是单纯“把另一个 token 顶上去”。当前最可信的写法是：`MLP17` 同时做两件事，一是把 direct-answer / no-tool 一侧写强，二是主动压低 `<tool_call>`，而 `L16H4` 提供 ordinary-answer 侧读入，`L23H6` 负责把已写好的 suppressive state 送到输出附近。

- `L16H4` inject into clean: `<tool_call>` `-0.250`, no-tool `0.375`, decision `-0.657`。
- `MLP17` inject into clean: `<tool_call>` `-0.625`, no-tool `1.125`, decision `-1.592`。
- `L23H6` inject into clean: `<tool_call>` `-0.375`, no-tool `0.625`, decision `-0.902`。

### 3. `L16H4` 在读什么

`L16H4` 最可信的定位仍是 ordinary-answer reader / branch ingress。旧 full-run attention 审计显示它主要读 task-body 和 tail-suffix，一点也不像 tool schema reader；QKV 结果也显示它主要靠 `z` 带出 suppressive state。
对照证据：`L16H4->MLP17` 是强 no-tool ingress edge，focused table 给出 `MLP16->MLP17` `promote mediated 0.220; suppress mediated 0.210`，`L16H4->MLP17` `minimal-cue mediated 0.076; signed summary suppress mediated 0.234 support-wise; strongest full-data no-tool edge inside minimal cue`。

### 4. `MLP17` 是不是主 suppressive writer

是，而且这一点是当前 suppressive 模块里最硬的结论。
`MLP17` 的 clean→corrupt residual writeout 对 no-tool 是 `0.219`，注入 suppressive direction 时 no-tool token 变化 `1.125`，`<tool_call>` token 变化 `-0.625`。
更关键的是，它会同时把 construction 线往 no-tool 侧推：`L20H5` `3.517`，`L21H1` `6.479`，`L21H12` `7.030`，`L24H6` `12.384`，`MLP27` `111.543`。

### 5. `L23H6` 是主要 writer 还是 late relay

更像 late relay。它当然有 suppressive 作用，但它不像 `MLP17` 那样直接把 no-tool 一侧写强；它更像把已经写好的 suppressive state 送到输出附近。
一个直接迹象是：clean→corrupt residual writeout 上，`L23H6` 对 `<tool_call>` 的变化很大 `-1.605`，但对 no-tool 并不是 strongest writer 样子 `-0.531`；而方向注入时，它能把 no-tool 顶上去 `0.625`，说明它在运输已成形的 suppressive state。

### 6. suppressive state 是单一方向还是多节点共同状态

更稳的写法是：存在节点局部一致的 suppressive direction，但 token-level 后果是分阶段积累出来的。也就是说，它不是单个节点瞬时完成，而是 `L16H4` 先读入、`MLP17` 主写、`L23H6` 后送。
方向一致性也支持这点：`L16H4` alignment `0.648`，`MLP17` `0.651`，`L23H6` `0.928`。

### 7. stagewise 上它是如何影响首个输出词的

- `L16H4` alone: `<tool_call>` top1 `0.986`, no-tool top1 `0.012`, decision `-0.657`。
- `+MLP17`: `<tool_call>` top1 `0.706`, no-tool top1 `0.289`, decision `-2.414`。
- `+L23H6`: `<tool_call>` top1 `0.204`, no-tool top1 `0.783`, decision `-3.951`。
这说明 token-level 后果并不是在 reader 阶段就出现，而是在 `MLP17` 加入后开始变得明显，最后由 `L23H6` 把 clean prompt 大范围推回 no-tool 一侧。

## 读什么 / 写什么 / 怎么传

| 节点 | 读什么 | 写什么 | 怎样传给下游 | 当前定位 |
| --- | --- | --- | --- | --- |
| `L16H4` | task-body / tail-suffix 的 ordinary-answer evidence | 早期 suppressive routed state | 主要送到 `MLP17` | anchor / suppressive reader-ingress |
| `MLP17` | 上游 ordinary-answer / direct-response state | no-tool-favoring residual，并同时压 `<tool_call>` | 送到 `L23H6`，并回扰 `L20H5/L21H1/L21H12/L24H6/MLP27` | anchor / main suppressive writer |
| `L23H6` | 已写好的 suppressive state | 输出附近的 late suppressive relay state | 进入 output-adjacent region | anchor / late suppressive relay |
| `MLP16` | shared route score | suppressive fork input | 主要送到 `MLP17` | support / boundary fork node |

## 与 Output-Route Decision 的连接

当前最稳的连接写法是：`MLP16 -> MLP17` 是 direct-answer / suppressive 分支的强 fork edge。`MLP16` 还属于 `Output-Route Decision`，但 `MLP17` 开始，状态才真正进入 suppression 模块。
旧 full-run focused table 明确把 `MLP16->MLP17` 写成 strong edge，证据为 `promote mediated 0.220; suppress mediated 0.210`。

## 候选节点比较

这轮没有发现足以推翻旧主线的新 anchor。`MLP12` 更像更早的 no-tool seed，`L16H8` 虽有 no-tool bias，但 attention 更混杂，`L15H5 / L16H13 / L16H9 / L17H2` 主要保留为 no-tool tail 候选。

## 写出类可视化结论

- stagewise 轨迹见 `/root/autodl-tmp/project/experiment/results/tool_call_suppression/20260320-065246-tool-call-suppression/figures/suppression_stagewise_trajectory.png`。这张图最直接回答 suppressive state 何时开始具备 token-level 后果。
- 节点 writeout 见 `/root/autodl-tmp/project/experiment/results/tool_call_suppression/20260320-065246-tool-call-suppression/figures/suppression_node_writeout.png`。这张图最直接区分 reader、writer、relay。
- downstream suppression heatmap 见 `/root/autodl-tmp/project/experiment/results/tool_call_suppression/20260320-065246-tool-call-suppression/figures/suppression_downstream_heatmap.png`。这张图回答 `MLP17` 是否真的在压 tool path。
- candidate comparison 见 `/root/autodl-tmp/project/experiment/results/tool_call_suppression/20260320-065246-tool-call-suppression/figures/suppression_candidate_comparison.png`。这张图回答为什么旧主线没有被候选节点推翻。
- attention panel 见 `/root/autodl-tmp/project/experiment/results/tool_call_suppression/20260320-065246-tool-call-suppression/figures/suppression_attention_panels.png`。这张图回答 `L16H4` 与 `L23H6` 的读入差别，以及 `L16H8` 为何停在 candidate。

## 未解决问题

- `L16H4` 读入的 ordinary-answer evidence 还不能被强写成更窄的单一 microfeature。
- `L23H6` 的精确 transported microfeature 仍更适合写成“suppressive state”，不宜过度命名。
- 候选 no-tool 头虽然存在，但当前没有一个具备足够强的 patching + writeout 证据来升格。

## 论文风格总结

当前最可信的 Tool-Call Suppression 机制是：`MLP16` 把 direct-response 一侧的 fork 输入送到 `MLP17` 后，`L16H4` 提供 ordinary-answer 侧的 suppressive 读入，`MLP17` 把这份状态写成同时抬高 no-tool、压低 `<tool_call>` 的主 suppressive direction，随后 `L23H6` 把已写好的 suppressive state 送到输出附近。最强证据来自三类 full-run 结果同时收敛：其一，reader / writer / relay 三者在 attention、direction inject、stagewise 上有清楚分工；其二，`MLP17` 的 intervention 不只改变 `<tool_call>` 与 no-tool token，还会同步把 `L20H5/L21H1/L21H12/L24H6/MLP27` 推向各自的 local no-tool 方向；其三，stagewise 结果显示 suppressive token-level 后果不是在 reader 阶段完成，而是在 `MLP17` 加入后 sharply 出现，再由 `L23H6` 扩展到输出附近。当前还不能强写的是：`L16H4` 的精确 microfeature 名称，以及任何候选 no-tool 头已经足以改写这条主链。

