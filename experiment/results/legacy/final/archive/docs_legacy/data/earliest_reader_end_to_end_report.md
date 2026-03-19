# 最早 Head Reader 到最终 Writer 的 End-to-End 机制链

## 1. 更新后的 Mechanistic Chain

1. `L2H14` 仍然是 24 节点 circuit 内最早的 head-level reader。
   这点现在可以强写，不再依赖“最早候选猜测”。
   证据有三层：
   它位于 `MLP11` 之前；
   它保留直接边 `L2H14 -> MLP11`，而 `L16H8 / L17H2 / L17H8 / L20H5` 都不是最早入口；
   `MLP11` block 会削弱它的 tool-side effect：source-only rescue `0.042`，blocked `0.030`，mediated median `0.009`。

2. `L2H14` 读取的不是晚层那种已经成型的 delivery-object scaffold。
   `delivery_object_2x2_strict` 全量结果说明：
   `L2H14 lead_k` 是明显 frame-dominant，
   same-object cross-frame `0.897`，
   same-frame cross-object `1.000`，
   gap `-0.103`；
   `L2H14 z` 也仍然偏 frame-dominant，
   same-object cross-frame `0.953`，
   same-frame cross-object `0.966`，
   gap `-0.014`。
   所以它不是“最早的纯 delivery-semantics writer”。

3. 但 `L2H14` 也不是完全没有 object 信息。
   新的 direction-level full audit 说明：
   它在 `write_file - write_answer` 与 `develop_file - develop_answer` 之间已经有一个一致的 shared file-vs-answer component，
   `write_vs_develop_direction_cosine = 0.972`。
   更准确的对象语言写法现在是：
   `L2H14` 读取 instruction opening 的 opening-side bundle，
   里面带有一个弱的、跨 frame 对齐的 file-vs-answer 分量，
   但这还不是第一个稳定 writer。

4. 这一点现在可以因果区分：
   只改 `L2H14` 的 shared file-vs-answer direction，几乎不会把末端决策拉过去。
   在 `write_answer` 上注入 file component 时，
   object-score 只变 `+0.0022`，
   tool logit 中位数变化 `0.0`，
   distractor logit 中位数变化 `0.0`，
   `MLP27` 投影只变 `+1.44`。
   从 `write_file` 擦掉这条 direction 时，
   object-score 变化也几乎是 `0`，
   tool logit 仍是 `0.0`，
   `MLP27` 投影只有 `+0.14`。
   所以 `L2H14` 是 earliest reader，但不是 first stable delivery-object writer。

5. `MLP11` 现在可以强写成 first stable delivery-object writer。
   这不再只是“representation 看起来更像语义”，而是两组独立证据同时成立：
   `delivery_object_2x2_strict` 里，
   `mlp11_out` 的 same-object cross-frame `0.992`，
   same-frame cross-object `0.974`，
   gap `+0.018`，
   object-wins `1.000`；
   同时 `MLP11` whole-node patch 在 `write` frame 上已经明显有效，
   file-rescue `0.332`，
   object-decision `0.141`，
   boundary `0.604`，
   tool-top1 `0.718`。

6. 更关键的是 direction-level causal evidence：
   只改 `MLP11` 的 shared file-vs-answer direction，
   就会把同一条对象轴强力写向下游。
   在 `write_answer` 上注入 file component 时：
   object-score `+0.678`，
   tool logit `+1.375`，
   distractor logit `-1.625`。
   从 `write_file` 擦掉这条 direction 时：
   object-score `-0.189`，
   tool logit `-0.500`，
   distractor logit `+0.375`。
   在 `develop` frame 上也仍然成立，只是末端行为更弱：
   注入时 object-score `+0.126`，
   tool logit `+1.3125`，
   distractor `-1.25`。
   所以 `MLP11` 不只是“最早看起来像语义”，而是第一个可以被 direction-level intervention 因果操纵的 delivery-object writer。

