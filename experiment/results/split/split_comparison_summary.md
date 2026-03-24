# Split Comparison Summary

## 数据切分

- `seed=42`，按 `lang × clean_candidate` 分层；总计 `1722`，train `1223`，test `499`。
- 由于每个分层组都对 test 侧向下取整，最终 test 为 499 条，不会超过 30%。

## Route Score 对比

| 指标 | 全量 (1722) | Train (1223) | Test (499) |
| --- | --- | --- | --- |
| MLP11 route AUC | 0.9669 | 0.9661 | 0.9677 |
| MLP16 route AUC | 0.9960 | 0.9960 | 0.9956 |
| MLP19 route AUC | 0.9944 | 0.9947 | 0.9934 |
| R_module AUC | 0.9947 | 0.9946 | 0.9943 |
| MLP11 Spearman | 0.7703 | 0.7728 | 0.7621 |
| MLP16 Spearman | 0.8519 | 0.8549 | 0.8428 |
| MLP19 Spearman | 0.8624 | 0.8646 | 0.8557 |
| R_module Spearman | 0.8494 | 0.8523 | 0.8411 |

## Edge Mediation 对比

| 边 | 全量 promote | Train promote | 全量 erase | Train erase |
| --- | --- | --- | --- | --- |
| MLP11->MLP16 | 0.1543 | 0.1555 | 0.0530 | 0.0516 |
| MLP16->MLP19 | 0.0946 | 0.0946 | 0.0589 | 0.0588 |
| MLP16->MLP17 | 0.1482 | 0.1491 | 0.0936 | 0.0949 |

## Construction Stagewise 对比

| 阶段 | 全量 top1 | Train top1 | Test top1 |
| --- | --- | --- | --- |
| corrupt_full | 0.0000 | 0.0000 | 0.0000 |
| +MLP19 | 0.0447 | 0.0433 | 0.0481 |
| +L20H5 | 0.1504 | 0.1464 | 0.1603 |
| +L21H1 | 0.5029 | 0.4890 | 0.5371 |
| +L21H12 | 0.8595 | 0.8585 | 0.8617 |
| +L24H6 | 0.9233 | 0.9280 | 0.9118 |
| +MLP27 | 0.9768 | 0.9787 | 0.9719 |

## Suppression Stagewise 对比

| 阶段 | 全量 no-tool top1 | Train no-tool top1 | Test no-tool top1 |
| --- | --- | --- | --- |
| L16H4 | 0.0116 | 0.0098 | 0.0140 |
| +MLP17 | 0.2892 | 0.2993 | 0.2705 |
| +L23H6 | 0.7828 | 0.7899 | 0.7816 |

## Signed Circuit 对比

| 指标 | 全量 | Train |
| --- | --- | --- |
| 节点数 | 24 | 24 |
| 边数 | 64 | 64 |
| 充分性 | 0.9997 / 0.9980 | 0.9997 / 0.9980 |
| 必要性 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |

## 简短结论

- Route module 的 AUC：train `0.9946`，test `0.9943`，一致（差值 0.0003）。
- Construction 最终 `+MLP27` 的 `<tool_call>` top1：train `0.9787`，test `0.9719`，一致（差值 0.0068）。
- Suppression 最终 `+L23H6` 的 no-tool top1：train `0.7899`，test `0.7816`，一致（差值 0.0083）。
- Signed circuit 在 train 上仍保持 `24` 个节点、`64` 条边，充分性与全量结果基本重合。

注：Signed Circuit 表中的“充分性”为 `promote / suppress` 两个 sufficiency median；“必要性”为 `promote / suppress` 两个 necessity median drop。
