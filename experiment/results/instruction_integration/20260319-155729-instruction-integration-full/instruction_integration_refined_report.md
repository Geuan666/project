# Instruction Integration 最终精炼报告

## 最终分层

- anchor nodes: `L2H14`, `L11H5`, `MLP11`
- support nodes: `L2H15`, `L13H9`, `L16H1`, `L18H13`
- candidate nodes: `L16H5`, `L9H2`, `L11H6`, `L18H12`
- contrast node: `L20H5`

## 最终结论

全量 heatmap 与全量 causal audit 共同支持一个两段式 Integration 图景：`L2H14` 提供最早的 opening-side ingress，而 `L11H5` 在进入 `MLP11` 的同层 block 内完成更强的 same-block handoff。到 `MLP11` 时，这份 user-side bundle 首次变成稳定可写给 decision spine 的状态。

## 关键证据

- `L2H14`: decision-row user density `0.043`，lead 绑定 `0.073`，best causal span `lead_phrase` rescue `0.025`，`MLP11` target-mediated `0.042`。
- `L11H5`: decision-row user density `0.057`，lead 绑定 `0.070`，best causal span `task_body` rescue `0.051`，`MLP11` target-mediated `0.197`。
- `L13H9`: file-biased binder，best causal span `file_target` rescue `0.049`，`MLP16/19` target-mediated `0.010` / `0.018`。
- `L16H1`: strongest mid-layer binder，lead 绑定 `0.420`，`MLP16` target-mediated `0.037`。
- `L18H13`: late pre-decision binder，decision-row user density `0.073`，`MLP19` target-mediated `0.025`。
- contrast `L20H5`: best causal span `function_body_anchor` rescue `0.038`，但 lead 绑定只有 `0.047`，更像 Construction。

## 机制描述

最可信的机制是：模型先用早层 attention 头把 opening request 和 instruction line 上的 function-body / file / suffix 重新绑成一个 user-side bundle；其中 `L2H14` 是最早 ingress，`L11H5` 是最强的 pre-MLP11/same-block handoff。随后 `L13H9 / L16H1 / L18H13` 继续把这份 bundle 保留到 `MLP16 / MLP19` 附近，使得 `MLP11 -> MLP16 -> MLP19` 能把它重编码成 route score。

## 尚不能强写

- `L2H15` 是否应升格为 anchor 仍缺全量 target-mediated。
- `L16H5` 的热图很像 Integration，但因果证据还不够稳。
- `L9H2 / L11H6 / L18H12` 仍只适合保留为 candidate。
