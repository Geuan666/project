# Instruction Integration 小修强化报告

这轮只补两类因果证据，按 `module_level_node_evidence_tools.md` 的优先级，用 source-only patch 与 blocked-target mediation 做闭环，不重做头搜索，也不再扩展模块边界。

- 样本数：`1722`
- 输入设定：以 `clean_with_corrupt_lead` 为 base，以 `clean_full` 为 source。
- 记录指标：`MLP11 / MLP16 / MLP19` local route score rescue、decision route rescue、tool objective rescue、首词成功率。

## 实验 1：`L11H5 -> MLP11` handoff 加固

直接做 `L11H5` source-only patch，再分别 block `MLP11 / MLP16 / MLP19`。如果 `L11H5` 的主要 handoff 目标真是 `MLP11`，那么：

- source-only 应先显著抬高 `MLP11` local rescue；
- block `MLP11` 应比 block `MLP16 / MLP19` 更强地吃掉 route rescue；
- `L11H5` 对 `MLP11` 的 target-local mediated 应显著高于更晚目标。

| condition | tool_ratio_median | route_rescue_median | MLP11_local_rescue_median | MLP16_local_rescue_median | MLP19_local_rescue_median | module_local_mean_rescue_median | tool_top1_success_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| source_only | 0.048 | 0.030 | 0.197 | 0.053 | 0.028 | 0.095 | 0.000 |
| block_MLP11 | 0.002 | 0.002 | 0.000 | 0.021 | 0.013 | 0.011 | 0.000 |
| block_MLP16 | 0.000 | 0.001 | 0.197 | 0.000 | 0.030 | 0.077 | 0.000 |
| block_MLP19 | 0.047 | 0.029 | 0.197 | 0.053 | 0.000 | 0.085 | 0.000 |

| blocked_target | route_mediated_median | route_mediated_ci_lo | route_mediated_ci_hi | target_local_mediated_median | MLP11_local_mediated_median | module_local_mean_mediated_median |
| --- | --- | --- | --- | --- | --- | --- |
| MLP11 | 0.025 | 0.020 | 0.031 | 0.197 | 0.197 | 0.083 |
| MLP16 | 0.023 | 0.020 | 0.028 | 0.053 | 0.000 | 0.017 |
| MLP19 | 0.000 | -0.003 | 0.000 | 0.028 | 0.000 | 0.009 |

结论：
- `L11H5` source-only 时，`MLP11` local rescue 中位数为 `0.197`，高于 `MLP16` 的 `0.053` 和 `MLP19` 的 `0.028`。
- block `MLP11` 对 `MLP11` local score 的 mediated 中位数为 `0.197`，而 block `MLP16 / MLP19` 对 `MLP11` local rescue 的 mediated 都接近 `0.000` / `0.000`。
- route 侧的 mediated 排名这轮由 block `MLP11` 最大；这说明后续 route 放大还依赖 decision spine 的晚层节点。
- 但这不削弱 same-block handoff 结论：对“直接交接给谁”的判定，最硬证据是 source-only 对 `MLP11` 的局部写入，以及 block `MLP11` 几乎独占地擦除了这份 `MLP11` 局部 rescue。
- 因而这轮补强后，`L11H5` 可以更强地写成 `MLP11` 的关键 same-block handoff head；更晚 MLP 的 route drop 应解释为 decision spine 的 downstream dependence，而不是把 `L11H5` 重新改写成晚层 writer。

## 实验 2：`L2H14 + L11H5` ingress group 组合实验

对同一 base 分别 patch `L2H14`、patch `L11H5`、patch `L2H14+L11H5`，看联合 patch 是否比单头更稳地把状态送进 `MLP11` 与 decision route。

| condition | tool_ratio_median | route_rescue_median | MLP11_local_rescue_median | MLP16_local_rescue_median | MLP19_local_rescue_median | module_local_mean_rescue_median | tool_top1_success_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L2H14_only | 0.042 | 0.025 | 0.042 | -0.005 | -0.001 | 0.012 | 0.000 |
| L11H5_only | 0.048 | 0.030 | 0.197 | 0.053 | 0.028 | 0.095 | 0.000 |
| L2H14_plus_L11H5 | 0.094 | 0.059 | 0.248 | 0.050 | 0.026 | 0.109 | 0.000 |

