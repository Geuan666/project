# Tool-Call Construction 主报告

## 模块定义

本报告把 Tool-Call Construction 定义为：在上游 `Output-Route Decision` 已经把状态推到 tool route 之后，晚层节点把这份 route state 继续绑定到文件名、函数体、tool instruction、tool_call example 与调用格式，并把首个输出词逐步写成 `<tool_call>`。
因此，`MLP19` 只被当作 Construction 的接口节点，而不是模块本体；真正属于 Construction 的，是那些在接到 route state 之后，继续组织 payload / protocol，并把 `<tool_call>` 写强的 late heads 与晚层 writer。

## 样本与结果范围

- 全部统计都基于 full run：`1223` 个有效样本。
- 复用的旧结果也只采用 full-dataset 版本，不使用 smoke 或小样本版本。

## 节点分层

- anchor nodes: `L20H5, L21H12, L24H6, MLP27`
- support nodes: `MLP19, L21H1`
- candidate nodes: `L25H10, L25H13, L26H15, L27H7, MLP24, MLP25, MLP26`

### 分层理由

- `L20H5` 是最早接住 tool-side payload 的 Construction 入口：它读文件名和函数体锚点，单节点 patch 已有稳定 rescue；新的 writeout 审计显示，它会把输出边界往 `<tool_call>` 方向推，但通常还不是最强 writer。
- `L21H12` 是最强的 late router / protocol binder：它对 `MLP27` 的边级 mediation 最强，而且更明显读取 tool_call example 与 instruction tail。
- `L24H6` 不是一般 reader，而是 pre-writer formatter / protocol commitment 节点：它强读 `tool_instruction`，在 stagewise 里把 `<tool_call>` margin 从“已翻正”继续推到稳定区。
- `MLP27` 仍是主 writer：旧的 steering 结果和新做的 direct logit effect 都显示，最终把 `<tool_call>` 写成 top-1 的主力仍然是它。
- `MLP19` 是 support，因为它主要负责把 route state 分发进 construction，而不是自己完成 `<tool_call>` 组装。
- `L21H1` 是 support，因为它明显参与 late routing，但读入对象比 `L21H12` 更杂，且对 `MLP27` 的传递略弱。

## 核心结论

### 1. 旧主线是否还成立

结论：`L20H5 / L21H1 / L21H12 / L24H6 / MLP27` 这条旧主线整体仍成立，但应该改写成“入口 + 双路 late routing + pre-writer formatter + main writer”，而不是把它们视作同质的 late tool heads。

### 2. `L20H5` 更像什么

`MLP19 -> L20H5` 的 route mediation 中位数为 `0.044`，target local rescue 为 `0.496`；同时它的 direct margin 写出在 clean 下已经为 `-0.103`。
因此 `L20H5` 仍然接收 route state，但更合适的定位不是“上游 decision 节点”，而是 Construction 入口：它是最早把 route state 接到文件名 / 函数体 payload 上的节点。它更像 payload binder / ingress，而不是已经完成 `<tool_call>` 写出的 main writer。

### 3. `L21H1` 和 `L21H12` 是并行冗余还是功能不同

二者都属于 late routing，但不是简单冗余。旧 full-run 里，`L21H12 -> MLP27` mediation 为 `0.328`，高于 `L21H1 -> MLP27` 的 `0.292`；而 `L20H5 + L21H12` 的 step rescue 也高于 `L20H5 + L21H1`。
结合 attention 证据，`L21H1` 更像把 construction state 路由到 output-start / example 相关位点的通用 late router；`L21H12` 更像把 tool protocol / example / instruction tail 绑定到 final writer 的 protocol-heavy router。

### 4. `L24H6` 更像什么

`L24H6` 在 attention 聚合里最稳定读取 `tool_instruction`；旧 full-run 中它到 `MLP27` 的 mediation 为 `0.305`，而 stagewise 从 `+L21H12` 到 `+L24H6` 时，route margin 从 `1.394` 升到 `1.723`，tool logit margin 从 `1.500` 升到 `1.875`。
因此它更像 protocol commitment / formatter，而不是普通 late router：它不是主要读取文件对象，而是把已经路由好的 tool state 压进合适的调用起始格式。

### 5. `MLP27` 是不是主要 writer

是。旧 full-run 里 `MLP27` 单节点 rescue 为 `0.809`，`corrupt_full` 上 alpha=`1.5` steering 的 `<tool_call>` top1 达到 `0.833`；新 full-run 里它的 clean direct tool logit effect 为 `13.562`，clean margin effect 为 `10.844`，也是链上最大。
但 `MLP27` 写的不是抽象 route state，而是更接近实际输出起始的 `<tool_call>`-favoring residual evidence。

### 6. `<tool_call>` 从哪里开始明显可见

