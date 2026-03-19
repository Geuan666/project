# Paper-Facing Mechanism Update

## 1. Scope

这份更新不重开 circuit localization 或 correctness。它只回答两个剩余问题：

1. 为什么最小 lead phrase cue 会沿前向链被读取、传播、放大，并最终把首 token 推到 `<tool_call>`。
2. `L16H4 -> MLP17 -> L23H6` 如何实现真正的 suppressive no-tool mechanism。

## 2. Question 1: Forward Mechanistic Story

当前可以强写的主链是：`minimal cue -> L2H14 -> MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27`。

- `L2H14` 是最早的 head-level reader，但还不是 first stable delivery-object writer。
- `MLP11` 是 first stable delivery-object writer。
- 只改 `MLP11` 的 shared file-vs-answer direction，就会把同一条对象轴推入 `MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27`。
- 最终后果不是只在中层表里好看，而是直接改变 `<tool_call>` / `no_tool` 与 `MLP27` 的终端写出。

对应主图：`figure_18` 到 `figure_21`。

## 3. Question 2: Suppression Mechanistic Story

当前可以强写的主链是：`L16H4 -> MLP17 -> L23H6`。

- `L16H4` 读的是 user-side ordinary-answer evidence，集中在 task-body / tail-suffix 一带，而不是 tool schema。
- `MLP17` 是 suppressive writer：它既抬高 `no_tool`，也压低 `<tool_call>`。
- `MLP17` 不只改末端 token；它还把 `L20H5 / L21H1 / L21H12 / L24H6 / MLP27` 推向各自的 local no-tool axis。
- `L23H6` 是 late suppressive relay，把已经写好的 suppressive state 送进输出附近。

对应主图：`figure_22` 到 `figure_25`。

## 4. Final Verdict

- Question 1 paper-ready: `True`.
- Question 2 paper-ready: `True`.
- Remaining Q1 gap: `exact microfeature inside L2H14`.
- Remaining Q2 gap: `exact microfeature inside L16H4`.

## 5. Deliverables

- `paper_facing_focused_evidence_table.csv`
- `paper_facing_claim_tiers.json`
- `paper_facing_still_unsolved.csv`
- `figures/PAPER_FIGURE_PLAN.md`
- `figure_18` to `figure_25`