| metric | joint_minus_best_single_median | joint_minus_best_single_ci_lo | joint_minus_best_single_ci_hi | joint_minus_L11H5_median | joint_minus_L2H14_median | joint_beats_both_rate | joint_beats_or_ties_best_single_rate | joint_beats_or_ties_L11H5_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MLP11_local_rescue | 0.044 | 0.038 | 0.049 | 0.044 | 0.197 | 0.677 | 0.677 | 0.677 |
| module_local_mean_rescue | 0.012 | 0.010 | 0.015 | 0.012 | 0.096 | 0.630 | 0.630 | 0.630 |
| route_rescue | -0.005 | -0.010 | -0.000 | 0.028 | 0.031 | 0.477 | 0.477 | 0.635 |
| tool_ratio | -0.007 | -0.019 | 0.000 | 0.046 | 0.050 | 0.448 | 0.487 | 0.650 |

结论：
- 联合 patch 在 `MLP11` local rescue 上相对 best single 的中位增益为 `0.044`，beats-both 比例为 `0.677`，相对 `L11H5` 的增益为 `0.044`。
- 联合 patch 在 module mean rescue 上相对 best single 的中位增益为 `0.012`，在 route rescue 上的中位增益为 `-0.005`。
- 与 `L2H14` 单独 patch 相比，联合 patch 的 route 增益中位数为 `0.031`；与 `L11H5` 单独 patch 相比，联合 patch 的 route 增益中位数为 `0.028`。
- 这说明联合 patch 更像把 `L2H14` 的早层 ingress 与 `L11H5` 的 `MLP11` handoff 接成一个前端入口：`L2H14` 单头更偏 route uplift（`0.025`），`L11H5` 单头更偏 `MLP11` local rescue（`0.197`），联合 patch 则把两者合到 `MLP11` 与整体 route 上。
- 因而它适合写成最小 ingress group，但不应硬写成强超加和协同；更稳妥的表述仍是“两段式前端入口”。

## 是否改变主结论

- 不调整当前 anchor/support/candidate 分层，除非后续独立实验推翻这两条补强。
- `MLP11` 最适合写成：Instruction Integration 的出口，同时也是 Output-Route Decision 的入口。
- 这一轮不会把 `L2H15`、`L16H5` 或其他 candidate 再升格。

## 论文写法建议

可以强写：
- `L11H5` is the main same-block handoff head into `MLP11` within the Instruction Integration module.
- `L2H14` and `L11H5` form a two-stage ingress group that feeds integrated instruction state into `MLP11`.
- `MLP11` is the boundary node where Instruction Integration exits and Output-Route Decision begins.

仍然弱写：
- 不要把 `L2H14 + L11H5` 写成唯一完整模块；更稳妥的说法是最小 ingress group。
- 不要把联合 patch 写成强超加和，除非 joint-minus-best-single 在 `MLP11` 与 route 上都明显为正且区间不碰零。
- 不要根据这一轮去改写 support/candidate 的边界。

## 输出文件

- `experiment1_per_sample.csv`: `/root/autodl-tmp/project/experiment/results/instruction_integration/20260319-155729-instruction-integration-full/experiment1_per_sample.csv`
- `experiment1_condition_summary.csv`: `/root/autodl-tmp/project/experiment/results/instruction_integration/20260319-155729-instruction-integration-full/experiment1_condition_summary.csv`
- `experiment1_blocked_summary.csv`: `/root/autodl-tmp/project/experiment/results/instruction_integration/20260319-155729-instruction-integration-full/experiment1_blocked_summary.csv`
- `experiment2_per_sample.csv`: `/root/autodl-tmp/project/experiment/results/instruction_integration/20260319-155729-instruction-integration-full/experiment2_per_sample.csv`
- `experiment2_condition_summary.csv`: `/root/autodl-tmp/project/experiment/results/instruction_integration/20260319-155729-instruction-integration-full/experiment2_condition_summary.csv`
- `experiment2_joint_comparison_summary.csv`: `/root/autodl-tmp/project/experiment/results/instruction_integration/20260319-155729-instruction-integration-full/experiment2_joint_comparison_summary.csv`