如果只看 late chain 的平均 direct-logit lens，`MLP19` 对 `<tool_call>` 已经有可见正 logit（`0.065`，rank `60534`），但这还更像 route-state spillover。
按 stagewise logit margin 看，`<tool_call>` 首次稳定翻正发生在 `plus_L21H12`；按 route margin 看，首次翻正发生在 `plus_L21H1`；按 `<tool_call>` top1 多数出现看，第一次超过半数样本发生在 `plus_L21H12`。
`L20H5` 更像“开始接住并推动这条路”，它的 clean margin 为 `-0.103`，但 clean-corrupt delta margin 为 `0.018`；真正把 `<tool_call>` 变成清晰输出候选的是 `L21H1/L21H12` 之后的 late routing，再由 `L24H6` 与 `MLP27` 放大并定型。

### 7. 哪些节点一边推 `<tool_call>`，一边压 competing token

- `L20H5`: clean `<tool_call>` logit `-0.043`，竞争 token logit `0.062`，margin `-0.103`，delta margin `0.018`。
- `L21H12`: clean `<tool_call>` logit `0.174`，竞争 token logit `-0.125`，margin `0.302`，delta margin `0.016`。
- `L24H6`: clean `<tool_call>` logit `2.484`，竞争 token logit `0.236`，margin `2.255`，delta margin `0.257`。
- `MLP27`: clean `<tool_call>` logit `13.562`，竞争 token logit `2.688`，margin `10.844`，delta margin `1.609`。
其中 `L24H6` 和 `MLP27` 的 margin 提升最像“同时抬 `<tool_call>`、压 competing token”；`L20H5` 更像先把 route state 接到 payload 上并轻推输出边界；`L21H12` 则处在路由和协议绑定之间。

### 8. 有没有漏掉的新 construction nodes

晚层新候选里，最好的一项是 `L25H13`，单节点 rescue 为 `0.099`，但仍明显弱于 anchor。
因此这轮没有发现足以推翻旧主线的新 anchor。`L25H13 / L25H10 / L26H15 / L27H7` 最多只能保留为 candidate：它们在 attention 聚合上确实带有 tool/protocol 痕迹，但在单节点 patch 和写出效果上都不够强。

## 读什么 / 写什么 / 怎么传

| 节点 | 读什么 | 写什么 | 怎样传给下游 | 当前定位 |
| --- | --- | --- | --- | --- |
| `L20H5` | 文件名、函数体锚点、少量 assistant prefix | 早期 payload-bound tool state | 把 payload-bound state 送到 `L21H1/L21H12` | anchor / Construction 入口 |
| `L21H1` | example / output-start 相关位置，夹带 task-body/preamble 信息 | late routed tool state | 一部分直送 `MLP27`，一部分送 `L24H6` | support / late router |
| `L21H12` | tool_call example、instruction tail、protocol 相关位点 | 更 protocol-heavy 的 routed tool state | 强送 `MLP27`，也送 `L24H6` | anchor / protocol-heavy router |
| `L24H6` | tool instruction / call format | `<tool_call>` 起始格式的 pre-writer state | 主要送 `MLP27` | anchor / formatter-commitment |
| `MLP27` | 已绑定好的 late tool state | `<tool_call>`-favoring residual direction | 直接写到输出 | anchor / main writer |
| `MLP19` | route score | tool-route state 本身 | fanout 到多个 construction 节点 | support / interface |

## 与 Output-Route Decision 的连接

### 哪些 construction 节点最直接接收 route state

- `MLP19 -> L20H5`: route mediation `0.044`，target local rescue `0.496`。
- `MLP19 -> L21H1`: route mediation `0.066`，target local rescue `0.496`。
- `MLP19 -> L21H12`: route mediation `0.057`，target local rescue `0.261`。
- `MLP19 -> L24H6`: route mediation `0.119`，target local rescue `0.719`。
- `MLP19 -> MLP27`: route mediation `0.145`，target local rescue `0.536`。
从这组 full-run 数据看，`MLP27` 是最强的 route-state 接收者之一，但它不是最早的 payload binder；`L20H5` 是最早把 route state 接到文件/函数体对象上的节点；`L21H1/L21H12` 进一步把这份 state 路由并协议化；`L24H6` 则把它压成更接近 `<tool_call>` 起始格式的 pre-writer state。

### route state 如何被转成 `<tool_call>` 偏好

最可信的链条是：`MLP19` 先把“该走 tool 协议输出”的 route state 分发到 late construction 区；`L20H5` 把这份状态绑定到 file/function payload；`L21H1/L21H12` 把已绑定状态继续路由到 example / protocol 相关位点；`L24H6` 把 route+payload state 压进具体调用起始格式；最后 `MLP27` 把它写成真正可见的 `<tool_call>` 首词偏好。

## 写出类可视化结论

