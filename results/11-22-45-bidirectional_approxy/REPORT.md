# 双向电路发现（全量 1189 样本报告）

本文档总结基于同一批 `1189` 对样本做出的双向电路发现结果。核心目标不是只找“促进 `<tool_call>` 的电路”，而是把任务拆成一个真实的双稳态决策：

- `tool-call` 端点：首 token 倾向 `<tool_call>`
- `no-tool` 端点：首 token 倾向自然语言回答起始

然后在两个方向上分别做电路发现、跨样本聚合、集合分解和跨方向因果验证。

## 运行设置

- 正向基线（促进 tool-call）：`results/11-21-37`
- 双向全量结果：`results/11-22-45-bidirectional_approxy`
- 模型：`/root/autodl-tmp/Qwen/Qwen3-1.7B`
- 数据：`datasets/clean`（tool-call prompt） vs `datasets/corrupt`（no-tool prompt）
- 反向 batch：`results/11-22-45-bidirectional_approxy/reverse_batch`
- 反向聚合：`results/11-22-45-bidirectional_approxy/reverse_aggregate_full/global_core_summary.json`
- 双向摘要：`results/11-22-45-bidirectional_approxy/bidirectional_full/bidirectional_summary.json`

## 1) 反向方向是稳定且定义良好的

反向目标 token 分布：

- `I`：`1174 / 1189`
- `The`：`9 / 1189`
- `To`：`6 / 1189`

这说明在这组样本上，模型的 no-tool 端点高度集中，并不是“很多离散 token 的混杂平均”。因此，把任务理解为：

- `<tool_call>` 模式
- `I` 主导的自然语言回答起始模式

是一个由数据和模型共同给出的真实决策边界，而不是人为简化。

## 2) 全量集合结构：共享骨架 + 方向性支路

正向 core：

- `MLP11, MLP16, MLP17, L17H8, MLP19, L21H1, L21H12, L23H6, L24H6, MLP27`

反向 core：

- `MLP16, L16H4, L16H8, MLP17, L17H8, MLP19, L21H12, L23H6, L24H6, MLP27`

对比结果：

- Core 节点 Jaccard：`0.6667`
- Core 边 Jaccard：`0.3235`
- 共享 core 节点：`L17H8, L21H12, L23H6, L24H6, MLP16, MLP17, MLP19, MLP27`
- 仅正向 core：`L21H1, MLP11`
- 仅反向 core：`L16H4, L16H8`

支持度分解后的三类关键集合：

- Shared backbone：
  `MLP11, MLP12, L12H6, L13H9, MLP16, L16H4, L16H8, MLP17, L17H8, MLP19, L20H5, L21H1, L21H12, L23H6, L24H6, MLP27`
- Forward-selective：
  `L2H14, MLP11, MLP18, L19H6, MLP21, L21H1, L21H12, L23H5`
- Reverse-selective：
  `MLP12, MLP16, L16H4, L16H8, L16H9, MLP17, L17H2, L20H5`

样本级 overlap 也稳定：

- 平均 node Jaccard：`0.5113`
- 中位数 node Jaccard：`0.5238`
- 平均共享节点数：`10.72`

这组结果支持一个清晰结构：模型不是靠两套完全独立的电路做选择，而是共享一条较大的决策骨架，再叠加正反两个方向性的支路。

## 3) 跨方向因果验证：确实同时存在促进与抑制

我们统一使用同一个 margin：

- `m_tool = logit(<tool_call>) - logit(distractor)`

其中 distractor 在这批样本里绝大多数是 `I`。单样本 gap 定义为：

- `gap = m_tool(tool_call_prompt) - m_tool(no_tool_prompt)`

然后做两个对称 patch：

- promote：把 tool-call 端点的激活 patch 到 no-tool base
- suppress：把 no-tool 端点的激活 patch 到 tool-call base

### 3.1 对角线验证（aligned）

见：

- `results/11-22-45-bidirectional_approxy/causal_eval_full_aligned/cross_eval_summary.json`

中位数结果：

- `promote__forward_only_core__ratio = 0.4706`
- `promote__forward_selective__ratio = 0.8201`
- `promote__shared_backbone__ratio = 0.9672`
- `promote__shared_core__ratio = 0.9538`
- `suppress__reverse_only_core__ratio = -0.1698`
- `suppress__reverse_selective__ratio = -0.5532`
- `suppress__shared_backbone__ratio = -0.9701`
- `suppress__shared_core__ratio = -0.9470`

解释：

- 正向选择性子图确实强力推动 `<tool_call>`。
- 反向选择性子图确实显著压制 `<tool_call>`。
- 共享骨架在两个方向都接近饱和，说明它不是“某一侧的专属支路”，而是共同承载决策的主干。

### 3.2 完整 2x2 矩阵验证（off-diagonal）

见：

- `results/11-22-45-bidirectional_approxy/causal_eval_full_matrix/cross_eval_summary.json`

新增的 off-diagonal 中位数结果：

- `promote__reverse_only_core__ratio = 0.3091`
- `promote__reverse_selective__ratio = 0.7429`
- `suppress__forward_only_core__ratio = -0.1591`
- `suppress__forward_selective__ratio = -0.6190`

这组数字的含义更强：

- 反向选择性节点不仅能把系统往 no-tool 方向推，也对维持 no-tool 状态具有“必要性”；把它们替换成 tool-call 端点的激活，会显著把 margin 拉回 tool-call。
- 正向选择性节点同样具有对称性质；把它们替换成 no-tool 端点的激活，会显著把系统拉向 no-tool。

因此，这里得到的不是“只有促进电路”，而是一个带方向性的竞争系统：

- 共享 backbone 决定大部分可翻转性
- forward-selective 更偏促进 `<tool_call>`
- reverse-selective 更偏抑制 `<tool_call>` / 维持 no-tool

