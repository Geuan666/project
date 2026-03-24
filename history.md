# 项目历史

## 1. 数据构造与问题设定

这个项目的起点不是一般的工具调用分析，而是一个非常刻意的数据构造：在每一对样本中，只改用户提示开头的一个动词或一个很短的词组，其余主体内容尽量保持不变。

当前保留的数据入口在 [experiment/datasets](/root/autodl-tmp/project/experiment/datasets)。这批数据有几个关键特征：

- `1700+` 对 clean/corrupt 样本。
- 使用 Qwen 原生工具调用格式。
- 关闭 thinking 模式。
- 当前统一使用的模型是 `/root/autodl-tmp/Qwen/Qwen3-1.7B`。
- 每对样本只有首个 user prompt 的一个动词或短词组不同。
- `clean` 会把首个输出词推向 `<tool_call>`。
- `corrupt` 不会把首个输出词推向 `<tool_call>`，而是落到普通回答一侧。

这批数据的重要性，不是再去证明“第一词很重要”，而是给了我们一个非常干净的最小干预接口：

> 只改开头要求的一小段，首个输出词就会翻转。

也正因为这个接口足够干净，我们才有机会追问：模型内部到底是如何把这么小的提示差异，逐层放大成最终的工具调用决策的。

## 2. 电路定位、方法创新与电路验证

在有了成对数据以后，项目进入第二阶段：寻找真正负责这类翻转现象的电路。

这部分工作并不是只依赖一种方法，而是结合了多种差分和因果工具去聚合电路，包括但不限于：

- Path Patching
- EAP-IG
- 头、MLP、边级别的补丁与干预
- 聚合式电路筛选
- 结构和行为层面的验证

项目在这里做出的关键方法创新，是**双向反转**。

以前的很多电路定位工作，天然更容易找到“促进某个目标输出”的那条线，但不容易把真正的抑制路线也找完整。这里我们采用了双向做法：

- 可以把 `<tool_call>` 一侧当作 clean 来找促进工具调用的部分；
- 也可以反过来把 `<tool_call>` 一侧当作 corrupt，去找压制工具调用、推动 `no_tool` 的部分。

这个设计带来的直接好处是：

- 不只找到促进线；
- 也能找到抑制线；
- 还能找出两边共享的部分；
- 最终得到的电路更 faithful，更接近真实决策过程。

目前已经得到并保留的核心结果是：

- 最终 signed circuit：`24` 个节点、`64` 条边。
- 该电路通过了充分性和必要性层面的验证。
- 当前正式结果包保存在 [experiment/results/legacy/final](/root/autodl-tmp/project/experiment/results/legacy/final)。
- 为了后续模块化重构，`legacy` 目录目前只保留仍有直接参考价值的主结果包，以及最小的 raw provenance：`experiment/results/legacy/final/archive/raw_runs/13-01-39-final-kl`。
- 对应代码入口主要在 [experiment/code/src](/root/autodl-tmp/project/experiment/code/src) 和 [experiment/code/scripts](/root/autodl-tmp/project/experiment/code/scripts)。

如果只从“找到 faithful circuit”这个角度看，这个项目其实已经足够形成一篇论文。但目前的问题不是电路对不对，而是叙事和机制解释还没有完全收束。

## 3. 机制假说、现有高价值实验与重构理由

在找到电路并验证之后，项目进入第三阶段：试图解释电路中的节点和边，到底在做什么。

过去这一阶段已经积累了非常多实验，也留下了很多结果文件。它们并不是没价值，恰恰相反，其中很多都很关键，但目前的主要问题是：

- 实验太多；
- 命名体系不统一；
- 叙事链条不够收束；
- 结果虽然多，但还没有完全组织成一个论文级的整体机制。

经过前面的讨论，现在新的总机制假说已经收束为 4 个模块：

1. `Instruction Integration`
2. `Output-Route Decision`
3. `Tool-Call Construction`
4. `Tool-Call Suppression`

### 当前机制猜想（英文）

> Before generating the first output token, the model first performs Instruction Integration, combining the opening request with the function-body phrase, the filename, and the remaining task description into a unified representation of what kind of answer is being asked for. It then enters an Output-Route Decision stage, where this integrated instruction state is converted into a stable internal choice between a tool-mediated output route and a direct-response route. If the decision favors the tool route, a Tool-Call Construction mechanism organizes filename cues, function-body content, and call-format structure to push the first token toward `<tool_call>`. If the decision favors the direct-response route, a competing Tool-Call Suppression mechanism strengthens the no-tool state while actively inhibiting the tool-calling pathway. In this view, tool use is not treated as an isolated yes-or-no switch, but as the outcome of a broader decision about how the answer should be produced and delivered.

对应的中文理解是：

> 模型先把开头要求、函数体、文件名和后半段说明放在一起理解；随后形成“接下来应该走哪条输出路线”的稳定内部决定；如果决定走工具路线，后面的节点就组织文件名、函数体和调用格式，把首个输出词推向 `<tool_call>`；如果决定不走工具路线，另一条链就写强 `no_tool`，同时压住工具调用路线。