- stagewise 轨迹见 `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data/figures/construction_stagewise_trajectory.png`。这张图显示：`<tool_call>` 的 logit margin 首次翻正发生在 `plus_L21H12`，首次在多数样本成为 top-1 发生在 `plus_L21H12`，再由 `MLP27` 推到最终稳定区。
- top token / top-1 变化图见 `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data/figures/construction_top_token_change.png`。它把 `<tool_call>` top-1 比例、boundary flip，以及主要 competing token 的 top-1 组成放到同一张图里。
- 节点 direct writeout 见 `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data/figures/construction_node_writeout.png`。这张图最直接回答“谁在写什么”。
- residual projection 见 `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data/figures/construction_node_projection.png`。它显示同一批节点怎样沿 `<tool_call>`-竞争方向累积偏置。
- `MLP19` fanout 图见 `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data/figures/construction_route_fanout.png`。它回答 route state 是怎么接进 construction 的。
- 平均 direct-logit lens 见 `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data/figures/construction_mean_logit_lens.png`。它回答 `<tool_call>` 在哪些节点开始变得“可见”。
- attention 读入面板见 `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/source_data/figures/construction_attention_panels.png`。这张图用于区分 `L20H5/L21H1/L21H12/L24H6` 读入对象的差别。

## 每个 anchor node 的证据包

### `L20H5`

- 读入证据：attention 聚合和 head audit 都显示它优先读 `file_target` / `function_body_anchor`。
- 写出证据：新的 direct logit effect 显示它会把 clean-corrupt 输出边界往 `<tool_call>` 方向推，哪怕它通常还不是局部最强 writer。
- 传递证据：旧 full-run 里 `L20H5 -> L21H12` 与 `L20H5 -> L21H1` 都有正 mediation，且前者更强。
- 行为证据：单节点 patch rescue 与 stagewise 第一跳都稳定为正。

### `L21H12`

- 读入证据：attention 聚合里它最稳定读 `tool_call_example` / instruction tail。
- 写出证据：新的 direct logit effect 与 projection 都比 `L21H1` 更强。
- 传递证据：`L21H12 -> MLP27` 是旧 full-run 中最强的 late tool edge。
- 行为证据：把它并入 stagewise 后，`<tool_call>` margin 由负转正。

### `L24H6`

- 读入证据：attention 聚合明确显示它最强读 `tool_instruction`。
- 写出证据：新的 direct effect 显示它明显提高 `<tool_call>` margin。
- 传递证据：旧 full-run 中 `L24H6 -> MLP27` mediation 很强。
- 行为证据：stagewise 从 `+L21H12` 到 `+L24H6` 时，`<tool_call>` top1 再次大幅上升。

### `MLP27`

- 写出证据：direct effect / projection 都是链上最强。
- 因果证据：steering 在 `corrupt_full` 上可把 `<tool_call>` top1 推到高比例。
- 传递证据：它直接接收来自 `L21H1/L21H12/L24H6` 的 late routed state，也能直接接收部分 `MLP19` fanout。
- 行为证据：stagewise 最后一跳主要由它把已成形的 `<tool_call>` 偏置写成稳定首词。

## 未解决问题

- 这轮虽然看到 `MLP19 -> MLP27` 的直接 fanout 很强，但还不能把它写成“绕过所有 late heads 的独立主路”；更像并行 receipt。
- `L21H1` 的功能已经能和 `L21H12` 区分开，但还没有足够强的限制性 patch 去精确分解二者的冗余比例。
- 新候选晚层头存在 attention 迹象，但没有足够强的 patching / writeout 证据，不能升格。

## 论文风格总结

当前最可信的 Tool-Call Construction 机制是：`MLP19` 把已定下来的 tool-route state 分发到晚层 construction 区后，`L20H5` 先把这份状态绑定到文件名与函数体对象，`L21H1/L21H12` 再把已绑定状态分别路由到 output-start/example 与更 protocol-heavy 的 tool-call example / instruction-tail 相关位点；随后 `L24H6` 把这份 route+payload state 压进更接近调用起始格式的 pre-writer state，最终由 `MLP27` 把它写成首词 `<tool_call>` 的强偏好。最强的证据来自三类 full-run 结果同时收敛：其一，旧的边级 patching 证明 `L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27` 不是共现链，而是有明确 late mediation 的传递链；其二，新的 direct logit effect / residual projection 显示 `<tool_call>` 的写出从 `L20H5` 开始可见，在 `L21H12/L24H6` 明显增强，并在 `MLP27` 达到最大；其三，新的 stagewise token trajectory 直接显示 `<tool_call>` 从弱偏置到稳定 top-1 的逐步形成过程。当前还不能强写的是：`MLP19 -> MLP27` 是否构成绕过 late heads 的独立主路，以及若干晚层候选头是否属于 construction 支路而非伴随激活。

## Artifact Index

- `construction_writeout_per_sample.csv`
- `construction_writeout_summary.csv`
- `construction_stagewise_per_sample.csv`
- `construction_stagewise_summary.csv`
- `construction_stagewise_top_tokens_summary.csv`
- `figures/construction_top_token_change.png`
- `construction_route_fanout_per_sample.csv`
- `construction_route_fanout_summary.csv`
- `construction_candidate_patch_summary.csv`
- `construction_mean_logit_lens_summary.csv`
