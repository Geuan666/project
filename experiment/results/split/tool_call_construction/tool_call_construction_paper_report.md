# Tool-Call Construction Paper Assets

## 范围

- 本报告只使用 split 口径正式结果：train `1223` 对样本用于发现与成图，test `499` 对样本用于泛化验证。
- 模块 3 不再引用旧的 `1722` full-run 叙事作为论文主口径；旧 refine 报告保留为历史审计。
- 新增的 logit-lens 轨迹是基于 train 集全量样本重新导出的 residual-stage 统计，不是 smoke。

## 核心结论

- Figure 6 的主线是单调递进的 construction 轨迹：train `<tool_call>` top-1 从 `0.0% -> 4.3% -> 14.6% -> 48.9% -> 85.9% -> 92.8% -> 97.9%`，test 对应终点为 `97.2%`。
- `+L21H1` 在 train 只能到 `48.9%`，因此不能再写成“几乎已经全部成形”；真正让 `<tool_call>` 在多数样本中稳定成为 top-1 的是 `+L21H12`。
- `L21H12` 分支明显强于 `L21H1` 分支：`L21H12_only` top-1 `67.3%` 对比 `L21H1_only` 的 `48.9%`；加上 `L24H6` 后分别为 `83.9%` 和 `73.2%`。
- writer 证据仍然集中在 `L24H6` 和 `MLP27`：`L24H6` clean margin `2.255`、delta margin `0.257`；`MLP27` clean margin `10.844`、delta margin `1.609`。

## MLP19 入口定位

- `MLP19` 在 stagewise 中只把 `<tool_call>` top-1 从 `0.0%` 推到 `4.3%`，但这不表示它无关紧要；更准确的写法是，它提供的是来自模块 2 的 route-state relay / late fanout 输入，而不是自己独立启动 construction。
- logit lens 也支持这个定位：在 `21_mid` 之前，clean-corrupt separation 的平均绝对差值只有 `0.032`，最大也只到 `0.125`（`16_pre`），真正的明显拉升从 `21_mid` 才开始。
- 可直接进主文的英文句：`MLP19 contributes only a small initial bias (4.3%), consistent with its role as the upstream route-state relay rather than a construction initiator; the logit lens shows that clean-corrupt separation remains weak until layer 21, when dedicated construction heads begin to engage.`

## 图表产物

- Figure 6: `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/figures/figure6_construction_stagewise_train_test.png`
- Logit lens: `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/figures/construction_logit_lens_train.png`
- Branch comparison: `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/figures/l21_branch_comparison_paper.png`
- Attention roles: `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/figures/construction_attention_roles.png`
- Train residual-stage lens summary CSV: `/root/autodl-tmp/project/experiment/results/split/tool_call_construction/construction_logit_lens_train_summary.csv`

## 实验 A：`<tool_call>` Logit Lens

- clean-corrupt 差值从 `21_mid` 开始进入明显拉升（delta `0.844`），到 `23_mid` 超过 `1.0`，并在 `24_mid` 首次把 clean median `<tool_call>` logit 拉到正值。
- 这与 stagewise 中 `+L20H5 -> +L21H1` 的大跳变方向一致：`<tool_call>` top-1 从 `14.6%` 跳到 `48.9%`，增加 `34.3` 个百分点。两者量纲不同，前者是 residual-stream median logit，后者是样本级 top-1 flip rate，但都把真正的 construction 启动点放在 21 层附近。
- 新图按 residual stage 画完整 train 轨迹：整数位置表示 block 输入，`.5` 表示 attention 后、MLP 前，`28` 表示最终输出。这样可以把 `L20H5 / L21H1 / L21H12 / L24H6` 的 head 位置标在 mid-stage，而把 `MLP27` 标在最终输出附近。
- 最晚层 clean median `<tool_call>` direct logit 为 `22.625`，corrupt 为 `18.875`，差值 `3.750`。

## 实验 B：Figure 6 Stagewise Construction Trajectory

- train: `corrupt -> +MLP19 -> +L20H5 -> +L21H1 -> +L21H12 -> +L24H6 -> +MLP27 = 0.0% -> 4.3% -> 14.6% -> 48.9% -> 85.9% -> 92.8% -> 97.9%`。
- test: `0.0% -> 4.8% -> 16.0% -> 53.7% -> 86.2% -> 91.2% -> 97.2%`，说明整条链在 held-out 样本上基本保持。
- test 终点句可直接写成：`On held-out test set (499 samples), +MLP27 achieves 97.2% <tool_call> top-1 (train: 97.9%).`

## 实验 C：`L21H1` vs `L21H12` 分支比较

- `L21H12_only` 的 logit margin 为 `0.625`，高于 `L21H1_only` 的 `0.000`。
- `both_L21` 在 `+L21` 阶段达到 `85.9%` / margin `1.500`，说明两头不是简单替代关系，但更强的单分支仍是 `L21H12`。

## 实验 D：Attention Role Summary