这一部分现阶段最有价值、应该保留并继续利用的材料主要有：

### 3.1 正式结果包

- [experiment/results/legacy/final/docs](/root/autodl-tmp/project/experiment/results/legacy/final/docs)
- [experiment/results/legacy/final/data](/root/autodl-tmp/project/experiment/results/legacy/final/data)
- [experiment/results/legacy/final/figures](/root/autodl-tmp/project/experiment/results/legacy/final/figures)

这里面包含当前主文档、图索引、数据索引、最终电路表、功能分组表、机制证据表等，是后续重构时最需要持续参考的正式出口。

### 3.2 机制相关高价值实验

下面这些实验结果虽然当前叙事还不够整齐，但都非常有价值，应作为重构时的重点保留材料：

- earliest reader 相关实验  
  说明最早的提示读取从哪里开始，以及它和后续稳定状态之间的关系。
- `MLP11 -> MLP16 -> MLP19` 方向编辑与桥接实验  
  这是当前支撑“中间稳定状态/决策模块”的最强证据之一。
- suppressive chain 相关实验  
  支撑 `L16H4 -> MLP17 -> L23H6` 这一条路不只是相关，而是真的在推动 `no_tool` 并干扰工具路线。
- 最终 signed circuit、功能分组、家族分组、层轨迹等实验  
  它们帮助我们理解哪些节点是主干、哪些是偏置、哪些是辅助。

### 3.3 注意力头专项实验

注意力头这一块尤其值得保留。

当前已经完成一次全量聚合实验，结果位于：

- [experiment/results/attentionhead/20260319-121000-attention-head-full](/root/autodl-tmp/project/experiment/results/attentionhead/20260319-121000-attention-head-full)

这部分实验已经覆盖：

- `1722` 个样本；
- `448` 个注意力头；
- `mass` 和 `density` 两个指标；
- 每个头的 `10x10` span heatmap；
- 每个头的 decision-row 图；
- 以及后续自动分析产物。

这一块的价值在于，它让我们第一次能系统地看清：

- 哪些头在看开头要求；
- 哪些头在看文件名、函数体和后半句说明；
- 哪些头在靠近 `<tool_call>` 组装；
- 哪些头在参与 suppressive 路线。

哪怕其中一些结果暂时还没有完全写进主叙事，它们也已经构成后续模块分析的重要证据库。

## 4. 为什么现在要重构

现在重构不是因为项目没有结果，而是因为项目已经有了太多结果，但它们还没有被放进一个足够清楚、足够统一、足够适合人和 Codex 协作推进的结构里。

这次重构的目标可以概括为 3 句话：

- 保留真正有价值的代码、数据和结果；
- 用更统一的目录、文档和任务顺序重新组织它们；
- 让后面的工作直接围绕 4 个模块推进，而不是继续在旧实验堆里扩散。

因此，本轮采用的是“保留核心、明确分层”的整理方式：

- 正式保留的结果继续作为主叙事出口；
- 高价值但尚未完全收束的结果保留为参考；
- 更早期、近似性更强或主要服务过程记录的结果降级归档；
- 后续所有新工作，都直接围绕 4 个模块推进。

## 7. 数据分离与泛化验证

在完成 4 个模块的全量实验后，项目进行了一次关键的方法论升级：将全部 1722 对样本按 70/30 比例划分为 train 集和 test 集，在 train 集上重新从头发现电路，在 test 集上验证泛化性。

### 7.1 分层抽样

- 按 `lang`（Python/Java/C++）× `clean_candidate`（15 种 clean 动词）分层随机抽样。
- `seed=42`，保证可复现。
- 最终划分：**train 1223 对（71.0%）**、**test 499 对（29.0%）**。
- 每种语言、每种动词在 train/test 中的分布大致均匀。
- 元数据记录在 `experiment/datasets/split_summary.json`。

### 7.2 train 集上的重新发现

在 train 集上完整重跑了主流水线（前向挖掘、反向挖掘、双向分析、签名电路构建、因果验证）和全部 4 个模块分析。结果：

- signed circuit 拓扑完全不变：仍为 **24 个节点、64 条边**。
- 电路 KL recovery：promote 1.000、suppress 0.998。
- 四个模块的结论与全量实验完全一致，未出现任何节点增减或主链变化。

### 7.3 test 集上的泛化验证

这是本轮最关键的产出。在 test 集上，**用 train 集上学到的 route score 方向和电路结构**进行验证：

| 指标 | 全量 (1722) | Train (1223) | Test (499) | Train→Test Δ |
|---|---|---|---|---|
| R_module AUC | 0.9947 | 0.9946 | **0.9943** | 0.0003 |
| MLP11 Spearman | 0.770 | 0.773 | **0.762** | 0.011 |
| MLP16 Spearman | 0.855 | 0.855 | **0.843** | 0.012 |
| Construction +MLP27 top1 | 97.68% | 97.87% | **97.19%** | 0.68% |
| Suppression +L23H6 no-tool top1 | 78.28% | 78.99% | **78.16%** | 0.83% |

