# Instruction Integration 模块 1正式结果

## 核心结论

这轮补口后的最稳说法需要收缩为：`L2H14 + L11H5` 构成一个互补的两段式 ingress group，而不是两个对称的全能整合头。`L11H5` 是最清楚的 same-block handoff head，稳定依赖 `tool schema / lead phrase / function body / filename / request suffix`；`L2H14` 更像早层 ingress，稳定依赖 `lead phrase / filename / request suffix`，并带有较弱但一致的 `function body / task body` 依赖。`MLP11` 仍应写作模块 1 的出口、模块 2 的入口。

## Figure 3：Attention Span Heatmap

- 图文件：`/root/autodl-tmp/project/experiment/results/split/instruction_integration/figures/figure3_instruction_integration_attention_span_heatmap.png`
- `L2H14` 最高的跨 span 读入对：`Request Suffix <- Filename` 0.0817; `Request Suffix <- Function Body` 0.0343; `Task Description <- Filename` 0.0307。
- `L11H5` 最高的跨 span 读入对：`Request Suffix <- Filename` 0.0921; `Filename <- Function Body` 0.0324; `Function Body <- Lead Phrase` 0.0324。
- 图上可以看到，两头都不是只盯着 `user lead phrase`；`L2H14` 更早地把 lead/body/file 拉到同一局部上下文，`L11H5` 则更像在 `MLP11` 前完成 same-block handoff。

### Figure 3 Caption

Figure 3. Span-level attention density for the two ingress heads identified in Module 1. `L2H14` behaves like an earlier ingress head, concentrating cross-span reads that pull the lead phrase and filename/suffix context into a shared early state, whereas `L11H5` shows a later same-block handoff profile that routes function-body, filename, and lead-phrase information toward `MLP11`. The causal test zeroes attention weights at these heads rather than replacing tokens, so the figure is descriptive support and the span-masking table carries the main causal claim.

## Attention Span Masking

### Paper-Ready Markdown Table

| masked span | L2H14 (train / test) | L11H5 (train / test) |
| --- | --- | --- |
| `system_preamble` | `-0.111 / -0.116` | `-0.017 / -0.013` |
| `tool_schema` | `-0.163 / -0.160` | `0.057 / 0.057` |
| `user_lead_phrase` | `0.042 / 0.040` | `0.049 / 0.057` |
| `function_body_anchor` | `0.014 / 0.008` | `0.045 / 0.055` |
| `file_target` | `0.013 / 0.014` | `0.052 / 0.057` |
| `instruction_suffix` | `0.046 / 0.039` | `0.045 / 0.037` |
| `task_body` | `0.019 / 0.021` | `-0.059 / -0.058` |

- `L11H5` 最稳的正向因果依赖是：`tool_schema` `0.057/0.057`、`user_lead_phrase` `0.049/0.057`、`function_body_anchor` `0.045/0.055`、`file_target` `0.052/0.057`、`instruction_suffix` `0.045/0.037`。
- `L2H14` 最稳的正向因果依赖是：`user_lead_phrase` `0.042/0.040`、`file_target` `0.013/0.014`、`instruction_suffix` `0.046/0.039`，以及较弱但同号的 `function_body_anchor` `0.014/0.008`、`task_body` `0.019/0.021`。
- 需要明确弱写：`L2H14` 对 `system_preamble / tool_schema` 是反号，`L11H5` 对 `task_body` 是反号。这说明模块 1 的因果结构更像互补分工，而不是“每个头都平均整合所有 span”。

## Optional Probe Check

- 在 `MLP11` 最后位置上训练的线性 probe，held-out test baseline accuracy 为 `1.0000`，`L11H5 + tool_schema mask` 后仍为 `1.0000`，accuracy drop = `0.0000`。
- 这说明 probe 这个二元指标已经饱和：mask 后表示虽然发生了连续位移，但还没有跨过线性分类边界。因此这里不把 probe 当作主证据，模块 1 的主因果指标仍然是 `MLP11 route score drop`。

## 入口链已有证据

- `L11H5 -> MLP11` same-block handoff：`MLP11 local rescue = 0.196`。
- `L2H14 + L11H5` 最小 ingress group：`route rescue = 0.060`。
- held-out test 泛化：`MLP11 route AUC = 0.9677`，`module_anchor_mean AUC = 0.9943`。

## 可直接进主文的英文段落

Before the route-decision spine stabilizes, a complementary two-head ingress group feeds `MLP11`: `L11H5` shows stable positive dependence on the tool schema, lead phrase, function-body anchor, filename, and request suffix, whereas `L2H14` contributes a narrower early-ingress signal centered on the lead phrase, filename, and request suffix, with weaker but same-sign function-body/task-body dependence. Figure 3 supports this split descriptively, with `L2H14` behaving like an earlier cross-span ingress head and `L11H5` behaving like the main same-block handoff head into `MLP11`. The joint `L2H14 + L11H5` route rescue is only 0.060, but this is a head-level local causal contribution rather than a full module flip, so it is consistent with a distributed ingress stage whose strongest discrete head pair only partially recovers the downstream decision state. `MLP11` is therefore best treated as the output boundary of Instruction Integration and the input boundary of Output-Route Decision, and this boundary generalizes cleanly to held-out data (`R_module` AUC on test = 0.9943).