## 4) 反向电路很早就稳定，不依赖全量才能出现

见：

- `results/11-22-45-bidirectional_approxy/reverse_stability_full.json`
- `results/11-22-45-bidirectional_approxy/reverse_stability_full.csv`

关键 checkpoint：

- `25` 个反向样本：node Jaccard vs forward = `0.8182`
- `50` 个反向样本：已经出现 `L16H4/L16H8`，node Jaccard vs forward = `0.75`
- `100/200/400/800` 个反向样本：core 节点集合不再变化（vs prev = `1.0`）
- `1189` 个样本：`L21H1` 退出 reverse core，最终 node Jaccard vs forward = `0.6667`

这说明 reverse-only 结构不是偶然噪声，而是在很早阶段就稳定浮现；全量的主要作用是把边界再收紧，而不是凭空制造结果。

## 5) 机制解释：no-tool 条件下，读取焦点会从工具格式迁移到用户内容

见：

- `results/11-22-45-bidirectional_approxy/head_reads_full/per_group_read_mass.csv`
- `results/11-22-45-bidirectional_approxy/head_reads_full/per_head_read_mass.csv`

按 group 聚合，`delta = no_tool - tool` 的大幅变化包括：

- `forward_only_core_heads / prefix_16 = +0.1604`
- `shared_core_heads / prefix_16 = +0.1266`
- `shared_core_heads / tools_block = +0.0562`
- `reverse_selective_heads / user_block = +0.0533`
- `reverse_only_core_heads / user_block = +0.0530`
- `reverse_only_core_heads / tools_block = -0.0295`
- `reverse_selective_heads / tools_block = -0.0205`

按单 head 看，最有解释力的几个例子：

- `L16H4`：`user_block +0.0613`
- `L16H8`：`user_block +0.0478`，`tools_block -0.0464`
- `L23H5`：`tool_call_tags -0.1611`，`user_block +0.0888`，`prefix_16 +0.0653`
- `L17H8`：`user_block +0.0511`，`tools_block -0.0393`
- `L24H6`：`tool_call_tags -0.3188`，`prefix_16 +0.2245`

可以把这理解成一个可解释的读写迁移：

- tool-call 模式更依赖工具 schema / tag / 格式线索
- no-tool 模式更依赖 user block 和自然语言前缀区域

这给 reverse-selective / reverse-only 节点提供了机制上的可解释支撑，而不只是数值上“能 patch 出负效应”。

## 6) 跨数据集与语言稳健

见：

- `results/11-22-45-bidirectional_approxy/stratified_full/stratified_causal_metrics.csv`

按 dataset + language 分层的中位数结果：

- `apps / python / 102`
  - `promote__forward_selective = 0.6991`
  - `suppress__reverse_selective = -0.5357`
  - `promote__shared_backbone = 1.0000`
  - `suppress__shared_backbone = -1.0118`
- `codecontests / cpp / 402`
  - `promote__forward_selective = 0.7934`
  - `suppress__reverse_selective = -0.5818`
  - `promote__shared_backbone = 0.9685`
  - `suppress__shared_backbone = -0.9815`
- `codecontests / java / 584`
  - `promote__forward_selective = 0.8508`
  - `suppress__reverse_selective = -0.5304`
  - `promote__shared_backbone = 0.9607`
  - `suppress__shared_backbone = -0.9328`
- `humaneval / python / 40`
  - `promote__forward_selective = 0.7027`
  - `suppress__reverse_selective = -0.5729`
  - `promote__shared_backbone = 1.0000`
  - `suppress__shared_backbone = -1.0169`
- `mbpp / python / 61`
  - `promote__forward_selective = 0.7000`
  - `suppress__reverse_selective = -0.5600`
  - `promote__shared_backbone = 1.0000`
  - `suppress__shared_backbone = -1.0167`

因此，这条 story 不依赖某一个数据源或语言；它在 `apps / codecontests / humaneval / mbpp` 上都成立。

## 7) 方法论总结

这套方法可以概括成一个可复用配方：

1. 为同一任务定义两个对称端点，而不是只盯住“正确行为”。
2. 在同一个 margin 上分别跑两个方向的电路发现。
3. 做跨样本聚合，得到两个共识电路。
4. 不只看并集/交集，而是做三类结构分解：
   - shared backbone
   - forward-selective
   - reverse-selective
5. 用同一个 margin 做跨方向 patch，验证“促进”和“抑制”是否同时存在。
6. 再用 head read 的位置集合迁移，给方向性支路提供机制解释。

如果把这套方法抽象出去，它适用于任何“模型在两个可识别端点之间做决策”的任务，而不只是 tool-call。

## 8) 复现入口

全量端到端入口：

```bash
bash scripts/run_toolcall_bidirectional_full.sh
```

关键输出目录：

- `results/11-22-45-bidirectional_approxy/reverse_aggregate_full`
- `results/11-22-45-bidirectional_approxy/bidirectional_full`
- `results/11-22-45-bidirectional_approxy/causal_eval_full_aligned`
- `results/11-22-45-bidirectional_approxy/causal_eval_full_matrix`
- `results/11-22-45-bidirectional_approxy/head_reads_full`
- `results/11-22-45-bidirectional_approxy/stratified_full`
- `results/11-22-45-bidirectional_approxy/reverse_stability_full.json`

## 9) 当前最强结论

在这 `1189` 对样本上，模型的 tool-call 决策不是一条单向“促进 `<tool_call>`”的电路，而是：

- 一条双向共享的 backbone
- 一组更偏正向的促进支路
- 一组更偏反向的抑制支路

并且这三部分都能被全量数据、跨方向因果 patch、稳定性分析、head read 迁移和跨数据集分层同时支持。
