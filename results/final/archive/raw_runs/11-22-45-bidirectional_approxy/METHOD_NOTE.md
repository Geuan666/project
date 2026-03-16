# 双向电路方法补充说明

这份说明聚焦两个问题：

1. 我们如何把“真实性”定义成一组可计算指标。
2. 我们如何进一步拆开 `shared backbone` 与 `directional branch`。

## 1) 真实性指标

在同一个样本上，设：

- `m_base`：base 端点上的 tool-call margin
- `m_source`：source 端点上的 tool-call margin
- `m_patch`：patch 之后的 tool-call margin

定义端点真实性：

`A = clip(1 - |m_patch - m_source| / |m_source - m_base|, 0, 1)`

解释：

- `A = 1`：patch 后完全重建 source 端点
- `A = 0`：patch 后还停留在 base 端点
- `0 < A < 1`：部分恢复 source 端点

配套再看三类行为指标：

- `sign consistency`：是否沿假设方向移动 margin
- `boundary flip rate`：是否跨过 `m = 0` 的决策边界
- `source dominance rate`：patch 后是否离 source 端点比离 base 端点更近

全量产物：

- `authenticity_full/per_group_authenticity.csv`
- `authenticity_full/group_duality.csv`
- `authenticity_full/authenticity_summary.json`

当前全量结论：

- `shared_backbone` 与 `shared_core` 的真实性最高，端点真实性中位数约 `0.94-0.96`，boundary flip rate 约 `0.996-0.999`
- `forward_selective` 仍然很强，promote 端点真实性中位数 `0.820`
- `reverse_selective` 明显较弱，但依然稳定，suppress 端点真实性中位数 `0.553`

## 2) 双向性指标

对同时有 promote / suppress 结果的 group，定义：

`duality balance = min(R_promote, R_suppress) / max(R_promote, R_suppress)`

其中 `R` 是 signed recovery 的中位数。

解释：

- 接近 `1`：两侧都强，属于真正的双向骨架
- 显著低于 `1`：更像单侧支路或偏置调制器

当前结果：

- `shared_backbone = 0.997`
- `shared_core = 0.993`
- `forward_selective = 0.755`
- `reverse_selective = 0.745`
- `forward_only_core = 0.338`
- `reverse_only_core = 0.549`

这支持一个更细的结构图景：

- 共享骨架是真正的双向可翻转子系统
- 方向性组更像“偏置 / 路由器”，而不是完整替代共享骨架

## 3) selective 质量分解

把 selective group 拆成：

- `overlap = selective ∩ shared_backbone`
- `unique = selective - shared_backbone`

并按对应方向的 support 质量求和。

全量产物：

- `mass_split_full/selective_mass_split.csv`
- `mass_split_full/selective_mass_split.json`

当前结果：

- `forward_selective`：
  - overlap mass fraction = `0.696`
  - unique mass fraction = `0.304`
  - overlap nodes = `L21H1, L21H12, MLP11`
- `reverse_selective`：
  - overlap mass fraction = `0.886`
  - unique mass fraction = `0.114`
  - overlap nodes = `L16H4, L16H8, L20H5, MLP12, MLP16, MLP17`
  - unique nodes = `L16H9, L17H2`

这说明 reverse-selective 的大部分质量并不在“孤立的抑制支路”里，而是写在 shared-backbone 重叠部分。

## 4) token-level 行为验证

margin 只是一个代理。为了更直接地看行为，我们新增了 token-level probe：

- promote：patch 后首 token 是否真的变成 `<tool_call>`
- suppress：patch 后首 token 是否真的变成 no-tool target

脚本：

- `scripts/evaluate_toolcall_bidirectional_token_flip.py`

5 样本 smoke test 的结果已经显示：

- `shared_backbone`：`promote_tool_top1_rate = 1.0`，`suppress_no_tool_top1_rate = 1.0`
- `shared_backbone_exclusive`：同样是 `1.0 / 1.0`
- `forward_selective_unique`：只有 `0.4 / 0.0`
- `reverse_selective_unique`：只有 `0.0 / 0.0`

这暗示一个很强的 story：

- 真正能把行为完整翻过去的核心不在“纯独有小支路”
- 更可能在 shared backbone 或 selective 与 backbone 的重叠部分
- 独有支路更像微调器，而不是独立完成决策翻转的主干

全量 token-level run 正在进行中：

- 输出目录：`token_flip_full`
- 日志：`token_flip_full.log`