**所有核心指标在 test 集上的下降不超过 1%**，证明电路结构和 route score 方向不是对特定样本的过拟合，而是模型内部真实存在的稳定计算模式。

### 7.4 结果位置

- train 主流水线：`experiment/results/split/pipeline/`
- train 注意力头：`experiment/results/split/attentionhead/`
- train 模块 1–4：`experiment/results/split/{instruction_integration,output_route_decision,tool_call_construction,tool_call_suppression}/`
- test 验证：`experiment/results/split/test_validation/`
- 全量对比表：`experiment/results/split/split_comparison_summary.md`

### 7.5 范式转换

从这一步开始，项目正式转入 **Discovery / Validation 分离范式**：

- 所有后续新实验（包括模型 scale-up、模块补强等）都必须在 train 集上发现、在 test 集上验证。
- 论文中引用的所有数字必须同时报告 train 和 test。
- 旧的全量结果（`results/` 下不在 `split/` 内的目录）降级为历史参考。

## 5. 当前冻结下来的 4 个模块

经过这一轮模块化重构，现在 4 个模块都已经分别完成，并且每个模块都有自己当前应优先引用的结果包。

### 5.1 `Instruction Integration`

当前最稳的结论是：

- `L2H14` 提供最早的 opening-side ingress；
- `L11H5` 是进入 `MLP11` 的 main same-block handoff head；
- `L2H14 + L11H5` 构成最小两段式 ingress group；
- `MLP11` 是 `Instruction Integration` 的出口，同时也是 `Output-Route Decision` 的入口。

当前规范结果包：

- [experiment/results/instruction_integration/20260319-155729-instruction-integration-full](/root/autodl-tmp/project/experiment/results/instruction_integration/20260319-155729-instruction-integration-full)

### 5.2 `Output-Route Decision`

当前最稳的结论是：

- `MLP11 -> MLP16 -> MLP19` 实现逐层重编码的连续 `route score`；
- 这个模块决定的不是单个 token，而是“工具协议输出 vs 直接回答”的输出路线偏好；
- `MLP16 -> MLP17` 是 direct-answer / suppressive 一侧的强分叉边；
- `MLP19` 是 tool-side 的 late fanout hub，而不是单一瓶颈。

当前规范结果包：

- [experiment/results/output_route_decision/20260319-110839-output-route-decision](/root/autodl-tmp/project/experiment/results/output_route_decision/20260319-110839-output-route-decision)

### 5.3 `Tool-Call Construction`

当前最稳的结论是：

- `MLP19` 把 tool-route state 扇出到 construction 区；
- `L20H5` 是 construction ingress / payload binder；
- `L21H1` 与 `L21H12` 不是简单冗余，而是两条不同的 late routing；
- `L24H6` 更像 formatter / protocol commitment；
- `MLP27` 是主 writer；
- `MLP19 -> MLP27` 虽强，但当前只能写成 strong parallel receipt，不能强写成独立 bypass 主路。

当前规范结果包：

- [experiment/results/tool_call_construction/20260320-031957-tool-call-construction](/root/autodl-tmp/project/experiment/results/tool_call_construction/20260320-031957-tool-call-construction)

### 5.4 `Tool-Call Suppression`

当前最稳的结论是：

- `MLP16 -> MLP17` 是从 `Output-Route Decision` 进入 suppressive line 的强 fork edge；
- `L16H4` 是 suppressive reader / ingress；
- `MLP17` 是主 suppressive writer，既抬高 `no_tool`，也压低 `<tool_call>`；
- `L23H6` 更像 late suppressive relay，而不是主要 writer。

当前规范结果包：

- [experiment/results/tool_call_suppression/20260320-065246-tool-call-suppression](/root/autodl-tmp/project/experiment/results/tool_call_suppression/20260320-065246-tool-call-suppression)

## 6. 当前项目已经收束成什么样

到目前为止，这个项目已经不再缺“模块实验”，而是开始转向“总图和总叙事”的阶段。

现在最稳的统一主线是：

> 模型先通过 `Instruction Integration` 把开头要求、函数体、文件名和后半句说明整合起来；随后通过 `Output-Route Decision` 把这些信息压成连续的输出路线分数；如果 tool-route 一侧占优，状态就进入 `Tool-Call Construction`，被逐步组织成 `<tool_call>` 的首词偏好；如果 direct-answer 一侧占优，状态就进入 `Tool-Call Suppression`，被写成更强的 `no_tool` / 普通回答状态，同时压住 tool path。

因此，当前最重要的后续工作已经变成：

- 统一 4 个模块之间的边界节点和接口节点；
- 统一论文主文里的机制叙事；
- 统一总图、图注和结果段的表达；
- 在不破坏当前模块结论的前提下，继续清理旧脚本、旧结果和旧命名。
