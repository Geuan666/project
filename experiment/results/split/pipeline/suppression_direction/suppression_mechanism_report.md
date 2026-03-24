# Suppression-Specific Mechanism Report

## 1. Bottom Line

在现有 24 节点 signed circuit 内，`L16H4 -> MLP17 -> L23H6` 现在可以写成真正的 suppressive mechanism，而不是只说它是 competing no-tool branch。

1. `L16H4` 不是在读 tool schema；它主要读 user-side task body / tail-suffix 一带的 ordinary-answer evidence。
   读入证据：task-body density `0.004`，tail-suffix density `0.010`；causal span 最强是 task-body，rescue `0.021`。
   组件级上，`L16H4` 主要靠 `z` 带出 suppressive state：`z` rescue `0.197`，`v` 只有 `0.034`。

2. `MLP17` 是真正把这份 user-side ordinary-answer evidence 写成 suppressive residual feature 的 writer。
   直接 residual 投影显示：从 clean 到 corrupt，`MLP17` 对 `<tool_call>` 的 logit-lens 贡献变化 `-0.016`，对 `no_tool` 的贡献变化 `0.188`。
   只注入 `MLP17` 的 suppressive direction 到 clean prompt，`<tool_call>` logit 中位数变化 `-0.625`，`no_tool` logit 变化 `1.125`，decision score 变化 `-1.586`。

3. `L23H6` 不是主要 reader，而是 late suppressive relay。它本身几乎不读 lead/file object，但它把已经写好的 no-tool state 送进输出附近。
   从 clean 到 corrupt，`L23H6` 对 `<tool_call>` 的 logit-lens 贡献变化 `-1.610`，对 `no_tool` 的贡献变化 `-0.562`。
   同时边级中介保持稳定：`L16H4->MLP17` `0.078`，`MLP17->L23H6` `0.066`。

## 2. Direct Answer To Q2

这条 suppressive chain 不是只做一件事。当前最强结论是：它同时抬高 `no_tool`，也压低 `<tool_call>`，其中 writer 级最强动作在 `MLP17`。

- `L16H4` direction inject into clean: tool-logit `-0.250`, no-tool-logit `0.375`, decision `-0.631`.
- `MLP17` direction inject into clean: tool-logit `-0.625`, no-tool-logit `1.125`, decision `-1.586`.
- `L23H6` direction inject into clean: tool-logit `-0.375`, no-tool-logit `0.625`, decision `-0.894`.

如果一个 intervention 同时让 `<tool_call>` 下降、`no_tool` 上升、并把 decision score 推向 no-tool 侧，那它就不是单纯“在末端写另一个 token”，而是在决策边界两边同时施压。

## 3. Tool Ingress Disturbance

- `MLP17` suppressive direction 的跨样本一致性 cosine `0.650`。
- 只注入 `MLP17` suppressive direction 时，`L20H5` 投影变化 `3.549`，`L21H1` `6.391`，`L21H12` `7.125`，`L24H6` `12.309`，`MLP27` `110.862`。
这些量都是沿各节点 clean->corrupt local suppressive axis 计算的。如果它们在 `MLP17` 注入后同步朝 no-tool 侧移动，就说明 suppressive writer 在直接扰动 tool ingress，而不只是末端另起炉灶。

## 4. Stagewise Suppression Accumulation

- step 1 / `L16H4`: tool-logit `-0.250`, no-tool-logit `0.375`, decision `-0.631`, no-tool-top1 `0.010`.
- step 2 / `L16H4|MLP17`: tool-logit `-1.000`, no-tool-logit `1.625`, decision `-2.434`, no-tool-top1 `0.299`.
- step 3 / `L16H4|MLP17|L23H6`: tool-logit `-1.625`, no-tool-logit `2.750`, decision `-3.953`, no-tool-top1 `0.790`.

这说明 suppressive state 不是单节点瞬时完成：`L16H4` 先读入 ordinary-answer evidence，`MLP17` 把它写成真正有 token-level 后果的 suppressive direction，`L23H6` 再把这份状态送到输出附近，最终把 clean prompt 推回 no-tool。

## 5. What Is Still Not Fully Closed

当前剩下的主要未闭环问题不是“这条链是否存在”，而是 `L16H4` 读入的 ordinary-answer evidence 是否能再细分成更窄的子对象（例如纯 function-body prior、plain-answer prior、或更细的 task-suffix bundle）。

