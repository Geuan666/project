# 论文大纲

## Abstract [0.3P]

- 一句话 setting + 一句话核心问题
- 方法：双向电路定位
- 发现：四模块机制（整合 → 决策 → 构造 vs 抑制），同时强调我们针对最核心的决策模块进行了feature-level的探究
- 结果：train/test 泛化 + 跨尺寸一致性

---

## I. Introduction [1P]

- 背景与动机：工具调用是 Agent 的核心能力，但模型内部如何决定调用工具几乎没有被研究过。
- 核心现象：只改 prompt 开头一个动词，首个输出 token 就在 `<tool_call>` 和普通回答之间翻转。
- **[Figure 1: Overview 总图]** 集成 Insight、Data、Method、Circuits、Results 五部分，占据显眼位置。
- 本文贡献（3–4 条）。

---

## II. Data & Model Setting [1P]

- **真实场景数据构造**：采用 Qwen3 原生工具调用 Template + Langgraph Agent 框架。借助 GPT-5.2 从 HumanEval、MBPP、APPS、CodeContests 中深度清洗提取 1700+ 条函数体补全任务。
- **多样性与控制变量**：clean / corrupt 各 15 条专用谓语随机构造；两集仅有开头几个 token 差异，完美控制自变量。
- **数据划分**：按 lang × verb 分层随机划分 70% train / 30% test（seed=42），消除过拟合；评估指标仅需观测下一个 token 是否为 `<tool_call>`。
- **模型选择（Why Qwen3）**：架构新、参数规模多样（1.7B / 4B / 8B / 14B）；具有原生 `<tool_call>` token 且工具调用能力强；完美适配 TransformerLens 且有现成 Transcoder。**主文以 Qwen3-1.7B 为主演示，其余尺寸结果见附录 D。**

→ **附录 A**：数据构造流程、语言/动词分布、样本示例

---

## III. Methodology & Global Circuit [1P]

- **[Figure 2: 方法与电路对比图]** 左侧展示寻路方法论，右侧展示最终 24 节点 / 64 边的全局电路。
- **第一段**：精炼介绍电路发现方法（具体方法待定）。
- **第二段**：解释双向（Bidirectional）机制——同时找到促进链和抑制链，使电路更 faithful。
- 一句话交代 train/test 分离设计：电路在 train 集上发现，所有指标同时报告 train 和 test 数字。
- **第三段**：提供具体的电路寻找和验证结果

→ **附录 B**：方法详细定义 + 不同方法对比表 + 双向 vs 单向 faithfulness 对比

---

## IV. Deep Dive into Four Modules [4.5P - 核心篇幅]

### 模块 1：Instruction Integration [1P]

- 这一节证明：模型在做路线决策之前，先把开头要求、函数体、文件名和任务描述整合成统一状态。
- **Span Patching → 注意力头热图**：展示哪些头在跨 span 绑定信息（如 `L2H14` 的早期入口、`L11H5` 的 MLP11 交接）。
- **[Figure 3: Attention Head Span Heatmap]**
- **Span Knockout 因果验证**：消除特定输入 span 后，MLPX route score 显著下降(或者probe结果下降)，证明整合确实发生。
- 结论：待定

### 模块 2：Output-Route Decision [1.5P]

- 这一节证明：中间层形成稳定的输出路线状态，并分叉传给两条竞争分支。

- **证据一（区分能力）**：定义 route score，在 MLP11 / MLP16 / MLP19 上 AUC 均 > 0.99；可结合 Probing 证实该特征可被线性解码。
  - **[Figure 4: Route Score AUC + Probing 对比]**

- **证据二（状态递进）**：三个锚点的 route score 逐层放大且方向不共线（余弦 < 0.05），说明是逐层重编码而非固定向量搬运。
  - **[Figure 5: 状态层层递进演化图]**

- **证据三（MLP 稀疏分析）**：用 Transcoder 分解关键 MLP（MLP11 / MLP17），从 feature-level 展示具体哪些稀疏特征驱动路线决策。
  
→ **附录 C**：Score 定义细节、Probing 方法论、Transcoder feature-level 详细分析

### 模块 3：Tool-Call Construction [1P]

- 这一节证明：工具路线占优后，模型如何把 `<tool_call>` 逐步组装出来。

- **Logit Lens 逐层分析**：展示 `<tool_call>` token 的 logit 在各层的演化轨迹。
- **Stagewise 重建**：从 corrupt 基线逐步 patch 节点，`<tool_call>` top1 从 0% → 4.3% → 14.6% → 48.9% → 85.9% → 92.8% → **97.9%**。
  - **[Figure 6: Construction Stagewise Trajectory]**
- **关键注意力头展示**：`L21H1` vs `L21H12` 的分支比较，说明不是简单冗余。

### 模块 4：Tool-Call Suppression [1P]

- 这一节证明：直接回答路线不是被动缺席，而是主动写强 `no_tool` 并压制工具链。

- **Logit Lens 逐层分析**：展示 `no_tool` 相关 token 的 logit 演化。
- **Stagewise 抑制**：逐步注入抑制节点，no-tool top1 从 1.0% → 29.9% → **79.0%**。
  - **[Figure 7: Suppression Stagewise + Downstream Heatmap]**
- **MLP17 双向写出**：同时抬高 `no_tool` 并压低 `<tool_call>`，且反向干扰 construction 区全部节点。

> **每个模块末尾**：一行文字报告 test 集验证数字（如 "On held-out test set (499 samples), +MLP27 achieves 97.2% top-1 (train: 97.9%)"）。

---

## V. Related Work [0.6P]

- **Circuit Discovery 方法**：Activation Patching、Attribution Patching、ACDC、EAP-IG 等。
- **Agent 与工具调用**：Agent 框架、工具调用能力评测、代码生成任务。

---

## VI. Conclusion [0.4P]

- 总结核心发现：四模块竞争机制。
- 贡献：首次对工具调用决策做模块级机制解释，并且对关键模块进行了feature-level的探测。
- 局限：单一模型家族、工作的应用价值不明显。
- 未来方向：跨架构泛化、feature-level 深入、更复杂工具调用场景。

---

## 附录结构

| 附录 | 内容 | 预估篇幅 |
|---|---|---|
| **A** | 数据构造流程、语言/动词分布表、样本示例 | 3P |
| **B** | 电路发现方法详细定义 + 不同方法对比表 + 双向 vs 单向 faithfulness 对比 | 3P |
| **C** | Route Score 定义细节、Probing 方法论、Transcoder feature-level 详细分析 | 3P |
| **D** | 跨尺寸泛化（4B / 8B / 14B 结果）+ Train/Test 对比总表 | 6P |
