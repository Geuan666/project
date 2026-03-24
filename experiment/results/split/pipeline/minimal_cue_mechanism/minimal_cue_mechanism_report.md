# Minimal Cue Mechanism Report

## 结论先行

在 24 节点 circuit 内，最小 lead cue 不像一个被单个 head 直接盯住的裸 token；它更像是先进入共享/用户侧状态，然后在晚期由 `L20H5` 作为决策性 tool ingress 接住，经 `L21H1/L21H12` 路由，在 `L24H6/MLP27` 区域被放大并写成 `<tool_call>`。
`no_tool` 链则不是单纯“另一个输出头”；它先由 `L16H4` 读入竞争性 user-side 状态，经 `MLP17` 写成 no-tool 偏置，再一边通过 `L23H6` 把这份状态送到晚期输出区，一边反压 `L20H5/L21H12` 这条 tool ingress。

## 1. 最小 cue 本身就足够翻转首 token

- `clean_full`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`
- `clean_with_corrupt_lead`: decision `-4.594`, tool-top1 `0.000`, no-tool-top1 `0.998`
- `corrupt_with_clean_lead`: decision `3.203`, tool-top1 `1.000`, no-tool-top1 `0.000`
- `corrupt_full`: decision `-4.594`, tool-top1 `0.000`, no-tool-top1 `0.998`

## 2. 在 24 节点里，谁最先稳定携带这份 cue

- 请求样本数：`all shared samples`；实际有效样本数：`1223`。
- 单节点扫描里，`tool` 方向最早超过 `0.10` rescue 的 cue-sensitive 节点是 `MLP12`（L12，rescue `0.255`）。
- 单节点扫描里，`no_tool` 方向最早超过 `0.10` rescue 的 cue-sensitive 节点是 `MLP12`（L12，rescue `0.227`）。
- 但决策性晚期主链仍应区分开看：tool 主链从 `L20H5` 进入，no-tool 最小 suppress chain 从 `L16H4` 进入。
- `tool` 方向 top 节点：
  - `MLP27` / L27: rescue `0.807`, boundary-flip `0.273`, group `symmetric_backbone`, hint `shared writer MLP`
  - `L21H12` / L21: rescue `0.705`, boundary-flip `0.139`, group `tool_bias_backbone`, hint `format/prefix router`
  - `L24H6` / L24: rescue `0.574`, boundary-flip `0.000`, group `symmetric_backbone`, hint `format/prefix router`
  - `L21H1` / L21: rescue `0.568`, boundary-flip `0.036`, group `tool_bias_backbone`, hint `format/prefix router`
  - `MLP17` / L17: rescue `0.552`, boundary-flip `0.087`, group `no_tool_bias_backbone`, hint `no-tool-biased writer MLP`
  - `L23H6` / L23: rescue `0.523`, boundary-flip `0.011`, group `tool_bias_backbone`, hint `tool-biased router`
  - `MLP16` / L16: rescue `0.522`, boundary-flip `0.073`, group `symmetric_backbone`, hint `shared writer MLP`
  - `L20H5` / L20: rescue `0.305`, boundary-flip `0.002`, group `symmetric_backbone`, hint `user-content reader`
- `no_tool` 方向 top 节点：
  - `MLP27` / L27: rescue `0.810`, boundary-flip `0.545`, group `symmetric_backbone`, hint `shared writer MLP`
  - `MLP17` / L17: rescue `0.474`, boundary-flip `0.090`, group `no_tool_bias_backbone`, hint `no-tool-biased writer MLP`
  - `MLP16` / L16: rescue `0.432`, boundary-flip `0.061`, group `symmetric_backbone`, hint `shared writer MLP`
  - `L24H6` / L24: rescue `0.426`, boundary-flip `0.043`, group `symmetric_backbone`, hint `format/prefix router`
  - `L21H12` / L21: rescue `0.371`, boundary-flip `0.026`, group `tool_bias_backbone`, hint `format/prefix router`
  - `L23H6` / L23: rescue `0.282`, boundary-flip `0.001`, group `tool_bias_backbone`, hint `tool-biased router`
  - `L21H1` / L21: rescue `0.264`, boundary-flip `0.002`, group `tool_bias_backbone`, hint `format/prefix router`
  - `MLP12` / L12: rescue `0.227`, boundary-flip `0.019`, group `no_tool_bias_backbone`, hint `no-tool-biased writer MLP`

读法上要注意：这里的“最先”指的是在 24 节点 final circuit 内，最早能稳定把最小 cue 重新补回决策的节点；它不等于原始 token 的唯一第一读头。

## 3. tool 链是如何被放大并写成 `<tool_call>` 的

- 分阶段 patch（`clean_full -> clean_with_corrupt_lead`）:
- 关键边介导：
- 对应 head 的 Q/K/V/Z 证据（来自已有 `final_head_attention_audit` 全量结果）：

这条链的关键信号很清楚：`L20H5` 单独只能带来很弱的 tool 恢复；加入 `L21H1/L21H12` 后决策边界开始翻正；`L24H6` 和尤其 `MLP27` 把差异推到稳定 `<tool_call>`。

## 4. `no_tool` 链到底如何发生

- 分阶段 patch（`corrupt_full -> corrupt_with_clean_lead` 的反向 no-tool 恢复）:
  - step 1 / `L16H4`: rescue `0.197`, decision `2.493`, no-tool-top1 `0.011`, boundary-flip `0.001`
  - step 2 / `L16H4|MLP17`: rescue `0.606`, decision `0.995`, no-tool-top1 `0.254`, boundary-flip `0.181`
  - step 3 / `L16H4|MLP17|L23H6`: rescue `0.792`, decision `0.086`, no-tool-top1 `0.517`, boundary-flip `0.473`
- 关键边介导：
  - `L16H4->MLP17`: source `0.197`, blocked `0.116`, mediated `0.078`
  - `MLP17->L21H12`: source `0.474`, blocked `0.399`, mediated `0.066`
  - `MLP17->L23H6`: source `0.474`, blocked `0.412`, mediated `0.066`
  - `MLP17->L21H1`: source `0.474`, blocked `0.411`, mediated `0.058`
  - `MLP17->L24H6`: source `0.474`, blocked `0.424`, mediated `0.051`
  - `MLP17->L20H5`: source `0.474`, blocked `0.430`, mediated `0.050`
- 对应 head 的 Q/K/V/Z 证据（来自已有 `final_head_attention_audit` 全量结果）：
  - `L16H4`: best-read `tail_suffix`, best-causal-span `task_body`, best-component `z` rescue `0.197`
  - `L23H6`: best-read `file_target`, best-causal-span `file_target`, best-component `z` rescue `0.282`

`no_tool` 链的发生方式因此是“双重的”：`MLP17` 既把 no-tool 状态往 `L23H6` / 输出区送，也对 `L20H5/L21H12` 这类 tool ingress 做抑制。所以它不是只在末端写一个 `no_tool` token，而是在晚期决策区同时做“写 no-tool”和“压 tool 路”。

## 5. 直接回答 TODO 里的五个子问题

1. 单节点扫描里，最早出现明显 cue-sensitivity 的 tool-side 节点是 `MLP12`，no-tool-side 节点是 `MLP12`；但决策性晚期主链分别从 `L20H5` 和 `L16H4` 进入。
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