7. `MLP11 -> MLP16 -> MLP19` 现在不仅是 stagewise rescue 段，也是 direction-level amplification 段。
   当只在 `MLP11` 上注入 file component 时，
   `write` frame 的下游投影变化是：
   `MLP16 +9.26`，
   `MLP19 +20.26`。
   擦除时则反向：
   `MLP16 -4.43`，
   `MLP19 -10.65`。
   `develop` frame 也同样：
   注入 `MLP16 +8.89`，
   `MLP19 +19.84`；
   擦除 `MLP16 -3.78`，
   `MLP19 -9.84`。
   这说明 `MLP11` 写出的对象轴先在 `MLP16` 被放大，再在 `MLP19` 变成可以稳定扇出的 late shared scaffold。

8. 这条 scaffold 进入晚层 tool writer 时，最清楚的 object-axis bridge 是
   `L20H5 -> L21H12 -> L24H6 -> MLP27`。
   只在 `MLP11` 上注入 file component 时，
   `write` frame 下游变化是：
   `L20H5 +1.80`，
   `L21H12 +8.26`，
   `L24H6 +27.38`，
   `MLP27 +94.68`。
   擦除则是：
   `L20H5 -0.24`，
   `L21H12 -1.84`，
   `L24H6 -4.70`，
   `MLP27 -26.74`。
   `develop` frame 也保持同向：
   `L20H5 +0.38`，
   `L21H12 +4.75`，
   `L24H6 +25.57`，
   `MLP27 +56.22`。
   所以从对象轴角度看，`L21H12` 是比 `L21H1` 更清楚的主要 late carrier；`L21H1` 仍然在既有晚层 tool route 里，但不是这条 file-vs-answer direction 最干净的单调 carrier。

9. no-tool 竞争支路的旧结论保持不变，但现在它和新链条的分工更清楚。
   `L2H14` 不是 no-tool writer；
   `MLP11 -> MLP16 -> MLP19` 把 shared scaffold 往 tool writer 侧送；
   no-tool 竞争路仍然是 `MLP16 -> MLP17 -> L23H6`，
   负责把 textual-answer / no-tool 偏向写回输出区并压 tool ingress。

10. 所以现在最强、最完整、并且可以论文级强写的 end-to-end chain 是：
    `最小 cue -> L2H14 -> MLP11 -> MLP16 -> MLP19 -> L20H5 -> L21H12 -> L24H6 -> MLP27`。
    这里 `L21H1` 仍然属于既有晚层 tool route，
    但在“shared file-vs-answer direction 的主桥接”里不是最清楚的主 carrier。

## 2. Focused Evidence Table

见 `earliest_reader_focused_evidence_table.csv`。

## 3. Claim Tier

见 `earliest_reader_claim_tiers.json`。

## 4. Still Unsolved

见 `earliest_reader_still_unsolved.csv`。

## 5. 明确结论

现在已经可以把“从最早 head-level reader 到最终 writer”的整条机制链写到论文级强度，但要注意强写的命题已经更新了：

1. 强写的不是
   “`L2H14` 是最早的纯 delivery-semantics reader”。

2. 强写的是
   `L2H14` 是最早的 head-level reader；
   它读取 opening-side bundle，其中已经带有弱的 file-vs-answer component；
   这份分量在 `L2H14` 处还太弱，单独编辑它几乎不改变末端行为；
   `MLP11` 才是 first stable delivery-object writer；
   `MLP11` 写出的 shared file-vs-answer direction 会被 `MLP16 -> MLP19` 放大，
   再进入 `L20H5 -> L21H12 -> L24H6 -> MLP27`，
   最终把 `<tool_call>` 一侧拉高，并压低 no-tool distractor。

3. 仍未完全锁死、但已经不阻塞整条链强写的问题只剩一个：
   `L2H14` 里那个弱的 shared file-vs-answer component，到底更接近词面、对象组合，还是 opening-side 的更细微抽象特征。
   这已经不是“链路不清楚”，而是“最早微特征命名还没完全压平”。
