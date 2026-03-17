# 最早 Head Reader 到最终 Writer 的 End-to-End 机制链

## 1. 更新后的 Mechanistic Chain

1. `L2H14` 是 24 节点 circuit 内最早的 head-level reader。
   它的 clean rank-1 tokens 是 `query`, `the`, `\n\n`, `assistant`, `below`, `how`；
   clean span density 在 `lead_phrase = 0.0161`，高于 `file_target = 0.0085`、`function_body_anchor = 0.0055`、`tail_suffix = 0.0069`、`task_body = 0.0016`；
   best causal span 是 `lead_phrase`，median rescue `0.0251`。
   但新的 within-opening matched counterfactual 说明：
   它更像读 instruction opening 的局部 frame / lexical scaffold，
   还不是一个已经抽象成 answer-delivery semantics 的纯语义 reader。

2. `L2H14` 不是后续 carrier。
   在优先候选 `L2H14 / L16H8 / L17H2 / L17H8 / L20H5` 里，只有 `L2H14` 同时满足：
   它位于 `MLP11` 之前；
   它保留直接边 `L2H14 -> MLP11`，`forward_support = 0.1874`、`reverse_support = 0.0447`；
   `MLP11` block 会削弱它的 tool-side effect：source-only rescue `0.042`，blocked `0.030`，mediated median `0.009`；
   这条中介分布不是噪声，`51.7%` 样本为正，`p75 = 0.082`，`p90 = 0.156`。

3. `L2H14` 对最小 cue 的读取主要发生在 lead-sensitive `K` 侧，进入 `MLP11` 的 surviving part 同时保留在 `K` 和 `Z`。
   组件级全量结果是：
   `K`: source rescue `0.066`，blocked-by-`MLP11` `0.055`，mediated `0.009`；
   `Q`: `0.004 -> 0.000 -> 0.000`；
   `V`: `0.038 -> 0.060 -> -0.018`；
   `Z`: `0.042 -> 0.030 -> 0.009`。
   最稳的写法不是“只有 `Z` 在写”，而是：
   `L2H14` 先通过 lead-sensitive key-side read 选中 instruction opening，
   再把这份差异写成 head output，送进 `MLP11`。
   within-opening matched counterfactual 进一步说明：
   `L2H14 lead_k` 和 `L2H14 z` 都是 same-frame opposite-semantic 更相近，而不是 same-semantic cross-frame 更相近。
   全量上：
   `l2h14_lead_k`: `0.924` vs `0.965`，gap `-0.042`；
   `l2h14_z`: `0.989` vs `0.993`，gap `-0.004`。
   所以 `L2H14` 这一步更像 opening-frame reader，而不是最早的抽象语义 writer。

4. `MLP11` 是最早的稳定 semantic scaffold writer。
   在 earliest-reader full chain 里，stage 1 只有 `L2H14` 时 rescue `0.042`、tool_top1 `0.000`；
   加上 `MLP11` 后，stage 2 变成 rescue `0.350`、tool_top1 `0.037`、boundary `0.036`。
   `MLP11` 的 tool-side writer evidence 也直接朝 `<tool_call>` 一侧偏：
   `<tool_call>` delta `0.750`，distractor delta `-0.875`。
   within-opening matched counterfactual 也支持这里才开始语义对齐：
   `mlp11_out` 对原始 line 的 semantic-correct rate 是
   `original_clean = 1.000`，
   `original_corrupt = 0.923`，
   centered margin 分别是 `1.120` 和 `0.615`。
   所以从对象语言上，更稳的说法是：
   `L2H14` 读 opening frame，
   `MLP11` 把这份 opening 差异第一次写成 tool-vs-no-tool answer-delivery scaffold。

5. `MLP11 -> MLP16 -> MLP19` 是最早强机制段。
   `MLP11 -> MLP16` 的边支持是 `0.2416 / 0.1766`；
   `MLP16 -> MLP19` 的边支持是 `0.3149 / 0.3415`。
   对应的 stagewise accumulation 是：
   stage 2 `0.350` -> stage 3 `0.577` -> stage 4 `0.846`。
   这说明 `MLP11` 写出的 opening scaffold 在 `MLP16` 被放大，在 `MLP19` 变成 late shared scaffold。

6. `MLP19` 把 scaffold 扇出到晚层 tool writer。
   `MLP19 -> L20H5 = 0.3061 / 0.3418`，
   `MLP19 -> L21H1 = 0.6261 / 0.3947`，
   `MLP19 -> L21H12 = 0.6529 / 0.6005`。
   从这里开始，shared scaffold 进入已经讲清楚的晚层 tool 路：
   `L20H5 -> L21H1/L21H12 -> L24H6 -> MLP27`。

7. 晚层 tool writer 仍然按既有机制工作。
   `L20H5` 读取 `file_target / function_body_anchor`，
   `L21H1` 读取 instruction boundary / code preamble，
   `L21H12` 读取 tail / protocol，
   `L24H6` 读取 `<tool_call>` start marker，
   `MLP27` 写 `<tool_call>` 方向。
   full chain `L2H14 -> MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H1 -> L21H12 -> L24H6 -> MLP27`
   在 `1722` 样本上达到：
   rescue `0.998`，tool_top1 `0.989`，boundary `1.000`。

8. no-tool 竞争路没有被重写，但它现在可以和 earliest-reader chain 对接。
   `MLP16 -> MLP17` 的边支持是 `0.4564 / 0.6140`；
   `L16H4 -> MLP17 = 0.1847 / 0.4193`；
   `MLP17 -> L23H6 = 0.0478 / 0.5528`。
   所以 shared scaffold 在 `MLP16` 处分叉：
   一侧进晚层 tool writer，
   一侧进 no-tool suppressive route。

## 2. Focused Evidence Table

见 `earliest_reader_focused_evidence_table.csv`。

## 3. Claim Tier

见 `earliest_reader_claim_tiers.json`。

## 4. Still Unsolved

见 `earliest_reader_still_unsolved.csv`。

## 5. 明确结论

现在可以强写的是：
在 24 节点 circuit 内，`L2H14` 是最早的 head-level reader；
它把 instruction opening 的局部 frame 差异送进 `MLP11`；
`MLP11` 第一次把这份差异写成 semantic scaffold；
`MLP11 -> MLP16 -> MLP19` 再把它放大并分叉到晚层 tool writer 和 no-tool suppressive route；
整条 earliest-reader-to-writer chain 在全量 `1722` 样本上已经闭环。

现在还不能强写到论文级的是：
`L2H14` 读取的 opening bundle 还没有被压缩成“单一、完全隔离、对象语言上无歧义”的最小语义特征；
更精确地说，现有 matched-opening 证据反而更支持它是 frame-sensitive reader，而不是最早的纯语义 reader。
所以，整条链的身份和传输已经达到论文级强度；
最早 reader 的精确对象语义还没有完全达到同等级强度。
