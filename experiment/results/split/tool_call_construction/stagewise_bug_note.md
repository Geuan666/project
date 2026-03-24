# Stagewise Bug 说明

## bug 在哪里

- bug 位于 `tool_call_construction_analysis.py` 的 `summarize_group()`。
- `tool_top1` 是布尔字段，但旧逻辑只把名字以 `_rate` / `_flip` / `_success` 结尾的指标当成比例处理。
- 因此 `tool_top1` 被按普通数值取了中位数，随后又在下游被重命名成 `tool_top1_rate`。

## 为什么会导致 summary 出错

- 对布尔值取中位数，本质上是在算“多数投票”，不是实际比例。
- 所以旧 `construction_stagewise_summary.csv` 里，`plus_L21H1` 这类真正比例约为 `0.503` 的 step，会被错误写成 `1.0`。
- `construction_stagewise_top_tokens_summary.csv` 用的是逐样本真实计数，所以两者自然不一致。
- 同样的口径问题也影响了 `construction_candidate_patch_summary.csv` 的 `tool_top1_rate`。

## 修复方式

- 修复后，`summarize_group()` 会把所有布尔型指标统一按比例汇总，不再依赖字段名后缀。
- `report-only` 也改成优先读取已有 per-sample 文件，重建 summary、图和报告，而不是继续沿用旧 summary。
- 这次 refine 结果全部基于旧 full-run 的 per-sample 文件重建，没有重跑原始全量 writeout / route fanout / candidate scan。

## 受影响并重生成的产物

- `construction_stagewise_summary.csv`
- `construction_candidate_patch_summary.csv`
- `figures/construction_stagewise_trajectory.png`
- `figures/construction_top_token_change.png`
- `tool_call_construction_refine_report.md` 中所有引用 `tool_top1_rate`、`首次过半`、`top-1 多数出现` 的表述

## stagewise 受影响最大的行

- `plus_L21H12`: 旧值 `1.000` -> 新值 `0.859`
- `plus_L24H6`: 旧值 `1.000` -> 新值 `0.928`
- `plus_MLP27`: 旧值 `1.000` -> 新值 `0.979`
- `plus_MLP19`: 旧值 `0.000` -> 新值 `0.043`
- `plus_L20H5`: 旧值 `0.000` -> 新值 `0.146`
- `plus_L21H1`: 旧值 `0.000` -> 新值 `0.489`
