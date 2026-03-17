# Minimal Cue Mechanism Report

## 结论先行

在 24 节点 circuit 内，最小 lead cue 不像一个被单个 head 直接盯住的裸 token；它更像是先进入共享/用户侧状态，然后在晚期由 `L2H14` 作为最早稳定的 tool ingress 接住，经 `L21H1/L21H12` 路由，在 `L24H6/MLP27` 区域被放大并写成 `<tool_call>`。
`no_tool` 链则不是单纯“另一个输出头”；它先由 `MLP12` 读入竞争性 user-side 状态，经 `MLP17` 写成 no-tool 偏置，再一边通过 `L23H6` 把这份状态送到晚期输出区，一边反压 `L20H5/L21H12` 这条 tool ingress。

## 1. 最小 cue 本身就足够翻转首 token

- `clean_full`: decision `6.188`, tool-top1 `1.000`, no-tool-top1 `0.000`
- `clean_with_corrupt_lead`: decision `-6.625`, tool-top1 `0.000`, no-tool-top1 `1.000`
- `corrupt_with_clean_lead`: decision `6.188`, tool-top1 `1.000`, no-tool-top1 `0.000`
- `corrupt_full`: decision `-6.625`, tool-top1 `0.000`, no-tool-top1 `1.000`

## 2. 在 24 节点里，谁最先稳定携带这份 cue

- 请求样本数：`3`；实际有效样本数：`3`。
- `tool` 方向最早超过 `0.10` rescue 的节点是 `L2H14`（L2，rescue `0.133`）。
- `no_tool` 方向最早超过 `0.10` rescue 的节点是 `MLP12`（L12，rescue `0.231`）。
- `tool` 方向 top 节点：
  - `MLP27` / L27: rescue `0.868`, boundary-flip `0.000`, group `symmetric_backbone`, hint `shared writer MLP`
  - `L21H12` / L21: rescue `0.847`, boundary-flip `0.000`, group `tool_bias_backbone`, hint `format/prefix router`
  - `MLP16` / L16: rescue `0.779`, boundary-flip `0.333`, group `symmetric_backbone`, hint `shared writer MLP`
  - `L21H1` / L21: rescue `0.660`, boundary-flip `0.000`, group `tool_bias_backbone`, hint `format/prefix router`
  - `L23H6` / L23: rescue `0.656`, boundary-flip `0.000`, group `tool_bias_backbone`, hint `tool-biased router`
  - `MLP19` / L19: rescue `0.632`, boundary-flip `0.000`, group `symmetric_backbone`, hint `shared writer MLP`
  - `MLP21` / L21: rescue `0.579`, boundary-flip `0.000`, group `tool_tail`, hint `tool-tail writer MLP`
  - `L24H6` / L24: rescue `0.578`, boundary-flip `0.000`, group `symmetric_backbone`, hint `format/prefix router`
- `no_tool` 方向 top 节点：
  - `MLP27` / L27: rescue `0.702`, boundary-flip `0.333`, group `symmetric_backbone`, hint `shared writer MLP`
  - `MLP16` / L16: rescue `0.584`, boundary-flip `0.333`, group `symmetric_backbone`, hint `shared writer MLP`
  - `MLP17` / L17: rescue `0.464`, boundary-flip `0.000`, group `no_tool_bias_backbone`, hint `no-tool-biased writer MLP`
  - `L24H6` / L24: rescue `0.405`, boundary-flip `0.000`, group `symmetric_backbone`, hint `format/prefix router`
  - `MLP19` / L19: rescue `0.300`, boundary-flip `0.000`, group `symmetric_backbone`, hint `shared writer MLP`
  - `MLP12` / L12: rescue `0.231`, boundary-flip `0.000`, group `no_tool_bias_backbone`, hint `no-tool-biased writer MLP`
  - `L23H6` / L23: rescue `0.205`, boundary-flip `0.000`, group `tool_bias_backbone`, hint `tool-biased router`
  - `L21H12` / L21: rescue `0.194`, boundary-flip `0.000`, group `tool_bias_backbone`, hint `format/prefix router`

读法上要注意：这里的“最先”指的是在 24 节点 final circuit 内，最早能稳定把最小 cue 重新补回决策的节点；它不等于原始 token 的唯一第一读头。

## 3. tool 链是如何被放大并写成 `<tool_call>` 的

- 分阶段 patch（`clean_full -> clean_with_corrupt_lead`）:
  - step 1 / `L20H5`: rescue `0.320`, decision `-3.472`, tool-top1 `0.000`, boundary-flip `0.000`
  - step 2 / `L20H5|L21H1`: rescue `0.803`, decision `-1.105`, tool-top1 `0.333`, boundary-flip `0.333`
  - step 3 / `L20H5|L21H1|L21H12`: rescue `0.990`, decision `2.371`, tool-top1 `0.667`, boundary-flip `0.667`
  - step 4 / `L20H5|L21H1|L21H12|L24H6`: rescue `0.993`, decision `2.863`, tool-top1 `1.000`, boundary-flip `1.000`
  - step 5 / `L20H5|L21H1|L21H12|L24H6|MLP27`: rescue `0.998`, decision `3.828`, tool-top1 `1.000`, boundary-flip `1.000`