- `L20H5`：clean decision density top span 是 `file_target` (`0.042`)，说明它最稳定地盯住 filename 对象；同时它的 decision mass L1 shift 为 `0.408`。
- `L21H12`：clean mass 与 density 的 top span 都是 `tool_call_example` / `tool_call_example`，对应 `tool_call_example` 主导的 protocol 读入；它的 decision mass L1 shift 为 `0.542`。
- `L24H6`：clean mass 与 density 的 top span 都是 `tool_instruction` / `tool_instruction`，直接指向 `tool_instruction`；它的 decision mass L1 shift 为 `0.602`。
- 这三者正好对应 payload binding、protocol routing、format commitment 三种功能分工，因此 attention 辅助图可以作为模块 3 的分工证据，而不必再扩搜新的 late head。

## Figure Captions

- Figure 6: `Stagewise restoration of the construction chain on the train and test splits. Restoring MLP19, L20H5, L21H1, L21H12, L24H6, and MLP27 raises <tool_call> top-1 from 0.0% to 97.9% on train and to 97.2% on held-out test. Solid lines denote train and dashed lines denote test, showing progressive construction rather than single-node control.`
- Logit lens: `The residual-stage logit lens remains weakly separated through layer 20, then clean-corrupt divergence rises from 21_mid onward and the clean median first turns positive at 24_mid. These turning points align with the late construction heads identified by the stagewise intervention chain.`
- Branch comparison: `On top of MLP19+L20H5, the L21H12 branch reaches 67.3% <tool_call> top-1, substantially above the 48.9% reached by the L21H1 branch. The gap remains after adding L24H6, arguing for differentiated late-routing roles rather than simple redundancy.`
- Attention roles: `L20H5, L21H12, and L24H6 preferentially read file_target, tool_call_example, and tool_instruction, respectively. Together they support a three-stage division of labor: payload binding, protocol routing, and format commitment.`

## 主文英文段落

MLP19 sits at the entrance to the construction module, but its stagewise effect is intentionally small: restoring MLP19 alone raises `<tool_call>` top-1 only to `4.3%`. This is consistent with MLP19 acting as the late fanout relay from the route-decision module rather than the node that initiates construction by itself. The logit lens supports the same reading, because clean-corrupt separation remains weak through layer 20 and begins to rise only from `21_mid`, when dedicated construction heads start to engage.

Figure 6 shows that Tool-Call Construction is progressive. Starting from the corrupt baseline, cumulative restoration of `MLP19`, `L20H5`, `L21H1`, `L21H12`, `L24H6`, and `MLP27` moves `<tool_call>` top-1 from `0.0%` to `4.3%`, `14.6%`, `48.9%`, `85.9%`, `92.8%`, and `97.9%` on the train split. The same chain reaches `97.2%` at `+MLP27` on the held-out test split, with train shown as solid lines and test as dashed lines. These numbers support gradual assembly rather than single-node instantaneous control.

The two layer-21 heads are not redundant. On top of `MLP19+L20H5`, `L21H12_only` reaches `67.3%` `<tool_call>` top-1, whereas `L21H1_only` reaches only `48.9%`; after adding `L24H6`, the corresponding branch endpoints are `83.9%` and `73.2%`. The same ordering also appears in margin, boundary-flip rate, and rescue ratio, which makes the branch asymmetry robust rather than metric-specific. This matches the logit-lens turning point at layer 21, even though the lens and stagewise metrics live on different scales.

Attention patterns further separate the roles of the late construction nodes. `L20H5` preferentially reads `file_target`, `L21H12` reads `tool_call_example`, and `L24H6` reads `tool_instruction`, supporting a division of labor from payload binding to protocol routing to format commitment. Downstream, `L24H6` already produces a strong positive clean margin (`2.255`), but `MLP27` is the main writer, with clean margin `10.844` and the strongest final-stage writeout. Together, these results support a construction pathway that binds payload, routes protocol, commits format, and finally writes `<tool_call>` into the first output token.

## 结果稳健性自检

- 单调性：`tool_top1_rate`、`margin_logit_median`、`route_margin_median` 在 train/test 两侧都严格单调上升，说明主线不是由单个异常 step 撑起来的。
- 泛化 gap：最终 `+MLP27` 的 test-train gap 只有 `0.7` 个百分点；全链最大 step gap 出现在 `plus_L21H1`，也只有 `4.8` 个百分点。
- 21 层拐点：`21_mid` 的 delta 已到 `0.844`，而 20 层及以前的平均绝对差值只有 `0.032`，说明“21 层附近启动 construction”是稳定信号，不是偶然摆动。
- 分支稳健性：`L21H12` 相比 `L21H1` 在 top1、margin、boundary flip、rescue ratio 上都更强，单分支优势分别是 `18.4pp`、`0.625`、`20.6pp`、`0.052`。
- 结论：当前结果已经足够写入论文并支撑“渐进式 construction”主 claim；但表述必须继续收紧为“MLP19 是上游 relay、L20H5 的 object evidence 主要来自 density 而非总 mass、L21H12 强于 L21H1 但二者并非完全替代”。

