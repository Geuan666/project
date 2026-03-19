# 模块级节点功能证据工具箱

## 这份笔记要回答什么

这份笔记只回答一个问题：

**当我们说“某个 attention head 或某个 MLP 有某种机制功能”时，究竟需要什么证据和什么工具来证明？**

这里的重点不是“节点重要不重要”，而是：

- 它读了什么
- 它写了什么
- 它怎样影响下游
- 它是否真的是某个模块的一部分

## 重点参考了哪些论文

- [prop-logic-transformer-circuit/paper/main_ArXiv.tex](/root/autodl-tmp/project/survey/references/prop-logic-transformer-circuit/paper/main_ArXiv.tex)
- [Which Attention Heads Matter for  In-Context Learning?/main.tex](/root/autodl-tmp/project/survey/references/Which Attention Heads Matter for  In-Context Learning?/main.tex)
- [How does GPT-2 compute greater-than copy/gpt2-years.tex](/root/autodl-tmp/project/survey/references/How%20does%20GPT-2%20compute%20greater-than%20copy/gpt2-years.tex)
- [Interpretability in the Wild: a Circuit for/sections/methods.tex](/root/autodl-tmp/project/survey/references/Interpretability%20in%20the%20Wild:%20a%20Circuit%20for/sections/methods.tex)
- [Interpretability in the Wild: a Circuit for/sections/experimental_validation.tex](/root/autodl-tmp/project/survey/references/Interpretability%20in%20the%20Wild:%20a%20Circuit%20for/sections/experimental_validation.tex)

## 从这些论文里学到的核心结论

### 1. 最硬的证据通常还是 patching

这一点在几篇论文里都很一致。

- `prop-logic` 用 QUERY-based patching 先找到头，再用 Q/K/V 子组件 patching 细分头的职责。
- `greater-than` 用 path patching 找路径，并用 path patching 验证电路的充分性和必要性。
- `Which Attention Heads Matter` 用 task-conditioned mean activation patching 定义 function vector score，本质上也是一种因果干预。
- `IOI` 用 activation patching、path patching、knockout、mean ablation 来验证节点和电路。

这类证据强，是因为它直接回答：

- 改这个节点，行为会不会变
- 改这个节点的哪一部分，行为会不会变
- 这个节点是不是通过某条路径影响后面

### 2. attention heatmap 很有用，但只能当“读入证据”或“辅助证据”

`prop-logic` 大量使用 attention statistics 去支持：

- queried-rule locating head 确实在看规则位置
- fact-processing head 确实在看事实区
- decision head 确实在看正确答案 token

但它并没有把 heatmap 当成单独证据闭环，而是总和 patching 放在一起。

所以 heatmap 的正确定位是：

- 它能帮助解释“它在看哪里”
- 但不能单独证明“它因此做了什么”

### 3. logit lens 很适合说明“写出了什么”

`greater-than` 这篇最典型。

它用 logit lens 去说明：

- attention head 输出在 unembedding 空间里更像“把起始年份写出来”
- 某些 MLP 输出更像“把大于起始年份的年份集合写出来”

这类证据的好处是很直观：

- 你能看到某个节点在把哪类 token 顶上去
- 很适合回答“writer”类问题

但它的局限也很清楚：

- 它更多是解释输出方向
- 不直接说明这个方向是不是对行为真的有因果作用

所以 `greater-than` 也专门补了 direct effect 分析，去证明 logit lens 看到的东西不是假象。

### 4. 方向向量 / steering 是非常值得重视的一类证据

这类证据在我们的项目里尤其重要。

`prop-logic` 在小模型部分明确做了这件事：

- 先在某个位置发现一个 routing direction
- 再通过加减这个方向，观察后续注意力模式和最终输出是否翻转

它的价值在于：

- 它不只是“发现一个方向存在”
- 而是直接测试“沿这个方向改动，会不会让模型切换到另一种内部路线”

对我们的 `Output-Route Decision` 来说，这种证据非常关键，因为我们正好要证明：

- 模型内部存在一个“输出路线决定”状态
- 这个状态可以被写入、被擦除、被注入
- 后续的 construction 和 suppression 都依赖它

### 5. 线性 probe 很有用，但只能证明“信息在这里能被读出来”

`prop-logic` 在多个位置用 affine classifier / linear probe 去说明：

- 某层某位置已经能线性读出答案
- 某层某位置能线性读出 LogOp 信息
- 某两个 head 拼起来能线性读出两个关键起点

这类证据能回答：

- 某个状态是不是已经在线性可读层面出现了

但不能单独回答：

- 模型是不是靠这个状态真的在做事

所以 probe 最好配合 patching 或向量干预一起用。

### 6. 只做 ablation 不够，要控制混淆

`Which Attention Heads Matter` 给了一个很重要的方法论提醒：

- 不能只看“去掉这类头以后性能掉没掉”
- 因为不同机制之间可能相关

