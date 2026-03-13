# TODO: `/root/autodl-tmp/project`

## 1. 总目标

当前主线目标不变，但需要重新收束成更清晰、也更符合导师讨论结果的版本：

- 找到一个 **faithful circuit**，解释模型在首个生成位置上是输出 `<tool_call>` 还是进入 no-tool 模式。
- 给这个 circuit 做 **功能优先的语义分组**，而不是把 `backbone / bias / tail` 当作最终解释语言。
- 用明确的 **circuit 指标** 证明电路有效。
- 用明确的 **grouping 指标** 证明语义分组合理。
- 在方法上突出 novelty：通过 **双向运行** 同时恢复促进机制和抑制机制，再把它们合成为一个 signed decision circuit。

一句话概括：最终要交付的是一个 **可验证的 signed circuit + 可信的功能语义分组 + 对应的验证链条**。

## 2. 当前情况

### 2.1 已有基础

- 主项目已经有一套可运行的双向分析流程，并产生过 signed circuit、group-level suff/nec、token flip、family mediation 等结果。
- 当前结果已经说明：模型的决策不是单向 promote circuit，而更像是共享子系统上叠加促进/抑制偏置。
- 已有报告、图和脚本主要集中在 `results/11-22-45-bidirectional_approxy/` 下。

### 2.2 当前主要问题

根据最新讨论，现有版本至少有以下三个核心问题：

1. **语义分组不够强，也不够“功能化”**
   - 现在的 `backbone / bias / tail` 更像结构描述，不是最终应使用的语义解释。
   - 需要把结构信息降为辅助信息，把最终叙事改成功能分组，例如：
     - promoting readers
     - suppressing readers
     - promoting routers / mediators
     - suppressing routers / mediators
     - promoting writers
     - suppressing writers
     - shared integrators / arbitration modules
   - 分组方式需要参考 [Answer.md](/root/autodl-tmp/project/Answer.md) 的思路：联合 read pattern、write pattern、causal role 来定义，而不是只按几何位置或聚合来源命名。

2. **目标函数需要从 logit difference 升级到 KL**
   - 直接用两个标量 logit 差值作为目标过于粗糙。
   - 下一版主目标应改成 clean / corrupt 两个方向在首个生成位置上的 **KL divergence** 或其对称变体，用来度量“整个 next-token 分布”而不是单个 token 标值差。

3. **方法比较还不够**
   - 当前主结果主要来自现有 pipeline 的 ACDC-style 局部化流程。
   - 还没有把 `EAP-IG`、`feature-circuits`、`RelP` 三种方法桥接进同一任务与评估框架。
   - 缺少“同一任务、同一数据、同一验证标准”下的方法对照。

## 3. 数据、环境与系统配置

### 3.1 数据

- 当前最新数据集位于 `datasets/clean/` 与 `datasets/corrupt/`。
- 最新计数为：
  - `clean`: 1722
  - `corrupt`: 1722
- 因此后续所有实验都应以 **1722 对样本** 为准，而不是旧版 1189。

### 3.2 环境

- Conda 环境：`base`
- Python：`3.12.3`
- Python 路径：`/root/miniconda3/bin/python`
- Pip 路径：`/root/miniconda3/bin/pip`

### 3.3 硬件

- GPU：`NVIDIA GeForce RTX 4090 D`
- 显存：`24GB`
- Driver：`580.76.05`
- CUDA：`13.0`

## 4. 主项目接下来必须改进的部分

### 4.1 目标函数改造：从 logit gap 到 KL objective

需要统一把双向目标重写为分布级目标。建议至少实现以下两个版本：

- `KL_tool`: clean 分布相对 corrupt 分布的 KL，在 `<tool_call>` endpoint 上定义
- `KL_no_tool`: clean 分布相对 corrupt 分布的 KL，在 no-tool endpoint 上定义

进一步可选：

- symmetric KL
- Jensen-Shannon divergence

要求：

- 明确记录使用的是首个生成位置的 logits 分布
- 明确记录 softmax 温度与 masking 规则
- 保持 forward / reverse 两个方向定义完全对称

### 4.2 语义分组重构：功能优先，结构辅助

要把当前分组体系升级成两层：

1. **最终展示层：功能语义组**
   - tool-schema readers
   - user-query readers
   - suppression readers
   - promotion routers / mediators
   - suppression routers / mediators
   - tool-call writers
   - no-tool writers
   - arbitration / integrator nodes

2. **内部分析层：结构辅助标签**
   - shared support
   - forward-only support
   - reverse-only support
   - overlap / tail / bridge

要求：

- 最终 PPT 和 paper 叙事以功能组为主，不以 `backbone` 为主。
- 结构标签只作为“这些功能节点来自哪里”的辅助信息。

### 4.3 语义分组证据链补强

必须补以下直观证据：

- **Attention heatmap**：说明 head 在读什么
- **Logit lens / residual trajectory**：说明节点在把表示往哪个 token / mode 上推
- **Causal validation**：说明这个组 patch 后真的改变行为
- **Group ablation / leave-one-group-out**：说明该组对整体 circuit 是必要的

还要进一步细化 head / MLP 的角色，不再停留在泛化标签上。

### 4.4 电路 faithful 性验证补强

对 final circuit 需要至少补齐以下验证：

- full-circuit sufficiency
- full-circuit necessity
- leave-one-node-out necessity
- leave-one-edge-out necessity
- leave-one-group-out necessity
- behavioral top-1 flip
- distributional KL recovery

说明：

- 不仅要看 margin 或 ratio，还要看分布级恢复。
- 最终 faithful 性应由“因果恢复 + 行为翻转 + 分布恢复”共同支撑。

### 4.5 方法比较框架统一

主项目需要提供一个统一评估接口，供三种外部方法接入：

- `EAP-IG`
- `feature-circuits`
- `RelP`

统一内容至少包括：

- 同一数据集
- 同一 forward / reverse 任务定义
- 同一 KL objective
- 同一 circuit 输出格式
- 同一 semantic grouping 流程
- 同一 validation 指标

## 5. 建议实施顺序

### 阶段 A：主项目方法升级

1. 把当前 objective 改写成 KL 版本。
2. 重跑双向主流程，得到新的 signed circuit 候选。
3. 基于 `Answer.md` 重构功能语义分组。
4. 补 attention heatmap 与 logit-lens 风格图。

### 阶段 B：faithfulness 与 grouping 验证

1. 对 final circuit 做 suff / nec / top-1 flip / KL recovery。
2. 对每个语义组做 group-level suff / nec。
3. 做 leave-one-group-out 与 family mediation。
4. 输出更直观的表和图。

### 阶段 C：方法扩展与对照

1. 把 EAP-IG 接进同一任务。
2. 把 feature-circuits 接进同一任务。
3. 把 RelP 接进同一任务。
4. 对比三种方法与当前 baseline：
   - faithfulness
   - sparsity
   - semantic coherence
   - runtime / GPU cost

## 6. 最终交付标准

主项目最终应该交付以下结果：

- 一个 final faithful signed circuit
- 一套功能优先的 semantic grouping
- 对 circuit 的 sufficiency / necessity / behavior / KL 验证
- 对 grouping 的 read / write / causal 验证
- 一套可视化：
  - circuit graph
  - attention heatmap
  - logit-lens or trajectory figure
  - suff/nec heatmap
  - node / edge importance
- 一个能支撑汇报与论文的故事线：
  - 双向方法如何发现促进与抑制
  - 为什么这种方法比单向更 faithful
  - 为什么功能语义分组是合理的