- 关键边介导：
  - `L21H12->MLP27`: source `0.847`, blocked `0.472`, mediated `0.375`
  - `L21H1->MLP27`: source `0.660`, blocked `0.330`, mediated `0.330`
  - `L24H6->MLP27`: source `0.578`, blocked `0.278`, mediated `0.312`
  - `L21H1->L24H6`: source `0.660`, blocked `0.452`, mediated `0.226`
  - `L21H12->L24H6`: source `0.847`, blocked `0.637`, mediated `0.210`
  - `L20H5->L21H12`: source `0.320`, blocked `0.187`, mediated `0.133`
- 对应 head 的 Q/K/V/Z 证据（来自已有 `final_head_attention_audit` 全量结果）：
  - `L20H5`: best-read `file_target`, best-causal-span `function_body_anchor`, best-component `z` rescue `0.308`
  - `L21H1`: best-read `file_target`, best-causal-span `file_target`, best-component `z` rescue `0.573`
  - `L21H12`: best-read `tail_suffix`, best-causal-span `tail_suffix`, best-component `z` rescue `0.707`
  - `L24H6`: best-read `file_target`, best-causal-span `file_target`, best-component `z` rescue `0.574`

这条链的关键信号很清楚：`L20H5` 单独只能带来很弱的 tool 恢复；加入 `L21H1/L21H12` 后决策边界开始翻正；`L24H6` 和尤其 `MLP27` 把差异推到稳定 `<tool_call>`。

## 4. `no_tool` 链到底如何发生

- 分阶段 patch（`corrupt_full -> corrupt_with_clean_lead` 的反向 no-tool 恢复）:
  - step 1 / `L16H4`: rescue `0.118`, decision `4.649`, no-tool-top1 `0.000`, boundary-flip `0.000`
  - step 2 / `L16H4|MLP17`: rescue `0.707`, decision `1.856`, no-tool-top1 `0.000`, boundary-flip `0.000`
  - step 3 / `L16H4|MLP17|L23H6`: rescue `0.910`, decision `-0.359`, no-tool-top1 `0.667`, boundary-flip `0.667`
- 关键边介导：
  - `L16H4->MLP17`: source `0.118`, blocked `0.061`, mediated `0.075`
  - `MLP17->L23H6`: source `0.464`, blocked `0.359`, mediated `0.061`
  - `MLP17->L21H1`: source `0.464`, blocked `0.391`, mediated `0.044`
  - `MLP17->L21H12`: source `0.464`, blocked `0.350`, mediated `0.044`
  - `MLP17->L24H6`: source `0.464`, blocked `0.427`, mediated `0.036`
  - `MLP17->L20H5`: source `0.464`, blocked `0.439`, mediated `0.025`
- 对应 head 的 Q/K/V/Z 证据（来自已有 `final_head_attention_audit` 全量结果）：
  - `L16H4`: best-read `tail_suffix`, best-causal-span `task_body`, best-component `z` rescue `0.198`
  - `L23H6`: best-read `file_target`, best-causal-span `file_target`, best-component `z` rescue `0.280`
- reverse overlap 补充：
  - reverse-aligned no-tool line: `L15H5, L16H13, L16H4, L16H8, L16H9, L17H2, L23H6, MLP12, MLP17`
  - reverse-selective recall `0.889`, precision `1.000`
  - The 3-node minimal no-tool chain is fully contained in the reverse core.
  - The 9-node reverse-aligned no-tool semantic line overlaps 8/8 reverse-selective nodes and 14/15 reverse-selective edges; the only extra node is L23H6, which sits in the shared late output backbone.

`no_tool` 链的发生方式因此是“双重的”：`MLP17` 既把 no-tool 状态往 `L23H6` / 输出区送，也对 `L20H5/L21H12` 这类 tool ingress 做抑制。所以它不是只在末端写一个 `no_tool` token，而是在晚期决策区同时做“写 no-tool”和“压 tool 路”。

## 5. 直接回答 TODO 里的五个子问题

1. 在 final 24-node circuit 内，最早稳定接住最小 cue 的 tool-side 节点是 `L2H14`；最早稳定接住 no-tool 竞争状态的是 `MLP12`。
2. 它们读到的不是孤立首词，而是 instruction lead / file target / function-body anchor 绑定出来的 user-side commitment state。
3. 在晚期 attention 头上，最强证据主要落在 `z` 写出而不是单独 `Q/K/V`，说明到 `L20H5/L21H12/L16H4/L23H6` 时，cue 已经被折叠成可直接传播的 head output state。
4. tool 放大发生在 `L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27`；no-tool 放大发生在 `L16H4 -> MLP17 -> L23H6`，并由 `MLP17 -> L20H5/L21H12` 产生额外 suppress。
5. `<tool_call>` 的主写出节点是 `MLP27`；`no_tool` 的主写出/抑制核心是 `MLP17`，`L23H6` 负责把这份状态带进晚期输出区。

## Artifact Index

- `minimal_cue_variant_summary.csv`
- `minimal_cue_node_summary.csv`
- `minimal_cue_step_summary.csv`
- `minimal_cue_edge_summary.csv`
- `minimal_cue_mechanism_summary.json`
- `minimal_cue_mechanism_report.md`