他们用了 exclusion ablation 去控制：

- ablate induction heads 时，排除 FV 头
- ablate FV heads 时，排除 induction 头

这个思路对我们也很重要，因为我们后面很容易遇到：

- 一个节点既像 Integration，又像 Decision
- 一个头既读开头要求，也参与 Tool-Call Construction

如果不控制相关性，就会很容易把“伴随出现”误当成“真正负责”。

### 7. 电路级验证要和节点级解释分开

`IOI` 和 `greater-than` 都很强调这点。

节点功能解释解决的是：

- 这个节点在做什么

电路验证解决的是：

- 这一组节点放在一起，能不能恢复行为
- 拿掉这一组节点，行为是不是垮掉

所以后面我们的实验应该分两层：

- 节点级功能证据
- 模块级和电路级 faithful 验证

## 工具清单

| 工具 | 主要回答什么 | 证据强度 | 典型参考 | 适合我们什么问题 |
| --- | --- | --- | --- | --- |
| activation patching / path patching | 这个节点或路径是否真的因果相关 | 很强 | `prop-logic`, `greater-than`, `IOI` | 找节点、找边、验证模块 |
| Q/K/V/Z 子组件 patching | 节点是靠读、写、路由中的哪一部分起作用 | 很强 | `prop-logic` | 区分 read / write / move |
| mean ablation / knockout | 去掉这类节点以后行为是否下降 | 强 | `Which`, `IOI` | 模块级必要性、头集比较 |
| exclusion ablation | 控制不同头集相关性后的真实作用 | 强 | `Which` | 避免把相关机制混在一起 |
| attention heatmap / attention statistics | 节点在看哪里 | 中等 | `prop-logic`, `IOI` | Integration 和读取类头 |
| logit lens | 节点在把什么 token 或方向写强 | 中等 | `greater-than` | Construction / Suppression / Writer |
| direct effect on logits | 节点对最终输出的直接写入作用 | 强 | `greater-than`, `IOI` | 判断 writer 和 suppressor |
| residual projection / direction projection | 节点是否沿某个目标方向写入状态 | 强 | 我们自己的方向实验 | Output-Route Decision |
| direction vector injection / erasure | 某个方向是否真能驱动机制翻转 | 很强 | `prop-logic` 小模型路由方向 | 决策状态、路由状态 |
| linear probe / affine classifier | 某种信息是否已在该层线性可读 | 中等 | `prop-logic` | 决策状态何时出现 |
| stagewise trajectory | 最小差异在哪层开始、在哪层放大 | 中等到强 | `prop-logic`, 我们已有结果 | Decision 模块形成过程 |
| sufficiency / necessity / completeness / minimality | 模块或电路整体是否 faithful | 很强 | `greater-than`, `IOI` | 最终主图验证 |

## 这些工具分别能给出什么样的结论

### 1. patching

适合得出的句子：

- “patch 这个节点后，首个输出词显著向 `<tool_call>` 翻转，因此它对 tool 路线有因果作用。”
- “只 patch Q 有效，patch V 无效，因此它更像在改变读取而不是直接写出。”
- “这条边的 mediated effect 很高，因此它不是并列相关，而是实际传递路径的一部分。”

不适合单独得出的句子：

- “它在语义上就是某种抽象决策器。”

### 2. attention heatmap

适合得出的句子：

- “这个头主要看开头要求词和文件名。”
- “这个头在 decision row 上明显偏向工具格式示例。”

不适合单独得出的句子：

- “所以它负责把模型推向 `<tool_call>`。”

### 3. logit lens / direct effect

适合得出的句子：

- “这个节点把 `<tool_call>` 方向写强。”
- “这个节点更像是在抬高 `no_tool`，而不是直接写 `<tool_call>`。”

不适合单独得出的句子：

- “所以它一定是上游读取模块的一部分。”

### 4. direction vector / steering

适合得出的句子：

- “这个方向一旦注入，就会把模型推向工具路线。”
- “擦除这个方向后，下游 construction 链明显变弱，因此这是真正的中间状态，而不是表面相关。”

这是最适合 `Output-Route Decision` 的工具之一。

### 5. linear probe

适合得出的句子：

- “到这一层，这个状态已经线性可读。”

不适合单独得出的句子：

- “模型就是靠这个状态在工作。”

## 对我们项目最重要的几类工具

### A. Output-Route Decision

这个模块最该优先用：

1. **方向向量干预**
2. **残差投影**
3. **patching 到下游模块**
4. **模块级充分性和必要性**
5. **线性 probe**

原因：

- 这个模块的核心不是“它看哪里”
- 而是“它有没有形成一个稳定的路线状态，并把后面两条路分开”

所以这里 heatmap 不是主角，方向向量和因果干预才是主角。

### B. Instruction Integration

这个模块最该优先用：

1. **attention heatmap**
2. **Q/K patching**
3. **局部 counterfactual surgery**
4. **到 Decision 模块的 transmission patching**

