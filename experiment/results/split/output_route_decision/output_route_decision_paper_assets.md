# Output-Route Decision Paper Assets

## Figure 4: Route Score + Linear Probe

- `MLP11`: route AUC train/test `0.9661` / `0.9677`; probe AUC train/test `1.0000` / `1.0000`; probe accuracy train/test `1.0000` / `1.0000`.
- `MLP16`: route AUC train/test `0.9960` / `0.9956`; probe AUC train/test `1.0000` / `1.0000`; probe accuracy train/test `1.0000` / `1.0000`.
- `MLP19`: route AUC train/test `0.9947` / `0.9934`; probe AUC train/test `1.0000` / `1.0000`; probe accuracy train/test `1.0000` / `1.0000`.

## Figure Captions

Figure 4 caption:
Figure 4 compares the original route-score AUC with a linear probe trained on train activations and evaluated on held-out test activations at `MLP11`, `MLP16`, and `MLP19`. All three anchors retain route-score AUC above `0.96`, while the probe reaches `1.00` AUC and `1.00` accuracy on both train and test. This shows that the route state is not only visible under the signed route-score projection, but is also trivially linearly decodable from each anchor representation.

Figure 5 caption:
Figure 5 shows that clean and corrupt route-score distributions remain separated at all three anchors while the local route directions stay nearly orthogonal across layers (cos(`MLP11`,`MLP16`) = `0.040`, cos(`MLP16`,`MLP19`) = `-0.006`, cos(`MLP11`,`MLP19`) = `0.052`). Because all pairwise cosines stay below `0.10`, the route state is better described as a progressively re-encoded scalar state than as a single direction transported unchanged across layers. This geometric result matches Figure 4: the same decision state remains linearly decodable even though its local direction changes from anchor to anchor.

## Figure 5: Route-State Evolution

- 该图直接使用 train 集全量 `route_score_base_per_sample.csv` 的三个 anchor score 分布，以及三对方向余弦。
- 三对余弦分别为：`cos(MLP11, MLP16) = 0.0401`，`cos(MLP16, MLP19) = -0.0056`，`cos(MLP11, MLP19) = 0.0521`。
- 三者都低于 `0.10`，因此这里仍应写成“逐层重编码而非方向搬运”，不需要改成共享方向复用叙事。
- route score 分布（train）：`MLP11` clean `1.000 ± 0.739` / corrupt `-1.000 ± 0.801`；`MLP16` clean `1.000 ± 0.682` / corrupt `-1.000 ± 0.478`；`MLP19` clean `1.000 ± 0.783` / corrupt `-1.000 ± 0.465`。

## Causal Edge Table

| Edge | Promote route mediation | Erase route mediation | Promote target-score mediation | Erase target-score mediation | Label |
| --- | ---: | ---: | ---: | ---: | --- |
| `MLP11->MLP16` | 0.156 | 0.052 | 0.145 | 0.149 | strong |
| `MLP16->MLP19` | 0.095 | 0.059 | 0.105 | 0.129 | strong |
| `MLP16->MLP17` | 0.149 | 0.095 | 0.208 | 0.243 | strong |

### MLP19 Fanout Note

- MLP19 的下游 fanout 已有直接 mediation 数字：`MLP19->L20H5` promote/erase route mediation = 0.044/0.034，`MLP19->L21H12` promote/erase route mediation = 0.057/0.028，`MLP19->MLP27` promote/erase route mediation = 0.145/0.059，`MLP19->L23H6` promote/erase route mediation = 0.051/0.033。这些单边都存在真实传递，但整体仍弱于 group block，所以更稳的说法仍是 late fanout hub，而不是唯一瓶颈。

## Appendix C: CLT Feature Analysis

- `MLP11` tool-route features `F3363/F15709/F14654` 在 train/test 上都集中响应 `save/edit/prefill/paste` 这一类“把函数体写进文件或补全现有文件”的 opening，说明模块 1 刚整合出的 instruction state 一进入 `MLP11`，就已经被压成偏 tool-mediated route 的早期写入特征。
- `MLP11` direct-route features `F12157/F17183/F842` 在 train/test 上稳定偏向 `design/devise/develop/author/supply` 一类“直接产出内容或方案”的 opening，说明 `MLP11` 同时也是最早把 direct-answer 倾向写成稳定局部 route state 的边界节点。
- `MLP16` tool-route features `F15958/F4287/F8698` 在 train/test 上主要跟 `save` 与 `directly implement` 类 opening 对齐，比 `MLP11` 更集中更强，符合 `MLP16` 作为 decision spine 中枢、对 tool-route state 做放大和稳定化的角色。
- `MLP16` direct-route features `F17168/F9563/F3411` 在 train/test 上则稳定偏向 `properly develop/supply/design/author/carefully implement` 类 opening，说明到 `MLP16` 时，竞争性的 no-tool 倾向已经被写成更强、并可继续分叉到 `MLP17` 的 suppressive pre-state。