原因：

- 这个模块的核心是“分散在 prompt 里的线索怎么被绑在一起”
- 所以最关键的是读取证据和信息整合证据

### C. Tool-Call Construction

这个模块最该优先用：

1. **patching**
2. **logit lens / direct effect**
3. **attention heatmap**
4. **stagewise trajectory**

原因：

- 这里既要证明“看了文件名、函数体、调用格式”
- 也要证明“真的把这些东西写向 `<tool_call>`”

### D. Tool-Call Suppression

这个模块最该优先用：

1. **patching**
2. **projection to `no_tool` and `<tool_call>` directions**
3. **direct effect**
4. **stagewise suppression trajectory**

原因：

- 这个模块最关键的是分清楚：
  - 是在抬高 `no_tool`
  - 还是在压低 `<tool_call>`
  - 还是两者同时发生

## 我们应该采用的标准证据包

以后如果要在主文里说“节点 X 属于模块 Y，并且有功能 Z”，最好至少给出下面 4 类证据中的 3 类。

### 标准证据包 1：读入证据

回答：

- 它读了什么

可用工具：

- attention heatmap
- decision-row
- top token / top span
- Q/K patching
- 专门设计的 counterfactual prompt

### 标准证据包 2：写出证据

回答：

- 它写了什么

可用工具：

- logit lens
- direct effect
- residual projection
- 对目标方向的增减量

### 标准证据包 3：传递证据

回答：

- 它怎样影响下游

可用工具：

- path patching
- per-edge mediated effect
- 子组件 patching
- 下游节点变化

### 标准证据包 4：行为验证证据

回答：

- 它对最终行为是否真的必要或足够

可用工具：

- 单节点或节点组 patching
- mean ablation
- exclusion ablation
- module-level sufficiency / necessity

## 对 Codex 的具体规范

后面做机制分析时，默认遵守下面这些规则。

1. **不要只用一个工具就下结论。**
   例如，只看 attention heatmap 不能说节点有某种功能。

2. **优先用因果证据给节点定性。**
   patching、ablation、direction intervention 的优先级最高。

3. **读入和写出要分开证明。**
   “看了哪里”和“把什么写出来”不是一回事。

4. **probe 只能当辅助证据。**
   线性可读不等于模型真在用。

5. **metric 必须和任务目标对齐。**
   `Which Attention Heads Matter` 说明了，指标选错会得出错结论。

6. **要控制相关性和混淆。**
   如果两个头集高度重合，不能直接比较它们的 ablation 效果。

7. **模块验证和节点解释要分层写。**
   节点功能、模块功能、电路 faithful 验证是三件不同的事。

## 对我们现有结果的直接启发

下面这些现有结果，已经对应到上面的几类工具，可以直接复用：

- [head_span_attention_summary.csv](/root/autodl-tmp/project/experiment/results/legacy/final/data/head_span_attention_summary.csv)
  这是读取证据库，适合 `Instruction Integration` 和部分 `Tool-Call Construction`。

- [head_qkv_patch_summary.csv](/root/autodl-tmp/project/experiment/results/legacy/final/data/head_qkv_patch_summary.csv)
  这是 attention 头子组件因果证据，适合区分读、写、路由。

- [query_decision_summary.json](/root/autodl-tmp/project/experiment/results/legacy/final/data/query_decision_summary.json)
  这是 construction 和 suppression 两条链的阶段式 rescue 证据。

- [delivery_object_direction_summary.json](/root/autodl-tmp/project/experiment/results/legacy/final/data/delivery_object_direction_summary.json)
  这是方向向量和投影类证据，最适合 `Output-Route Decision`。

- [l2h14_mlp11_component_summary.csv](/root/autodl-tmp/project/experiment/results/legacy/final/data/l2h14_mlp11_component_summary.csv)
  这是 bridge 和子组件作用证据，适合看早期读取怎样进入后续模块。

- [suppression_summary.json](/root/autodl-tmp/project/experiment/results/legacy/final/data/suppression_summary.json)
  这是 suppressive 路线的模块化证据入口。

## 目前我对工具优先级的判断

如果只按“对我们这篇论文后面最值得投入”的优先级排，我会这样排：

1. **patching / path patching / direction intervention**
2. **residual projection / direct effect**
3. **attention heatmap**
4. **Q/K/V/Z 子组件 patching**
5. **linear probe**
6. **module-level sufficiency / necessity**

如果只按“最适合 `Output-Route Decision`”排：

1. **方向向量注入与擦除**
2. **残差投影**
3. **到 construction / suppression 的路径 patching**
4. **模块级充分性和必要性**
5. **线性 probe**

## 一句话总结

**一个节点有没有某种功能，最硬的证据永远是因果干预；attention heatmap 主要用来说明它在看什么，logit lens 主要用来说明它在写什么，方向向量和残差投影最适合说明中间状态是否真的存在并驱动后续模块。**