Appendix C English paragraph:
At the feature level, the route state is not carried by a diffuse average over many CLT units. In `MLP11`, tool-route features are strongest on openings such as `save`, `edit`, `prefill`, and `paste`, whereas direct-route features are strongest on `design`, `develop`, `author`, `devise`, and `supply`-style requests, matching the boundary interpretation that `MLP11` converts the integrated instruction into an early route commitment. In `MLP16`, tool-route features sharpen around `save` / `directly implement` requests while direct-route features cluster around `properly develop`, `design`, `author`, and `carefully implement` patterns, consistent with `MLP16` acting as the central route amplifier before the spine forks toward `MLP19` and `MLP17`. All selected features preserve their sign on held-out test examples, supporting the claim that the route state is written by a sparse and stable set of interpretable decision features rather than by an undifferentiated dense direction.

- `MLP11` selected features:
  - `F3363` (tool_route): train corr `0.665`, test corr `0.657`; train Δ `0.057`, test Δ `0.058`; dataset hint `save(2), edit(1)`.
  - `F15709` (tool_route): train corr `0.652`, test corr `0.653`; train Δ `0.090`, test Δ `0.091`; dataset hint `prefill(1), edit(1), paste(1)`.
  - `F14654` (tool_route): train corr `0.644`, test corr `0.645`; train Δ `0.033`, test Δ `0.033`; dataset hint `edit(1), save(2)`.
  - `F12157` (direct_route): train corr `-0.890`, test corr `-0.878`; train Δ `-0.172`, test Δ `-0.173`; dataset hint `design(1), devise(1), supply(1)`.
  - `F17183` (direct_route): train corr `-0.840`, test corr `-0.838`; train Δ `-0.107`, test Δ `-0.105`; dataset hint `devise(2), develop(1)`.
  - `F842` (direct_route): train corr `-0.834`, test corr `-0.837`; train Δ `-0.159`, test Δ `-0.159`; dataset hint `manually develop(1), author(2)`.
- `MLP16` selected features:
  - `F15958` (tool_route): train corr `0.779`, test corr `0.780`; train Δ `0.308`, test Δ `0.310`; dataset hint `save(3)`.
  - `F4287` (tool_route): train corr `0.776`, test corr `0.782`; train Δ `0.367`, test Δ `0.360`; dataset hint `save(3)`.
  - `F8698` (tool_route): train corr `0.747`, test corr `0.735`; train Δ `0.176`, test Δ `0.176`; dataset hint `save(2), directly implement(1)`.
  - `F17168` (direct_route): train corr `-0.872`, test corr `-0.869`; train Δ `-0.524`, test Δ `-0.525`; dataset hint `properly develop(1), supply(1), design(1)`.
  - `F9563` (direct_route): train corr `-0.774`, test corr `-0.781`; train Δ `-0.325`, test Δ `-0.330`; dataset hint `properly develop(2), author(1)`.
  - `F3411` (direct_route): train corr `-0.761`, test corr `-0.740`; train Δ `-0.384`, test Δ `-0.389`; dataset hint `manually develop(1), design(1), carefully implement(1)`.

## Self-Check

- 用本次重新抽取的 MLP 激活复算 route score 后，与正式 train/test 汇总的最大 AUC 偏差为 `0.000721`。
- probe logit 与 held-out test 上的 local route score / module route score 仍强相关：`MLP11` `0.890` / `0.922`，`MLP16` `0.941` / `0.916`，`MLP19` `0.933` / `0.893`。
- leave-one-clean-candidate-out robustness (`MLP11`): all held-out candidate AUCs stay at least `1.000`; 最差 accuracy 出现在 `properly add`，为 `0.712`。
- leave-one-clean-candidate-out robustness (`MLP16`): all held-out candidate AUCs stay at least `1.000`; 最差 accuracy 出现在 `properly add`，为 `0.833`。
- leave-one-clean-candidate-out robustness (`MLP19`): all held-out candidate AUCs stay at least `1.000`; 最差 accuracy 出现在 `create`，为 `0.984`。

